#!/usr/bin/env python3
"""Baseball Card Valuation pipeline — Flask API + static UI."""

from __future__ import annotations

import base64
import io
import json
import os
import re
import threading
import time
import uuid
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, send_file, Response

from dev_log import (
    check_key,
    clear as clear_dev_log,
    human_tail,
    log as dev_log,
    log_exception,
    startup_note,
    stats as dev_log_stats,
    tail as dev_log_tail,
    LOG_FILE,
)

BASE_DIR = Path(__file__).resolve().parent
STAN_DIR = Path.home() / ".stan"
if str(STAN_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(STAN_DIR))

try:
    import drive_handoff
except ImportError:
    drive_handoff = None  # type: ignore

import billing

from scan_pipeline import (
    build_grade_response,
    build_lester_cheats,
    evaluate_gate,
    issue_gate_token,
    live_config,
    scan_record_from_grade,
    valuation_sandbox,
    verify_gate_token,
    consume_gate_token,
)

from collx_data import (
    auto_import_from_drive,
    CANONICAL_PATH,
    COLLX_CURRENT,
    discover_collx_csv_paths,
    ensure_inbox_layout,
    estimate_from_collx,
    fetch_and_import_collx,
    find_catalog_image,
    find_match,
    import_csv_text,
    load_catalog,
    load_meta,
    purge_test_cards,
    reimport_last_source,
    reset_collection,
    search_catalog,
    status as collx_status,
    audit_pipeline,
    tidy_inbox_after_import,
    valuation_from_price,
    COLLX_INBOX,
)

_collx_poll_started = False

DATA_FILE = BASE_DIR / "data" / "collection.json"
UPLOAD_DIR = BASE_DIR / "uploads"
THUMB_DIR = UPLOAD_DIR / "collx_thumbs"

app = Flask(__name__)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _load_collection() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_collection(cards: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2)


def _sum_valuations(cards: list[dict], field: str) -> float:
    total = 0.0
    for card in cards:
        val = card.get("valuation", {}).get(field)
        if val is not None:
            total += float(val)
    return round(total, 2)


def _find_card(card_id: str) -> dict | None:
    return next((c for c in _load_collection() if c.get("id") == card_id), None)


def _collection_totals(cards: list[dict]) -> dict[str, float | int]:
    priced = sum(1 for c in cards if c.get("valuation", {}).get("priced"))
    return {
        "count": len(cards),
        "priced_count": priced,
        "total_mid": _sum_valuations(cards, "estimate_mid"),
        "total_low": _sum_valuations(cards, "estimate_low"),
        "total_high": _sum_valuations(cards, "estimate_high"),
    }


def estimate_value(
    player: str,
    year: int,
    card_set: str,
    condition: str,
    rookie: bool = False,
    autograph: bool = False,
    card_number: str = "",
) -> dict:
    """CollX catalog only — no fabricated prices."""
    return estimate_from_collx(player, year, card_set, condition, rookie, autograph, card_number)


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return cleaned[:120] or "upload"


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index_baseball.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


