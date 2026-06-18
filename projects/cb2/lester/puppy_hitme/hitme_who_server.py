#!/usr/bin/env python3
"""hitme.dev — who roster + fleet links (port 8770)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, abort, jsonify, request, send_file

from design_links import DESK_SECTIONS

from bus_lane import bus_root, safe_is_file, safe_read_text, safe_mkdir, STAN, LOGS

BUS = bus_root()
DRIVE = BUS
WHO_JSON = DRIVE / "fleet/WHO.json"
CARD_DEMO = DRIVE / "lester/heritage/card_demo.html"
DOMAIN_FILE = DRIVE / "fleet/HITME_DOMAIN.txt"
LOCAL_DOMAIN = STAN / "hitme_domain.txt"
SCREEN_LATEST = STAN / "screen" / "latest.png"
SCREEN_META = "fleet/bus/DADDY_SCREEN.txt"
PORT = int(__import__("os").environ.get("HITME_PORT", "8770"))

app = Flask(__name__)


def _domain() -> str:
    if safe_is_file(DOMAIN_FILE):
        line = safe_read_text(DOMAIN_FILE).strip().splitlines()
        if line and line[0]:
            return line[0]
    if LOCAL_DOMAIN.is_file():
        line = safe_read_text(LOCAL_DOMAIN).strip().splitlines()
        if line and line[0]:
            return line[0]
    return "hitme.dev"


def _hitme_url(path: str = "/") -> str:
    """Canonical public URL — always hitme.dev, never trycloudflare or LAN."""
    p = path if path.startswith("/") else f"/{path}"
    return f"https://{_domain()}{p}"


def _public_goal_url() -> str:
    return _hitme_url("/goal")


TALK_MARKER = "--- type below ---"
INBOX_MARKER = "--- TYPE BELOW (one line) ---"
LANE_PREFIX = {
    "auto": "",
    "cpt": "CPT",
    "buddy": "BUDDY",
    "gem": "BUDDY",
    "net": "NET",
    "uncle": "UNCLE",
    "all": "ALL",
}


def _apply_lane(text: str, lane: str) -> str:
    import re

    msg = text.strip()
    key = (lane or "auto").lower()
    prefix = LANE_PREFIX.get(key, "")
    if not prefix or re.match(rf"^{re.escape(prefix)}\b", msg, re.I):
        return msg
    return f"{prefix}: {msg}"


def _inbox_tail(bus, rel: str, n: int = 5) -> str:
    p = bus / rel
    if not safe_is_file(p):
        return "(empty)"
    text = safe_read_text(p)
    chunk = text.split(INBOX_MARKER, 1)[1] if INBOX_MARKER in text else text
    lines = [ln.strip() for ln in chunk.splitlines() if ln.strip() and not ln.startswith("#")]
    if not lines:
        return "(empty)"
    return "\n".join(lines[-n:])


def _recent_brian_lines(n: int = 4) -> str:
    bus = bus_root()
    lines: list[str] = []
    for path in (bus / "TALK.txt", bus / "fleet/bus/BRIAN_INBOX.txt"):
        if not safe_is_file(path):
            continue
        text = safe_read_text(path)
        marker = TALK_MARKER if "TALK" in path.name else INBOX_MARKER
        chunk = text.split(marker, 1)[1] if marker in text else text
        for ln in chunk.splitlines():
            s = ln.strip()
            if s and not s.startswith("#"):
                lines.append(s[:120])
    if not lines:
        return "(nothing yet — type below)"
    return "\n".join(lines[-n:])


def _append_brian_line(text: str, lane: str = "auto") -> dict:
    """Brian types on /goal → TALK + inbox → router."""
    import subprocess
    import sys

    msg = _apply_lane(text, lane)
    if not msg.strip():
        return {"ok": False, "error": "empty"}
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    via = f"goal/{lane}" if lane and lane != "auto" else "goal"
    line = f"[{now} Brian via {via}] {msg.strip()}"

    talk = bus / "TALK.txt"
    inbox = bus / "fleet/bus/BRIAN_INBOX.txt"
    safe_mkdir(inbox.parent)

    if not safe_is_file(talk):
        talk.write_text(
            "BRIAN — talk here.\n\n" + TALK_MARKER + "\n\n",
            encoding="utf-8",
        )
    t = safe_read_text(talk)
    if TALK_MARKER in t:
        head, _ = t.split(TALK_MARKER, 1)
        talk.write_text(f"{head}{TALK_MARKER}\n\n{line}\n", encoding="utf-8")
    else:
        talk.write_text(t + "\n" + line + "\n", encoding="utf-8")

    if not safe_is_file(inbox):
        inbox.write_text(
            "# Brian — one line. CPT routes.\n\n" + INBOX_MARKER + "\n\n",
            encoding="utf-8",
        )
    i = safe_read_text(inbox)
    if INBOX_MARKER in i:
        head, _ = i.split(INBOX_MARKER, 1)
        inbox.write_text(f"{head}{INBOX_MARKER}\n\n{line}\n", encoding="utf-8")
    else:
        inbox.write_text(i + "\n" + line + "\n", encoding="utf-8")

    routed = ""
    route_hint = ""
    try:
        r = subprocess.run(
            [sys.executable, str(STAN / "brian_router.py"), "once"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        routed = "yes" if r.returncode == 0 else "router-warn"
        summary = safe_read_text(bus / "fleet/bus/BRIAN_ROUTED_SUMMARY.txt")
        if "Word:" in summary:
            route_hint = summary.split("Word:")[-1].split("\n")[0].strip()[:120]
    except (OSError, subprocess.SubprocessError):
        routed = "queued"

    ack = bus / "fleet/bus/BRIAN_LAST_POST.txt"
    ack.write_text(
        f"BRIAN_LAST_POST — {now}\nline={line}\nlane={lane}\nrouted={routed}\nroute={route_hint}\n",
        encoding="utf-8",
    )
    return {"ok": True, "line": line, "lane": lane, "routed": routed, "route": route_hint}


def _who() -> dict:
    raw = safe_read_text(WHO_JSON)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return {"entries": [], "updated": None}


LANDING = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{domain}</title>
<style>
  body {{ font-family: system-ui,sans-serif; max-width: 36rem; margin: 0 auto; padding: 1.2rem;
    background: #0f0f1a; color: #eee; }}
  h1 {{ font-size: 1.5rem; color: #ff6b9d; letter-spacing: 0.02em; }}
  .tag {{ color: #888; font-size: 0.9rem; }}
  a {{ color: #7bed9f; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin: 1rem 0; }}
  th, td {{ text-align: left; padding: 0.4rem; border-bottom: 1px solid #333; }}
  th {{ color: #ff6b9d; }}
  .links {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0; }}
  .links a {{ background: #1a1a2e; padding: 0.5rem 0.75rem; border-radius: 8px; text-decoration: none; }}
</style>
</head>
<body>
<h1>{domain}</h1>
<p class="tag">Fleet who's-who · say "hit me dot dev"</p>
<div class="links">
  <a href="/desk"><strong>Design desk</strong></a>
  <a href="/goal"><strong>Fleet goal</strong></a>
  <a href="/fleet"><strong>Fleet board</strong></a>
  <a href="/gem"><strong>GEM watch</strong></a>
  <a href="/team"><strong>Team words</strong></a>
  <a href="/daddy"><strong>Daddy screen</strong></a>
  <a href="/voice"><strong>CPT Voice</strong></a>
  <a href="/who">Who table</a>
  <a href="https://sarah.{domain}/sarah">Sarah</a>
  <a href="/who.json">JSON</a>
</div>
{table}
<p class="tag">Updated {updated}</p>
</body>
</html>"""


