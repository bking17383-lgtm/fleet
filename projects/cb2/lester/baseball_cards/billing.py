"""Stripe billing — Card Reader Pro · free 5 scans/mo · Gem indie."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
USAGE_FILE = DATA_DIR / "billing_usage.json"
PRO_FILE = DATA_DIR / "billing_pro.json"
STAN_ENV = Path.home() / ".stan" / "stripe.env"
LESTER_KEYS = Path("/mnt/shared/GoogleDrive/MyDrive/lester/lester_keys.md")
if not LESTER_KEYS.is_file():
    alt = Path.home() / "GoogleDrive/MyDrive/lester/lester_keys.md"
    if alt.is_file():
        LESTER_KEYS = alt

FREE_SCANS_PER_MONTH = 5
PLANS = {
    "monthly": {"amount": 499, "mode": "subscription", "interval": "month", "label": "Pro $4.99/mo"},
    "yearly": {"amount": 2900, "mode": "payment", "interval": None, "label": "Pro $29/yr"},
}


def _load_env() -> None:
    if STAN_ENV.is_file():
        for line in STAN_ENV.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if os.environ.get("STRIPE_SECRET_KEY", "").strip():
        return
    if not LESTER_KEYS.is_file():
        return
    import re

    text = LESTER_KEYS.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("STRIPE_SECRET_KEY="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                os.environ.setdefault("STRIPE_SECRET_KEY", val)
        elif line.startswith("STRIPE_PUBLISHABLE_KEY="):
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                os.environ.setdefault("STRIPE_PUBLISHABLE_KEY", val)
    if not os.environ.get("STRIPE_SECRET_KEY", "").strip():
        sk = re.search(r"(sk_(?:test|live)_[A-Za-z0-9]+)", text)
        pk = re.search(r"(pk_(?:test|live)_[A-Za-z0-9]+)", text)
        if sk:
            os.environ.setdefault("STRIPE_SECRET_KEY", sk.group(1))
        if pk:
            os.environ.setdefault("STRIPE_PUBLISHABLE_KEY", pk.group(1))


def _month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _read_json(path: Path, default: dict) -> dict:
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return default


def _write_json(path: Path, data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def stripe_secret() -> str:
    return (os.environ.get("STRIPE_SECRET_KEY") or "").strip()


def stripe_configured() -> bool:
    return bool(stripe_secret())


_load_env()


def client_id_from_request(req) -> str:
    cid = (req.headers.get("X-Client-Id") or req.cookies.get("card_client_id") or "").strip()
    if cid and len(cid) <= 64:
        return cid
    return "anonymous"


def _pro_map() -> dict:
    data = _read_json(PRO_FILE, {"clients": {}})
    clients = data.get("clients") or {}
    now = datetime.now(timezone.utc)
    changed = False
    for cid, rec in list(clients.items()):
        until = rec.get("pro_until")
        if until:
            try:
                exp = datetime.fromisoformat(until.replace("Z", "+00:00"))
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < now:
                    del clients[cid]
                    changed = True
            except ValueError:
                pass
    if changed:
        data["clients"] = clients
        _write_json(PRO_FILE, data)
    return clients


def is_pro(client_id: str) -> bool:
    if client_id == "anonymous":
        return False
    return client_id in _pro_map()


def scans_used(client_id: str) -> int:
    data = _read_json(USAGE_FILE, {"months": {}})
    month = _month_key()
    return int(((data.get("months") or {}).get(month) or {}).get(client_id) or 0)


def record_scan(client_id: str) -> int:
    data = _read_json(USAGE_FILE, {"months": {}})
    month = _month_key()
    months = data.setdefault("months", {})
    bucket = months.setdefault(month, {})
    bucket[client_id] = int(bucket.get(client_id) or 0) + 1
    _write_json(USAGE_FILE, data)
    return bucket[client_id]


def billing_status(client_id: str) -> dict:
    pro = is_pro(client_id)
    used = scans_used(client_id)
    return {
        "pro": pro,
        "scans_used": used,
        "scans_limit": FREE_SCANS_PER_MONTH,
        "scans_remaining": max(0, FREE_SCANS_PER_MONTH - used) if not pro else None,
        "stripe_configured": stripe_configured(),
        "plans": {k: v["label"] for k, v in PLANS.items()},
        "month": _month_key(),
    }


def scan_allowed(client_id: str) -> tuple[bool, str]:
    if is_pro(client_id):
        return True, ""
    used = scans_used(client_id)
    if used >= FREE_SCANS_PER_MONTH:
        return False, (
            f"Free limit reached ({FREE_SCANS_PER_MONTH} scans this month). "
            "Upgrade to Pro for unlimited PSA prep scans."
        )
    return True, ""


def grant_pro(client_id: str, plan: str, days: int = 32) -> None:
    if not client_id or client_id == "anonymous":
        return
    data = _read_json(PRO_FILE, {"clients": {}})
    clients = data.setdefault("clients", {})
    until = datetime.now(timezone.utc)
    if plan == "yearly":
        until = until.replace(year=until.year + 1)
    else:
        from datetime import timedelta

        until = until + timedelta(days=days)
    clients[client_id] = {
        "plan": plan,
        "pro_until": until.isoformat(),
        "granted_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(PRO_FILE, data)


def _stripe_post(path: str, fields: dict) -> dict:
    key = stripe_secret()
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY not set — add ~/.stan/stripe.env")
    body = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.stripe.com/v1{path}",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _stripe_get(path: str) -> dict:
    key = stripe_secret()
    req = urllib.request.Request(
        f"https://api.stripe.com/v1{path}",
        method="GET",
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def create_checkout(client_id: str, plan: str, base_url: str) -> dict:
    if plan not in PLANS:
        raise ValueError("invalid plan")
    if not stripe_configured():
        raise RuntimeError("Stripe not configured")
    p = PLANS[plan]
    base = base_url.rstrip("/")
    fields = {
        "mode": p["mode"],
        "client_reference_id": client_id,
        "success_url": f"{base}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{base}/billing/cancel",
        "line_items[0][quantity]": "1",
        "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][product_data][name]": "Card Reader Pro — PSA prep scans",
        "line_items[0][price_data][unit_amount]": str(p["amount"]),
        "metadata[client_id]": client_id,
        "metadata[plan]": plan,
    }
    if p["mode"] == "subscription":
        fields["line_items[0][price_data][recurring][interval]"] = p["interval"] or "month"
    session = _stripe_post("/checkout/sessions", fields)
    return {"url": session.get("url"), "id": session.get("id")}


def activate_session(session_id: str, client_id: str) -> dict:
    if not session_id:
        raise ValueError("session_id required")
    session = _stripe_get(f"/checkout/sessions/{urllib.parse.quote(session_id)}")
    if session.get("payment_status") not in ("paid", "no_payment_required"):
        if session.get("status") != "complete":
            raise RuntimeError("Checkout not complete")
    ref = session.get("client_reference_id") or session.get("metadata", {}).get("client_id")
    if ref and ref != client_id:
        raise RuntimeError("client mismatch")
    plan = (session.get("metadata") or {}).get("plan") or "monthly"
    grant_pro(client_id, plan, days=366 if plan == "yearly" else 32)
    return billing_status(client_id)
