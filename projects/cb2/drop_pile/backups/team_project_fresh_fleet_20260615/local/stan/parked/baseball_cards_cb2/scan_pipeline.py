"""Hybrid scan pipeline (C): Gemini Live = capture/quality gate; Flask = grade + CollX math."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from collx_data import DRIVE_ROOT

GRADE_MULT: dict[int, float] = {
    1: 0.25, 2: 0.38, 3: 0.5, 4: 0.7, 5: 0.92,
    6: 1.75, 7: 2.33, 8: 3.75, 9: 6.67, 10: 15.0,
}
GRADE_TITLE: dict[int, str] = {
    1: "Poor (PR)", 2: "Good (GD)", 3: "Very Good (VG)", 4: "VG-EX",
    5: "Excellent (EX)", 6: "EX-MT", 7: "Near Mint (NM)", 8: "NM-MT",
    9: "Mint (MT)", 10: "Gem Mint (GEM-MT)",
}
TOP_TIER_RAW = 100.0
GRADING_FEE = 15.0
SHIPPING = 5.0
GATE_TTL_SEC = 600
RETAKE_CONFIDENCE_THRESHOLD = 75

LESTER_CHEATS_PATHS = [
    DRIVE_ROOT / "lester" / "scan_cheats.json",
    DRIVE_ROOT / "lester" / "baseball_cards" / "scan_cheats.json",
    DRIVE_ROOT / "collx_inbox" / "lester_scan_cheats.json",
]

_gate_sessions: dict[str, dict[str, Any]] = {}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_lester_cheats_file() -> dict[str, Any]:
    for path in LESTER_CHEATS_PATHS:
        if path.is_file():
            data = _load_json(path)
            if isinstance(data, dict):
                return data
    return {}


def is_top_tier(card: dict[str, Any]) -> bool:
    mid = (card.get("valuation") or {}).get("estimate_mid")
    return mid is not None and float(mid) >= TOP_TIER_RAW


def graded_estimate(raw: float | None, grade: int) -> float:
    if not raw or raw <= 0:
        return 0.0
    return round(float(raw) * GRADE_MULT.get(grade, 1.0), 2)


def rog_calculation(raw: float, graded: float) -> float:
    return round(graded - (float(raw) + GRADING_FEE + SHIPPING), 2)


def route_decision(rog: float, graded: float, top_tier: bool) -> dict[str, str]:
    if graded > 400 and top_tier and rog > 0:
        return {"action": "collector", "label": "Collector route — hold / slab", "class": "action-registry"}
    if rog >= 50 and rog >= 0.2 * graded:
        return {"action": "grade", "label": "Grading arbitrage route", "class": "action-grade"}
    return {"action": "sell_raw", "label": "Fast-nickel route — sell raw", "class": "action-hold"}


def valuation_sandbox(card: dict[str, Any], grade: int) -> dict[str, Any]:
    raw = (card.get("valuation") or {}).get("estimate_mid")
    graded = graded_estimate(raw, grade) if raw is not None else None
    rog = rog_calculation(float(raw), graded) if raw is not None and graded else None
    top = is_top_tier(card)
    route = route_decision(rog or 0, graded or 0, top) if raw is not None and graded else {
        "action": "no_price",
        "label": "Sync CollX for raw price first",
        "class": "action-hold",
    }
    return {
        "raw": raw,
        "graded": graded,
        "rog": rog,
        "grade": grade,
        "grade_title": GRADE_TITLE.get(grade, ""),
        "top_tier": top,
        "route": route,
        "grading_fee": GRADING_FEE,
        "shipping": SHIPPING,
    }


def build_lester_cheats(card: dict[str, Any]) -> dict[str, Any]:
    """Card-specific Gemini Live session — NOT general-purpose chat."""
    v = card.get("valuation") or {}
    mid = v.get("estimate_mid")
    top = is_top_tier(card)
    cheats_file = load_lester_cheats_file()
    global_hint = cheats_file.get("global_prompt") or cheats_file.get("global") or ""
    per_card = cheats_file.get("cards") or {}
    extra = per_card.get(card.get("collx_id")) or per_card.get(card.get("id")) or cheats_file.get("default") or ""

    player = card.get("player", "")
    year = card.get("year", "")
    card_set = card.get("set", "")
    num = card.get("card_number", "")
    title = f"{year} {card_set} {player}".strip()
    if num:
        title += f" #{num}"

    raw_line = f"${mid:.2f}" if mid is not None else "UNKNOWN — user must Sync CollX first"
    back_rule = (
        "REQUIRE front AND back photos before grade (high-value card)."
        if top
        else "Front photo required; back optional."
    )

    system_instruction = (
        "You are the LIVE CAMERA COACH for Brian's Baseball Cards app — one card only.\n"
        "This is NOT general Gemini Live. Do not discuss other projects or topics.\n\n"
        f"TARGET CARD (from CollX catalog): {title}\n"
        f"CollX raw market_value: {raw_line} — NEVER invent or guess prices.\n"
        f"Listed condition: {card.get('condition', '')} · Flags: {card.get('flags') or 'none'}\n"
        f"Team: {card.get('team', '')} · Brand: {card.get('brand', '')}\n\n"
        "YOUR ROLE (Hybrid C — you own capture + quality gate only):\n"
        "1. Coach phone camera: flat surface, fill frame, no glare, hold steady.\n"
        f"2. {back_rule}\n"
        "3. Reject blur and glare — tell user exactly how to fix.\n"
        "4. After photos pass, assess PSA-style: centering, corners, edges, surface.\n"
        "5. Output PSA grade 1–10 + confidence %.\n"
        "6. Call window.BaseballScan.postGate() when photos pass.\n"
        "7. Call window.BaseballScan.postGrade() with your visual report.\n"
        "Flask on this server applies CollX math — you do NOT calculate dollar values.\n"
    )
    if global_hint:
        system_instruction += f"\nLester notes:\n{global_hint}\n"
    if extra:
        system_instruction += f"\nThis card:\n{extra}\n"

    prompt = system_instruction
    return {
        "session_type": "baseball_card_psa_capture",
        "prompt": prompt,
        "system_instruction": system_instruction,
        "card_title": title,
        "card_id": card.get("id"),
        "collx_id": card.get("collx_id"),
        "top_tier": top,
        "raw_mid": mid,
        "requirements": {
            "front_required": True,
            "back_required": top,
            "reject_blur": True,
            "reject_glare": True,
        },
        "api": {
            "gate": "/api/scan/gate",
            "grade": "/api/scan/grade",
            "context": f"/api/scan/context/{card.get('id')}",
        },
        "gemini_live": {
            "use_case": "baseball_card_scan",
            "not_general_chat": True,
            "post_gate": "window.BaseballScan.postGate({ front_ok, back_ok, blur, glare })",
            "post_grade": "window.BaseballScan.postGrade({ grade, confidence, centering, corners, edges, surface })",
        },
    }


def evaluate_gate(card: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Quality gate from Gemini Live (or practice capture)."""
    blur = bool(payload.get("blur"))
    glare = bool(payload.get("glare"))
    front_ok = bool(payload.get("front_ok"))
    back_ok = bool(payload.get("back_ok"))
    top = is_top_tier(card)

    if blur:
        return {"ok": False, "message": "Blur detected — hold steady and re-take."}
    if glare:
        return {"ok": False, "message": "Glare on surface — adjust lighting or angle."}
    if not front_ok:
        return {"ok": False, "message": "Front photo required."}
    if top and not back_ok:
        return {"ok": False, "message": "High-value card — front and back photos required."}

    return {
        "ok": True,
        "message": "Photo quality gate passed.",
        "top_tier": top,
        "source": payload.get("source") or "live",
    }