def _table_html(data: dict) -> str:
    rows = ["<table><tr><th>id</th><th>callsign</th><th>role</th></tr>"]
    for e in data.get("entries", []):
        rows.append(
            f"<tr><td>{e.get('fleet_id','')}</td><td>{e.get('callsign','')}</td>"
            f"<td>{e.get('role','')}</td></tr>"
        )
    rows.append("</table>")
    return "\n".join(rows)


DESK_CSS = """
  body { font-family: system-ui,sans-serif; max-width: 42rem; margin: 0 auto; padding: 1rem 1.2rem;
    background: #0a0a12; color: #eee; }
  h1 { color: #ff6b9d; font-size: 1.4rem; }
  h2 { color: #ffb347; font-size: 1rem; margin: 1.25rem 0 0.5rem; border-bottom: 1px solid #333; padding-bottom: 0.25rem; }
  .sub { color: #888; font-size: 0.9rem; margin-bottom: 1rem; }
  ul { list-style: none; padding: 0; margin: 0; }
  li { margin: 0.35rem 0; }
  a.btn { display: block; padding: 0.65rem 0.85rem; background: #151525; border: 1px solid #333;
    border-radius: 10px; color: #7bed9f; text-decoration: none; font-size: 0.95rem; }
  a.btn:hover { border-color: #ff6b9d; }
  a.btn small { display: block; color: #666; font-size: 0.75rem; margin-top: 0.2rem; word-break: break-all; }
  .top { margin-bottom: 1rem; }
  .top a { color: #ff6b9d; }
  .ok { color: #7bed9f; }
  .warn { color: #ffb347; }
  .bad { color: #ff6b6b; }
  pre { background: #151525; padding: 0.75rem; border-radius: 8px; font-size: 0.8rem; overflow-x: auto; }
  #holdBtn { display: block; width: 100%; max-width: 20rem; margin: 1.5rem auto; padding: 2rem;
    font-size: 1.25rem; font-weight: 700; border: none; border-radius: 999px; cursor: pointer;
    background: #ff6b9d; color: #0a0a12; touch-action: none; user-select: none; }
  #holdBtn:active, #holdBtn.on { background: #7bed9f; }
  #voiceStatus { text-align: center; color: #888; min-height: 1.5rem; }
  #voiceReply { margin-top: 1rem; }
"""