def _safe_collx_id(collx_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", collx_id)[:64]


def _cache_collx_thumb(collx_id: str) -> Path | None:
    url = find_catalog_image(collx_id)
    if not url:
        return None
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    dest = THUMB_DIR / f"{_safe_collx_id(collx_id)}.jpg"
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "baseball-cards-collx/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        if len(data) < 100:
            return None
        dest.write_bytes(data)
        return dest
    except OSError:
        return None


@app.route("/api/collx/thumb/<collx_id>")
def collx_thumb(collx_id: str):
    path = _cache_collx_thumb(collx_id)
    if path and path.is_file():
        return send_from_directory(path.parent, path.name, mimetype="image/jpeg")
    url = find_catalog_image(collx_id)
    if url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "baseball-cards-collx/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            return Response(data, mimetype=resp.headers.get_content_type() or "image/jpeg")
        except OSError:
            pass
    return jsonify({"status": "error", "message": "Thumbnail not found."}), 404


@app.route("/api/collx/reimport", methods=["POST"])
def collx_reimport_route():
    result = reimport_last_source()
    if result.get("status") != "success":
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/brian/status")
def brian_status_route():
    try:
        import brian_os

        text = brian_os.read_brian_status()
        return jsonify({"status": "ok", "text": text, "summary": brian_os.brian_status_summary()})
    except ImportError:
        return jsonify({"status": "error", "message": "brian_os not available"}), 503


@app.route("/api/cards", methods=["GET"])
def list_cards():
    cards = _load_collection()
    totals = _collection_totals(cards)
    return jsonify(
        {
            "cards": cards,
            **totals,
            "collx": collx_status(),
        }
    )


@app.route("/api/cards", methods=["POST"])
def add_card():
    payload = request.get_json(silent=True) or {}
    player = (payload.get("player") or "").strip()
    year_raw = payload.get("year")
    card_set = (payload.get("set") or payload.get("card_set") or "Unknown").strip()
    condition = (payload.get("condition") or "near mint").strip()
    card_number = (payload.get("card_number") or "").strip()
    notes = (payload.get("notes") or "").strip()
    rookie = bool(payload.get("rookie"))
    autograph = bool(payload.get("autograph"))

    if not player:
        return jsonify({"status": "error", "message": "Player name is required."}), 400

    try:
        year = int(year_raw)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Valid year is required."}), 400

    if year < 1880 or year > datetime.now().year + 1:
        return jsonify({"status": "error", "message": "Year out of range."}), 400

    valuation = estimate_value(player, year, card_set, condition, rookie, autograph, card_number)
    match = find_match(player, year, card_set, card_number)
    card = {
        "id": str(uuid.uuid4())[:8],
        "collx_id": match.get("collx_id") if match else None,
        "match_key": match.get("match_key") if match else None,
        "player": player,
        "year": year,
        "set": card_set,
        "card_number": card_number,
        "condition": condition,
        "rookie": rookie,
        "autograph": autograph,
        "notes": notes,
        "image": payload.get("image") or (match.get("image_url") if match else None),
        "valuation": valuation,
        "created_at": _now(),
        "source": "manual",
    }

    cards = _load_collection()
    cards.insert(0, card)
    _save_collection(cards)
    return jsonify({"status": "success", "card": card})


@app.route("/api/cards/<card_id>", methods=["PUT"])
def update_card(card_id: str):
    payload = request.get_json(silent=True) or {}
    cards = _load_collection()
    idx = next((i for i, c in enumerate(cards) if c.get("id") == card_id), None)
    if idx is None:
        return jsonify({"status": "error", "message": "Card not found."}), 404

    card = cards[idx]
    player = (payload.get("player") or card.get("player") or "").strip()
    year_raw = payload.get("year", card.get("year"))
    card_set = (payload.get("set") or payload.get("card_set") or card.get("set") or "Unknown").strip()
    condition = (payload.get("condition") or card.get("condition") or "near mint").strip()
    card_number = (payload.get("card_number") or card.get("card_number") or "").strip()
    notes = (payload.get("notes") or card.get("notes") or "").strip()
    rookie = bool(payload.get("rookie", card.get("rookie")))
    autograph = bool(payload.get("autograph", card.get("autograph")))

    if not player:
        return jsonify({"status": "error", "message": "Player name is required."}), 400

    try:
        year = int(year_raw)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Valid year is required."}), 400

    valuation = estimate_value(player, year, card_set, condition, rookie, autograph, card_number)
    match = find_match(player, year, card_set, card_number)
    image = payload.get("image") or card.get("image")
    if not image and match:
        image = match.get("image_url")

    card.update(
        {
            "collx_id": match.get("collx_id") if match else card.get("collx_id"),
            "match_key": match.get("match_key") if match else card.get("match_key"),
            "player": player,
            "year": year,
            "set": card_set,
            "card_number": card_number,
            "condition": condition,
            "rookie": rookie,
            "autograph": autograph,
            "notes": notes,
            "image": image,
            "valuation": valuation,
            "updated_at": _now(),
        }
    )
    cards[idx] = card
    _save_collection(cards)
    return jsonify({"status": "success", "card": card})


@app.route("/api/cards/<card_id>", methods=["DELETE"])
def delete_card(card_id: str):
    cards = _load_collection()
    new_cards = [c for c in cards if c.get("id") != card_id]
    if len(new_cards) == len(cards):
        return jsonify({"status": "error", "message": "Card not found."}), 404
    _save_collection(new_cards)
    return jsonify({"status": "success"})


@app.route("/api/estimate", methods=["POST"])
def estimate_only():
    payload = request.get_json(silent=True) or {}
    player = (payload.get("player") or "").strip()
    if not player:
        return jsonify({"status": "error", "message": "Player name is required."}), 400
    try:
        year = int(payload.get("year"))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Valid year is required."}), 400

    valuation = estimate_value(
        player,
        year,
        (payload.get("set") or "Unknown").strip(),
        (payload.get("condition") or "near mint").strip(),
        bool(payload.get("rookie")),
        bool(payload.get("autograph")),
        (payload.get("card_number") or "").strip(),
    )
    return jsonify({"status": "success", "valuation": valuation})


@app.route("/api/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file provided."}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "message": "Empty filename."}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return jsonify({"status": "error", "message": "Image must be jpg, png, webp, or gif."}), 400

    filename = f"{uuid.uuid4().hex[:12]}_{_safe_filename(file.filename)}"
    dest = UPLOAD_DIR / filename
    file.save(dest)
    return jsonify({"status": "success", "image": f"/uploads/{filename}"})