def _prune_gate_sessions() -> None:
    now = time.time()
    expired = [k for k, v in _gate_sessions.items() if now - v.get("at", 0) > GATE_TTL_SEC]
    for k in expired:
        _gate_sessions.pop(k, None)


def issue_gate_token(card_id: str, gate: dict[str, Any]) -> str:
    _prune_gate_sessions()
    token = uuid.uuid4().hex
    _gate_sessions[token] = {
        "card_id": card_id,
        "at": time.time(),
        "gate": gate,
    }
    return token


def verify_gate_token(token: str | None, card_id: str) -> bool:
    if not token:
        return False
    _prune_gate_sessions()
    entry = _gate_sessions.get(token)
    if not entry or entry.get("card_id") != card_id:
        return False
    if time.time() - entry.get("at", 0) > GATE_TTL_SEC:
        _gate_sessions.pop(token, None)
        return False
    return bool((entry.get("gate") or {}).get("ok"))


def consume_gate_token(token: str | None) -> None:
    if token:
        _gate_sessions.pop(token, None)


def normalize_live_report(report: dict[str, Any]) -> dict[str, Any]:
    grade = report.get("grade") or report.get("psa_grade") or report.get("predicted_grade")
    try:
        grade = int(round(float(grade)))
    except (TypeError, ValueError):
        grade = 7
    grade = max(1, min(10, grade))

    confidence = report.get("confidence") or report.get("grade_confidence") or 84
    try:
        confidence = int(round(float(confidence)))
    except (TypeError, ValueError):
        confidence = 84

    return {
        "grade": grade,
        "confidence": max(0, min(100, confidence)),
        "centering": str(report.get("centering") or "—"),
        "corners": str(report.get("corners") or "—"),
        "edges": str(report.get("edges") or "—"),
        "surface": str(report.get("surface") or "—"),
        "source": report.get("source") or "gemini_live",
    }