def _fleet_status_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    lines: list[str] = []

    def bus_snip(rel: str, n: int = 12) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        text = safe_read_text(p).strip()
        return "\n".join(text.splitlines()[:n]) or "(empty)"

    def mtime(rel: str) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return "missing"
        try:
            return datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat(timespec="seconds")
        except OSError:
            return "?"

    puppy = bus_snip("fleet/bus/puppy_outbox.txt", 8)
    puppy_path = bus / "fleet/bus/puppy_outbox.txt"
    puppy_age: float | None = None
    try:
        if safe_is_file(puppy_path):
            puppy_age = (
                datetime.now().astimezone() - datetime.fromtimestamp(puppy_path.stat().st_mtime).astimezone()
            ).total_seconds()
    except OSError:
        puppy_age = None
    puppy_poison = (
        "from: uncle" in puppy.lower()
        or "uncle_scan" in puppy.lower()
        or "net clean" in puppy.lower()
    )
    puppy_ok = (
        puppy_age is not None
        and puppy_age <= 90
        and not puppy_poison
        and "PUPPY CHECKIN — puppy64" in puppy
    )
    gem = bus_snip("fleet/bus/gem_to_cpt.txt", 3)
    aws = bus_snip("fleet/bus/AWS_STATUS.txt", 2)
    vital = bus_snip("fleet/bus/BRIAN_VITAL.txt", 6)
    focus = bus_snip("fleet/bus/CPT_FOCUS.txt", 8)

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<meta http-equiv='refresh' content='30'>",
        f"<title>Fleet board — {_domain()}</title><style>{DESK_CSS}</style></head><body>",
        "<h1>Fleet board</h1>",
        f'<p class="sub">CPT live · refreshes every 30s · {now}',
        ' · <span class="top"><a href="/">hitme</a> · <a href="/desk">desk</a></span></p>',
        "<h2>Focus</h2>",
        f"<pre>{focus}</pre>",
        f"<h2>Boxes</h2><ul>",
        f'<li>CPT <span class="ok">✓</span> — mesh/sarah/desk local</li>',
        f'<li>PUPPY <span class="{"ok" if puppy_ok else "warn"}">{"✓" if puppy_ok else "✗"}</span>'
        f" — needs PUPPY CHECKIN &lt;90s · not NET clean · mtime {mtime('fleet/bus/puppy_outbox.txt')}</li>",
        f'<li>STUDIO <span class="warn">~</span> — uncle loop</li>',
        f'<li>GEM keys — {gem}</li>',
        f'<li>AWS — {aws}</li>',
        "</ul>",
        "<h2>Vital</h2>",
        f"<pre>{vital}</pre>",
        "<h2>Puppy outbox</h2>",
        f"<pre>{puppy}</pre>",
        "<h2>Quick links</h2><ul>",
        '<li><a class="btn" href="/voice">CPT Voice (AWS LLM)<small>/voice</small></a></li>',
        '<li><a class="btn" href="/f/fleet/GEM_BUSY.txt">GEM_BUSY law<small>/f/fleet/GEM_BUSY.txt</small></a></li>',
        '<li><a class="btn" href="/f/fleet/bus/PUPPY_SYNC_FAIL.txt">PUPPY_SYNC_FAIL<small>/f/fleet/bus/PUPPY_SYNC_FAIL.txt</small></a></li>',
        '<li><a class="btn" href="/f/fleet/VAULT_KEEPER.txt">VAULT law<small>/f/fleet/VAULT_KEEPER.txt</small></a></li>',
        "</ul></body></html>",
    ]
    return "".join(parts)


def _fleet_tv_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    def bus_snip(rel: str, n: int = 8) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        text = safe_read_text(p).strip()
        return "\n".join(text.splitlines()[:n]) or "(empty)"

    pri = bus_snip("fleet/bus/AWS_FLEET_PRIORITIES.txt", 12)
    vital = bus_snip("fleet/bus/BRIAN_VITAL.txt", 8)
    delegate = bus_snip("fleet/bus/CPT_DELEGATE_NOW.txt", 10)
    focus = bus_snip("fleet/bus/CPT_FOCUS.txt", 6)
    checkin = bus_snip("fleet/bus/FLEET_CHECKIN.txt", 28)

    tv_css = DESK_CSS + """
  body { max-width: 96vw; font-size: 1.65rem; line-height: 1.45; }
  h1 { font-size: 2.4rem; }
  h2 { font-size: 1.75rem; color: #7bed9f; }
  pre { font-size: 1.35rem; white-space: pre-wrap; }
  .sub { font-size: 1.1rem; }
  .checkin { border: 4px solid #7bed9f; border-radius: 16px; padding: 1rem 1.25rem; margin: 1rem 0; }
  .checkin h2 { margin-top: 0; color: #7bed9f; border: none; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='25'>"
        f"<title>Fleet TV — {_domain()}</title><style>{tv_css}</style></head><body>"
        f"<h1>Fleet roll call</h1>"
        f'<p class="sub">Garage TV · 25s refresh · {now} · <a href="/goal">goal</a></p>'
        f'<div class="checkin"><h2>Who checked in?</h2><pre>{checkin}</pre></div>'
        f"<h2>Focus</h2><pre>{focus}</pre>"
        f"<h2>Delegate</h2><pre>{delegate}</pre>"
        f"<h2>Vital</h2><pre>{vital}</pre>"
        f"<h2>Priorities</h2><pre>{pri}</pre>"
        "</body></html>"
    )


def _checkin_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    board = safe_read_text(bus / "fleet/bus/FLEET_CHECKIN.txt") if safe_is_file(bus / "fleet/bus/FLEET_CHECKIN.txt") else "(run fleet_checkin.py once)"
    css = DESK_CSS + """
  body { max-width: 52rem; font-size: 1.15rem; }
  pre { font-size: 1rem; }
  .board { border: 3px solid #7bed9f; border-radius: 14px; padding: 1rem; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='25'>"
        f"<title>Check-in — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Roll call</h1>"
        f'<p class="sub">25s refresh · {now} · <a href="/tv">TV</a> · <a href="/goal">goal</a></p>'
        f'<div class="board"><pre>{board}</pre></div>'
        "</body></html>"
    )