def _phone_url(port: int = 8002) -> str:
    url_file = BASE_DIR / "PHONE_URL.txt"
    try:
        if url_file.is_file():
            text = url_file.read_text(encoding="utf-8").strip()
            if text.startswith("http"):
                return text
    except OSError:
        pass
    env_url = os.environ.get("BASEBALL_PHONE_URL", "").strip()
    if env_url.startswith("http"):
        return env_url
    return f"http://127.0.0.1:{port}"


def _qr_png_bytes(url: str) -> bytes:
    import qrcode

    buf = io.BytesIO()
    qr = qrcode.QRCode(version=None, box_size=8, border=3, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return buf.getvalue()


@app.route("/qr.png")
def qr_png():
    url = request.args.get("url") or _phone_url()
    return Response(_qr_png_bytes(url), mimetype="image/png")


@app.route("/qr")
def qr_page():
    url = request.args.get("url") or _phone_url()
    b64 = base64.b64encode(_qr_png_bytes(url)).decode("ascii")
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Baseball App QR</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #1a2744; color: #f5f0e1;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 100vh; margin: 0; padding: 1.5rem; text-align: center; }}
  img {{ background: #fff; padding: 12px; border-radius: 12px; max-width: 90vw; }}
  a {{ color: #c41e3a; font-size: 1.1rem; word-break: break-all; }}
  p {{ max-width: 28rem; line-height: 1.5; color: #ccc; }}
</style></head><body>
  <h1>Scan to open Baseball Cards</h1>
  <img src="data:image/png;base64,{b64}" alt="QR code">
  <p><a href="{url}">{url}</a></p>
  <p>Scan with your phone camera or Chrome. Keep this Chromebook awake.</p>
  <p><a href="/">Open app</a></p>
</body></html>"""
    return Response(html, mimetype="text/html")


@app.route("/manifest.json")
def manifest():
    return jsonify(
        {
            "short_name": "Baseball Cards",
            "name": "Baseball Card Valuation",
            "description": "CollX-powered collection with PSA precursor scan",
            "version": "1.0.0",
            "icons": [{"src": "/qr.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}],
            "start_url": "/",
            "background_color": "#0c1f3f",
            "theme_color": "#0c1f3f",
            "display": "standalone",
            "orientation": "portrait",
        }
    )


@app.route("/api/collx/status")
def collx_status_route():
    return jsonify({"status": "ok", **collx_status()})


@app.route("/api/collx/search")
def collx_search_route():
    q = (request.args.get("q") or "").strip()
    limit = min(int(request.args.get("limit", 25)), 100)
    return jsonify({"status": "ok", "results": search_catalog(q, limit=limit)})


@app.route("/api/collx/import", methods=["POST"])
def collx_import_route():
    mode = (request.form.get("mode") or "replace").strip().lower()
    if mode not in {"replace", "merge"}:
        mode = "replace"
    if "file" in request.files and request.files["file"].filename:
        text = request.files["file"].read().decode("utf-8", errors="replace")
        source = request.files["file"].filename
    else:
        body = request.get_json(silent=True) or {}
        text = (body.get("csv") or body.get("text") or "").strip()
        source = body.get("source") or "api"
    if not text:
        return jsonify({"status": "error", "message": "Upload a CollX CSV file or paste CSV text."}), 400
    ensure_inbox_layout()
    try:
        CANONICAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        CANONICAL_PATH.write_text(text, encoding="utf-8")
        source = str(CANONICAL_PATH)
    except OSError:
        pass
    result = import_csv_text(text, source=source, mode=mode)
    if result.get("status") != "success":
        return jsonify(result), 400
    if result.get("status") == "success" and "tidy" not in result:
        result["tidy"] = tidy_inbox_after_import(result.get("imported"))
    return jsonify(result)


@app.route("/api/collx/audit")
def collx_audit_route():
    """Garbage-in/garbage-out audit — Drive CSVs + Gmail attachment row counts (no import)."""
    try:
        audit = audit_pipeline()
        dev_log("api_collx_audit", verdict=audit.get("verdict"), client=request.remote_addr)
        return jsonify({"status": "ok", **audit})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/collx/discover")
def collx_discover_route():
    found = discover_collx_csv_paths()
    return jsonify(
        {
            "status": "ok",
            "found": found,
            "count": len(found),
            "inbox_path": str(COLLX_INBOX),
            "current_path": str(COLLX_CURRENT),
            "canonical_path": str(CANONICAL_PATH),
            "hint": "Save as collx_inbox/current/collx_export.csv (one file only)",
        }
    )


@app.route("/api/collx/auto-import", methods=["POST"])
def collx_auto_import_route():
    result = auto_import_from_drive()
    return jsonify(result)


@app.route("/api/collx/fetch", methods=["POST"])
def collx_fetch_route():
    use_gmail = request.get_json(silent=True) or {}
    gmail = use_gmail.get("gmail", True)
    dev_log("api_collx_fetch", client=request.remote_addr, gmail=bool(gmail))
    result = fetch_and_import_collx(use_gmail=bool(gmail))
    return jsonify(result)


@app.route("/live/capture")
def live_capture_page():
    return send_from_directory(BASE_DIR, "live_capture.html")


@app.route("/api/scan/live-config")
def scan_live_config_route():
    base = request.url_root.rstrip("/")
    return jsonify({"status": "ok", **live_config(base)})


@app.route("/api/scan/context/<card_id>")
def scan_context_route(card_id: str):
    card = _find_card(card_id)
    if not card:
        return jsonify({"status": "error", "message": "Card not found."}), 404
    cheats = build_lester_cheats(card)
    return jsonify(
        {
            "status": "ok",
            "card": card,
            "lester_cheats": cheats,
            "hybrid_mode": "c",
        }
    )


@app.route("/api/scan/gate", methods=["POST"])
def scan_gate_route():
    payload = request.get_json(silent=True) or {}
    card_id = (payload.get("card_id") or "").strip()
    card = _find_card(card_id)
    if not card:
        return jsonify({"status": "error", "message": "Card not found."}), 404

    gate = evaluate_gate(card, payload)
    dev_log("scan_gate", card_id=card_id, ok=gate.get("ok"), source=payload.get("source"))
    if not gate.get("ok"):
        return jsonify({"status": "blocked", "gate": gate, "message": gate.get("message")})

    token = issue_gate_token(card_id, gate)
    return jsonify(
        {
            "status": "ok",
            "gate": gate,
            "gate_token": token,
            "message": gate.get("message"),
            "next": "/api/scan/grade",
        }
    )


@app.route("/api/scan/grade", methods=["POST"])
def scan_grade_route():
    payload = request.get_json(silent=True) or {}
    client_id = billing.client_id_from_request(request)
    allowed, reason = billing.scan_allowed(client_id)
    if not allowed:
        return jsonify(
            {
                "status": "upgrade_required",
                "message": reason,
                "billing": billing.billing_status(client_id),
            }
        ), 402

    card_id = (payload.get("card_id") or "").strip()
    card = _find_card(card_id)
    if not card:
        return jsonify({"status": "error", "message": "Card not found."}), 404

    token = (payload.get("gate_token") or "").strip()
    gate_payload = payload.get("gate")
    if token and verify_gate_token(token, card_id):
        consume_gate_token(token)
    elif isinstance(gate_payload, dict):
        gate = evaluate_gate(card, gate_payload)
        if not gate.get("ok"):
            return jsonify({"status": "blocked", "message": gate.get("message"), "gate": gate}), 400
    else:
        return jsonify(
            {
                "status": "error",
                "message": "Quality gate not passed. Call /api/scan/gate first or include gate_token.",
            }
        ), 400

    live_report = payload.get("live_report") or payload.get("report") or {}
    if not live_report and payload.get("grade"):
        live_report = payload
    if not live_report:
        return jsonify({"status": "error", "message": "live_report required (grade, confidence, centering, etc.)."}), 400

    result = build_grade_response(card, live_report)
    if not billing.is_pro(client_id):
        billing.record_scan(client_id)
    dev_log(
        "scan_grade",
        card_id=card_id,
        grade=result.get("grade"),
        source=live_report.get("source"),
        raw=result.get("valuation", {}).get("raw"),
    )
    return jsonify(result)


def _billing_base_url() -> str:
    env = (os.environ.get("BILLING_PUBLIC_URL") or "").strip()
    if env:
        return env.rstrip("/")
    return request.url_root.rstrip("/")


@app.route("/api/billing/status")
def billing_status_route():
    cid = billing.client_id_from_request(request)
    return jsonify({"status": "ok", **billing.billing_status(cid), "client_id": cid})


@app.route("/api/billing/checkout", methods=["POST"])
def billing_checkout_route():
    body = request.get_json(silent=True) or {}
    cid = (body.get("client_id") or billing.client_id_from_request(request)).strip()
    plan = (body.get("plan") or "monthly").strip()
    if not billing.stripe_configured():
        return jsonify(
            {
                "status": "error",
                "message": "Stripe not configured. Add ~/.stan/stripe.env — see STRIPE_SETUP.md",
            }
        ), 503
    try:
        session = billing.create_checkout(cid, plan, _billing_base_url())
        return jsonify({"status": "ok", "url": session.get("url"), "session_id": session.get("id")})
    except Exception as exc:
        dev_log("billing_checkout_error", error=str(exc))
        return jsonify({"status": "error", "message": str(exc)}), 400


@app.route("/billing/success")
def billing_success_page():
    session_id = (request.args.get("session_id") or "").strip()
    cid = billing.client_id_from_request(request)
    msg = "Pro activated — unlimited scans."
    err = ""
    try:
        if session_id:
            billing.activate_session(session_id, cid)
    except Exception as exc:
        err = str(exc)
        msg = "Payment received — if Pro not active, contact support."
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="3;url=/">
<title>Pro activated</title>
<style>body{{font-family:system-ui;background:#0c1f3f;color:#f4efe3;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:1rem;text-align:center}}
a{{color:#3ecf8e}}</style></head><body>
<h1>{msg}</h1>
<p>{err}</p>
<p><a href="/">Back to cards →</a></p>
</body></html>"""
    return Response(html, mimetype="text/html")


@app.route("/billing/cancel")
def billing_cancel_page():
    return Response(
        """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Checkout cancelled</title></head><body style="font-family:system-ui;background:#0c1f3f;color:#f4efe3;text-align:center;padding:2rem">
<h1>Checkout cancelled</h1><p><a href="/" style="color:#3ecf8e">Return to app</a></p></body></html>""",
        mimetype="text/html",
    )


def _persist_last_scan(card_id: str, payload: dict) -> dict | None:
    cards = _load_collection()
    idx = next((i for i, c in enumerate(cards) if c.get("id") == card_id), None)
    if idx is None:
        return None
    card = cards[idx]
    scan = dict(payload)
    scan["scanned_at"] = _now()
    card["last_scan"] = scan
    cards[idx] = card
    _save_collection(cards)
    return card


@app.route("/api/cards/<card_id>/scan", methods=["POST"])
def save_card_scan(card_id: str):
    """Save PSA precursor scan to card — list reads last_scan."""
    payload = request.get_json(silent=True) or {}
    cards = _load_collection()
    card = next((c for c in cards if c.get("id") == card_id), None)
    if not card:
        return jsonify({"status": "error", "message": "Card not found."}), 404

    if payload.get("from_grade_response"):
        live_report = payload.get("live_report") or {}
        source = payload.get("source") or live_report.get("source") or "scan"
        scan = scan_record_from_grade(card, live_report, source=source)
        grade_override = payload.get("grade")
        if grade_override is not None:
            try:
                g = max(1, min(10, int(grade_override)))
                sandbox = valuation_sandbox(card, g)
                route = sandbox.get("route") or {}
                scan["grade"] = g
                scan["grade_label"] = f"PSA {g} — {sandbox.get('grade_title', '')}".rstrip(" —")
                scan["graded"] = sandbox.get("graded")
                scan["rog"] = sandbox.get("rog")
                scan["route_action"] = route.get("action")
                scan["route_label"] = route.get("label")
            except (TypeError, ValueError):
                pass
        if payload.get("confidence") is not None:
            scan["confidence"] = payload["confidence"]
        if payload.get("criteria"):
            scan["criteria"] = payload["criteria"]
        for key in ("graded", "rog", "route_label", "route_action", "retake_recommended"):
            if key in payload and payload[key] is not None:
                scan[key] = payload[key]
    else:
        allowed = {
            "grade", "grade_label", "confidence", "criteria", "graded", "rog",
            "route_action", "route_label", "source", "retake_recommended", "hardware",
        }
        scan = {k: payload[k] for k in allowed if k in payload}
        if not scan.get("grade"):
            return jsonify({"status": "error", "message": "grade required."}), 400

    saved = _persist_last_scan(card_id, scan)
    if not saved:
        return jsonify({"status": "error", "message": "Card not found."}), 404
    dev_log("scan_saved", card_id=card_id, grade=scan.get("grade"), confidence=scan.get("confidence"))
    return jsonify({"status": "success", "card": saved, "last_scan": saved.get("last_scan")})


def _dev_key_from_request() -> str:
    return (request.args.get("key") or request.headers.get("X-Dev-Key") or "").strip()


def _dev_key_or_403():
    key = _dev_key_from_request()
    if not check_key(key):
        return None
    return key


@app.route("/api/dev/info")
def dev_info_route():
    """Public stats about the debug log (no content, no key)."""
    return jsonify({"status": "ok", **dev_log_stats(), "download_path": "/api/dev/log/download"})


@app.route("/api/dev/log")
def dev_log_route():
    if not _dev_key_or_403():
        return jsonify(
            {
                "status": "error",
                "message": "Invalid or missing dev key. Read data/dev/dev.key on the server.",
            }
        ), 403
    max_lines = min(int(request.args.get("tail", 200)), 2000)
    fmt = (request.args.get("format") or "text").strip().lower()
    if fmt == "json":
        raw = dev_log_tail(max_lines)
        lines = [json.loads(line) for line in raw.splitlines() if line.strip()]
        return jsonify({"status": "ok", "lines": lines, "stats": dev_log_stats()})
    return jsonify(
        {
            "status": "ok",
            "text": human_tail(max_lines),
            "stats": dev_log_stats(),
        }
    )


@app.route("/api/dev/log/download")
def dev_log_download_route():
    if not _dev_key_or_403():
        return jsonify({"status": "error", "message": "Invalid or missing dev key."}), 403
    if not LOG_FILE.is_file():
        return jsonify({"status": "error", "message": "No debug log file yet."}), 404
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return send_file(
        LOG_FILE,
        mimetype="text/plain",
        as_attachment=True,
        download_name=f"baseball_debug_{stamp}.log",
    )


@app.route("/api/dev/log/clear", methods=["POST"])
def dev_log_clear_route():
    if not _dev_key_or_403():
        return jsonify({"status": "error", "message": "Invalid or missing dev key."}), 403
    return jsonify(clear_dev_log())


def _collx_poll_loop(interval: float = 120.0) -> None:
    while True:
        try:
            fetch_and_import_collx(use_gmail=True)
        except Exception as exc:
            log_exception("collx_poll_error", exc)
        time.sleep(interval)


def start_collx_poll(interval: float = 120.0) -> None:
    global _collx_poll_started
    if _collx_poll_started:
        return
    t = threading.Thread(target=_collx_poll_loop, args=(interval,), name="collx-poll", daemon=True)
    t.start()
    _collx_poll_started = True


@app.route("/api/collx/reset", methods=["POST"])
def collx_reset_route():
    body = request.get_json(silent=True) or {}
    keep_catalog = bool(body.get("keep_catalog", True))
    result = reset_collection(keep_catalog=keep_catalog)
    return jsonify(result)


@app.route("/api/collx/purge-tests", methods=["POST"])
def collx_purge_tests_route():
    return jsonify(purge_test_cards())


@app.route("/api/health")
def health():
    meta = load_meta()
    cards = _load_collection()
    payload = {
        "status": "ok",
        "service": "baseball-card-valuation",
        "ui_version": "phase2_scan_collx",
        "commercial_version": "1.0.0",
        "data_mode": "collx",
        "cards": len(cards),
        "collx_catalog": meta.get("last_import_rows") or len(cards),
    }
    return jsonify(payload)


@app.route("/api/handoff/puppy", methods=["GET", "POST"])
def handoff_puppy():
    if not drive_handoff:
        return jsonify({"status": "error", "message": "drive_handoff module missing"}), 503
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        text = (body.get("message") or body.get("text") or "").strip()
        if text:
            drive_handoff.PUPPY_IN.parent.mkdir(parents=True, exist_ok=True)
            drive_handoff.PUPPY_IN.write_text(text, encoding="utf-8")
        result = drive_handoff.poll_puppy_note(integrate=True)
    else:
        result = drive_handoff.poll_puppy_note(integrate=True)
    return jsonify({"status": "ok", **result})


def _load_gmail_env() -> None:
    env_file = STAN_DIR / "gmail.env"
    if not env_file.is_file():
        return
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and val and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


if __name__ == "__main__":
    _load_gmail_env()
    dev_key_path = startup_note("0.0.0.0", 8002)
    print(f"[dev] phone_debug.log → data/dev/phone_debug.log", flush=True)
    print(f"[dev] pull key from → data/dev/dev.key", flush=True)

    def _startup_background() -> None:
        auto_import_from_drive()
        start_collx_poll(interval=30.0)
        try:
            import brian_os

            brian_os.refresh_brian_status()
            brian_os.start_queue_watcher(interval=90.0)
        except ImportError:
            pass
        if drive_handoff:
            drive_handoff.start_drive_handoff_watcher(interval=60.0)

    threading.Thread(target=_startup_background, name="startup-bg", daemon=True).start()
    app.run(host="0.0.0.0", port=8002, debug=False, threaded=True)