def scan_record_from_grade(
    card: dict[str, Any], live_report: dict[str, Any], *, source: str = ""
) -> dict[str, Any]:
    """Persistable scan snapshot for collection.json (PSA precursor)."""
    norm = normalize_live_report(live_report)
    sandbox = valuation_sandbox(card, norm["grade"])
    route = sandbox.get("route") or {}
    criteria = (
        f"CENTER {norm['centering']} · CORNERS {norm['corners']} · "
        f"EDGES {norm['edges']} · SURFACE {norm['surface']}"
    )
    confidence = norm["confidence"]
    return {
        "grade": norm["grade"],
        "grade_label": f"PSA {norm['grade']} — {GRADE_TITLE.get(norm['grade'], '')}",
        "confidence": confidence,
        "criteria": criteria,
        "graded": sandbox.get("graded"),
        "rog": sandbox.get("rog"),
        "route_action": route.get("action"),
        "route_label": route.get("label"),
        "source": source or norm.get("source") or "scan",
        "retake_recommended": confidence < RETAKE_CONFIDENCE_THRESHOLD,
        "hardware": "precursor",
    }


def build_grade_response(card: dict[str, Any], live_report: dict[str, Any]) -> dict[str, Any]:
    norm = normalize_live_report(live_report)
    sandbox = valuation_sandbox(card, norm["grade"])
    scan_rec = scan_record_from_grade(card, live_report)
    return {
        "status": "success",
        "mode": "hybrid_c",
        "grade": norm["grade"],
        "grade_label": scan_rec["grade_label"],
        "confidence": norm["confidence"],
        "criteria": scan_rec["criteria"],
        "live_report": norm,
        "valuation": sandbox,
        "retake_recommended": scan_rec["retake_recommended"],
        "retake_message": (
            "Low confidence — retake photos on a flat surface with even light for a tighter PSA estimate."
            if scan_rec["retake_recommended"]
            else ""
        ),
        "card": {
            "id": card.get("id"),
            "player": card.get("player"),
            "year": card.get("year"),
            "set": card.get("set"),
        },
    }


def live_config(base_url: str = "") -> dict[str, Any]:
    """Tell UI + puppy where Live capture lives."""
    puppy_live = os.environ.get("SCAN_LIVE_URL", "").strip()
    for path in [
        DRIVE_ROOT / "lester" / "gemini_live_url.txt",
        DRIVE_ROOT / "puppy_outbox.txt",
    ]:
        if not puppy_live and path.is_file():
            try:
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if line.startswith("http") and "live" in line.lower():
                        puppy_live = line.split()[0]
                        break
            except OSError:
                pass

    capture_path = "/live/capture"
    return {
        "mode": "hybrid_c",
        "description": "Gemini Live = capture + quality gate; Flask = grade + CollX math",
        "live_capture_path": capture_path,
        "live_capture_url": f"{base_url.rstrip('/')}{capture_path}" if base_url else capture_path,
        "puppy_live_url": puppy_live or None,
        "lester_cheats_paths": [str(p) for p in LESTER_CHEATS_PATHS],
        "lester_cheats_loaded": any(p.is_file() for p in LESTER_CHEATS_PATHS),
        "endpoints": {
            "context": "/api/scan/context/<card_id>",
            "gate": "/api/scan/gate",
            "grade": "/api/scan/grade",
            "config": "/api/scan/live-config",
        },
    }