def _fleet_goal_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    goal_url = _public_goal_url()

    def bus_snip(rel: str, n: int = 14) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        text = safe_read_text(p).strip()
        return "\n".join(text.splitlines()[:n]) or "(empty)"

    goal = bus_snip("fleet/FIRST_PRIORITY.txt", 18)
    stuck = bus_snip("fleet/STUCK_BOARD.txt", 22)
    delegate = bus_snip("fleet/bus/CPT_DELEGATE_NOW.txt", 12)
    pulse = bus_snip("fleet/bus/FLEET_SELF_CHECK.txt", 10)
    checkin = bus_snip("fleet/bus/FLEET_CHECKIN.txt", 22)
    ready = bus_snip("fleet/bus/CPT_READY.txt", 12)
    arch = "fleet/FLEET_ARCHITECTURE.txt · FLEET_FAILOVER.txt · AWS_FIX_ANYONE.txt"
    pri = bus_snip("fleet/bus/AWS_FLEET_PRIORITIES.txt", 10)

    css = DESK_CSS + """
  body { max-width: 52rem; font-size: 1.05rem; }
  .urlbox { background: #1a2a1a; border: 2px solid #7bed9f; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 1rem 0 1.5rem; }
  .urlbox h2 { margin: 0 0 0.5rem; color: #7bed9f; font-size: 1.2rem; border: none; }
  .urlbox code { display: block; font-size: 1.15rem; color: #fff; word-break: break-all;
    margin: 0.35rem 0; }
  .urlbox .hint { color: #888; font-size: 0.85rem; margin-top: 0.5rem; }
  .inboxbox { background: #151525; border: 2px solid #ff6b9d; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 1rem 0 1.5rem; }
  .inboxbox h2 { margin: 0 0 0.75rem; color: #ff6b9d; font-size: 1.2rem; border: none; }
  .inboxbox input { width: 100%; font-size: 1.1rem; padding: 0.75rem; border-radius: 8px;
    border: 1px solid #444; background: #0a0a12; color: #eee; box-sizing: border-box; }
  .inboxbox button { margin-top: 0.6rem; padding: 0.65rem 1.2rem; font-size: 1rem;
    background: #ff6b9d; color: #0a0a12; border: none; border-radius: 8px; cursor: pointer; font-weight: 700; }
  .inboxbox .recent { color: #aaa; font-size: 0.85rem; margin-top: 0.75rem; white-space: pre-wrap; }
  .inboxbox select { margin-top: 0.5rem; padding: 0.45rem; font-size: 0.95rem;
    border-radius: 8px; border: 1px solid #444; background: #0a0a12; color: #eee; }
  .lanebox { background: #12121f; border: 1px solid #333; border-radius: 10px;
    padding: 0.75rem 1rem; margin: 0.75rem 0; font-size: 0.85rem; }
  .lanebox h3 { margin: 0 0 0.35rem; color: #ffb347; font-size: 0.95rem; }
  #brianStatus { color: #7bed9f; min-height: 1.2rem; margin-top: 0.5rem; font-size: 0.95rem; }
  h2 { color: #ffb347; }
  pre { font-size: 0.88rem; }
"""
    recent = _recent_brian_lines(4)
    buddy_in = _inbox_tail(bus, "fleet/bus/BUDDY_INBOX.txt", 3)
    route_sum = bus_snip("fleet/bus/BRIAN_ROUTED_SUMMARY.txt", 10)
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='25'>"
        f"<title>Fleet goal — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Fleet goal</h1>"
        f'<p class="sub">Team board · <a href="/team">one word each</a> · 20s screen on <a href="/daddy">/daddy</a> · 25s refresh · {now} · '
        '<a href="/checkin">roll call</a> · <a href="/fleet">ops</a> · <a href="/tv">TV</a></p>'
        '<div class="urlbox"><h2>TEAM — bookmark this one URL</h2>'
        f'<code>{goal_url}</code>'
        '<p class="hint">Always <strong>hitme.dev</strong> — phone · TV · garage · puppy. '
        f'Local only if tunnel down: <a href="http://127.0.0.1:{PORT}/goal">127.0.0.1:{PORT}</a></p>'
        "</div>"
        '<div class="urlbox" style="border-color:#c9a227"><h2 style="color:#c9a227">HERITAGE — product demo</h2>'
        f'<a class="btn" href="/heritage">Open heritage card <small>{_hitme_url("/heritage")}</small></a>'
        '<p class="hint">Landscape phone · three modes · rotate to flex. Payment path TBD.</p>'
        "</div>"
        '<div class="inboxbox"><h2>Brian — inbox</h2>'
        '<form id="brianForm"><select id="brianLane" name="lane">'
        '<option value="auto">Auto route</option>'
        '<option value="buddy">→ Buddy (Gem pane)</option>'
        '<option value="cpt">→ CPT (Cursor)</option>'
        '<option value="net">→ NET (puppy)</option>'
        '<option value="uncle">→ Uncle (STUDIO)</option>'
        '<option value="all">→ ALL</option>'
        '</select>'
        '<input id="brianLine" name="line" autocomplete="off" '
        'placeholder="one line · BUDDY keys · NET up · UNCLE scan …" />'
        '<button type="submit">Send</button></form>'
        '<p id="brianStatus"></p>'
        f'<div class="recent">Recent:\n{recent}</div>'
        f'<div class="lanebox"><h3>Buddy inbox</h3><pre>{buddy_in}</pre></div>'
        f'<p class="hint"><a href="/inbox">Full inbox</a> · routed summary below</p></div>'
        "<script>"
        "document.getElementById('brianForm').onsubmit=async(e)=>{"
        "e.preventDefault();"
        "const t=document.getElementById('brianLine').value.trim();"
        "const lane=document.getElementById('brianLane').value;"
        "if(!t)return;"
        "document.getElementById('brianStatus').textContent='Sending…';"
        "try{"
        "const r=await fetch('/api/brian',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({text:t,lane})});"
        "const d=await r.json();"
        "document.getElementById('brianStatus').textContent=d.ok?"
        "('Sent → '+(d.route||d.routed||'queued')):('err: '+(d.error||'?'));"
        "if(d.ok)document.getElementById('brianLine').value='';"
        "}catch(x){document.getElementById('brianStatus').textContent='fail';}"
        "};</script>"
        "<h2>Last routed</h2>"
        f"<pre>{route_sum}</pre>"
        "<h2>Roll call — job + check-in</h2>"
        f"<pre>{checkin}</pre>"
        "<h2>CPT ready (autopilot)</h2>"
        f"<pre>{ready}</pre>"
        f'<p class="hint">Architecture: {arch}</p>'
        "<h2>#1 goal now</h2>"
        f"<pre>{goal}</pre>"
        "<h2>Self-check pulse (25s)</h2>"
        f"<pre>{pulse}</pre>"
        "<h2>Delegate queue</h2>"
        f"<pre>{delegate}</pre>"
        "<h2>Priorities (AWS watch)</h2>"
        f"<pre>{pri}</pre>"
        "<h2>Stuck / money</h2>"
        f"<pre>{stuck}</pre>"
        "</body></html>"
    )


