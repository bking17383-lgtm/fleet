#!/usr/bin/env python3
"""Curated clickable links for Brian design desk."""
from __future__ import annotations

from bus_lane import bus_root, safe_is_file, safe_read_text, safe_mkdir, STAN, LOGS

BUS = bus_root()
DRIVE = BUS
DRIVE_URI = f"file://{BUS}"
DESK_BASE = "http://127.0.0.1:8770"
CF_ACCOUNT = "ad430a8e50c3ba0990c395528f3482ba"
TUNNEL_ID = "11431ecb-5cbd-40a5-b635-cec2aff9de03"


def _f(rel: str) -> str:
    return f"{DRIVE_URI}/{rel}"


def _h(rel: str) -> str:
    """Clickable from browser (desk + phone on LAN). Prefer over file://."""
    return f"{DESK_BASE}/f/{rel}"


DESK_SECTIONS = [
    {
        "title": "AWS + cloud CPT (investigate)",
        "links": [
            ("AWS investigation guide", _h("fleet/AWS_INVESTIGATION.txt")),
            ("Cloud CPT fallback plan", _h("fleet/CLOUD_CPT_FALLBACK.txt")),
            ("AWS probe report", _h("fleet/bus/AWS_PROBE_REPORT.txt")),
            ("Sandbox IAM policy (paste in console)", _h("fleet/AWS_SANDBOX_IAM.json")),
        ],
    },
    {
        "title": "Spawn / PACK",
        "links": [
            ("BOOT PACK checklist", _h("fleet/BOOT_PACK.txt")),
            ("Gemini boot paste", _h("drop_pile/to_gemini/GEMINI_BOOT_PASTE.txt")),
            ("Gemini Drive law", _h("fleet/GEMINI_DRIVE_LAW.txt")),
            ("Brian law (fill)", _h("fleet/BRIAN_LAW.txt")),
            ("CPT boot", _h("drop_pile/to_cursor/CPT_BOOT_NOW.md")),
        ],
    },
    {
        "title": "Stuck + money",
        "links": [
            ("STUCK BOARD (read when lost)", _h("fleet/STUCK_BOARD.txt")),
            ("Naming law (CPT not Daddy)", _h("fleet/NAMING_LAW.txt")),
            ("FAILSAFE — machine dies", _h("fleet/FLEET_FAILSAFE.txt")),
        ],
    },
    {
        "title": "Orders + fleet",
        "links": [
            ("Orders — 3 computers", _h("fleet/orders/ORDERS_HERE.txt")),
            ("CB2 orders", _h("fleet/orders/CB2_ORDERS.txt")),
            ("Puppy orders", _h("fleet/orders/PUPPY_ORDERS.txt")),
            ("CB1 orders", _h("fleet/orders/CB1_ORDERS.txt")),
            ("Slave report (gaps)", _h("fleet/bus/SLAVE_REPORT.txt")),
            ("Brian catch-up (out of context)", _h("fleet/BRIAN_CATCH_UP.txt")),
            ("Fresh fleet guide", _h("fleet/FRESH_FLEET.txt")),
            ("Pack status", _h("fleet/bus/PACK_STATUS.txt")),
            ("Pack before wipe", _h("fleet/bus/PACK_BEFORE_WIPE.txt")),
            ("Fleet status", _h("fleet/FLEET_AVAILABLE.txt")),
            ("Brian inbox", _h("fleet/bus/BRIAN_INBOX.txt")),
        ],
    },
    {
        "title": "Any terminal (Brian law)",
        "links": [
            ("Terminal anywhere law", _f("fleet/TERMINAL_ANYWHERE.txt")),
            ("Fleet status", _f("fleet/FLEET_AVAILABLE.txt")),
            ("Brian inbox", _f("fleet/bus/BRIAN_INBOX.txt")),
            ("Heritage card demo (landscape)", "http://127.0.0.1:8770/card"),
            ("Card file (if browser blocks file://)", _f("lester/heritage/card_demo.html")),
        ],
    },
    {
        "title": "Uncle · CB1",
        "links": [
            ("Uncle boot NOW", _f("drop_pile/to_cursor/UNCLE_BOOT_NOW.md")),
            ("Network without Puppy", _f("fleet/NETWORK_WITHOUT_PUPPY.txt")),
            ("Hardware protocols", _f("drop_pile/to_cursor/UNCLE_HARDWARE_PROTOCOLS.md")),
            ("CB1 reload notes", _f("fleet/CB1_LINUX_RELOAD.txt")),
        ],
    },
    {
        "title": "Repair crew",
        "links": [
            ("Repair crew doc", _f("fleet/REPAIR_CREW.txt")),
            ("Repair log", _f("fleet/bus/REPAIR_LOG.txt")),
            ("Human alert (if any)", _f("fleet/bus/REPAIR_NOW.txt")),
        ],
    },
    {
        "title": "Start here",
        "links": [
            ("Design desk (this page)", "/desk"),
            ("Who's who", "/who"),
            ("Type one line — Brian inbox", _f("fleet/bus/BRIAN_INBOX.txt")),
            ("Fleet status", _f("fleet/FLEET_AVAILABLE.txt")),
            ("Who bulk JSON", _f("fleet/WHO.json")),
        ],
    },
    {
        "title": "hitme.dev",
        "links": [
            ("Manage hitme", _f("fleet/HITME_MANAGE.txt")),
            ("Hitme status", _f("fleet/HITME_STATUS.txt")),
            ("Tunnel hostnames setup", _f("fleet/HITME_TUNNEL_HOSTNAMES.txt")),
            ("API token how-to", _f("fleet/HITME_API_TOKEN.txt")),
            ("Sarah send link", _f("fleet/SARAH_SEND_WHEN_READY.txt")),
        ],
    },
    {
        "title": "Live apps (CB2)",
        "links": [
            ("Sarah demo", "http://127.0.0.1:8766/sarah"),
            ("Sarah dev log", "http://127.0.0.1:8766/dev"),
            ("Sarah QR", "http://127.0.0.1:8766/qr"),
            ("Who server local", "http://127.0.0.1:8770/desk"),
            ("Sarah HTTPS (when tunnel live)", "https://sarah.hitme.dev/sarah"),
            ("hitme.dev root (when tunnel live)", "https://hitme.dev/desk"),
        ],
    },
    {
        "title": "Cloudflare dashboards",
        "links": [
            ("hitme.dev zone", f"https://dash.cloudflare.com/{CF_ACCOUNT}/hitme.dev"),
            ("Email routing", f"https://dash.cloudflare.com/{CF_ACCOUNT}/hitme.dev/email/routing"),
            ("Tunnel cb2-daddy", f"https://dash.cloudflare.com/{CF_ACCOUNT}/networks/tunnels/{TUNNEL_ID}"),
            ("API tokens", "https://dash.cloudflare.com/profile/api-tokens"),
            ("Register domains", f"https://dash.cloudflare.com/{CF_ACCOUNT}/domains/register"),
        ],
    },
    {
        "title": "Design lanes",
        "links": [
            ("Camel desk", _f("fleet/CAMEL_DESK.txt")),
            ("Camel architect", _f("fleet/CAMEL_ARCHITECT_CAPTN.txt")),
            ("Sarah calendar", _f("fleet/SARAH_CALENDAR.txt")),
            ("Appointment request", _f("fleet/APPOINTMENT_REQUEST.txt")),
            ("QB / network back", _f("fleet/QB_NETWORK_BACK.txt")),
            ("Puppy stays (no wipe)", _f("fleet/PUPPY_STAYS.txt")),
            ("Uncle hardware", _f("drop_pile/to_cursor/UNCLE_HARDWARE_PROTOCOLS.md")),
        ],
    },
    {
        "title": "Puppy · network",
        "links": [
            ("PUPPY.txt order", _f("PUPPY.txt")),
            ("Puppy network", _f("fleet/PUPPY_NETWORK.txt")),
            ("mac_inbox bus", _f("fleet/bus/mac_inbox.txt")),
            ("puppy_outbox", _f("fleet/bus/puppy_outbox.txt")),
            ("Captain puppy loop", _f("fleet/CAPTAIN_PUPPY_LOOP.txt")),
        ],
    },
    {
        "title": "Photos · inbox",
        "links": [
            ("convert_inbox (snaps)", _f("convert_inbox/")),
            ("Sarah post-its", _f("lester/sarah/postits/")),
            ("CAPTN face", _f("fleet/captn/CAPTN_FACE.jpg")),
        ],
    },
]
