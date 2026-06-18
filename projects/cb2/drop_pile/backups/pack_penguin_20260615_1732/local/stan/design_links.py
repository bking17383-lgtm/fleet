#!/usr/bin/env python3
"""Curated clickable links for Brian design desk."""
from __future__ import annotations

from pathlib import Path

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
DRIVE_URI = "file:///mnt/shared/GoogleDrive/MyDrive"
CF_ACCOUNT = "ad430a8e50c3ba0990c395528f3482ba"
TUNNEL_ID = "11431ecb-5cbd-40a5-b635-cec2aff9de03"


def _f(rel: str) -> str:
    return f"{DRIVE_URI}/{rel}"


DESK_SECTIONS = [
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