def _desk_html() -> str:
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>Design desk — {_domain()}</title><style>{DESK_CSS}</style></head><body>",
        f"<h1>Design desk</h1>",
        '<p class="sub">Click — no hunting paths. '
        '<span class="top"><a href="/">← hitme</a> · <a href="/voice">voice</a></span></p>',
    ]
    for sec in DESK_SECTIONS:
        parts.append(f"<h2>{sec['title']}</h2><ul>")
        for label, href in sec["links"]:
            parts.append(
                f'<li><a class="btn" href="{href}">{label}'
                f"<small>{href}</small></a></li>"
            )
        parts.append("</ul>")
    parts.append("</body></html>")
    return "".join(parts)


def _voice_html() -> str:
    dom = _domain()
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CPT Voice — {dom}</title>
<style>{DESK_CSS}</style></head><body>
<h1>CPT Voice</h1>
<p class="sub">Hold · talk · AWS Bedrock · <a href="/fleet">fleet</a></p>
<p id="voiceStatus">Tap and hold the button · or type below</p>
<button id="holdBtn" type="button">HOLD · talk to CPT</button>
<textarea id="typed" rows="3" style="width:100%;margin-top:1rem;background:#151525;color:#eee;border:1px solid #333;border-radius:8px;padding:0.75rem;" placeholder="Type if mic blocked…"></textarea>
<button type="button" id="sendBtn" style="margin-top:0.5rem;padding:0.75rem 1.25rem;background:#151525;color:#7bed9f;border:1px solid #333;border-radius:8px;">Send typed</button>
<div id="voiceReply"></div>
<script>
const status = document.getElementById('voiceStatus');
const btn = document.getElementById('holdBtn');
const typed = document.getElementById('typed');
const reply = document.getElementById('voiceReply');

function speak(t) {{
  if (!t || !window.speechSynthesis) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(t);
  u.rate = 1.05;
  speechSynthesis.speak(u);
}}

async function sendText(text) {{
  if (!text.trim()) return;
  status.textContent = 'Thinking…';
  reply.innerHTML = '<pre>…</pre>';
  try {{
    const r = await fetch('/api/voice/talk', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{text: text.trim()}})
    }});
    const d = await r.json();
    reply.innerHTML = '<pre>' + (d.reply || d.error || '?') + '</pre>';
    status.textContent = d.ok ? 'Done' : 'Error';
    if (d.ok) speak(d.reply);
    typed.value = '';
    typed.focus();
  }} catch (e) {{
    status.textContent = 'Fetch failed';
    reply.textContent = String(e);
  }}
}}

document.getElementById('sendBtn').onclick = () => sendText(typed.value);

if (window.SpeechRecognition || window.webkitSpeechRecognition) {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SR();
  rec.continuous = false;
  rec.interimResults = false;
  rec.lang = 'en-US';
  let heard = '';
  rec.onresult = ev => {{ heard = ev.results[0][0].transcript; }};
  rec.onend = () => {{ if (heard) sendText(heard); heard = ''; btn.classList.remove('on'); }};
  rec.onerror = ev => {{ status.textContent = 'Mic: ' + ev.error; btn.classList.remove('on'); }};
  const start = () => {{ heard = ''; btn.classList.add('on'); status.textContent = 'Listening…'; try {{ rec.start(); }} catch(x) {{}} }};
  const stop = () => {{ try {{ rec.stop(); }} catch(x) {{}} status.textContent = 'Processing…'; }};
  btn.addEventListener('mousedown', start);
  btn.addEventListener('mouseup', stop);
  btn.addEventListener('mouseleave', stop);
  btn.addEventListener('touchstart', e => {{ e.preventDefault(); start(); }});
  btn.addEventListener('touchend', e => {{ e.preventDefault(); stop(); }});
}} else {{
  status.textContent = 'No speech API — use Type + Send';
}}
</script>
</body></html>"""


def _aws_talk(text: str) -> str:
    import aws_lane as al

    al._load_env()
    return al.load_session().send(text.strip())


def _inbox_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    def snip(rel: str, n: int = 8) -> str:
        return _inbox_tail(bus, rel, n)

    lanes = [
        ("Buddy (Gem)", "fleet/bus/BUDDY_INBOX.txt"),
        ("CPT", "fleet/bus/CPT_BRIAN_INBOX.txt"),
        ("NET", "fleet/bus/NET_INBOX.txt"),
        ("Uncle", "fleet/bus/UNCLE_INBOX.txt"),
        ("Main", "fleet/bus/BRIAN_INBOX.txt"),
    ]
    summary = safe_read_text(bus / "fleet/bus/BRIAN_ROUTED_SUMMARY.txt") if safe_is_file(bus / "fleet/bus/BRIAN_ROUTED_SUMMARY.txt") else "(no routes yet)"
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<meta http-equiv='refresh' content='25'>",
        f"<title>Inbox — {_domain()}</title><style>{DESK_CSS}</style></head><body>",
        "<h1>Fleet inbox</h1>",
        f'<p class="sub">Per-lane · 25s refresh · {now} · '
        '<a href="/goal">goal</a> · <a href="/gem">buddy</a></p>',
        '<div class="inboxbox" style="border:2px solid #ff6b9d;padding:1rem;border-radius:12px;margin:1rem 0">',
        '<h2 style="color:#ff6b9d;margin:0 0 0.5rem">Send</h2>',
        '<form id="inboxForm"><select id="lane"><option value="buddy">Buddy</option>',
        '<option value="cpt">CPT</option><option value="net">NET</option>',
        '<option value="uncle">Uncle</option><option value="all">ALL</option>',
        '<option value="auto">Auto</option></select> ',
        '<input id="line" style="width:60%" placeholder="order…" /> ',
        '<button type="submit">Send</button></form><p id="st"></p></div>',
        "<script>document.getElementById('inboxForm').onsubmit=async(e)=>{e.preventDefault();"
        "const t=document.getElementById('line').value.trim();if(!t)return;"
        "const r=await fetch('/api/brian',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({text:t,lane:document.getElementById('lane').value})});"
        "const d=await r.json();document.getElementById('st').textContent=d.ok?('→ '+(d.route||'sent')):d.error;"
        "if(d.ok)document.getElementById('line').value='';};</script>",
    ]
    for title, rel in lanes:
        parts.append(f"<h2>{title}</h2><pre>{snip(rel, 6)}</pre>")
    parts.append("<h2>Routed summary</h2>")
    parts.append(f"<pre>{summary[:2500]}</pre></body></html>")
    return "".join(parts)


def _gem_watch_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    def bus_snip(rel: str, n: int = 20) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        return "\n".join(safe_read_text(p).strip().splitlines()[:n]) or "(empty)"

    def mtime(rel: str) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return "missing"
        try:
            return datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat(timespec="seconds")
        except OSError:
            return "?"

    keys_md = safe_read_text(bus / "lester/lester_keys.md")
    akia = "YES" if "AKIA" in keys_md else "NO"
    akia_cls = "ok" if akia == "YES" else "bad"

    buddy_in = _inbox_tail(bus, "fleet/bus/BUDDY_INBOX.txt", 8)
    routed = bus_snip("fleet/bus/routed/cb2_chrome.txt", 8)

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<meta http-equiv='refresh' content='25'>",
        f"<title>Buddy watch — {_domain()}</title><style>{DESK_CSS}</style></head><body>",
        "<h1>Buddy watch</h1>",
        f'<p class="sub">Gem pane · 25s refresh · {now}',
        ' · <a href="/inbox">inbox</a> · <a href="/goal">goal</a></p>',
        '<div style="border:2px solid #ff6b9d;padding:1rem;border-radius:12px;margin:1rem 0">',
        '<h2 style="color:#ff6b9d;margin:0 0 0.5rem">Brian → Buddy</h2>',
        '<form id="bf"><input id="bl" style="width:70%" placeholder="order for Buddy…" />',
        '<button type="submit">Send Buddy</button></form><p id="bs"></p></div>',
        "<script>document.getElementById('bf').onsubmit=async(e)=>{e.preventDefault();"
        "const t=document.getElementById('bl').value.trim();if(!t)return;"
        "const r=await fetch('/api/brian',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({text:t,lane:'buddy'})});const d=await r.json();"
        "document.getElementById('bs').textContent=d.ok?'sent':'fail';if(d.ok)document.getElementById('bl').value='';"
        "};</script>",
        f"<h2>Buddy inbox</h2><pre>{buddy_in}</pre>",
        f"<h2>Routed paste (cb2_chrome)</h2><pre>{routed}</pre>",
        f'<h2>Keys on Drive</h2><p>AKIA in lester_keys.md: <span class="{akia_cls}">{akia}</span>',
        f" · mtime {mtime('lester/lester_keys.md')}</p>",
        f"<h2>gem_to_cpt (mtime {mtime('fleet/bus/gem_to_cpt.txt')})</h2>",
        f"<pre>{bus_snip('fleet/bus/gem_to_cpt.txt', 5)}</pre>",
        f"<h2>GEM_UNDERSTAND tail</h2>",
        f"<pre>{bus_snip('fleet/bus/GEM_UNDERSTAND.txt', 15)}</pre>",
        f"<h2>CPT → GEM order</h2>",
        f"<pre>{bus_snip('fleet/bus/cpt_to_gem.txt', 12)}</pre>",
        "<h2>Your one paste (Gemini Chrome tab)</h2>",
        "<pre>KEYS — read fleet/bus/cpt_to_gem.txt on Drive · export AWS to lester/lester_keys.md · post GEM_UNDERSTAND</pre>",
        "</body></html>",
    ]
    return "".join(parts)


def _team_words_html() -> str:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    team_url = _hitme_url("/team")
    boxes = [
        ("Daddy", "DADDY", "Captain · penguin · this box", "#ff6b9d"),
        ("Puppy", "PUPPY", "NET · mesh · tunnel", "#7bed9f"),
        ("Uncle", "UNCLE", "CB1 execute · Gem = loader same box", "#ffb347"),
    ]
    cards = []
    for title, word, hint, color in boxes:
        cards.append(
            f'<div class="card" style="border-color:{color}">'
            f'<p class="box">{title}</p>'
            f'<p class="word" style="color:{color}">{word}</p>'
            f'<p class="hint">{hint}</p></div>'
        )
    css = """
  body { font-family: system-ui,sans-serif; max-width: 96vw; margin: 0 auto; padding: 1rem;
    background: #0a0a12; color: #eee; text-align: center; }
  h1 { font-size: 2rem; color: #ff6b9d; }
  .sub { color: #888; font-size: 1rem; margin-bottom: 1.5rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 1rem; }
  .card { background: #151525; border: 4px solid; border-radius: 20px; padding: 1.5rem 1rem; }
  .box { font-size: 1.1rem; color: #aaa; margin: 0 0 0.5rem; }
  .word { font-size: clamp(3rem, 12vw, 6rem); font-weight: 800; margin: 0; letter-spacing: 0.05em; }
  .hint { font-size: 0.95rem; color: #888; margin: 0.75rem 0 0; }
  .url { background: #1a2a1a; border: 2px solid #7bed9f; border-radius: 12px; padding: 1rem;
    margin: 1.5rem 0; word-break: break-all; font-size: 1.1rem; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='30'>"
        f"<title>Team words — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>One word = machine name</h1>"
        f'<p class="sub">Wakeup · 30s refresh · {now} · '
        f'<a href="/checkin" style="color:#7bed9f">roll call</a> · '
        f'<a href="/goal" style="color:#ffb347">goal</a></p>'
        f'<div class="url"><a href="{team_url}" style="color:#7bed9f">{team_url}</a></div>'
        f'<div class="grid">{"".join(cards)}</div>'
        "<p class=\"sub\">3 machines · Daddy · Puppy · Uncle · Gem = loader on Uncle's box</p>"
        "</body></html>"
    )


def _puppy_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    puppy_url = _hitme_url("/puppy")
    cmd = "bash ~/GoogleDrive/MyDrive/lester/PUPPY_ONE_COMMAND.sh"
    outbox = safe_read_text(bus / "fleet/bus/puppy_outbox.txt") if safe_is_file(bus / "fleet/bus/puppy_outbox.txt") else "(no check-in yet)"
    tail = "\n".join(outbox.splitlines()[-12:])
    css = """
  body { font-family: system-ui,sans-serif; max-width: 40rem; margin: 0 auto; padding: 1.5rem;
    background: #0a0a12; color: #eee; text-align: center; }
  h1 { color: #7bed9f; font-size: 2rem; }
  .one { font-size: clamp(1rem, 4vw, 1.35rem); background: #151525; border: 3px solid #7bed9f;
    border-radius: 16px; padding: 1.25rem; margin: 1.5rem 0; word-break: break-all; }
  .sub { color: #888; font-size: 0.95rem; }
  pre { text-align: left; font-size: 0.8rem; background: #12121f; padding: 1rem; border-radius: 8px;
    overflow-x: auto; color: #aaa; }
  a { color: #ffb347; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='30'>"
        f"<title>Puppy fix — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Puppy</h1>"
        f'<p class="sub">Word: <strong>PUPPY</strong> · {now} · '
        f'<a href="/goal">team board</a></p>'
        '<p class="sub">Run this one command on puppy64:</p>'
        f'<div class="one"><code>bash ~/GoogleDrive/MyDrive/lester/PUPPY_LEASH.sh</code></div>'
        '<p class="sub"><strong>Opens now:</strong> <code>http://127.0.0.1:8770/puppy</code> '
        '(local on puppy — use this if hitme.dev fails)</p>'
        '<p class="sub">Then run on page:</p>'
        f'<div class="one"><code>{cmd}</code></div>'
        '<p class="sub">Then post <code>PUPPY CHECKIN — puppy64 — &lt;ip&gt; — &lt;time&gt;</code> '
        'to <code>fleet/bus/puppy_outbox.txt</code></p>'
        f'<p class="sub">Bookmark: <a href="{puppy_url}">{puppy_url}</a></p>'
        "<h2>Last outbox</h2>"
        f"<pre>{tail}</pre>"
        "</body></html>"
    )


def _daddy_screen_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    meta = safe_read_text(bus / SCREEN_META) if safe_is_file(bus / SCREEN_META) else "(no DADDY_SCREEN.txt yet)"
    delegate = safe_read_text(bus / "fleet/bus/CPT_DELEGATE_NOW.txt") if safe_is_file(bus / "fleet/bus/CPT_DELEGATE_NOW.txt") else "(no delegate queue)"
    ready = safe_read_text(bus / "fleet/bus/CPT_READY.txt") if safe_is_file(bus / "fleet/bus/CPT_READY.txt") else ""
    ts = int(datetime.now().timestamp())
    img_ok = SCREEN_LATEST.is_file()
    img_block = (
        f'<img src="/screen/latest.png?t={ts}" alt="Daddy screen" '
        'style="max-width:100%;border:2px solid #333;border-radius:12px;" />'
        if img_ok
        else '<p class="warn">No capture yet — run bash ~/.stan/daddy_background.sh</p>'
    )
    css = DESK_CSS + """
  body { max-width: 56rem; }
  .screenbox { background: #0a0a12; border: 2px solid #7bed9f; border-radius: 14px;
    padding: 0.75rem; margin: 1rem 0; text-align: center; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='20'>"
        f"<title>Daddy screen — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Daddy screen</h1>"
        f'<p class="sub">Background eyes · 20s refresh · {now} · '
        '<a href="/goal">goal</a> · <a href="/fleet">fleet</a></p>'
        f'<div class="screenbox">{img_block}</div>'
        "<h2>Screen status</h2>"
        f"<pre>{meta[:1200]}</pre>"
        "<h2>Delegate now</h2>"
        f"<pre>{delegate[:1200]}</pre>"
        "<h2>CPT ready</h2>"
        f"<pre>{ready[:800] if ready else '(autopilot)'}</pre>"
        "</body></html>"
    )


@app.route("/voice")
def voice_page():
    return Response(_voice_html(), mimetype="text/html")


@app.route("/api/brian", methods=["POST"])
def api_brian_inbox():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or data.get("line") or "").strip()
    lane = (data.get("lane") or "auto").strip().lower()
    try:
        return jsonify(_append_brian_line(text, lane=lane))
    except OSError as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/inbox")
def inbox_page():
    return Response(_inbox_html(), mimetype="text/html")


@app.route("/api/voice/talk", methods=["POST"])
def api_voice_talk():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    try:
        reply = _aws_talk(text)
        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/f/<path:rel>")
def drive_file(rel: str):
    """Serve bus files as clickable http links (desk + LAN)."""
    try:
        root = DRIVE.resolve()
        path = (DRIVE / rel).resolve()
        if not str(path).startswith(str(root)) or not path.is_file():
            abort(404)
        return send_file(path, mimetype="text/plain; charset=utf-8", download_name=path.name)
    except OSError:
        abort(404)


@app.route("/card")
@app.route("/heritage")
@app.route("/heritage/card_demo.html")
def card_demo():
    if safe_is_file(CARD_DEMO):
        return send_file(CARD_DEMO, mimetype="text/html")
    return Response("card demo missing on bus", status=404)


@app.route("/team")
def team_words_page():
    return Response(_team_words_html(), mimetype="text/html")


@app.route("/puppy")
def puppy_page():
    return Response(_puppy_html(), mimetype="text/html")


@app.route("/daddy")
def daddy_screen_page():
    return Response(_daddy_screen_html(), mimetype="text/html")


@app.route("/screen/latest.png")
def daddy_screen_png():
    if not SCREEN_LATEST.is_file():
        abort(404)
    return send_file(
        SCREEN_LATEST,
        mimetype="image/png",
        download_name="latest.png",
        max_age=0,
        conditional=False,
    )


@app.route("/gem")
def gem_watch_page():
    return Response(_gem_watch_html(), mimetype="text/html")


@app.route("/fleet")
def fleet_page():
    return Response(_fleet_status_html(), mimetype="text/html")


@app.route("/checkin")
def checkin_page():
    return Response(_checkin_html(), mimetype="text/html")


@app.route("/tv")
def fleet_tv_page():
    return Response(_fleet_tv_html(), mimetype="text/html")


@app.route("/goal")
@app.route("/fleet-goal")
def fleet_goal_page():
    return Response(_fleet_goal_html(), mimetype="text/html")


@app.route("/desk")
def desk_page():
    return Response(_desk_html(), mimetype="text/html")


@app.route("/")
def home():
    from flask import redirect

    return redirect("/goal", code=302)


@app.route("/home")
def home_full():
    data = _who()
    dom = _domain()
    html = LANDING.format(
        domain=dom,
        table=_table_html(data),
        updated=data.get("updated") or "—",
    )
    return Response(html, mimetype="text/html")


@app.route("/who")
def who_page():
    return home_full()


@app.route("/who.json")
@app.route("/api/who")
def who_json():
    return jsonify(_who())


@app.route("/health")
def health():
    return jsonify({"ok": True, "domain": _domain(), "port": PORT})


def main():
    safe_mkdir(DRIVE)
    safe_mkdir(DOMAIN_FILE.parent)
    if not safe_is_file(DOMAIN_FILE):
        LOCAL_DOMAIN.write_text("hitme.dev\n", encoding="utf-8")
    app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    main()
