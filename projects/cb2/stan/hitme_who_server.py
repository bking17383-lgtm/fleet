#!/usr/bin/env python3
"""hitme.dev — who roster + fleet links (port 8770)."""
from __future__ import annotations

import json
import html as html_mod
import mimetypes
from datetime import datetime
from pathlib import Path
from urllib.parse import quote as url_quote

from flask import Flask, Response, abort, jsonify, request, send_file

from design_links import DESK_SECTIONS

from bus_lane import bus_root, safe_is_file, safe_read_text, safe_mkdir, STAN, LOGS
from sarah_test_page import for_sarah_html, seminary_preview_html, seminary_application_html
from heartbeat_america import heartbeat_html, dirt_strong_html
from redneck_parcels import parcels_game_html
from pee_page import pee_game_html
from drop_page import drop_page_html

BUS = bus_root()
DRIVE = BUS
WHO_JSON = DRIVE / "fleet/WHO.json"
CARD_DEMO = DRIVE / "lester/heritage/card_demo.html"
PRODUCED = DRIVE / "drop_pile/from_daddy/produced"
KEATON_BUNNY = DRIVE / "drop_pile/from_bbbunny/keaton.html"
KEATON_PRODUCED = PRODUCED / "keaton.html"
KEATON_SOUND_OK = DRIVE / "drop_pile/from_bbbunny/KEATON_SOUND_OK.txt"
KEATON_LANDING_LIVE = DRIVE / "fleet/keaton/LANDING_LIVE.txt"
KEATON_JINGLE = DRIVE / "lester/hitme_simple/keaton/alex_keaton_hes_so_cute_jingle.mp3"
KEATON_JINGLE_SHORT = DRIVE / "drop_pile/from_bbbunny/alex_keaton_hes_so_cute_SHORT.mp3"
DONE_DIR = DRIVE / "drop_pile/done"
DONE_FEED = DRIVE / "fleet/bus/DONE_FEED.txt"
READY_DIR = DRIVE / "drop_pile/ready"
READY_FEED = DRIVE / "fleet/bus/READY_FEED.txt"
PROJECTS_CATALOG = DRIVE / "fleet/PROJECTS_CATALOG.json"
DOMAIN_FILE = DRIVE / "fleet/HITME_DOMAIN.txt"
NEEDS_JSON = DRIVE / "fleet/bus/FLEET_NEEDS.json"
NEEDS_TXT = DRIVE / "fleet/bus/FLEET_NEEDS_SERVER.txt"
SPIN_TXT = DRIVE / "fleet/bus/FLEET_SPIN.txt"
ACTIVITY_MARKER = "--- DADDY ACTIVITY ---"
SCREEN_LATEST = STAN / "screen" / "latest.png"
SCREEN_META = "fleet/bus/DADDY_SCREEN.txt"
LOCAL_DOMAIN = STAN / "fleet/HITME_DOMAIN.local.txt"
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


def _esc(text: str) -> str:
    return html_mod.escape(text or "", quote=True)


def _turf_dir() -> Path:
    for base in (DRIVE, Path.home() / "fleet"):
        p = base / "projects" / "turf-mark"
        if safe_is_file(p / "barn.html"):
            return p
    return Path.home() / "fleet" / "projects" / "turf-mark"


READER_SCRIPT = """
<script>
(function(){
  const KEY='hitme_reader_on';
  const SEQ_KEY='hitme_say_ack';
  const AUTO=(location.search.indexOf('reader=1')>=0||location.pathname.indexOf('/alexa')>=0);
  let lastSpoken='';
  let lastAck=parseInt(localStorage.getItem(SEQ_KEY)||'0',10)||0;
  let readerOn=localStorage.getItem(KEY)==='1'||AUTO;
  let speaking=false;
  const status=document.getElementById('readerStatus');
  const btn=document.getElementById('readerBtn');
  const sayEl=document.getElementById('sayLine');

  function setStatus(t,isErr){
    if(!status)return;
    status.textContent=t;
    status.style.color=isErr?'#ff6b6b':'#888';
  }

  async function markHeard(seq){
    if(!seq||seq<=lastAck)return;
    try{
      await fetch('/api/alexa/ack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seq})});
      lastAck=seq;
      localStorage.setItem(SEQ_KEY,String(seq));
    }catch(e){}
  }

  function speakNow(t,seq){
    if(!t||t.startsWith('('))return false;
    if(!window.speechSynthesis){
      setStatus('Speech blocked — use Chrome/Edge with audio on',true);
      return false;
    }
    try{
      speechSynthesis.cancel();
      const u=new SpeechSynthesisUtterance(t);
      u.rate=1.05;
      u.onerror=e=>{speaking=false;setStatus('Speech error: '+(e.error||'blocked'),true);};
      u.onend=()=>{
        speaking=false;
        if(seq)markHeard(seq);
        setStatus(readerOn?'Mic open — waiting for new line':'Reader off');
      };
      speechSynthesis.speak(u);
      lastSpoken=t;
      speaking=true;
      return true;
    }catch(e){
      speaking=false;
      setStatus('Speech failed: '+e,true);
      return false;
    }
  }

  function syncBtn(){
    if(!btn)return;
    btn.textContent=readerOn?'Mic open · watching':'Mic off';
    btn.style.background=readerOn?'#7bed9f':'#333';
    btn.style.color=readerOn?'#0a0a12':'#ccc';
  }

  async function poll(){
    if(!readerOn||speaking)return;
    try{
      const r=await fetch('/api/alexa/say');
      if(!r.ok){setStatus('API '+r.status,true);return;}
      const d=await r.json();
      if(!d.ok)return;
      const show=d.aloud||'(George)';
      if(sayEl)sayEl.textContent=show;
      if(!d.pending||!d.aloud||d.aloud.startsWith('('))return;
      const seq=d.seq||0;
      if(seq<=lastAck&&d.aloud===lastSpoken)return;
      if(seq<=lastAck)return;
      setStatus('Speaking…');
      speakNow(d.aloud,seq);
    }catch(e){setStatus('Poll failed — server down?',true);}
  }

  if(btn){
    btn.onclick=()=>{
      readerOn=!readerOn;
      localStorage.setItem(KEY,readerOn?'1':'0');
      syncBtn();
      if(readerOn){
        setStatus('Mic open — tap once if silent (browser rule)');
        poll();
      }else{
        try{speechSynthesis.cancel();}catch(x){}
        speaking=false;
        setStatus('Mic off');
      }
    };
    syncBtn();
    if(readerOn){
      setStatus('Mic open — tap button once if silent');
      poll();
    }
  }

  const playBtn=document.getElementById('playBtn');
  if(playBtn){
    playBtn.onclick=async()=>{
      const r=await fetch('/api/alexa/say');
      const d=await r.json();
      if(d.ok&&d.pending&&d.aloud&&speakNow(d.aloud,d.seq))setStatus('Playing…');
    };
  }

  setInterval(()=>{if(readerOn&&!speaking)poll();},12000);
})();
</script>
"""


def _alexa_paths() -> tuple[Path, Path, Path]:
    bus = bus_root()
    return (
        bus / "phone/say.txt",
        bus / "fleet/bus/AWS_SPEAK_ALOUD.txt",
        bus / "fleet/bus/AWS_SPEAK.txt",
    )


def _alexa_last_aloud() -> str:
    try:
        from alexa_queue import status as queue_status

        st = queue_status()
        if st["aloud"]:
            return st["aloud"]
    except Exception:
        pass
    say, aloud, _full = _alexa_paths()
    for p in (say, aloud):
        if safe_is_file(p):
            t = safe_read_text(p).strip()
            if t and not t.startswith("("):
                return t
    return "(George)"


def _alexa_html() -> str:
    dom = _domain()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    say, aloud_path, full_path = _alexa_paths()
    aloud = _alexa_last_aloud()
    full = safe_read_text(full_path).strip() if safe_is_file(full_path) else ""
    fast = safe_read_text(bus_root() / "fleet/ALEXA_FAST.txt").strip()
    fast_snip = "\n".join(fast.splitlines()[:18]) if fast else "(see fleet/ALEXA_FAST.txt on Drive)"
    say_mtime = "—"
    if safe_is_file(say):
        try:
            say_mtime = datetime.fromtimestamp(say.stat().st_mtime).astimezone().isoformat(
                timespec="seconds"
            )
        except OSError:
            pass
    aloud_h = _esc(aloud)
    full_h = _esc(full[:1200] if full else "(none)")
    fast_h = _esc(fast_snip)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="15">
<title>Alexa — {dom}</title>
<style>{DESK_CSS}
  .echobox {{ background: #1a1a2e; border: 2px solid #7bed9f; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 1rem 0; }}
  .echobox h2 {{ margin: 0 0 0.5rem; color: #7bed9f; border: none; font-size: 1.15rem; }}
  .sayline {{ font-size: 1.25rem; color: #fff; line-height: 1.45; }}
  .chip {{ display: inline-block; background: #151525; border: 1px solid #444;
    border-radius: 999px; padding: 0.35rem 0.75rem; margin: 0.25rem 0.35rem 0.25rem 0;
    color: #ffb347; text-decoration: none; font-size: 0.9rem; }}
</style></head><body>
<h1>George · real Echo</h1>
<p class="sub">GL/Alexa-style · your Echo speaks answers · self-upgrades from what you say · Updated {say_mtime} ·
<a href="/goal">goal</a> · <a href="/voice">George</a> · <a href="/f/fleet/GEORGE.txt">card</a></p>
<div class="echobox"><h2>Last line for Echo (phone/say.txt)</h2>
<p class="sayline" id="sayLine" aria-live="polite">{aloud_h}</p>
<button type="button" id="readerBtn" style="margin-top:0.75rem;padding:0.65rem 1.1rem;border:none;border-radius:8px;font-weight:700;cursor:pointer;">Mic off</button>
<button type="button" id="playBtn" style="margin-top:0.75rem;margin-left:0.5rem;padding:0.65rem 1.1rem;background:#151525;color:#7bed9f;border:1px solid #444;border-radius:8px;font-weight:700;cursor:pointer;">Play once</button>
<p id="readerStatus" class="hint" style="color:#888;font-size:0.85rem;margin-top:0.75rem;" aria-live="polite">Show browser only — real Echo uses her own voice from say.txt.</p></div>
<div class="echobox"><h2>One-time Echo speed-up</h2>
<p>Say: <strong>"Alexa, enable Brief Mode"</strong> — shorter replies, chime not "OK got it".</p>
<a class="chip" href="/f/fleet/ALEXA_FAST.txt">ALEXA_FAST.txt</a>
<a class="chip" href="/f/fleet/bus/ALEXA_FIX.txt">ALEXA_FIX.txt</a></div>
<h2>Full bus reply (silent — not for Echo)</h2>
<pre>{full_h}</pre>
<h2>Speed tricks (snippet)</h2>
<pre>{fast_h}</pre>
{READER_SCRIPT}
</body></html>"""


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
SPIN_DEFAULT_PREFIX = "CPT: "


def _normalize_brian_msg(text: str) -> str:
    """Collapse newlines for single-line bus files; keep paragraph breaks visible."""
    parts = [p.strip() for p in text.replace("\r\n", "\n").split("\n") if p.strip()]
    return " · ".join(parts)


def _apply_lane(text: str, lane: str) -> str:
    import re

    msg = _normalize_brian_msg(text)
    key = (lane or "auto").lower()
    prefix = LANE_PREFIX.get(key, "")
    if not prefix or re.match(rf"^{re.escape(prefix)}\s*:?\s", msg, re.I):
        return msg
    return f"{prefix}: {msg}"


def _lane_from_prefix(text: str) -> str:
    import re

    msg = text.strip()
    for lane, prefix in LANE_PREFIX.items():
        if prefix and re.match(rf"^{re.escape(prefix)}\s*:", msg, re.I):
            return lane
    return "auto"


def _resolve_lane(text: str, lane: str) -> str:
    from_prefix = _lane_from_prefix(text)
    if from_prefix != "auto":
        return from_prefix
    return (lane or "auto").lower()


def _has_message_after_prefix(text: str) -> bool:
    import re

    msg = text.strip()
    if not msg:
        return False
    for prefix in LANE_PREFIX.values():
        if prefix and re.match(rf"^{re.escape(prefix)}\s*:\s*$", msg, re.I):
            return False
    return True


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


CPT_OPEN_REL = "fleet/bus/CPT_OPEN.txt"


def _write_cpt_open(url: str, *, label: str = "page") -> None:
    bus = bus_root()
    p = bus / CPT_OPEN_REL
    safe_mkdir(p.parent)
    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    p.write_text(f"CPT_OPEN — {ts}\nurl={url}\nlabel={label}\n", encoding="utf-8")


def _cpt_open_poll_js(*guard_field_ids: str) -> str:
    """Open CPT link in new tab — never while Brian is typing in a brian-field."""
    ids = json.dumps(list(guard_field_ids))
    return f"""<script>
(function(){{
  const guardIds={ids};
  function brianTyping(){{
    const focused=document.querySelector('textarea.brian-field:focus,input.brian-field:focus');
    if(focused)return true;
    for(const id of guardIds){{
      const ta=document.getElementById(id);
      if(!ta)continue;
      if(document.activeElement===ta)return true;
    }}
    return false;
  }}
  let seen='';
  async function poll(){{
    if(brianTyping())return;
    try{{
      const r=await fetch('/api/cpt/open');
      const d=await r.json();
      if(d.ok&&d.url&&d.id&&d.id!==seen){{
        seen=d.id;
        window.open(d.url,'_blank','noopener');
      }}
    }}catch(e){{}}
  }}
  poll();
  setInterval(poll,3000);
}})();
</script>"""


def _brian_draft_guard_js(
    field_id: str,
    storage_key: str,
    refresh_sec: int = 25,
    *,
    poll_url: str | None = None,
    poll_map: dict[str, str] | None = None,
) -> str:
    """Save textarea draft · never reload while Brian types · optional reply poll."""
    fid = json.dumps(field_id)
    key = json.dumps(storage_key)
    poll_url_js = json.dumps(poll_url) if poll_url else "null"
    poll_map_js = json.dumps(poll_map or {})
    return f"""<script>
(function(){{
  const KEY={key};
  const ta=document.getElementById({fid});
  if(!ta)return;
  document.querySelectorAll('meta[http-equiv=refresh]').forEach(m=>m.remove());
  const saved=sessionStorage.getItem(KEY);
  if(saved){{ta.value=saved;ta.setSelectionRange(saved.length,saved.length);}}
  let lastInput=Date.now();
  let composing=false;
  function saveDraft(){{
    if(ta.value)sessionStorage.setItem(KEY,ta.value);
    else sessionStorage.removeItem(KEY);
    lastInput=Date.now();
  }}
  ta.addEventListener('input',saveDraft);
  ta.addEventListener('compositionstart',()=>{{composing=true;}});
  ta.addEventListener('compositionend',()=>{{composing=false;saveDraft();}});
  window.addEventListener('beforeunload',saveDraft);
  window.__clearBrianDraft=function(){{sessionStorage.removeItem(KEY);}};
  function typing(){{
    return document.activeElement===ta||composing||(Date.now()-lastInput<45000)||ta.value.length>0;
  }}
  const pollUrl={poll_url_js};
  const pollMap={poll_map_js};
  async function pollPanels(){{
    if(!pollUrl||typing())return;
    try{{
      const r=await fetch(pollUrl);
      const d=await r.json();
      if(!d.ok)return;
      for(const[id,field] of Object.entries(pollMap)){{
        const el=document.getElementById(id);
        if(el&&d[field]!=null)el.textContent=d[field];
      }}
    }}catch(e){{}}
  }}
  let refreshSec={refresh_sec};
  let timer;
  function scheduleRefresh(){{
    clearTimeout(timer);
    if(typing()){{timer=setTimeout(scheduleRefresh,2000);return;}}
    if(pollUrl){{timer=setTimeout(()=>{{pollPanels();scheduleRefresh();}},refreshSec*1000);return;}}
    timer=setTimeout(()=>location.reload(),refreshSec*1000);
  }}
  ta.addEventListener('focus',()=>clearTimeout(timer));
  ta.addEventListener('blur',scheduleRefresh);
  scheduleRefresh();
}})();
</script>"""


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


def _append_brian_line(text: str, lane: str = "auto", *, via: str = "goal") -> dict:
    """Brian types on /goal → TALK + inbox → router."""
    import subprocess
    import sys

    lane = _resolve_lane(text, lane)
    msg = _apply_lane(text, lane)
    if not _has_message_after_prefix(msg):
        return {"ok": False, "error": "empty"}
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    if via == "goal":
        via_tag = f"goal/{lane}" if lane and lane != "auto" else "goal"
    else:
        via_tag = via
    line = f"[{now} Brian via {via_tag}] {msg.strip()}"

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
    try:
        drop_log = bus / "drop_pile/from_brian/DROP_LOG.txt"
        safe_mkdir(drop_log.parent)
        prev = safe_read_text(drop_log) if safe_is_file(drop_log) else ""
        drop_log.write_text(prev + line + "\n", encoding="utf-8")
    except OSError:
        pass
    try:
        hf = STAN / "handoff"
        safe_mkdir(hf)
        (hf / "brian_drop.txt").write_text(
            f"BRIAN → DADDY\nstamp: {now}\nvia: {via_tag}\nlane: {lane}\n\n{msg.strip()}\n",
            encoding="utf-8",
        )
        (hf / "cb2_job_pending.txt").write_text(
            f"{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')} · Brian drop ({via_tag})\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    if lane in ("cpt", "daddy", "captn"):
        cpt_in = bus / "fleet/bus/CPT_BRIAN_INBOX.txt"
        if not safe_is_file(cpt_in):
            cpt_in.write_text(
                "# Brian → Daddy/CPT lab · plain lines below\n\n" + INBOX_MARKER + "\n\n",
                encoding="utf-8",
            )
        ci = safe_read_text(cpt_in)
        if INBOX_MARKER in ci:
            head, _ = ci.split(INBOX_MARKER, 1)
            cpt_in.write_text(f"{head}{INBOX_MARKER}\n\n{line}\n", encoding="utf-8")
        else:
            cpt_in.write_text(ci + "\n" + line + "\n", encoding="utf-8")
    try:
        from daddy_team_say import announce

        src = "/daddy" if via_tag == "daddy" else "/goal"
        announce(f"Brian posted on {src}", f"lane={lane} · {msg.strip()[:80]}")
    except ImportError:
        pass
    if via_tag == "daddy" and lane in ("cpt", "daddy", "captn", "auto"):
        try:
            _append_spin_note(msg.strip(), who="Brian")
        except OSError:
            pass
        try:
            subprocess.Popen(
                [sys.executable, str(STAN / "cpt_lab_auto.py"), "once"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass
    if lane in ("buddy", "gem"):
        try:
            subprocess.run(
                [sys.executable, str(STAN / "cpt_gem_loop.py"), "forward"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            subprocess.run(
                [sys.executable, str(STAN / "cpt_gem_loop.py"), "listen"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            pass
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
  <a href="/voice"><strong>George</strong></a>
  <a href="/alexa"><strong>Alexa</strong></a>
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
  pre { background: #151525; padding: 0.75rem; border-radius: 8px; font-size: 0.8rem;
    white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere; }
  #holdBtn { display: block; width: 100%; max-width: 20rem; margin: 1.5rem auto; padding: 2rem;
    font-size: 1.25rem; font-weight: 700; border: none; border-radius: 999px; cursor: pointer;
    background: #ff6b9d; color: #0a0a12; touch-action: none; user-select: none; }
  #holdBtn:active, #holdBtn.on { background: #7bed9f; }
  #voiceStatus { text-align: center; color: #888; min-height: 1.5rem; }
  #voiceReply { margin-top: 1rem; }
"""

BRIAN_FIELD_CSS = """
  textarea.brian-field, input.brian-field {
    display: block;
    width: 100%;
    box-sizing: border-box;
    font-family: inherit;
    font-size: 1.05rem;
    line-height: 1.45;
    padding: 0.75rem 0.85rem;
    border-radius: 8px;
    border: 1px solid #444;
    background: #0a0a12;
    color: #eee;
    overflow-wrap: anywhere;
    word-break: break-word;
    white-space: pre-wrap;
    overflow-x: hidden;
    overflow-y: auto;
    resize: vertical;
    min-height: 3rem;
    max-height: 70vh;
  }
  textarea.brian-field {
    field-sizing: content;
    min-height: 5.5rem;
  }
  pre.full-pre, .replybox pre, .loopbox pre, .panel-pre {
    white-space: pre-wrap;
    word-break: break-word;
    overflow-wrap: anywhere;
    max-height: none;
    overflow: visible;
  }
"""


def _textarea_autogrow_js(*field_ids: str) -> str:
    ids = json.dumps(list(field_ids))
    return f"""<script>
(function(){{
  const ids={ids};
  function grow(ta){{
    if(document.activeElement===ta){{
      const start=ta.selectionStart,end=ta.selectionEnd;
      ta.style.height='auto';
      const cap=Math.max(120,Math.floor(window.innerHeight*0.65));
      ta.style.height=Math.min(Math.max(ta.scrollHeight,80),cap)+'px';
      if(start!=null)ta.setSelectionRange(start,end);
      return;
    }}
    ta.style.height='auto';
    const cap=Math.max(120,Math.floor(window.innerHeight*0.65));
    ta.style.height=Math.min(Math.max(ta.scrollHeight,80),cap)+'px';
  }}
  ids.forEach(id=>{{
    const ta=document.getElementById(id);
    if(!ta)return;
    ta.classList.add('brian-field');
    let growTimer;
    ta.addEventListener('input',()=>{{
      clearTimeout(growTimer);
      growTimer=setTimeout(()=>grow(ta),120);
    }});
    if(ta.value)grow(ta);
    else ta.style.minHeight='5.5rem';
  }});
  window.__growBrianField=function(id){{
    const ta=document.getElementById(id);
    if(ta)grow(ta);
  }};
}})();
</script>"""


def _bus_full(rel: str, max_chars: int = 12000) -> str:
    p = bus_root() / rel
    if not safe_is_file(p):
        return f"(missing {rel})"
    text = safe_read_text(p).strip()
    if not text:
        return "(empty)"
    if len(text) > max_chars:
        return text[:max_chars] + "\n… (truncated — full file on Drive)"
    return text


def _needs_payload() -> dict:
    if safe_is_file(NEEDS_JSON):
        try:
            return json.loads(safe_read_text(NEEDS_JSON))
        except json.JSONDecodeError:
            pass
    if safe_is_file(NEEDS_TXT):
        return {"text": safe_read_text(NEEDS_TXT), "roll": "?"}
    return {"roll": "?", "needs": [], "blockers": [], "keyboard": []}


def _needs_html_block() -> str:
    p = _needs_payload()
    if p.get("text"):
        body = p["text"]
    else:
        lines = [
            f"roll: {p.get('roll', '?')}",
            f"from: {p.get('from', '—')}",
            f"time: {p.get('time', '—')}",
            "",
            "NEEDS:",
            *[f"  • {n}" for n in p.get("needs") or []],
            "",
            "BLOCKERS:",
            *[f"  • {b}" for b in p.get("blockers") or []],
            "",
            "KEYBOARD:",
            *[f"  • {k}" for k in p.get("keyboard") or []],
        ]
        body = "\n".join(lines)
    return f'<div class="lanebox"><h3>Fleet needs (server)</h3><pre>{body[:4000]}</pre></div>'


def _spin_activity_lines(bus: Path | None = None) -> list[str]:
    root = bus or bus_root()
    p = root / "fleet/bus/TEAM_ACTIVITY.txt"
    if not safe_is_file(p):
        return []
    text = safe_read_text(p)
    if ACTIVITY_MARKER not in text:
        return []
    _, _, tail = text.partition(ACTIVITY_MARKER)
    return [ln.strip() for ln in tail.strip().splitlines() if ln.strip()][-12:]


def _spin_doing_now(bus: Path | None = None) -> dict[str, str]:
    root = bus or bus_root()
    p = root / "fleet/bus/DADDY_DOING_NOW.txt"
    out: dict[str, str] = {}
    if not safe_is_file(p):
        return out
    for line in safe_read_text(p).splitlines():
        if line.startswith("DADDY DOING NOW — "):
            out["time"] = line.replace("DADDY DOING NOW — ", "").strip()
        elif line.startswith("action: "):
            out["action"] = line[8:].strip()
        elif line.startswith("detail: "):
            out["detail"] = line[8:].strip()
    return out


def _spin_note_lines(bus: Path | None = None) -> list[str]:
    root = bus or bus_root()
    p = root / "fleet/bus/FLEET_SPIN.txt"
    if not safe_is_file(p):
        return []
    return [ln.strip() for ln in safe_read_text(p).splitlines() if ln.strip() and not ln.startswith("FLEET SPIN")][-15:]


def _spin_payload() -> dict:
    bus = bus_root()
    auto = safe_read_text(bus / "fleet/bus/CPT_LAB_AUTO.txt") if safe_is_file(bus / "fleet/bus/CPT_LAB_AUTO.txt") else ""
    lab_status = "idle"
    for ln in auto.splitlines():
        if ln.startswith("status="):
            lab_status = ln.split("=", 1)[1].strip()
            break
    lock_busy = (STAN / "cpt_lab_auto.lock").is_file()
    return {
        "ok": True,
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "doing": _spin_doing_now(bus),
        "activity": _spin_activity_lines(bus),
        "notes": _spin_note_lines(bus),
        "lab_status": lab_status,
        "lab_busy": lab_status in ("busy", "queued") or lock_busy,
    }


def _append_spin_note(text: str, who: str = "Brian") -> dict:
    msg = text.strip()
    if not _has_message_after_prefix(msg):
        return {"ok": False, "error": "empty"}
    line = msg
    safe_mkdir(SPIN_TXT.parent)
    prev = safe_read_text(SPIN_TXT) if safe_is_file(SPIN_TXT) else "FLEET SPIN — live notes while board spins\n\n"
    if "FLEET SPIN" not in prev:
        prev = "FLEET SPIN — live notes while board spins\n\n"
    rows = prev.rstrip().splitlines()
    rows.append(line)
    if len(rows) > 42:
        rows = rows[:2] + rows[-38:]
    SPIN_TXT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return {"ok": True, "line": line}


def _checkin_box_cards(bus: Path | None = None) -> list[dict[str, str]]:
    root = bus or bus_root()
    p = root / "fleet/bus/FLEET_CHECKIN.txt"
    if not safe_is_file(p):
        return []
    cards: list[dict[str, str]] = []
    for raw in safe_read_text(p).splitlines():
        line = raw.strip()
        if not line or line[0] not in "✓✗~":
            continue
        icon = line[0]
        rest = line[2:].strip()
        name = rest.split("(")[0].strip() if "(" in rest else rest.split("—")[0].strip()
        cards.append(
            {
                "name": name,
                "status": "ok" if icon == "✓" else "bad" if icon == "✗" else "warn",
                "summary": rest.split("—")[-1].strip() if "—" in rest else rest,
            }
        )
    return cards


FLEET_SPIN_CSS = """
  .spinbox { position: sticky; top: 0; z-index: 10; background: #0f1525; border: 2px solid #ff6b9d;
    border-radius: 14px; padding: 0.85rem 1rem; margin: 0 0 1rem; box-shadow: 0 4px 24px #0008; }
  .spinbox h2 { margin: 0 0 0.35rem; color: #ff6b9d; font-size: 1rem; border: none; padding: 0; }
  .spin-doing { font-size: 1.02rem; color: #fff; margin: 0.25rem 0; line-height: 1.35; }
  .spin-doing strong { color: #7bed9f; }
  .spin-feed { max-height: 10rem; overflow-y: auto; font-size: 0.82rem; color: #aaa;
    border-top: 1px solid #333; margin-top: 0.5rem; padding-top: 0.45rem; }
  .spin-feed div { margin: 0.22rem 0; word-break: break-word; }
  .spin-form { display: flex; flex-direction: column; gap: 0.45rem; margin-top: 0.55rem; }
  .spin-form .spin-row { display: flex; gap: 0.4rem; align-items: flex-start; }
  .spin-form textarea, .spin-form input { flex: 1; min-width: 0; padding: 0.65rem 0.75rem; border-radius: 8px;
    border: 1px solid #444; background: #0a0a12; color: #eee; font-size: 1rem; font-family: inherit;
    line-height: 1.45; white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word;
    overflow-x: hidden; overflow-y: auto; resize: vertical; min-height: 2.75rem; max-height: 40vh;
    box-sizing: border-box; field-sizing: content; }
  .spin-form button { padding: 0.55rem 0.85rem; background: #ff6b9d; color: #0a0a12; border: none;
    border-radius: 8px; font-weight: 700; cursor: pointer; white-space: nowrap; }
  #spinStatus { font-size: 0.82rem; color: #7bed9f; min-height: 1rem; margin-top: 0.25rem; }
  .boxes { display: grid; grid-template-columns: 1fr 1fr; gap: 0.45rem; margin: 0.5rem 0 1rem; }
  .boxcard { background: #151525; border: 1px solid #333; border-radius: 10px; padding: 0.55rem 0.65rem;
    font-size: 0.86rem; line-height: 1.3; }
  .boxcard .name { font-weight: 700; display: block; }
  .boxcard .sub { color: #888; font-size: 0.78rem; margin-top: 0.15rem; }
  .navrow { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.5rem 0 1rem; }
  .navrow a { padding: 0.4rem 0.65rem; background: #151525; border: 1px solid #333; border-radius: 8px;
    color: #7bed9f; text-decoration: none; font-size: 0.88rem; }
  .navrow a:hover { border-color: #ff6b9d; }
  .fold { margin: 0.75rem 0; }
  .fold summary { cursor: pointer; color: #ffb347; font-weight: 600; padding: 0.35rem 0; }
  .pulse { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #7bed9f;
    animation: fleetpulse 1.2s infinite; margin-right: 0.35rem; vertical-align: middle; }
  @keyframes fleetpulse { 0%,100%{opacity:1} 50%{opacity:0.25} }
  @media (max-width: 420px) { .boxes { grid-template-columns: 1fr; } }
"""

FLEET_SPIN_JS = """
<script>
(function(){
  const PREFIX='CPT: ';
  const feed=document.getElementById('spinFeed');
  const doingEl=document.getElementById('spinDoing');
  const statusEl=document.getElementById('spinStatus');
  const form=document.getElementById('spinForm');
  const input=document.getElementById('spinLine');
  let lastJson='';

  function resetInput(){
    if(!input)return;
    input.value=PREFIX;
    input.focus();
    const pos=PREFIX.length;
    if(input.setSelectionRange)input.setSelectionRange(pos,pos);
    if(window.__growBrianField)window.__growBrianField('spinLine');
  }

  function render(d){
    if(!d||!d.ok)return;
    const act=d.doing||{};
    const action=act.action||'(idle)';
    const detail=act.detail&&act.detail!=='(none)'?' — '+act.detail:'';
    if(doingEl)doingEl.innerHTML='<strong>Daddy:</strong> '+action.replace(/</g,'&lt;')+detail.replace(/</g,'&lt;');
    if(!feed)return;
    const rows=[].concat(d.notes||[],d.activity||[]).slice(-18).reverse();
    feed.innerHTML=rows.length?rows.map(l=>'<div>'+l.replace(/</g,'&lt;')+'</div>').join(''):'<div style="color:#666">Type CPT: … below — browser remembers</div>';
  }

  async function poll(){
    try{
      const r=await fetch('/api/fleet/spin');
      const d=await r.json();
      const j=JSON.stringify(d);
      if(j!==lastJson){lastJson=j;render(d);}
    }catch(e){if(statusEl)statusEl.textContent='Spin poll failed';}
  }

  if(input){
    if(!input.value||input.value==='CPT:')resetInput();
    input.addEventListener('focus',()=>{
      if(!input.value.trim())resetInput();
    });
  }

  if(form&&input){
    form.addEventListener('submit',async e=>{
      e.preventDefault();
      const t=input.value.trim();
      if(!t||t===PREFIX.trim())return;
      if(statusEl)statusEl.textContent='Sending…';
      try{
        const r=await fetch('/api/fleet/spin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
        const d=await r.json();
        if(d.ok){resetInput();if(statusEl)statusEl.textContent='Added — team sees it';poll();}
        else{if(statusEl)statusEl.textContent=d.error||'Failed';}
      }catch(x){if(statusEl)statusEl.textContent='Send failed';}
    });
  }

  poll();
  setInterval(poll,4000);
})();
</script>
"""

DADDY_BUG_JS = """
<script>
(function(){
  const PREFIX='CPT: ';
  const feed=document.getElementById('spinFeed');
  const doingEl=document.getElementById('spinDoing');
  const statusEl=document.getElementById('spinStatus');
  const form=document.getElementById('spinForm');
  const input=document.getElementById('spinLine');
  const busyEl=document.getElementById('daddyBusy');
  let lastJson='';

  function resetInput(){
    if(!input)return;
    input.value=PREFIX;
    input.focus();
    const pos=PREFIX.length;
    if(input.setSelectionRange)input.setSelectionRange(pos,pos);
    if(window.__growBrianField)window.__growBrianField('spinLine');
  }

  function render(d){
    if(!d||!d.ok)return;
    const act=d.doing||{};
    const action=act.action||'(idle)';
    const detail=act.detail&&act.detail!=='(none)'?' — '+act.detail:'';
    if(doingEl)doingEl.innerHTML='<strong>Daddy:</strong> '+action.replace(/</g,'&lt;')+detail.replace(/</g,'&lt;');
    if(busyEl){
      const roll=d.lab_busy||false;
      busyEl.textContent=roll?'Rolling — your bug queues for wake':'Watching — bug wakes Daddy now';
      busyEl.style.color=roll?'#ffb347':'#7bed9f';
    }
    if(!feed)return;
    const rows=[].concat(d.notes||[],d.activity||[]).slice(-18).reverse();
    feed.innerHTML=rows.length?rows.map(l=>'<div>'+l.replace(/</g,'&lt;')+'</div>').join(''):'<div style="color:#666">Type CPT: … below</div>';
  }

  async function poll(){
    try{
      const r=await fetch('/api/daddy/bug');
      const d=await r.json();
      const j=JSON.stringify(d);
      if(j!==lastJson){lastJson=j;render(d);}
    }catch(e){if(statusEl)statusEl.textContent='Poll failed';}
  }

  if(input){
    if(!input.value||input.value==='CPT:')resetInput();
    input.addEventListener('focus',()=>{if(!input.value.trim())resetInput();});
  }

  if(form&&input){
    form.addEventListener('submit',async e=>{
      e.preventDefault();
      const t=input.value.trim();
      if(!t||t===PREFIX.trim())return;
      if(statusEl)statusEl.textContent='Sending…';
      try{
        const r=await fetch('/api/daddy/bug',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
        const d=await r.json();
        if(d.ok){
          resetInput();
          if(statusEl)statusEl.textContent=d.queued?'Queued — Daddy rolling':'Sent — waking Daddy';
          poll();
        }else{if(statusEl)statusEl.textContent=d.error||'Failed';}
      }catch(x){if(statusEl)statusEl.textContent='Send failed';}
    });
  }

  poll();
  setInterval(poll,4000);
})();
</script>
"""


def _daddy_bug_html_block() -> str:
    payload = _spin_payload()
    doing = payload.get("doing") or {}
    action = doing.get("action") or "(idle)"
    detail = doing.get("detail") or ""
    detail_bit = f" — {_esc(detail)}" if detail and detail != "(none)" else ""
    rows = list(payload.get("notes") or []) + list(payload.get("activity") or [])
    feed_html = (
        "".join(f"<div>{_esc(ln)}</div>" for ln in reversed(rows[-18:]))
        or '<div style="color:#666">Type CPT: … below — browser remembers</div>'
    )
    roll = payload.get("lab_busy")
    roll_txt = "Rolling — bug queues" if roll else "Idle — bug wakes now"
    roll_cls = "warn" if roll else "ok"
    return (
        '<div class="spinbox">'
        '<h2><span class="pulse"></span>Bug Daddy while rolling</h2>'
        f'<p id="daddyBusy" class="{roll_cls}" style="margin:0.2rem 0 0.45rem;font-size:0.9rem">{roll_txt}</p>'
        f'<p class="spin-doing" id="spinDoing"><strong>Daddy:</strong> {_esc(action)}{detail_bit}</p>'
        f'<div class="spin-feed" id="spinFeed" aria-live="polite">{feed_html}</div>'
        '<form class="spin-form" id="spinForm">'
        f'<textarea id="spinLine" class="brian-field" name="daddy-bug" rows="2" autocomplete="on" '
        f'placeholder="CPT: interrupt me…">{_esc(SPIN_DEFAULT_PREFIX)}</textarea>'
        '<div class="spin-row"><button type="submit">Bug</button></div></form>'
        '<p id="spinStatus"></p>'
        '<p class="sub" style="margin:0.35rem 0 0;font-size:0.75rem">CPT: prefix · live feed · queues if rolling</p>'
        "</div>"
    )


def _fleet_spin_html_block() -> str:
    payload = _spin_payload()
    doing = payload.get("doing") or {}
    action = doing.get("action") or "(idle)"
    detail = doing.get("detail") or ""
    detail_bit = f" — {_esc(detail)}" if detail and detail != "(none)" else ""
    rows = list(payload.get("notes") or []) + list(payload.get("activity") or [])
    feed_html = (
        "".join(f"<div>{_esc(ln)}</div>" for ln in reversed(rows[-18:]))
        or '<div style="color:#666">Nothing spinning yet — add a note below</div>'
    )
    return (
        '<div class="spinbox">'
        '<h2><span class="pulse"></span>Live spin</h2>'
        f'<p class="spin-doing" id="spinDoing"><strong>Daddy:</strong> {_esc(action)}{detail_bit}</p>'
        f'<div class="spin-feed" id="spinFeed" aria-live="polite">{feed_html}</div>'
        '<form class="spin-form" id="spinForm">'
        f'<textarea id="spinLine" class="brian-field" name="fleet-spin" rows="2" autocomplete="on" '
        f'placeholder="CPT: your note…">{_esc(SPIN_DEFAULT_PREFIX)}</textarea>'
        '<div class="spin-row"><button type="submit">Add</button></div></form>'
        '<p id="spinStatus"></p>'
        '<p class="sub" style="margin:0.35rem 0 0;font-size:0.75rem">Prefix in field · browser autofill · NET: UNCLE: BUDDY: work too</p>'
        "</div>"
    )


def _fleet_status_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    fleet_css = DESK_CSS + FLEET_SPIN_CSS + """
  body { max-width: 48rem; }
  pre { font-size: 0.82rem; max-height: 12rem; overflow-y: auto; }
"""

    def bus_snip(rel: str, n: int = 8) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        text = safe_read_text(p).strip()
        return "\n".join(text.splitlines()[:n]) or "(empty)"

    focus = bus_snip("fleet/bus/CPT_FOCUS.txt", 6)
    vital = bus_snip("fleet/bus/BRIAN_VITAL.txt", 5)
    cards = _checkin_box_cards(bus)
    box_html = "".join(
        f'<div class="boxcard"><span class="{c["status"]}">{("✓" if c["status"]=="ok" else "✗" if c["status"]=="bad" else "~")}</span> '
        f'<span class="name">{_esc(c["name"])}</span>'
        f'<span class="sub">{_esc(c["summary"])}</span></div>'
        for c in cards
    ) or '<div class="boxcard"><span class="warn">~</span><span class="name">Roll call</span><span class="sub">run fleet_checkin.py</span></div>'

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<meta http-equiv='refresh' content='45'>",
        f"<title>Fleet board — {_domain()}</title><style>{fleet_css}</style></head><body>",
        "<h1>Fleet board</h1>",
        f'<p class="sub">Ops · <a href="https://fleet.hitme.dev">fleet.hitme.dev</a> · 45s refresh · {now}</p>',
        '<div class="navrow">',
        '<a href="/goal">goal</a>',
        '<a href="/checkin">roll call</a>',
        '<a href="/george">George</a>',
        '<a href="/lab">lab</a>',
        '<a href="/desk">desk</a>',
        "</div>",
        _fleet_spin_html_block(),
        "<h2>Who checked in</h2>",
        f'<div class="boxes">{box_html}</div>',
        '<details class="fold"><summary>Focus</summary>',
        f"<pre>{_esc(focus)}</pre></details>",
        '<details class="fold"><summary>Brian vital</summary>',
        f"<pre>{_esc(vital)}</pre></details>",
        _needs_html_block(),
        "</body>",
        FLEET_SPIN_JS,
        _textarea_autogrow_js("spinLine"),
        "</html>",
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
        f"{_needs_html_block()}"
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
    stamps = bus_snip("fleet/bus/STAMPS.txt", 8)
    delegate = bus_snip("fleet/bus/CPT_DELEGATE_NOW.txt", 12)
    pulse = bus_snip("fleet/bus/FLEET_SELF_CHECK.txt", 10)
    checkin = bus_snip("fleet/bus/FLEET_CHECKIN.txt", 22)
    ready = bus_snip("fleet/bus/CPT_READY.txt", 12)
    arch = "fleet/FLEET_ARCHITECTURE.txt · FLEET_FAILOVER.txt · AWS_FIX_ANYONE.txt"
    pri = bus_snip("fleet/bus/AWS_FLEET_PRIORITIES.txt", 10)

    css = DESK_CSS + BRIAN_FIELD_CSS + """
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
  .inboxbox input, .inboxbox textarea { width: 100%; font-size: 1.1rem; padding: 0.75rem; border-radius: 8px;
    border: 1px solid #444; background: #0a0a12; color: #eee; box-sizing: border-box; font-family: inherit; }
  .inboxbox textarea { min-height: 5.5rem; resize: vertical; line-height: 1.45; }
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
        f"<title>Fleet goal — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Fleet goal</h1>"
        f'<p class="sub">Team board · <a href="/team"><strong>one word · dogbarf</strong></a> · <a href="/gem"><strong>Gem watch</strong></a> · <a href="/alexa">Alexa</a> · <a href="/voice">voice</a> · 20s screen on <a href="/daddy">/daddy</a> · 25s refresh · {now} · '
        '<a href="/checkin">roll call</a> · <a href="/fleet">ops</a> · <a href="/tv">TV</a></p>'
        '<div class="urlbox" style="border-color:#7bed9f;background:#0f1a14"><h2 style="color:#7bed9f">Stamps — nobody waits blind</h2>'
        f'<pre style="margin:0;font-size:0.95rem">{stamps}</pre>'
        '<p class="hint">fleet/STAMP_LAW.txt · if waiting with no stamp → ping Daddy</p></div>'
        '<div class="urlbox" style="border-color:#ffb347;background:#1a1520"><h2 style="color:#ffb347">Alexa — last aloud</h2>'
        f'<p class="sayline" id="sayLine" aria-live="polite" style="font-size:1.1rem;color:#fff;margin:0.35rem 0">{_esc(_alexa_last_aloud()[:220])}</p>'
        '<button type="button" id="readerBtn" style="padding:0.5rem 1rem;border:none;border-radius:8px;font-weight:700;cursor:pointer;margin-right:0.5rem;">Mic off</button>'
        '<button type="button" id="playBtn" style="padding:0.5rem 1rem;background:#151525;color:#7bed9f;border:1px solid #444;border-radius:8px;cursor:pointer;">Play once</button>'
        '<p id="readerStatus" class="hint" style="margin-top:0.5rem;" aria-live="polite">Real Echo in room · say.txt once each line.</p>'
        '<p class="hint"><a href="/alexa"><strong>Full Alexa page →</strong></a></p></div>'
        '<div class="urlbox"><h2>TEAM — bookmark this one URL</h2>'
        f'<code>{goal_url}</code>'
        '<p class="hint">Always <strong>hitme.dev</strong> — phone · TV · garage · puppy. '
        f'Local only if tunnel down: <a href="http://127.0.0.1:{PORT}/goal">127.0.0.1:{PORT}</a></p>'
        "</div>"
        '<div class="inboxbox"><h2>Brian — inbox</h2>'
        '<form id="brianForm"><select id="brianLane" name="lane">'
        '<option value="auto">Auto route</option>'
        '<option value="buddy">→ Buddy (Gem pane)</option>'
        '<option value="cpt" selected>→ CPT (Cursor · auto)</option>'
        '<option value="net">→ NET (puppy)</option>'
        '<option value="uncle">→ Uncle (STUDIO)</option>'
        '<option value="all">→ ALL</option>'
        '</select>'
        '<textarea id="brianLine" class="brian-field" name="brian-inbox" rows="5" autocomplete="on" '
        f'placeholder="CPT: type here — browser remembers · NET: UNCLE: BUDDY: too">{_esc(SPIN_DEFAULT_PREFIX)}</textarea>'
        '<button type="submit">Send</button></form>'
        '<p id="brianStatus"></p>'
        '<p class="hint">Draft saved while you type · refresh waits · Ctrl+Enter sends · dropdown = backup route</p>'
        f'<div class="recent" id="goalRecent">Recent:\n{recent}</div>'
        f'<div class="lanebox"><h3>Buddy inbox</h3><pre>{buddy_in}</pre></div>'
        f'<p class="hint"><a href="/inbox">Full inbox</a> · routed summary below</p></div>'
        "<script>"
        "const BRIAN_PREFIX='CPT: ';"
        "function resetBrianInput(){"
        "const el=document.getElementById('brianLine');"
        "if(!el)return;"
        "el.value=BRIAN_PREFIX;"
        "if(document.activeElement===el)el.setSelectionRange(BRIAN_PREFIX.length,BRIAN_PREFIX.length);"
        "}"
        "async function sendBrianForm(){"
        "const t=document.getElementById('brianLine').value.trim();"
        "const lane=document.getElementById('brianLane').value;"
        "if(!t||t===BRIAN_PREFIX.trim())return;"
        "document.getElementById('brianStatus').textContent='Sending…';"
        "try{"
        "const r=await fetch('/api/brian',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({text:t,lane})});"
        "const d=await r.json();"
        "document.getElementById('brianStatus').textContent=d.ok?"
        "('Sent → '+(d.route||d.routed||'queued')):('err: '+(d.error||'?'));"
        "if(d.ok){resetBrianInput();if(window.__clearBrianDraft)window.__clearBrianDraft();}"
        "}catch(x){document.getElementById('brianStatus').textContent='fail';}"
        "}"
        "document.getElementById('brianForm').onsubmit=async(e)=>{e.preventDefault();await sendBrianForm();};"
        "document.getElementById('brianLine').addEventListener('keydown',(e)=>{"
        "if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();sendBrianForm();}"
        "});"
        "if(sessionStorage.getItem('goal_brian_draft')===null)resetBrianInput();"
        "</script>"
        f"{_brian_draft_guard_js('brianLine', 'goal_brian_draft', 25, poll_url='/api/goal/status', poll_map={'goalRecent': 'recent'})}"
        f"{_textarea_autogrow_js('brianLine')}"
        "<h2>Last routed</h2>"
        f"<pre>{route_sum}</pre>"
        f"{_needs_html_block()}"
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
        f"{READER_SCRIPT}"
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


def _voice_html(*, float_mode: bool = False, host: str = "") -> str:
    dom = _domain()
    h = (host or "").split(":")[0].lower()
    if h.startswith("george."):
        public = f"https://{h}/"
        bookmark = public + "?float=1"
    else:
        public = f"https://{dom}/george"
        bookmark = f"https://george.{dom}/" if dom else public
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0a0a12">
<link rel="manifest" href="/george/manifest.json">
<title>George — {dom}</title>
<style>{DESK_CSS}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: #0a0a12; color: #eee; }}
body {{ max-width: 28rem; margin: 0 auto; padding: 1rem 1rem 6rem; }}
body.float-mode {{ padding: 0.75rem 0.75rem 5.5rem; }}
.pageChrome {{ }}
#learnBadge {{ font-size: 0.9rem; padding: 0.35rem 0; }}
#voiceStatus {{ font-size: 1rem; font-weight: 700; }}
#transcriptBox {{ margin: 0.75rem 0 1rem; text-align: left; }}
#liveRow {{ display: flex; align-items: center; gap: 0.5rem; margin: 0.65rem 0 0.85rem;
  padding: 0.55rem 0.75rem; background: #12121f; border: 1px solid #333; border-radius: 10px; }}
#liveDot {{ width: 11px; height: 11px; border-radius: 50%; background: #555; flex-shrink: 0; }}
#liveDot.on {{ background: #7bed9f; box-shadow: 0 0 0 0 rgba(123,237,159,0.5);
  animation: livepulse 1.4s infinite; }}
#liveDot.think {{ background: #ffb347; animation: none; }}
#liveDot.speak {{ background: #ff6b9d; animation: livepulse 1s infinite; }}
@keyframes livepulse {{ 0%,100% {{ box-shadow: 0 0 0 0 rgba(123,237,159,0.45); }} 50% {{ box-shadow: 0 0 0 7px rgba(123,237,159,0); }} }}
#liveLabel {{ font-size: 0.92rem; font-weight: 700; flex: 1; text-align: left; }}
#liveHint {{ font-size: 0.75rem; color: #888; margin: -0.35rem 0 0.65rem; text-align: left; }}
.txLabel {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  color: #888; margin: 0.5rem 0 0.2rem; }}
.txLabel.you {{ color: #ffb347; }}
  .txTurn {{ margin: 0.65rem 0 0.85rem; padding-bottom: 0.65rem; border-bottom: 1px solid #222; }}
  .txTurn:last-child {{ border-bottom: none; }}
  .txTurn .g {{ color: #7bed9f; font-size: 0.95rem; white-space: pre-wrap; word-break: break-word; margin: 0.25rem 0 0; }}
  #voiceReply {{ max-height: min(42vh, 20rem); overflow-y: auto; }}
#heardLine {{ color: #ffb347; font-size: 1.05rem; min-height: 1.4rem; line-height: 1.4;
  white-space: pre-wrap; word-break: break-word; margin: 0; }}
#heardInterim {{ color: #888; font-size: 0.88rem; min-height: 1rem; font-style: italic; margin: 0; }}
#micBtn {{
  border: none; border-radius: 999px; cursor: pointer; font-weight: 800;
  background: #484f58; color: #e6edf3; touch-action: manipulation;
}}
#micBtn.on {{ background: #e67e22; color: #0a0a12; animation: pulse 2s infinite; }}
@keyframes pulse {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.03); }} }}
#typed {{ width: 100%; background: #151525; color: #eee; border: 1px solid #333;
  border-radius: 0.75rem; padding: 0.75rem; font-size: 1rem; }}
#sendBtn {{ width: 100%; margin-top: 0.5rem; padding: 0.75rem; font-size: 1rem;
  background: #151525; color: #7bed9f; border: 1px solid #333; border-radius: 0.75rem; }}
#voiceReply pre {{ background: #0a0a12; border: 1px solid #333; border-radius: 0.75rem;
  padding: 0.75rem; font-size: 0.95rem; white-space: pre-wrap; word-break: break-word;
  max-height: none; overflow: visible; margin: 0; }}
.oneMic {{ font-size: 0.75rem; color: #888; margin: 0.25rem 0; }}
#georgeFloat {{
  display: none; position: fixed; left: 0; right: 0; bottom: 0; z-index: 2147483646;
  padding: 0 0.5rem calc(0.5rem + env(safe-area-inset-bottom, 0px));
  pointer-events: none;
}}
body.float-mode #georgeFloat {{ display: block; }}
body.float-mode .pageMic {{ display: none; }}
.floatShell {{
  pointer-events: auto; background: rgba(10,10,18,0.94); backdrop-filter: blur(12px);
  border: 1px solid #333; border-radius: 1.1rem 1.1rem 0.85rem 0.85rem;
  box-shadow: 0 -8px 32px rgba(0,0,0,0.55); overflow: hidden;
}}
.floatBar {{
  display: flex; align-items: center; gap: 0.5rem; padding: 0.55rem 0.65rem;
}}
.floatBar #micBtn {{ flex: 0 0 auto; min-width: 4.5rem; min-height: 3.2rem; padding: 0 1rem; font-size: 0.85rem; }}
.floatBar #voiceStatus {{ flex: 1; font-size: 0.85rem; min-height: auto; margin: 0; }}
#expandBtn {{
  flex: 0 0 auto; width: 2.5rem; height: 2.5rem; border-radius: 999px;
  border: 1px solid #444; background: #151525; color: #7bed9f; font-size: 1rem;
}}
#floatPanel {{ display: none; padding: 0 0.65rem 0.65rem; border-top: 1px solid #222; }}
#floatPanel.open {{ display: block; }}
.pageMic #micBtn {{ display: block; width: 100%; min-height: 4.5rem; margin: 0.75rem 0; font-size: 1.35rem; }}
</style></head><body class="float-mode">
<div class="pageChrome">
<h1>George</h1>
<p class="sub">Front-end · Daddy back-end · <a href="/lab">lab</a> · bookmark <strong>{public}</strong></p>
<p class="sub warn" style="color:#ff6b6b;font-size:.85rem">george.hitme.dev = dead DNS · use {public}</p>
<p id="netNote" class="oneMic"></p>
<p id="learnBadge">Loading…</p>
<div id="liveRow"><span id="liveDot"></span><span id="liveLabel">Tap MIC — talk live</span></div>
<p id="liveHint">Type works · voice needs MIC tap · tap MIC again while George talks to stop him</p>
<p class="oneMic" id="voiceNote">Voice: loading…</p>
<p class="oneMic" id="oneMicNote">One mic only — close George on other phones/tabs</p>
<div id="transcriptBox">
  <p class="txLabel you">You said</p>
  <p id="heardLine">(mic or type below)</p>
  <p id="heardInterim"></p>
  <p class="txLabel george">George</p>
  <div id="voiceReply"><pre>…</pre></div>
</div>
</div>
<div id="georgeFloat">
  <div class="floatShell">
    <div class="floatBar">
      <button id="micBtn" type="button">MIC</button>
      <div id="voiceStatus">Starting…</div>
      <button id="expandBtn" type="button" aria-label="Expand">▲</button>
    </div>
    <div id="floatPanel">
      <textarea id="typed" rows="2" placeholder="Type if mic blocked…"></textarea>
      <button type="button" id="sendBtn">Send typed</button>
    </div>
  </div>
</div>
<script>
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) || window.innerWidth < 720;
if (isMobile || location.search.indexOf('float=1')>=0) document.body.classList.add('float-mode');
const floatMode = document.body.classList.contains('float-mode');
const status = document.getElementById('voiceStatus');
const heardLine = document.getElementById('heardLine');
const heardInterim = document.getElementById('heardInterim');
const micBtn = document.getElementById('micBtn');
const typed = document.getElementById('typed');
const reply = document.getElementById('voiceReply');
const expandBtn = document.getElementById('expandBtn');
const floatPanel = document.getElementById('floatPanel');
const liveDot = document.getElementById('liveDot');
const liveLabel = document.getElementById('liveLabel');
let micOn = false, speaking = false, sending = false, learnMode = false, lastReplyAt = 0;
let georgeVoice = null, speechUnlocked = false;
const SPEAK_COOLDOWN_MS = 2800;
const GEORGE_PITCH = 0.86;
const GEORGE_RATE = 0.91;
let georgeAudio = null;

function pickGeorgeVoice() {{
  if (!window.speechSynthesis) return null;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;
  const en = voices.filter(v => /^en([_-]|$)/i.test(v.lang || ''));
  const pool = en.length ? en : voices;
  const female = /female|samantha|zira|victoria|karen|moira|fiona|alice|susan|anna|kate|serena|tessa|google uk english female/i;
  const prefer = [
    /Daniel/i, /Alex/i, /Fred/i, /David/i, /Aaron/i, /Guy/i, /Mark/i, /James/i, /Tom/i,
    /Microsoft David/i, /Microsoft Guy/i, /Microsoft Mark/i,
    /Google US English/i, /en-us.*male/i, /Male/i, /com.apple.voice.compact.en-US.Alex/i
  ];
  for (const pat of prefer) {{
    const hit = pool.find(v => pat.test(v.name) && !female.test(v.name));
    if (hit) return hit;
  }}
  return pool.find(v => !female.test(v.name)) || pool[0] || null;
}}

function initGeorgeVoice() {{
  georgeVoice = pickGeorgeVoice();
  const note = document.getElementById('voiceNote');
  if (!note) return;
  if (georgeVoice) {{
    const short = georgeVoice.name.split(/[ (]/).slice(0, 2).join(' ');
    note.textContent = isMobile ? 'Voice: George · natural male' : ('Voice: ' + short + ' · natural male');
  }} else {{
    note.textContent = 'Voice: George · natural male';
  }}
}}
if (window.speechSynthesis) {{
  speechSynthesis.onvoiceschanged = initGeorgeVoice;
  initGeorgeVoice();
  setTimeout(initGeorgeVoice, 300);
  setTimeout(initGeorgeVoice, 1200);
}}
const TAB_ID = sessionStorage.getItem('george_tab') || ('g'+Math.random().toString(36).slice(2,9));
sessionStorage.setItem('george_tab', TAB_ID);
const MIC_KEY = 'george_mic_lock';

function claimMic() {{
  try {{
    const raw = localStorage.getItem(MIC_KEY);
    const lock = raw ? JSON.parse(raw) : null;
    const now = Date.now();
    if (lock && lock.id !== TAB_ID && (now - lock.ts) < 12000) {{
      status.textContent = 'Mic busy — close other George tab';
      document.getElementById('oneMicNote').textContent = 'Another tab has the mic. Close it here or there.';
      return false;
    }}
    localStorage.setItem(MIC_KEY, JSON.stringify({{id: TAB_ID, ts: now}}));
    return true;
  }} catch(e) {{ return true; }}
}}
function heartbeatMic() {{
  if (!micOn) return;
  try {{ localStorage.setItem(MIC_KEY, JSON.stringify({{id: TAB_ID, ts: Date.now()}})); }} catch(e) {{}}
}}
setInterval(heartbeatMic, 4000);

async function loadLearnMode() {{
  try {{
    const [lr, st] = await Promise.all([
      fetch('/api/alexa/learn').then(r=>r.json()),
      fetch('/api/george/status').then(r=>r.json()).catch(()=>({{}}))
    ]);
    learnMode = lr.learn !== false;
    const badge = learnMode ? 'LEARN only — tap MIC still talks' : 'LIVE · George talks back';
    document.getElementById('learnBadge').textContent = badge;
  }} catch (e) {{ learnMode = false; document.getElementById('learnBadge').textContent = 'LIVE · George talks back'; }}
}}
loadLearnMode();

function setLive(state, label) {{
  liveDot.className = '';
  if (state === 'listen') {{ liveDot.classList.add('on'); }}
  else if (state === 'think') {{ liveDot.classList.add('think'); }}
  else if (state === 'speak') {{ liveDot.classList.add('speak'); }}
  else if (state === 'on') {{ liveDot.classList.add('on'); }}
  liveLabel.textContent = label;
}}

function micStatus() {{
  if (sending) return 'George thinking…';
  if (speaking) return 'George speaking…';
  return micOn ? 'Listening — talk now' : 'Tap MIC to talk';
}}

function appendTurn(you, george, meta) {{
  const box = document.getElementById('voiceReply');
  if (box.querySelector('pre') && box.children.length === 1) box.innerHTML = '';
  const turn = document.createElement('div');
  turn.className = 'txTurn';
  const y = document.createElement('p');
  y.className = 'txLabel you';
  y.textContent = 'You';
  const yt = document.createElement('p');
  yt.textContent = you;
  const gl = document.createElement('p');
  gl.className = 'txLabel george';
  gl.textContent = 'George' + (meta ? ' · ' + meta : '');
  const gt = document.createElement('p');
  gt.className = 'g';
  gt.textContent = george;
  turn.appendChild(y); turn.appendChild(yt); turn.appendChild(gl); turn.appendChild(gt);
  box.appendChild(turn);
  box.scrollTop = box.scrollHeight;
}}

function stopSpeaking() {{
  try {{ speechSynthesis.cancel(); }} catch(x) {{}}
  if (georgeAudio) {{ try {{ georgeAudio.pause(); georgeAudio.src = ''; }} catch(x) {{}} georgeAudio = null; }}
  speaking = false;
  setLive(micOn ? 'listen' : 'idle', micOn ? 'Listening — your turn' : 'Tap MIC to talk live');
  status.textContent = micStatus();
}}

function speakDone() {{
  speaking = false;
  lastReplyAt = Date.now();
  heardInterim.textContent = '';
  setLive(micOn ? 'listen' : 'idle', micOn ? 'Listening — your turn' : 'Tap MIC for next line');
  status.textContent = micStatus();
  if (micOn && recOpen && claimMic()) setTimeout(() => {{ try {{ recOpen.start(); }} catch(x) {{}} }}, SPEAK_COOLDOWN_MS);
}}

function speakBrowser(t) {{
  if (!window.speechSynthesis) {{ speakDone(); return; }}
  speechSynthesis.cancel();
  const chunks = String(t).match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [String(t)];
  let idx = 0;
  function speakNext() {{
    if (idx >= chunks.length) {{ speakDone(); return; }}
    const bit = chunks[idx++].trim();
    if (!bit) {{ speakNext(); return; }}
    const u = new SpeechSynthesisUtterance(bit);
    applyGeorgeVoice(u);
    u.onend = () => {{ setTimeout(speakNext, 140); }};
    u.onerror = () => {{ stopSpeaking(); }};
    speechSynthesis.speak(u);
  }}
  speakNext();
}}

async function speakServer(t) {{
  try {{
    const r = await fetch('/api/george/tts', {{
      method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{text: t}})
    }});
    if (!r.ok) throw new Error('tts ' + r.status);
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    if (georgeAudio) {{ try {{ georgeAudio.pause(); }} catch(x) {{}} }}
    georgeAudio = new Audio(url);
    georgeAudio.onended = () => {{ URL.revokeObjectURL(url); georgeAudio = null; speakDone(); }};
    georgeAudio.onerror = () => {{ URL.revokeObjectURL(url); georgeAudio = null; speakBrowser(t); }};
    await georgeAudio.play();
  }} catch (e) {{
    speakBrowser(t);
  }}
}}

function speak(t) {{
  if (!t) return;
  speaking = true;
  setLive('speak', 'George speaking…');
  status.textContent = 'George speaking… · tap MIC to stop';
  if (micOn && recOpen) {{ try {{ recOpen.stop(); }} catch(x) {{}} }}
  try {{ speechSynthesis.cancel(); }} catch(x) {{}}
  speakServer(t);
}}

async function sendText(text) {{
  const msg = text.trim();
  if (!msg || sending) return;
  if (!deskLinked) {{
    status.textContent = 'Not linked — wait or reload';
    await pingGeorge();
    if (!deskLinked) return;
  }}
  sending = true;
  setLive('think', 'George heard you · thinking…');
  status.textContent = 'George heard you · thinking…';
  heardLine.textContent = msg;
  heardInterim.textContent = '';
  if (!floatPanel.classList.contains('open')) {{ floatPanel.classList.add('open'); expandBtn.textContent = '▼'; }}
  const t0 = Date.now();
  try {{
    const body = {{text: msg, source: 'voice', mode: 'execute'}};
    const r = await fetch('/api/voice/talk', {{
      method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(body)
    }});
    if (!r.ok) throw new Error('server ' + r.status);
    const d = await r.json();
    const display = d.reply || d.full || d.error || '?';
    const toSpeak = d.speak || d.aloud || display;
    const modeTag = d.mode === 'learn' ? ' [learn-only]' : '';
    const meta = (d.skill || '') + modeTag + ' · ' + (Date.now()-t0) + 'ms';
    if (display && display !== '?') appendTurn(msg, display, meta);
    else reply.innerHTML = '<pre>' + (d.error || '?') + '</pre>';
    if (d.ok && toSpeak && toSpeak !== '?') {{
      setLive('speak', 'George replying…');
      speak(toSpeak);
    }} else {{
      setLive('idle', 'Tap MIC to try again');
      status.textContent = d.error || 'Error';
    }}
    const shouldOpen = d.open_url && (d.skill === 'open' || (d.actions || []).some(a => String(a).startsWith('open:')));
    if (shouldOpen) setTimeout(() => {{ window.location.href = d.open_url; }}, 800);
    typed.value = '';
  }} catch (e) {{
    setLive('idle', 'Offline — try hitme.dev/george');
    status.textContent = 'Offline? ' + String(e.message || e);
    const nn = document.getElementById('netNote');
    if (nn) nn.textContent = 'Can\\'t reach desk — bookmark https://hitme.dev/george (stable) or george.hitme.dev when DNS is up';
    reply.innerHTML = '<pre>' + String(e) + '</pre>';
  }} finally {{ sending = false; if (!speaking) {{ setLive(micOn?'listen':'idle', micOn?'Listening — your turn':'Tap MIC to talk live'); status.textContent = micStatus(); }} }}
}}

document.getElementById('sendBtn').onclick = () => sendText(typed.value);
expandBtn.onclick = () => {{
  const open = floatPanel.classList.toggle('open');
  expandBtn.textContent = open ? '▼' : '▲';
}};

let recOpen = null;
function applyGeorgeVoice(u) {{
  if (georgeVoice) u.voice = georgeVoice;
  u.lang = 'en-US';
  try {{ u.pitch = GEORGE_PITCH; u.rate = GEORGE_RATE; u.volume = 1; }} catch(e) {{}}
}}

function unlockSpeech() {{
  if (speechUnlocked || !window.speechSynthesis) return;
  initGeorgeVoice();
  const u = new SpeechSynthesisUtterance(' ');
  u.volume = 0.01;
  applyGeorgeVoice(u);
  u.onend = () => {{ speechUnlocked = true; initGeorgeVoice(); }};
  u.onerror = () => {{ speechUnlocked = true; }};
  try {{ speechSynthesis.speak(u); }} catch(e) {{ speechUnlocked = true; }}
}}

let deskLinked = true;
async function pingGeorge() {{
  const nn = document.getElementById('netNote');
  try {{
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    const r = await fetch('/health', {{ cache: 'no-store', signal: ctrl.signal }});
    clearTimeout(timer);
    if (!r.ok) throw new Error('health ' + r.status);
    deskLinked = true;
    if (nn && !sending) nn.textContent = 'Linked to desk';
    if (!micOn && !speaking && !sending) liveLabel.textContent = 'Linked · tap MIC to talk';
  }} catch (e) {{
    deskLinked = false;
    if (nn) nn.textContent = 'Not linked — reload or open https://hitme.dev/george';
    if (!sending && !speaking) setLive('idle', 'Not linked to desk');
  }}
}}

function startMic() {{
  unlockSpeech();
  initGeorgeVoice();
  if (!claimMic()) {{ micOn = false; micBtn.classList.remove('on'); micBtn.textContent = 'BUSY'; setLive('idle', 'Mic busy — close other George tab'); return; }}
  micOn = true;
  micBtn.textContent = 'ON';
  micBtn.classList.add('on');
  setLive('listen', 'Listening — talk now');
  status.textContent = micStatus();
  try {{ recOpen.start(); }} catch(x) {{ setLive('idle', 'Tap MIC · allow microphone'); status.textContent = 'Tap MIC · allow mic in browser settings'; }}
}}
function stopMic() {{
  micOn = false;
  micBtn.textContent = 'MIC';
  micBtn.classList.remove('on');
  try {{ recOpen.stop(); }} catch(x) {{}}
  heardInterim.textContent = '';
  setLive('idle', 'Tap MIC to talk live');
  status.textContent = 'MIC OFF · type still works';
}}
micBtn.onclick = () => {{
  if (speaking) {{ stopSpeaking(); return; }}
  micOn ? stopMic() : startMic();
}};

if (window.SpeechRecognition || window.webkitSpeechRecognition) {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recOpen = new SR();
  recOpen.continuous = !isMobile;
  recOpen.interimResults = true;
  recOpen.lang = 'en-US';
  recOpen.onstart = () => {{
    if (micOn) {{ setLive('listen', 'Listening — talk now'); status.textContent = micStatus(); }}
  }};
  recOpen.onspeechstart = () => {{
    if (micOn && !sending && !speaking) setLive('listen', 'Hearing you…');
  }};
  recOpen.onresult = ev => {{
    let fin = '', interim = '';
    for (let i = ev.resultIndex; i < ev.results.length; i++) {{
      const t = ev.results[i][0].transcript;
      if (ev.results[i].isFinal) fin += t; else interim += t;
    }}
    if (fin.trim()) {{
      const low = fin.trim().toLowerCase();
      if (speaking && /\\b(stop|enough|quiet|shut up|cancel|never mind)\\b/.test(low)) {{
        stopSpeaking();
        heardLine.textContent = fin.trim();
        heardInterim.textContent = '';
        return;
      }}
      heardLine.textContent = fin.trim();
      heardInterim.textContent = '';
      setLive('think', 'Got it — sending…');
      if (!speaking && !sending && (Date.now() - lastReplyAt) > SPEAK_COOLDOWN_MS) sendText(fin.trim());
    }} else if (interim.trim()) {{
      heardInterim.textContent = interim.trim();
      setLive('listen', 'Hearing: ' + interim.trim().slice(0, 36));
      status.textContent = interim.trim().slice(0, 48);
    }} else {{
      heardInterim.textContent = '';
      if (!sending && !speaking) status.textContent = micStatus();
    }}
  }};
  recOpen.onerror = ev => {{
    if (ev.error === 'not-allowed') {{ setLive('idle', 'Allow mic in browser settings'); status.textContent = 'Mic blocked — check settings'; }}
    else if (ev.error === 'aborted') {{}}
    else if (ev.error === 'no-speech' && micOn) {{ setLive('listen', 'Listening — say something'); status.textContent = 'Listening…'; }}
    else if (ev.error !== 'no-speech') {{ setLive('idle', 'Mic error: ' + ev.error); status.textContent = 'Mic: ' + ev.error; }}
  }};
  recOpen.onend = () => {{
    if (micOn && !speaking && !sending && claimMic() && (Date.now() - lastReplyAt) > SPEAK_COOLDOWN_MS)
      setTimeout(() => {{ try {{ recOpen.start(); }} catch(x) {{ setLive('idle', 'Tap MIC again'); micOn = false; micBtn.classList.remove('on'); micBtn.textContent = 'MIC'; }} }}, isMobile ? 650 : 400);
  }};
  fetch('/api/george/history').then(r=>r.json()).then(d=>{{
    if(!d.ok||!d.turns)return;
    d.turns.forEach(t=>appendTurn(t[0], t[1], 'saved'));
  }}).catch(()=>{{}});
  document.addEventListener('visibilitychange', () => {{
    if (document.hidden) stopMic();
  }});
  pingGeorge();
  setInterval(pingGeorge, 25000);
  setLive('idle', 'Tap MIC to talk live');
  status.textContent = 'Tap MIC · then talk';
  micBtn.textContent = 'MIC';
}} else {{
  setLive('idle', 'No speech API — use type box');
  status.textContent = 'Voice not supported here — type below';
  micBtn.disabled = true;
  document.getElementById('liveHint').textContent = 'This browser has no speech-to-text — typed send works.';
}}
</script>
</body></html>"""


def _aws_talk(text: str, *, echo: bool = False) -> str:
    import aws_lane as al

    al._load_env()
    sess = al.load_session()
    if echo:
        return sess.send_echo(text.strip())
    return sess.send(text.strip())


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
    indie_css = """
  .inboxbox { background: #151525; border: 2px solid #ff6b9d; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 1rem 0; }
  .indiegrid { display: grid; grid-template-columns: 1fr; gap: 0.65rem; margin: 0.5rem 0 1rem; }
  @media (min-width: 520px) { .indiegrid { grid-template-columns: 1fr 1fr 1fr; } }
  .indiecard { background: #151525; border-radius: 10px; padding: 0.65rem 0.75rem; font-size: 0.82rem; }
  .indiecard h3 { margin: 0 0 0.35rem; font-size: 0.92rem; border: none; }
  .indiecard.bunny { border: 2px solid #ffb347; }
  .indiecard.gem { border: 2px solid #7bed9f; }
  .indiecard.daddy { border: 2px solid #ff6b9d; }
  .indiecard pre { margin: 0; font-size: 0.78rem; white-space: pre-wrap; word-break: break-word;
    overflow-wrap: anywhere; max-height: none; overflow: visible; background: transparent; padding: 0; }
"""
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<meta http-equiv='refresh' content='25'>",
        f"<title>Inbox — {_domain()}</title><style>{DESK_CSS}{indie_css}</style></head><body>",
        "<h1>Fleet inbox</h1>",
        f'<p class="sub">Indie loop + lanes · 25s refresh · {now} · '
        '<a href="/goal">goal</a> · <a href="/gem">buddy</a> · <a href="/daddy">daddy</a></p>',
    ]
    parts.append("<h2>Indie loop</h2><div class=\"indiegrid\">")
    for cls, label, rel in [
        ("bunny", "Bunny", "fleet/indie_loop/FROM_BUNNY.txt"),
        ("gem", "Gem", "fleet/indie_loop/FROM_GEM.txt"),
        ("daddy", "Daddy", "fleet/indie_loop/FROM_DADDY.txt"),
    ]:
        p = bus / rel
        if safe_is_file(p):
            text = safe_read_text(p).strip()[:900] or "(empty)"
        else:
            text = "(missing)"
        parts.append(
            f'<div class="indiecard {cls}"><h3>{label}</h3><pre>{_esc(text)}</pre></div>'
        )
    parts.append("</div>")
    parts.extend([
        '<div class="inboxbox" style="border:2px solid #ff6b9d;padding:1rem;border-radius:12px;margin:1rem 0">',
        '<h2 style="color:#ff6b9d;margin:0 0 0.5rem">Send</h2>',
        '<form id="inboxForm"><select id="lane"><option value="buddy">Buddy</option>',
        '<option value="cpt">CPT</option><option value="net">NET</option>',
        '<option value="uncle">Uncle</option><option value="all">ALL</option>',
        '<option value="auto">Auto</option></select> ',
        '<textarea id="line" class="brian-field" rows="3" style="width:100%;margin-top:0.5rem" placeholder="order…"></textarea> '
        '<button type="submit" style="margin-top:0.5rem">Send</button></form><p id="st"></p></div>',
        "<script>document.getElementById('inboxForm').onsubmit=async(e)=>{e.preventDefault();"
        "const t=document.getElementById('line').value.trim();if(!t)return;"
        "const r=await fetch('/api/brian',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({text:t,lane:document.getElementById('lane').value})});"
        "const d=await r.json();document.getElementById('st').textContent=d.ok?('→ '+(d.route||'sent')):d.error;"
        "if(d.ok)document.getElementById('line').value='';};</script>",
        _textarea_autogrow_js("line"),
    ])
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

    gem_txt = safe_read_text(bus / "fleet/bus/gem_to_cpt.txt") if safe_is_file(bus / "fleet/bus/gem_to_cpt.txt") else ""
    ack_txt = safe_read_text(bus / "fleet/bus/cpt_ack_gem.txt") if safe_is_file(bus / "fleet/bus/cpt_ack_gem.txt") else ""
    gem_m = mtime("fleet/bus/gem_to_cpt.txt")
    try:
        gem_age = (
            datetime.now().astimezone()
            - datetime.fromtimestamp(
                (bus / "fleet/bus/gem_to_cpt.txt").stat().st_mtime
            ).astimezone()
        ).total_seconds()
    except OSError:
        gem_age = 9999
    loop_live = gem_age < 120 and "GEM ok" in gem_txt
    buddy_pending = "buddy_pending: YES" in ack_txt
    loop_cls = "ok" if loop_live else "bad"
    job_cls = "warn" if buddy_pending else "ok"
    loop_label = "LIVE — Gem on CB1" if loop_live else "STALE — refresh Gem on CB1"
    job_label = "keys sprint — waiting reply" if buddy_pending else "none pending"

    buddy_in = _inbox_tail(bus, "fleet/bus/BUDDY_INBOX.txt", 8)
    routed = bus_snip("fleet/bus/routed/cb2_chrome.txt", 8)

    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<meta http-equiv='refresh' content='25'>",
        f"<title>Buddy watch — {_domain()}</title><style>{DESK_CSS}</style></head><body>",
        "<h1>Buddy watch</h1>",
        f'<p class="sub">Gem · CB1 loader · 25s refresh · {now}',
        ' · <a href="/inbox">inbox</a> · <a href="/goal">goal</a></p>',
        '<div style="border:2px solid #7bed9f;border-radius:12px;padding:0.75rem 1rem;margin:1rem 0">'
        '<p style="margin:0 0 0.35rem;color:#7bed9f;font-weight:700">Gem bookmark (Tailscale)</p>'
        '<p style="margin:0;word-break:break-all"><a href="http://100.115.92.26:8770/gem">'
        'http://100.115.92.26:8770/gem</a> · gate <a href="/gem/live">/gem/live</a></p></div>',
        f'<div style="border:3px solid #7bed9f;border-radius:14px;padding:1rem;margin:1rem 0;background:#121f1a">'
        f'<h2 style="color:#7bed9f;margin:0 0 0.5rem;border:none">Connection: <span class="{loop_cls}">{loop_label}</span></h2>'
        f'<p style="margin:0.35rem 0">gem_to_cpt mtime: {gem_m} · age {int(gem_age)}s</p>'
        f'<p style="margin:0.35rem 0">Brian job: <span class="{job_cls}">{job_label}</span></p>'
        f'<pre style="margin:0.5rem 0 0">{gem_txt[:400] or "(empty)"}</pre></div>',
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
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    team_url = _hitme_url("/team")
    boxes = [
        ("Daddy", "DADDY", "Captain · penguin", "#ff6b9d", "DADDY"),
        ("Bunny", "BUNNY", "Builder · 4GB · indie loop", "#ffb347", "BUNNY"),
        ("Uncle", "UNCLE", "CB1 Linux execute", "#ffb347", "UNCLE"),
        ("Clerk", "CLERK", "CB1 Chrome · plain .txt", "#7bed9f", "GEM"),
    ]
    cards = []
    for title, word, hint, color, key in boxes:
        db = bus / f"fleet/dogbarf/{key}.txt"
        paste = safe_read_text(db).strip() if safe_is_file(db) else f"ONE WORD: {word}\n\nELSE:\n---\n{word}: "
        cards.append(
            f'<div class="card" style="border-color:{color}">'
            f'<p class="box">{title}</p>'
            f'<p class="word" style="color:{color}">{word}</p>'
            f'<p class="hint">{hint}</p>'
            f'<p class="opt">else → dogbarf</p>'
            f'<pre id="db_{key}" class="paste">{_esc(paste)}</pre>'
            f'<button type="button" class="copybtn" onclick="copyDog(\'db_{key}\',this)">Copy dogbarf</button>'
            f"</div>"
        )
    brian = safe_read_text(bus / "fleet/dogbarf/BRIAN.txt").strip() if safe_is_file(bus / "fleet/dogbarf/BRIAN.txt") else ""
    css = """
  body { font-family: system-ui,sans-serif; max-width: 96vw; margin: 0 auto; padding: 1rem;
    background: #0a0a12; color: #eee; text-align: center; }
  h1 { font-size: 2rem; color: #ff6b9d; }
  .sub { color: #888; font-size: 1rem; margin-bottom: 1rem; }
  .law { background: #1a1520; border: 2px solid #ffb347; border-radius: 12px; padding: 0.75rem 1rem;
    margin: 0 0 1.25rem; font-size: 1.05rem; color: #fff; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: 0.85rem; text-align: left; }
  .card { background: #151525; border: 4px solid; border-radius: 16px; padding: 1rem 0.75rem; }
  .box { font-size: 1rem; color: #aaa; margin: 0 0 0.35rem; text-align: center; }
  .word { font-size: clamp(2.2rem, 10vw, 4.5rem); font-weight: 800; margin: 0; letter-spacing: 0.05em; text-align: center; }
  .hint { font-size: 0.82rem; color: #888; margin: 0.5rem 0 0; text-align: center; }
  .opt { font-size: 0.78rem; color: #ffb347; margin: 0.65rem 0 0.25rem; text-align: center; font-weight: 700; }
  .paste { font-size: 0.78rem; color: #ccc; background: #0a0a12; border: 1px solid #333; border-radius: 8px;
    padding: 0.65rem; white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere;
    max-height: none; overflow: visible; margin: 0; }
  .copybtn { display: block; width: 100%; margin-top: 0.5rem; padding: 0.55rem; border: none; border-radius: 8px;
    background: #333; color: #7bed9f; font-weight: 700; cursor: pointer; font-size: 0.85rem; }
  .copybtn.ok { background: #7bed9f; color: #0a0a12; }
  .url { background: #1a2a1a; border: 2px solid #7bed9f; border-radius: 12px; padding: 1rem;
    margin: 1rem 0; word-break: break-all; font-size: 1.1rem; text-align: center; }
  .brianbox { margin-top: 1.25rem; text-align: left; background: #151525; border: 2px solid #ff6b9d;
    border-radius: 14px; padding: 1rem; }
  .brianbox h2 { margin: 0 0 0.5rem; color: #ff6b9d; font-size: 1.1rem; text-align: center; border: none; }
"""
    copy_js = """
<script>
function copyDog(id,btn){
  const el=document.getElementById(id);
  if(!el)return;
  const t=el.textContent;
  navigator.clipboard.writeText(t).then(()=>{
    btn.textContent='Copied';btn.classList.add('ok');
    setTimeout(()=>{btn.textContent='Copy dogbarf';btn.classList.remove('ok');},1500);
  }).catch(()=>{
    const r=document.createRange();r.selectNode(el);
    window.getSelection().removeAllRanges();window.getSelection().addRange(r);
    try{document.execCommand('copy');btn.textContent='Copied';}catch(e){}
  });
}
</script>
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='30'>"
        f"<title>Team — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Two options only</h1>"
        f'<p class="sub">30s refresh · {now} · '
        f'<a href="/checkin" style="color:#7bed9f">roll call</a> · '
        f'<a href="/inbox" style="color:#ffb347">inbox</a> · '
        f'<a href="/goal" style="color:#ff6b9d">goal</a></p>'
        '<p class="law"><strong>1)</strong> one word &nbsp;·&nbsp; <strong>2)</strong> else copy '
        f'<a href="/backrub" style="color:#ffb347">backrub</a> or dogbarf'
        ' &nbsp;·&nbsp; <strong style="color:#7bed9f">LOOP</strong> = Bunny fuse fix</p>'
        f'<div class="url"><a href="{team_url}" style="color:#7bed9f">{team_url}</a></div>'
        f'<div class="grid">{"".join(cards)}</div>'
        f'<div class="brianbox"><h2>Brian</h2>'
        f'<pre id="db_BRIAN" class="paste">{_esc(brian)}</pre>'
        f'<button type="button" class="copybtn" onclick="copyDog(\'db_BRIAN\',this)">Copy dogbarf</button></div>'
        f"{copy_js}</body></html>"
    )


def _base_url() -> str:
    try:
        return request.host_url.rstrip("/")
    except RuntimeError:
        return f"http://127.0.0.1:{PORT}"


COPY_JS = """
<script>
function copyText(id, btn){
  const el=document.getElementById(id);
  if(!el)return;
  const t=el.dataset.copy||el.textContent.trim();
  function ok(){ if(btn){btn.textContent='Copied!'; setTimeout(()=>{btn.textContent=btn.dataset.label||'Copy';},1500);} }
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(ok).catch(()=>fallback(t,ok));
  }else{ fallback(t,ok); }
}
function fallback(t,ok){
  const ta=document.createElement('textarea');
  ta.value=t; ta.style.position='fixed'; ta.style.left='-9999px';
  document.body.appendChild(ta); ta.select();
  try{ document.execCommand('copy'); ok(); }catch(e){ alert('Select and copy manually'); }
  document.body.removeChild(ta);
}
</script>
"""


def _wake_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    base = _base_url()
    wake_url = f"{base}/w"
    short_ts = f"http://100.115.92.26:{PORT}/w"
    short_local = f"http://127.0.0.1:{PORT}/w"
    short_public = "https://hitme.dev/w"
    cmd = "bash ~/GoogleDrive/MyDrive/lester/NEW_PUPPY_BOOT.sh"
    alt = "bash /mnt/shared/GoogleDrive/MyDrive/lester/NEW_PUPPY_BOOT.sh"
    check = "ls ~/GoogleDrive/MyDrive/fleet/bus"
    checkin_path = bus / "fleet/bus/FLEET_CHECKIN.txt"
    roll = safe_read_text(checkin_path) if safe_is_file(checkin_path) else ""
    roll = "\n".join(roll.splitlines()[:8])
    puppy_line = ""
    for ln in roll.splitlines():
        if "PUPPY" in ln or "roll=" in ln:
            puppy_line += ln + "\n"
    live = safe_read_text(bus / "fleet/HITME_LIVE_URL.txt") if safe_is_file(bus / "fleet/HITME_LIVE_URL.txt") else ""
    tunnel = ""
    for ln in live.splitlines():
        if ln.strip().startswith("https://") and "trycloudflare" in ln:
            tunnel = ln.strip().replace("/goal", "/wake")
            break
    ts_url = f"http://100.115.92.26:{PORT}/wake"
    css = """
  body { font-family: system-ui,sans-serif; max-width: 42rem; margin: 0 auto; padding: 1.25rem;
    background: #0a0a12; color: #eee; }
  h1 { color: #7bed9f; font-size: 1.75rem; text-align: center; margin-bottom: 0.25rem; }
  .sub { color: #888; font-size: 0.95rem; text-align: center; margin: 0.5rem 0 1.25rem; }
  .box { background: #151525; border: 3px solid #7bed9f; border-radius: 16px; padding: 1rem 1.1rem;
    margin: 1rem 0; }
  .cmd { font-size: clamp(0.95rem, 3.5vw, 1.15rem); word-break: break-all; line-height: 1.45;
    font-family: ui-monospace, monospace; }
  .btn { display: block; width: 100%; margin-top: 0.85rem; padding: 1rem 1.25rem; font-size: 1.25rem;
    font-weight: 700; border: none; border-radius: 12px; background: #7bed9f; color: #0a0a12;
    cursor: pointer; }
  .btn.secondary { background: #2a2a44; color: #eee; font-size: 1rem; margin-top: 0.5rem; }
  .urls { font-size: 0.85rem; color: #aaa; word-break: break-all; }
  .urls a { color: #ffb347; }
  .status { background: #12121f; border-radius: 12px; padding: 0.85rem; font-size: 0.85rem;
    color: #aaa; white-space: pre-wrap; }
  a { color: #ffb347; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='25'>"
        f"<title>Wake Puppy — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Wake Puppy</h1>"
        f'<p class="sub">Short URL · tap copy · {now}</p>'
        '<p class="sub"><strong>Shortest (Tailscale)</strong></p>'
        f'<div class="box urls"><strong>{_esc(short_ts)}</strong>'
        f'<button type="button" class="btn" data-label="Copy short URL" '
        f"onclick=\"copyText('shortTs', this)\">Copy short URL</button>"
        f'<span id="shortTs" style="display:none" data-copy="{_esc(short_ts)}"></span></div>'
        f'<p class="sub">Same keyboard: {_esc(short_local)} · '
        f'when DNS fixed: {_esc(short_public)}</p>'
        f'<p class="sub"><a href="/checkin">checkin</a> · <a href="/goal">goal</a></p>'
        '<p class="sub"><strong>Step 1</strong> — Drive mounted? (optional check)</p>'
        f'<div class="box"><div class="cmd" id="checkCmd" data-copy="{_esc(check)}">{_esc(check)}</div>'
        f'<button type="button" class="btn secondary" data-label="Copy check" '
        f"onclick=\"copyText('checkCmd', this)\">Copy check</button></div>"
        '<p class="sub"><strong>Step 2</strong> — wake (one command)</p>'
        f'<div class="box"><div class="cmd" id="wakeCmd" data-copy="{_esc(cmd)}">{_esc(cmd)}</div>'
        f'<button type="button" class="btn" data-label="Copy wake command" '
        f"onclick=\"copyText('wakeCmd', this)\">Copy wake command</button></div>"
        f'<p class="sub">Alt path if home differs:</p>'
        f'<div class="box"><div class="cmd" id="altCmd" data-copy="{_esc(alt)}">{_esc(alt)}</div>'
        f'<button type="button" class="btn secondary" data-label="Copy alt" '
        f"onclick=\"copyText('altCmd', this)\">Copy alt path</button></div>"
        "<h2 style='font-size:1.1rem;color:#ffb347;margin-top:1.5rem'>Long tunnel (if short fails)</h2>"
        f'<div class="box urls"><a href="{_esc(wake_url)}">{_esc(wake_url)}</a></div>'
        f'<p class="sub urls">Tailscale full: <a href="{_esc(short_ts.replace("/w","/wake"))}">{_esc(short_ts.replace("/w","/wake"))}</a>'
        + (f'<br>Public tunnel: <a href="{_esc(tunnel)}">{_esc(tunnel)}</a>' if tunnel else "")
        + "</p>"
        "<h2 style='font-size:1.1rem;color:#7bed9f'>Fleet truth</h2>"
        f'<pre class="status">{_esc(puppy_line.strip() or roll.strip() or "(refreshing)")}</pre>'
        "<p class=\"sub\">Daddy drops TEMP when real PUPPY CHECKIN lands on Drive.</p>"
        f"{COPY_JS}</body></html>"
    )



def _daddy_screen_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    meta = safe_read_text(bus / SCREEN_META) if safe_is_file(bus / SCREEN_META) else "(no DADDY_SCREEN.txt yet)"
    delegate = safe_read_text(bus / "fleet/bus/CPT_DELEGATE_NOW.txt") if safe_is_file(bus / "fleet/bus/CPT_DELEGATE_NOW.txt") else "(no delegate queue)"
    ready = safe_read_text(bus / "fleet/bus/CPT_READY.txt") if safe_is_file(bus / "fleet/bus/CPT_READY.txt") else ""
    lab_auto = safe_read_text(bus / "fleet/bus/CPT_LAB_AUTO.txt") if safe_is_file(bus / "fleet/bus/CPT_LAB_AUTO.txt") else "(lab auto not started)"
    lab_reply = safe_read_text(bus / "fleet/bus/LAB_REPLY.txt") if safe_is_file(bus / "fleet/bus/LAB_REPLY.txt") else "(no reply yet)"
    live_url = safe_read_text(bus / "fleet/LIVE_URL.txt") if safe_is_file(bus / "fleet/LIVE_URL.txt") else ""
    gem = safe_read_text(bus / "fleet/bus/gem_to_cpt.txt") if safe_is_file(bus / "fleet/bus/gem_to_cpt.txt") else ""
    ts = int(datetime.now().timestamp())
    img_ok = SCREEN_LATEST.is_file()
    img_block = (
        f'<img src="/screen/latest.png?t={ts}" alt="Daddy screen" '
        'style="max-width:100%;border:2px solid #333;border-radius:12px;" />'
        if img_ok
        else '<p class="warn">No capture yet — run bash ~/.stan/daddy_background.sh</p>'
    )
    fleet_map = (
        "HOW DADDY TALKS TO THE FLEET\n"
        "  Brian → /lab or /goal (CPT lane) → cursor-agent auto (this box)\n"
        "  Brian → /george mic → AWS George → Echo speaks (NOT this chat)\n"
        "  Daddy → fleet/bus/cpt_to_puppy.txt → Puppy/NET executes\n"
        "  Daddy → fleet/bus/cpt_to_uncle.txt → Uncle on CB1 Linux\n"
        "  Daddy → fleet/bus/cpt_to_gem.txt → Gem loader on CB1 Chrome\n"
        "  All boxes → Drive bus files · Daddy reads · never Uncle cosplay\n"
    )
    css = DESK_CSS + FLEET_SPIN_CSS + """
  body { max-width: 56rem; }
  .screenbox { background: #0a0a12; border: 2px solid #7bed9f; border-radius: 14px;
    padding: 0.75rem; margin: 1rem 0; text-align: center; }
  .mapbox { background: #12121f; border: 2px solid #ffb347; border-radius: 12px;
    padding: 0.85rem; margin: 1rem 0; font-size: 0.88rem; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<meta http-equiv='refresh' content='20'>"
        f"<title>Daddy screen — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Daddy screen</h1>"
        f'<p class="sub">Eyes + bug lane · 20s refresh · {now} · '
        '<a href="/lab">lab</a> · <a href="/george">George</a> · '
        '<a href="/fleet">fleet</a> · <a href="/goal">goal</a></p>'
        f"{_daddy_bug_html_block()}"
        f'<div class="screenbox">{img_block}</div>'
        "<h2>Lab auto (type → Daddy wakes)</h2>"
        f"<pre>{lab_auto[:600]}</pre>"
        "<h2>Last lab reply</h2>"
        f"<pre>{lab_reply[:800]}</pre>"
        f'<div class="mapbox"><pre>{fleet_map}</pre></div>'
        "<h2>Website (Gem lane)</h2>"
        f"<pre>{live_url[:400] or '(no LIVE_URL.txt)'}\n\nGem last:\n{gem[:300]}</pre>"
        "<h2>Screen status</h2>"
        f"<pre>{meta[:1200]}</pre>"
        "<h2>Delegate now</h2>"
        f"<pre>{delegate[:1200]}</pre>"
        "<h2>CPT ready</h2>"
        f"<pre>{ready[:800] if ready else '(autopilot)'}</pre>"
        f"{DADDY_BUG_JS}"
        f"{_textarea_autogrow_js('spinLine')}"
        f"{_cpt_open_poll_js('spinLine')}"
        "</body></html>"
    )


@app.route("/voice")
@app.route("/george")
@app.route("/gl")
@app.route("/float")
def voice_page():
    from flask import redirect, request

    if request.path == "/float":
        return redirect("/george?float=1", code=302)
    host = (request.host or "").split(":")[0]
    return Response(_voice_html(float_mode=True, host=host), mimetype="text/html")


@app.route("/george/manifest.json")
def george_manifest():
    from flask import request

    host = (request.host or "").split(":")[0].lower()
    dom = _domain()
    if host.startswith("george."):
        start = f"https://{host}/?float=1"
    else:
        start = f"https://{dom}/george?float=1" if dom else "/george?float=1"
    return jsonify(
        {
            "name": "George",
            "short_name": "George",
            "start_url": start,
            "display": "standalone",
            "background_color": "#0a0a12",
            "theme_color": "#e67e22",
            "orientation": "portrait",
        }
    )


@app.route("/api/george/status")
def api_george_status():
    from alexa_learn import learn_mode

    try:
        from george_echo import status as geo

        st = geo()
    except ImportError:
        st = {}
    from alexa_queue import status as queue_status

    return jsonify({"ok": True, "learn": learn_mode(), "echo": queue_status(), **st})


@app.route("/api/george/history")
def api_george_history():
    try:
        from george_echo import get_history

        hist = get_history()
        return jsonify({"ok": True, "turns": [[u, a] for u, a in hist]})
    except ImportError:
        return jsonify({"ok": True, "turns": []})


@app.route("/api/george/tts", methods=["POST"])
def api_george_tts():
    from george_tts import prepare_speech, synthesize_mp3

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    aloud = prepare_speech(text)
    if not aloud:
        return jsonify({"ok": False, "error": "nothing to speak"}), 400
    mp3 = synthesize_mp3(aloud)
    if mp3:
        return Response(mp3, mimetype="audio/mpeg")
    return jsonify({"ok": False, "error": "tts unavailable", "fallback": "browser"}), 503


@app.route("/jane")
def jane_page():
    from jane_voice_page import jane_html

    host = (request.host or "").split(":")[0]
    float_mode = request.args.get("float") == "1"
    return Response(jane_html(float_mode=float_mode, host=host), mimetype="text/html")


@app.route("/jane/manifest.json")
def jane_manifest():
    host = (request.host or "").split(":")[0].lower()
    dom = _domain()
    if host.startswith("jane."):
        start = f"https://{host}/?float=1"
    else:
        start = f"https://{dom}/jane?float=1" if dom else "/jane?float=1"
    return jsonify(
        {
            "name": "Jane",
            "short_name": "Jane",
            "start_url": start,
            "display": "standalone",
            "background_color": "#0a0a12",
            "theme_color": "#9b59b6",
            "orientation": "portrait",
        }
    )


@app.route("/api/jane/status")
def api_jane_status():
    try:
        from jane_echo import status as jst

        return jsonify({"ok": True, **jst()})
    except ImportError:
        return jsonify({"ok": True, "agent": "jane", "turns": 0})


@app.route("/api/jane/history")
def api_jane_history():
    try:
        from jane_echo import get_history

        hist = get_history()
        return jsonify({"ok": True, "turns": [[u, a] for u, a in hist]})
    except ImportError:
        return jsonify({"ok": True, "turns": []})


@app.route("/api/jane/talk", methods=["POST"])
def api_jane_talk():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    try:
        from jane_echo import talk as jane_talk
        from jane_tts import prepare_speech

        reply, extra = jane_talk(text)
        aloud = prepare_speech(reply, max_len=400) or reply
        return jsonify({"ok": True, "reply": reply, "speak": aloud, "aloud": aloud, **extra})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/jane/tts", methods=["POST"])
def api_jane_tts():
    from jane_tts import prepare_speech, synthesize_mp3

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    aloud = prepare_speech(text)
    if not aloud:
        return jsonify({"ok": False, "error": "nothing to speak"}), 400
    mp3 = synthesize_mp3(aloud)
    if mp3:
        return Response(mp3, mimetype="audio/mpeg")
    return jsonify({"ok": False, "error": "tts unavailable", "fallback": "browser"}), 503


@app.route("/alexa")
def alexa_page():
    return Response(_alexa_html(), mimetype="text/html")


@app.route("/api/alexa/say")
def api_alexa_say():
    from alexa_queue import status as queue_status

    say, aloud_path, full_path = _alexa_paths()
    st = queue_status()
    full = safe_read_text(full_path).strip() if safe_is_file(full_path) else ""
    mtime = None
    if safe_is_file(say):
        try:
            mtime = datetime.fromtimestamp(say.stat().st_mtime).astimezone().isoformat(
                timespec="seconds"
            )
        except OSError:
            pass
    return jsonify(
        {
            "ok": True,
            "aloud": st["aloud"] or None,
            "pending": st["pending"],
            "seq": st["seq"],
            "ack": st["ack"],
            "full": full or None,
            "mtime": mtime,
        }
    )


@app.route("/api/alexa/ack", methods=["POST"])
def api_alexa_ack():
    from alexa_queue import ack as queue_ack

    data = request.get_json(silent=True) or {}
    seq = data.get("seq")
    try:
        seq_i = int(seq) if seq is not None else None
    except (TypeError, ValueError):
        seq_i = None
    st = queue_ack(seq_i)
    return jsonify({"ok": True, **st})


@app.route("/api/alexa/learn")
def api_alexa_learn():
    from alexa_learn import learn_mode, recent

    try:
        from george_memory import status as george_status

        geo = george_status()
    except ImportError:
        geo = {}
    return jsonify({"ok": True, "learn": learn_mode(), "recent": recent(), "george": geo})


@app.route("/api/alexa/hear", methods=["POST"])
def api_alexa_hear():
    from alexa_learn import hear

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    entry = hear(text, source=(data.get("source") or "alexa"))
    return jsonify({"ok": True, "mode": "learn", "saved": entry})


@app.route("/api/needs", methods=["GET", "POST"])
def api_needs():
    if request.method == "GET":
        return jsonify({"ok": True, **_needs_payload()})
    data = request.get_json(silent=True) or {}
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {
        "time": data.get("time") or now,
        "from": data.get("from") or "unknown",
        "roll": data.get("roll") or "?/?",
        "needs": data.get("needs") or [],
        "blockers": data.get("blockers") or [],
        "keyboard": data.get("keyboard") or [],
        "sources": data.get("sources") or [],
    }
    safe_mkdir(NEEDS_JSON.parent)
    NEEDS_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"FLEET NEEDS — {payload['time']}",
        f"from: {payload['from']}",
        f"roll: {payload['roll']}",
        "",
        "NEEDS",
        *[f"  • {n}" for n in payload["needs"]],
        "",
        "BLOCKERS",
        *[f"  • {b}" for b in payload["blockers"]],
        "",
        "KEYBOARD (Brian once)",
        *[f"  • {k}" for k in payload["keyboard"]],
    ]
    NEEDS_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return jsonify({"ok": True, "stored": str(NEEDS_TXT), **payload})


@app.route("/api/cpt/open")
def api_cpt_open():
    bus = bus_root()
    p = bus / CPT_OPEN_REL
    if not safe_is_file(p):
        return jsonify({"ok": False})
    text = safe_read_text(p)
    url = ""
    ts = ""
    for ln in text.splitlines():
        if ln.startswith("url="):
            url = ln.split("=", 1)[1].strip()
        elif ln.startswith("CPT_OPEN"):
            ts = ln.split("—", 1)[-1].strip() if "—" in ln else ""
    if not url:
        return jsonify({"ok": False})
    if ts:
        try:
            t0 = datetime.fromisoformat(ts)
            age = (datetime.now().astimezone() - t0).total_seconds()
            if age > 120:
                return jsonify({"ok": False, "reason": "stale"})
        except ValueError:
            pass
    import hashlib

    oid = hashlib.sha256(text.encode()).hexdigest()[:12]
    return jsonify({"ok": True, "url": url, "id": oid})


@app.route("/api/brian", methods=["POST"])
def api_brian_inbox():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or data.get("line") or "").strip()
    lane = (data.get("lane") or "auto").strip().lower()
    via = (data.get("via") or "inbox").strip().lower()
    if via == "drop" and lane == "auto":
        lane = "daddy"
    try:
        return jsonify(_append_brian_line(text, lane=lane, via=via))
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
    mode = (data.get("mode") or "").strip().lower()
    source = (data.get("source") or "voice").strip().lower()
    try:
        from alexa_learn import hear, learn_mode

        # George phone page always talks back — not learn-only voicemail
        if mode != "execute" and learn_mode() and source not in ("voice", "george"):
            entry = hear(text, source=(data.get("source") or "voice"))
            return jsonify(
                {
                    "ok": True,
                    "mode": "learn",
                    "reply": "George heard you — memory upgraded · no tokens.",
                    "saved": entry,
                }
            )

        import aws_speech as asp

        echo = asp.real_alexa()
        try:
            from george_echo import talk as george_talk

            reply, geo_extra = george_talk(text)
        except ImportError:
            reply, geo_extra = _aws_talk(text, echo=echo), {}
        from alexa_speech import for_aloud
        from george_self import _asks_timestamp, strip_spoken_timestamps

        # Echo queue + phone TTS: no timestamps unless Brian asked.
        aloud = for_aloud(reply, max_len=2000) or reply
        if not _asks_timestamp(text):
            aloud = strip_spoken_timestamps(aloud) or aloud
        method = asp.speak(aloud)
        from alexa_queue import status as queue_status

        st = queue_status()
        browser = source in ("voice", "george")
        display = reply if _asks_timestamp(text) else (strip_spoken_timestamps(reply) or reply)
        return jsonify(
            {
                "ok": True,
                "mode": "execute",
                "brain": "aws-echo" if echo else "aws",
                "reply": display if browser else aloud,
                "speak": aloud,
                "full": None,
                "aloud": aloud,
                "queued": method,
                "seq": st["seq"],
                "pending": st["pending"],
                "open_url": geo_extra.get("open_url"),
                "skill": geo_extra.get("skill"),
                "actions": geo_extra.get("actions") or [],
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


def _keaton_html_path() -> Path | None:
    for path in (KEATON_BUNNY, KEATON_PRODUCED):
        if safe_is_file(path):
            return path
    return None


def _keaton_landing_live() -> bool:
    return safe_is_file(KEATON_LANDING_LIVE) and _keaton_html_path() is not None


@app.route("/f/<path:rel>")
def drive_file(rel: str):
    """Serve bus files as clickable http links (desk + LAN)."""
    try:
        root = DRIVE.resolve()
        path = (DRIVE / rel).resolve()
        if not str(path).startswith(str(root)) or not path.is_file():
            abort(404)
        mime, _ = mimetypes.guess_type(str(path))
        return send_file(path, mimetype=mime or "application/octet-stream", download_name=path.name)
    except OSError:
        abort(404)


@app.route("/card")
@app.route("/heritage/card_demo.html")
def card_demo():
    if safe_is_file(CARD_DEMO):
        return send_file(CARD_DEMO, mimetype="text/html")
    return Response("card demo missing on bus", status=404)


@app.route("/cards/sell")
@app.route("/sell")
def cards_sell():
    path = PRODUCED / "sell_sheet.html"
    if not safe_is_file(path):
        import subprocess

        subprocess.run(
            [__import__("sys").executable, str(STAN / "brian_produce.py"), "sell"],
            check=False,
            timeout=30,
        )
    if safe_is_file(path):
        return send_file(path, mimetype="text/html")
    # Fallback — never bad-gateway blank; show message
    return Response(
        "<!DOCTYPE html><html><body style='font-family:system-ui;background:#0a0a12;color:#eee;"
        "padding:2rem;text-align:center'><h1>Sell sheet loading</h1>"
        "<p>497 cards · ~$2,092 mid · illiquid until Brian says sell.</p>"
        "<p><a href='/for-sarah' style='color:#7bed9f'>Sarah test</a> · "
        "<a href='/seminary-app' style='color:#7bed9f'>Seminary app</a></p></body></html>",
        mimetype="text/html",
        status=503,
    )


@app.route("/cards/story")
def cards_story():
    if request.args.get("new"):
        import subprocess

        subprocess.run(
            [__import__("sys").executable, str(STAN / "brian_produce.py"), "story"],
            check=False,
            timeout=90,
        )
    latest = PRODUCED / "story_latest.json"
    if safe_is_file(latest):
        try:
            meta = json.loads(safe_read_text(latest))
            path = Path(meta.get("path") or "")
            if path.is_file():
                return send_file(path, mimetype="text/html")
        except (json.JSONDecodeError, OSError):
            pass
    return Response(
        '<p><a href="/cards/story?new=1">Draw a story card</a></p>',
        mimetype="text/html",
        status=404,
    )


def _produced_html(name: str, cmd: str) -> Response:
    path = PRODUCED / name
    if request.args.get("new") or not safe_is_file(path):
        import subprocess

        subprocess.run(
            [__import__("sys").executable, str(STAN / "brian_produce.py"), cmd],
            check=False,
            timeout=90,
        )
    if safe_is_file(path):
        return send_file(path, mimetype="text/html")
    return Response(f"run: python3 ~/.stan/brian_produce.py {cmd}", status=404)


@app.route("/checkout")
def checkout_page():
    env = STAN / "stripe.env"
    pub = ""
    if safe_is_file(env):
        for line in safe_read_text(env).splitlines():
            if line.startswith("STRIPE_PUBLISHABLE_KEY="):
                pub = line.split("=", 1)[1].strip().strip("'\"")
    if pub:
        html = (
            "<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>Enter studio — hitme.dev</title>"
            "<script src='https://js.stripe.com/v3/'></script>"
            "<style>body{font-family:system-ui;background:#0a0a12;color:#eee;display:flex;min-height:100dvh;"
            "align-items:center;justify-content:center;text-align:center;padding:1.5rem}"
            "button{padding:0.9rem 1.6rem;border:0;border-radius:999px;background:#ff6b9d;color:#0a0a12;"
            "font-size:1rem;font-weight:700;cursor:pointer}a{color:#7bed9f}</style></head><body>"
            "<div><h1>Enter studio</h1><p>Paywall loads when checkout session is wired.</p>"
            f"<p><a href='/studio'>Preview free →</a></p></div></body></html>"
        )
        return Response(html, mimetype="text/html")
    html = (
        "<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Enter studio — hitme.dev</title>"
        "<style>body{font-family:system-ui;background:#0a0a12;color:#eee;display:flex;min-height:100dvh;"
        "align-items:center;justify-content:center;text-align:center;padding:1.5rem}"
        "a{color:#7bed9f}</style></head><body>"
        "<div><h1>Paywall coming online</h1><p>Stripe keys landing now.</p>"
        "<p><a href='/studio'>Browse studio while we wire checkout →</a></p>"
        "<p><a href='/landing'>← landing</a></p></div></body></html>"
    )
    return Response(html, mimetype="text/html")


@app.route("/keaton/jingle.mp3")
def keaton_jingle():
    for path in (KEATON_JINGLE, PRODUCED / "alex_keaton_hes_so_cute_jingle.mp3"):
        if safe_is_file(path):
            return send_file(path, mimetype="audio/mpeg")
    abort(404)


@app.route("/keaton/jingle_short.mp3")
def keaton_jingle_short():
    for path in (
        KEATON_JINGLE_SHORT,
        DRIVE / "drop_pile/from_bbbunny/alex_keaton_hes_so_cute_SHORT.mp3",
    ):
        if safe_is_file(path):
            return send_file(path, mimetype="audio/mpeg")
    abort(404)


@app.route("/done/<prefix>.mp3")
def done_mp3(prefix: str):
    """Mobile audio receipt — fleet/AUDIO_DONE.txt"""
    key = prefix.lower().replace("-", "_")
    for name in (f"{key}.mp3", f"{key}_done.mp3"):
        path = DONE_DIR / name
        if safe_is_file(path):
            return send_file(path, mimetype="audio/mpeg")
    abort(404)


@app.route("/done")
def done_feed_page():
    """Phone inbox — tap last done clips."""
    rows: list[str] = []
    if safe_is_file(DONE_FEED):
        for line in safe_read_text(DONE_FEED).splitlines():
            line = line.strip()
            if not line or line.startswith("DONE FEED") or line.startswith("format:"):
                continue
            rows.append(line)
    rows = rows[-20:]
    items = []
    for line in reversed(rows):
        parts = [p.strip() for p in line.split("·")]
        url = next((p for p in parts if p.startswith("http")), "")
        prefix = parts[2] if len(parts) > 2 else "done"
        label = parts[-1] if parts else prefix
        if not url and prefix:
            url = f"/done/{prefix}.mp3"
        items.append(
            f"<li><a href='{html_mod.escape(url)}' style='color:#7bed9f;font-size:1.1rem'>"
            f"{html_mod.escape(prefix)}</a>"
            f"<span style='color:#888;font-size:.85rem'> — {html_mod.escape(label)}</span></li>"
        )
    if not items:
        items = ["<li style='color:#888'>No done clips yet — machines post to drop_pile/done/</li>"]
    html = (
        "<!DOCTYPE html><html><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Done — hitme.dev</title>"
        "<style>body{font-family:system-ui;background:#0a0a12;color:#ccc;"
        "max-width:28rem;margin:0 auto;padding:1.5rem}h1{color:#ff6b9d;font-size:1.4rem}"
        "ul{list-style:none;padding:0}li{padding:.75rem 0;border-bottom:1px solid #222}"
        "a{text-decoration:none}</style></head><body>"
        "<h1>Done</h1><p style='color:#888;font-size:.9rem'>Tap to hear what finished</p>"
        f"<ul>{''.join(items)}</ul>"
        "<p style='margin-top:2rem;font-size:.8rem;color:#555'>"
        "Law: fleet/AUDIO_DONE.txt</p></body></html>"
    )
    return Response(html, mimetype="text/html")


@app.route("/listen")
@app.route("/hear")
def listen_page():
    """Mobile — TAP once to hear Daddy loop (iOS blocks silent autoplay)."""
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Hear Daddy — hitme.dev</title>"
        "<style>body{font-family:system-ui;background:#0a0a12;color:#eee;"
        "max-width:24rem;margin:0 auto;padding:2rem 1.25rem;text-align:center}"
        "h1{color:#ffb347;font-size:1.35rem}button{font-size:1.2rem;padding:1rem 1.5rem;"
        "background:#ffb347;color:#0a0a12;border:none;border-radius:12px;font-weight:700;"
        "width:100%;margin:1rem 0}#st{color:#888;font-size:.9rem;min-height:2rem}"
        "a{color:#7bed9f}</style></head><body>"
        "<h1>I need a job.</h1>"
        "<p>Daddy is free · waiting for your order</p>"
        "<audio id='player' controls loop playsinline style='width:100%;margin:1rem 0'>"
        "<source src='/ready/daddy.mp3' type='audio/mpeg'></audio>"
        "<button id='go' type='button'>TAP TO HEAR · loops until you reply</button>"
        "<p id='st'>Tap the button OR press ▶ on the player above</p>"
        "<p style='font-size:.85rem;color:#ff6b6b;margin:1rem 0'>"
        "Wrong bookmarks: george.hitme.dev · bun.hitme.dev — use hitme.dev paths</p>"
        "<p style='font-size:.85rem;color:#666'>Reply on <a href='/daddy'>/daddy</a> · "
        "<a href='/goal'>/goal</a> · stops loop</p>"
        "<script>"
        "let a=document.getElementById('player'),on=false;"
        "function play(){"
        "a.src='/ready/daddy.mp3?t='+Date.now();"
        "a.loop=true;"
        "a.play().then(()=>{document.getElementById('st').textContent='Playing…';"
        "}).catch(()=>{document.getElementById('st').textContent='Tap ▶ on player or yellow button';});"
        "}"
        "document.getElementById('go').onclick=()=>{on=true;play();};"
        "a.addEventListener('play',()=>{document.getElementById('st').textContent='Playing…';});"
        "</script></body></html>"
    )
    return Response(html, mimetype="text/html")


@app.route("/ready/<box>")
def ready_box_redirect(box: str):
    from flask import redirect

    key = box.lower().replace("-", "_")
    if safe_is_file(READY_DIR / f"{key}.mp3"):
        return redirect(f"/ready/{key}.mp3", code=302)
    if safe_is_file(READY_DIR / f"{key}_ready.mp3"):
        return redirect(f"/ready/{key}_ready.mp3", code=302)
    abort(404)


@app.route("/ready/<box>.mp3")
def ready_mp3(box: str):
    """Mobile ready clip — fleet/AUDIO_READY.txt"""
    key = box.lower().replace("-", "_")
    for name in (f"{key}.mp3", f"{key}_ready.mp3"):
        path = READY_DIR / name
        if safe_is_file(path):
            return send_file(path, mimetype="audio/mpeg")
    abort(404)


@app.route("/ready")
def ready_feed_page():
    """Phone inbox — who wants a job."""
    rows: list[str] = []
    if safe_is_file(READY_FEED):
        for line in safe_read_text(READY_FEED).splitlines():
            line = line.strip()
            if not line or line.startswith("READY FEED") or line.startswith("format:"):
                continue
            rows.append(line)
    rows = rows[-20:]
    items = []
    for line in reversed(rows):
        parts = [p.strip() for p in line.split("·")]
        url = next((p for p in parts if p.startswith("http")), "")
        box = parts[1] if len(parts) > 1 else "box"
        if not url and box:
            url = f"/ready/{box}.mp3"
        items.append(
            f"<li><a href='{html_mod.escape(url)}' style='color:#ffb347;font-size:1.1rem'>"
            f"{html_mod.escape(box)}</a>"
            f"<span style='color:#888;font-size:.85rem'> — ready for job</span></li>"
        )
    if not items:
        items = ["<li style='color:#888'>Nobody ready yet — post to drop_pile/ready/</li>"]
    html = (
        "<!DOCTYPE html><html><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Ready — hitme.dev</title>"
        "<style>body{font-family:system-ui;background:#0a0a12;color:#ccc;"
        "max-width:28rem;margin:0 auto;padding:1.5rem}h1{color:#ffb347;font-size:1.4rem}"
        "ul{list-style:none;padding:0}li{padding:.75rem 0;border-bottom:1px solid #222}"
        "a{text-decoration:none}</style></head><body>"
        "<h1>Ready</h1><p style='color:#888;font-size:.9rem'>Tap — who wants work</p>"
        f"<ul>{''.join(items)}</ul>"
        "<p style='margin-top:2rem;font-size:.8rem;color:#555'>"
        "Code word: I need a job. · "
        "<a href='/done' style='color:#7bed9f'>Done</a></p>"
        "<script>"
        "(function(){"
        "const p=new URLSearchParams(location.search);"
        "const box=(p.get('loop')||'daddy').toLowerCase();"
        "let a=null;function play(){"
        "if(a){try{a.pause();}catch(e){}} a=new Audio('/ready/'+box+'.mp3?b='+Date.now());"
        "a.onended=()=>setTimeout(play,1200); a.onerror=()=>setTimeout(play,4000); a.play().catch(()=>setTimeout(play,3000));}"
        "if(p.get('loop')) play();"
        "})();"
        "</script></body></html>"
    )
    return Response(html, mimetype="text/html")


@app.route("/keaton")
@app.route("/index.html")
def keaton_page():
    path = _keaton_html_path()
    if path:
        return send_file(path, mimetype="text/html")
    html = (
        "<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Keaton — hitme.dev</title>"
        "<style>body{font-family:system-ui;background:#0a0a12;color:#ccc;display:flex;min-height:100dvh;"
        "align-items:center;justify-content:center;text-align:center;padding:2rem}</style></head><body>"
        "<div><h1 style='color:#ff6b9d'>Keaton</h1>"
        "<p>Bunny wiring the Alex jingle…</p>"
        "<p><a href='/keaton/jingle_short.mp3' style='color:#7bed9f'>Short · so cuute</a> · "
        "<a href='/keaton/jingle.mp3' style='color:#7bed9f'>Full jingle</a></p></div></body></html>"
    )
    return Response(html, mimetype="text/html", status=503)


@app.route("/landing")
@app.route("/welcome")
def public_landing():
    return _produced_html("hitme_landing.html", "hitme")


@app.route("/studio")
def studio_page():
    return _produced_html("studio.html", "studio")


@app.route("/dirt-strong")
@app.route("/strong")
def dirt_strong_page():
    return Response(dirt_strong_html(), mimetype="text/html")


@app.route("/heartbeat")
@app.route("/america")
@app.route("/roots")
@app.route("/homestead")
def heartbeat_america_page():
    from flask import redirect
    return redirect("/dirt-strong", code=302)


@app.route("/parcels")
@app.route("/five-parcels")
@app.route("/redneck")
def redneck_parcels_game():
    return Response(parcels_game_html(), mimetype="text/html")


@app.route("/qr-sarah")
@app.route("/handoff")
def sarah_qr_page():
    # Prefer public HTTPS base when behind tunnel (X-Forwarded-Host)
    host = request.headers.get("X-Forwarded-Host") or request.host
    scheme = request.headers.get("X-Forwarded-Proto") or request.scheme
    base = f"{scheme}://{host}".rstrip("/")
    link = f"{base}/s"
    esc = html_mod.escape
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Sarah — open this</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; background: #0b0b0f; color: #eee;
    text-align: center; padding: max(1.5rem, env(safe-area-inset-top)) 1rem 2rem; }}
  h1 {{ font-size: 1.25rem; color: #ff6b9d; margin-bottom: 0.5rem; }}
  .sub {{ color: #888; font-size: 0.9rem; margin-bottom: 1.25rem; }}
  #qr {{ margin: 0 auto 1rem; background: #fff; padding: 12px; border-radius: 12px; display: inline-block; }}
  .go {{ display: block; margin: 1rem auto; padding: 1.1rem 1.5rem; max-width: 20rem;
    background: #7bed9f; color: #0a0a12; font-size: 1.15rem; font-weight: 700; border-radius: 999px;
    text-decoration: none; }}
  .link {{ color: #7bed9f; word-break: break-all; font-size: 0.8rem; margin-top: 1rem; display: block; }}
  .err {{ color: #ff6b6b; font-size: 0.85rem; min-height: 1.2rem; }}
</style>
</head><body>
  <h1>Sarah — scan or tap</h1>
  <p class="sub">Brian's phone can show this · or scan with yours</p>
  <div id="qr"></div>
  <p class="err" id="err"></p>
  <a class="go" href="/s">Open test page</a>
  <a class="link" href="{esc(link)}">{esc(link)}</a>
  <script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.4/build/qrcode.min.js"></script>
  <script>
  (function(){{
    var url = {json.dumps(link)};
    var box = document.getElementById('qr');
    if (typeof QRCode === 'undefined') {{
      document.getElementById('err').textContent = 'QR lib blocked — tap the green button instead.';
      return;
    }}
    QRCode.toCanvas(document.createElement('canvas'), url, {{ width: 260, margin: 1 }}, function (err, canvas) {{
      if (err) {{ document.getElementById('err').textContent = 'QR failed — tap green button.'; return; }}
      box.appendChild(canvas);
    }});
  }})();
  </script>
</body></html>"""
    return Response(html, mimetype="text/html")


@app.route("/s")
@app.route("/go")
def sarah_short_link():
    from flask import redirect

    return redirect("/for-sarah", code=302)


@app.route("/for-sarah")
@app.route("/sarah-test")
def for_sarah_page():
    voice = "/sarah"
    for rel in ("fleet/SARAH_LTE_URL.txt", "fleet/SARAH_VOICE_URL.txt"):
        p = DRIVE / rel
        if safe_is_file(p):
            line = safe_read_text(p).strip().splitlines()
            if line and line[0].startswith("http"):
                voice = line[0]
                break
    return Response(for_sarah_html(voice), mimetype="text/html")


@app.route("/seminary-app")
@app.route("/seminary/application")
def seminary_application_page():
    return Response(seminary_application_html(), mimetype="text/html")


@app.route("/seminary")
@app.route("/seminary/preview")
def seminary_preview_page():
    return Response(seminary_preview_html(), mimetype="text/html")


@app.route("/sarah")
def sarah_pitch_page():
    return _produced_html("sarah_pitch.html", "sarah")


@app.route("/bundles")
def bundles_page():
    return _produced_html("bundles.html", "bundles")


@app.route("/setlist")
def setlist_page():
    return _produced_html("setlist.html", "setlist")


@app.route("/mick")
def mick_index_page():
    return _produced_html("mick_index.html", "mick")


@app.route("/app-solution")
@app.route("/appsolution")
def app_solution_page():
    return _produced_html("app_solution.html", "app-solution")


@app.route("/fortune")
def fortune_page():
    return _produced_html("fortune.html", "fortune")


@app.route("/scan")
def scan_one_pager():
    return _produced_html("scan_one_pager.html", "scan")


@app.route("/radio")
def garage_radio_page():
    return _produced_html("garage_radio.html", "radio")


@app.route("/encore")
def encore_page():
    return _produced_html("encore.html", "encore")


@app.route("/cockpit")
def cockpit_page():
    return _produced_html("cockpit.html", "cockpit")


@app.route("/dossier")
def dossier_page():
    return _produced_html("dossier.html", "dossier")


@app.route("/brochure")
def brochure_page():
    return _produced_html("brochure.html", "brochure")


@app.route("/911")
@app.route("/nine")
def nine_one_one_page():
    return _produced_html("nine_one_one.html", "nine")


@app.route("/bundles.csv")
def bundles_csv_download():
    path = PRODUCED / "bundles_ebay.csv"
    if not safe_is_file(path):
        import subprocess

        subprocess.run(
            [__import__("sys").executable, str(STAN / "brian_produce.py"), "export"],
            check=False,
            timeout=30,
        )
    if safe_is_file(path):
        return send_file(path, mimetype="text/csv", download_name="bundles_ebay.csv")
    return Response("run: python3 ~/.stan/brian_produce.py export", status=404)


@app.route("/manifest.json")
@app.route("/api/manifest")
def produce_manifest_json():
    path = PRODUCED / "INVENT_CATALOG.json"
    if safe_is_file(path):
        try:
            return jsonify(json.loads(safe_read_text(path)))
        except json.JSONDecodeError:
            pass
    return jsonify({"updated": None, "items": [], "links": {
        "cockpit": "/cockpit", "dossier": "/dossier", "brochure": "/brochure",
        "sell": "/cards/sell", "studio": "/studio", "landing": "/landing",
    }})


@app.route("/projects.json")
def projects_json():
    if not safe_is_file(PROJECTS_CATALOG):
        try:
            import subprocess

            subprocess.run(
                [__import__("sys").executable, str(STAN / "fleet_projects_build.py")],
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    if not safe_is_file(PROJECTS_CATALOG):
        return jsonify({"ok": False, "error": "catalog missing"}), 404
    return Response(safe_read_text(PROJECTS_CATALOG), mimetype="application/json")


def _projects_html() -> str:
    if not safe_is_file(PROJECTS_CATALOG):
        try:
            import subprocess

            subprocess.run(
                [__import__("sys").executable, str(STAN / "fleet_projects_build.py")],
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    data: dict = {"count": 0, "updated": "?", "by_tier": {}, "projects": []}
    if safe_is_file(PROJECTS_CATALOG):
        try:
            data = json.loads(safe_read_text(PROJECTS_CATALOG))
        except json.JSONDecodeError:
            pass
    count = data.get("count") or len(data.get("projects") or [])
    updated = data.get("updated") or "?"
    archive_count = "?"
    archive_path = DRIVE / "fleet/PROJECTS_ARCHIVE.json"
    if safe_is_file(archive_path):
        try:
            archive_count = str(json.loads(safe_read_text(archive_path)).get("count", "?"))
        except json.JSONDecodeError:
            pass
    by_tier = data.get("by_tier") or {}
    tier_labels = {
        "ship": "Ship now",
        "money": "Money",
        "platform": "Platform",
        "creative": "Creative",
        "backlog": "Backlog",
        "spike": "Spike/R&D",
    }
    chips = ['<button type="button" class="chip on" data-tier="all">All</button>']
    for key, label in tier_labels.items():
        n = by_tier.get(key, 0)
        if n:
            chips.append(
                f'<button type="button" class="chip" data-tier="{_esc(key)}">{_esc(label)} ({n})</button>'
            )
    rows = []
    for p in data.get("projects") or []:
        tid = _esc(str(p.get("id", "")))
        tier = _esc(str(p.get("tier", "")))
        src = str(p.get("source") or "")
        link = f"/f/{src}" if src and not src.startswith("/") else (src if src.startswith("/") else "")
        src_cell = (
            f'<a href="{_esc(link)}">{_esc(src.split("/")[-1])}</a>'
            if link
            else _esc(src[:40])
        )
        rows.append(
            f'<tr data-tier="{tier}">'
            f'<td class="name"><b>{_esc(p.get("name", ""))}</b>'
            f'<span class="st">{_esc(p.get("status", ""))}</span></td>'
            f'<td>{_esc(p.get("end_user", ""))}</td>'
            f'<td class="profit">{_esc(p.get("profit", ""))}</td>'
            f'<td class="src">{src_cell}</td></tr>'
        )
    if not rows:
        rows = ['<tr><td colspan="4">Catalog building…</td></tr>']
    css = """
  body { font-family: system-ui,sans-serif; background:#0a0a12; color:#eee; margin:0; padding:1rem;
    max-width:52rem; margin-inline:auto; }
  h1 { color:#ff6b9d; font-size:1.35rem; margin:0 0 .25rem; }
  .sub { color:#888; font-size:.88rem; margin-bottom:.75rem; }
  .chips { display:flex; flex-wrap:wrap; gap:.35rem; margin:.75rem 0 1rem; }
  .chip { border:1px solid #444; background:#151525; color:#ccc; border-radius:999px;
    padding:.35rem .65rem; font-size:.75rem; cursor:pointer; }
  .chip.on { border-color:#7bed9f; color:#7bed9f; }
  table { width:100%; border-collapse:collapse; font-size:.82rem; }
  th { text-align:left; color:#ffb347; font-size:.72rem; text-transform:uppercase;
    letter-spacing:.04em; padding:.5rem .35rem; border-bottom:1px solid #333; }
  td { vertical-align:top; padding:.65rem .35rem; border-bottom:1px solid #1a1a28; line-height:1.35; }
  .name b { display:block; color:#fff; font-size:.95rem; }
  .st { display:block; font-size:.72rem; color:#888; margin-top:.15rem; }
  .profit { color:#7bed9f; min-width:7rem; }
  .src { font-size:.72rem; }
  a { color:#7bed9f; }
  @media (max-width:640px){
    th:nth-child(4), td.src { display:none; }
    td { padding:.55rem .25rem; }
  }
"""
    js = """
<script>
document.querySelectorAll('.chip').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('.chip').forEach(b=>b.classList.remove('on'));
    btn.classList.add('on');
    const t=btn.dataset.tier;
    document.querySelectorAll('tbody tr').forEach(tr=>{
      tr.style.display=(t==='all'||tr.dataset.tier===t)?'':'none';
    });
  });
});
</script>
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Projects ({count}) — {_domain()}</title>"
        f"<style>{css}</style></head><body>"
        f"<h1>Projects · {count}</h1>"
        f'<p class="sub">Bunny list (keaton + sprint) · {updated} · '
        f'<a href="/f/fleet/PROJECTS_BUNNY.txt">law</a> · '
        f'<a href="/f/fleet/PROJECTS_ARCHIVE.json">archive ({archive_count})</a> · '
        f'<a href="/produce">produce</a> · <a href="/projects.json">json</a></p>'
        f'<div class="chips">{"".join(chips)}</div>'
        "<table><thead><tr><th>Name</th><th>End user</th><th>Profit</th><th>Source</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        f"{js}</body></html>"
    )


@app.route("/projects")
def projects_page():
    return Response(_projects_html(), mimetype="text/html")


@app.route("/produce")
def produce_index():
    latest = safe_read_text(PRODUCED / "LATEST.txt") if safe_is_file(PRODUCED / "LATEST.txt") else "(none yet)"
    html = (
        "<!DOCTYPE html><html><head><meta charset=utf-8><title>Produce</title>"
        "<style>body{font-family:system-ui;background:#0c0c14;color:#eee;padding:1.5rem;max-width:640px;margin:0 auto}"
        "a{color:#7bed9f}pre{background:#161622;padding:1rem;border-radius:8px}</style></head><body>"
        "<h1>Produce lane</h1>"
        "<p>Artifacts — not fleet bus. · <a href='/projects'><strong>Bunny projects (15)</strong></a></p>"
        "<ul>"
        '<li><a href="/landing">hitme landing (Ship B)</a></li>'
        '<li><a href="/studio">Studio deck</a></li>'
        '<li><a href="/sarah">Sarah pitch (Ship A)</a></li>'
        '<li><a href="/cards/sell">497-card sell sheet (Ship C)</a></li>'
        '<li><a href="/bundles">Bundle lots</a></li>'
        '<li><a href="/setlist">Top 10 setlist</a></li>'
        '<li><a href="/cockpit">Garage cockpit (precision)</a></li>'
        '<li><a href="/dossier">Deduction dossier</a></li>'
        '<li><a href="/brochure">Top card brochure</a></li>'
        '<li><a href="/911">9·1·1 daily</a></li>'
        '<li><a href="/bundles.csv">eBay bundle CSV</a></li>'
        '<li><a href="/encore">Encore meter</a></li>'
        '<li><a href="/cards/story?new=1">Story card</a></li>'
        '<li><a href="/card">Heritage demo</a></li>'
        '<li><a href="/dirt-strong"><strong>DIRT STRONG</strong> — redneck homestead · Morgan</a></li>'
        '<li><a href="/parcels">Five Parcels game</a></li>'
        "</ul>"
        f"<h2>Latest</h2><pre>{_esc(latest)}</pre>"
        f'<p><a href="/produce?new=1">Regenerate all</a> · python3 ~/.stan/brian_produce.py invent</p>'
        "</body></html>"
    )
    if request.args.get("new"):
        import subprocess

        subprocess.run(
            [__import__("sys").executable, str(STAN / "brian_produce.py"), "invent"],
            check=False,
            timeout=300,
        )
    return Response(html, mimetype="text/html")


@app.route("/team")
def team_words_page():
    return Response(_team_words_html(), mimetype="text/html")


def _backrub_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    path = bus / "backrub.txt"
    if not safe_is_file(path):
        try:
            from daddy_indie_status import write_backrub

            write_backrub()
        except Exception:
            pass
    text = safe_read_text(path).strip() if safe_is_file(path) else "(backrub warming up…)"
    words = "DADDY · BUNNY · UNCLE · CLERK · LOOP"
    css = """
  body { font-family: system-ui,sans-serif; max-width: 28rem; margin: 0 auto; padding: 1.5rem 1rem 3rem;
    background: #0a0a12; color: #eee; text-align: center; }
  h1 { font-size: 2.4rem; color: #ffb347; margin: 0 0 0.25rem; letter-spacing: 0.04em; }
  .sub { color: #888; font-size: 0.9rem; margin-bottom: 1rem; }
  .words { font-size: clamp(1.1rem, 4vw, 1.35rem); color: #7bed9f; font-weight: 700;
    line-height: 1.6; margin: 1rem 0; }
  pre { text-align: left; white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere;
    background: #151525; border: 2px solid #ffb347; border-radius: 12px; padding: 1rem;
    font-size: 0.92rem; line-height: 1.45; max-height: none; overflow: visible; }
  .copy { display: block; width: 100%; margin: 1rem 0; padding: 1rem; border: none; border-radius: 999px;
    background: #ffb347; color: #0a0a12; font-size: 1.15rem; font-weight: 800; cursor: pointer; }
  .copy.ok { background: #7bed9f; }
  a { color: #7bed9f; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>backrub — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>backrub</h1>"
        f'<p class="sub">weird name · Drive Recent · {now}</p>'
        f'<p class="words">{words}</p>'
        f'<pre id="br">{_esc(text)}</pre>'
        '<button type="button" class="copy" id="copyBtn" onclick="copyBackrub()">Copy backrub</button>'
        f'<p class="sub"><a href="/team">team</a> · <a href="/bunny">bunny</a> · <a href="/lab">lab</a></p>'
        "<script>"
        "function copyBackrub(){"
        "const t=document.getElementById('br').textContent;"
        "const b=document.getElementById('copyBtn');"
        "navigator.clipboard.writeText(t).then(()=>{"
        "b.textContent='Copied';b.classList.add('ok');"
        "setTimeout(()=>{b.textContent='Copy backrub';b.classList.remove('ok');},1800);"
        "}).catch(()=>{b.textContent='Select + copy';});"
        "}"
        "</script></body></html>"
    )


@app.route("/backrub")
def backrub_page():
    return Response(_backrub_html(), mimetype="text/html")


@app.route("/puppy")
@app.route("/wake")
@app.route("/w")
def puppy_page():
    return Response(_wake_html(), mimetype="text/html")


@app.route("/drop")
@app.route("/feed")
def brian_drop_page():
    return Response(drop_page_html(domain=_domain()), mimetype="text/html")


@app.route("/pee")
def pee_game_page():
    return Response(pee_game_html(domain=_domain()), mimetype="text/html")


@app.route("/api/pee/status")
def api_pee_status():
    from pee_log import status as pee_status

    return jsonify(pee_status())


@app.route("/api/pee/log", methods=["POST"])
def api_pee_log():
    from pee_log import log_pee

    data = request.get_json(silent=True) or {}
    return jsonify(log_pee(note=(data.get("note") or "").strip()))


@app.route("/turf")
def turf_index_page():
    path = _turf_dir() / "index.html"
    if safe_is_file(path):
        return send_file(path, mimetype="text/html")
    abort(404)


@app.route("/turf/barn")
def turf_barn_page():
    path = _turf_dir() / "barn.html"
    if safe_is_file(path):
        return send_file(path, mimetype="text/html")
    abort(404)


@app.route("/turf/setup")
def turf_setup_page():
    path = _turf_dir() / "setup.html"
    if safe_is_file(path):
        return send_file(path, mimetype="text/html")
    abort(404)


@app.route("/turf/treasure")
@app.route("/turf/map")
@app.route("/turf/points")
def turf_treasure_page():
    path = _turf_dir() / "treasure.html"
    if safe_is_file(path):
        return send_file(path, mimetype="text/html")
    abort(404)


@app.route("/turf/intro")
@app.route("/pee/how")
def turf_intro_page():
    path = _turf_dir() / "intro.html"
    if safe_is_file(path):
        return send_file(path, mimetype="text/html")
    abort(404)


@app.route("/api/turf/yard/<yard_id>")
def api_turf_yard_get(yard_id):
    import turf_marks as tm

    yard = tm.get_yard(yard_id)
    if not yard:
        return jsonify({"ok": False, "error": "yard not found"}), 404
    return jsonify({"ok": True, "yard": yard, "stats": tm.stats(yard_id)})


@app.route("/api/turf/yard", methods=["POST"])
def api_turf_yard_save():
    import turf_marks as tm

    data = request.get_json(silent=True) or {}
    yard_id = (data.get("id") or "").strip()
    try:
        yard = tm.save_yard(
            yard_id,
            name=(data.get("name") or "").strip(),
            mode=(data.get("mode") or "polygon"),
            polygon=data.get("polygon"),
            center=data.get("center"),
            radius_m=data.get("radius_m"),
        )
        return jsonify({"ok": True, "yard": yard, "stats": tm.stats(yard["id"])})
    except (TypeError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/turf/station", methods=["POST"])
def api_turf_station():
    import turf_marks as tm

    data = request.get_json(silent=True) or {}
    try:
        yard_id = (data.get("yard_id") or "").strip()
        station = tm.add_station(
            yard_id,
            (data.get("name") or "").strip(),
            float(data.get("lat")),
            float(data.get("lng")),
        )
        return jsonify({"ok": True, "station": station, "stats": tm.stats(yard_id)})
    except (TypeError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/turf/peg", methods=["POST"])
def api_turf_peg():
    import turf_marks as tm

    data = request.get_json(silent=True) or {}
    try:
        out = tm.mark_station(
            (data.get("yard_id") or "").strip(),
            station_id=(data.get("station_id") or "").strip(),
            slug=(data.get("slug") or "").strip(),
            callsign=(data.get("callsign") or "").strip(),
        )
        return jsonify({"ok": True, **out})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/turf/mark", methods=["POST"])
def api_turf_mark():
    import turf_marks as tm

    data = request.get_json(silent=True) or {}
    try:
        out = tm.add_mark(
            (data.get("yard_id") or "").strip(),
            float(data.get("lat")),
            float(data.get("lng")),
            label=(data.get("label") or "").strip(),
            callsign=(data.get("callsign") or "").strip(),
            method=(data.get("method") or "gps"),
        )
        return jsonify({"ok": True, **out})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


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


@app.route("/gem/live")
def gem_live_gate():
    return jsonify({"ok": True, "gate": "gem/live", "domain": _domain(), "port": PORT})


@app.route("/gem")
def gem_watch_page():
    return Response(_gem_watch_html(), mimetype="text/html")


@app.route("/api/daddy/bug", methods=["GET", "POST"])
def api_daddy_bug():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or data.get("line") or "").strip()
        try:
            payload = _spin_payload()
            result = _append_brian_line(text, lane="cpt", via="daddy")
            if not result.get("ok"):
                return jsonify(result), 400
            result["queued"] = bool(payload.get("lab_busy"))
            return jsonify(result)
        except OSError as e:
            return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify(_spin_payload())


@app.route("/api/fleet/spin", methods=["GET", "POST"])
def api_fleet_spin():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or data.get("line") or "").strip()
        who = (data.get("who") or "Brian").strip()[:24]
        try:
            return jsonify(_append_spin_note(text, who=who))
        except OSError as e:
            return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify(_spin_payload())


@app.route("/fleet")
def fleet_page():
    return Response(_fleet_status_html(), mimetype="text/html")


@app.route("/checkin")
def checkin_page():
    return Response(_checkin_html(), mimetype="text/html")


@app.route("/tv")
def fleet_tv_page():
    return Response(_fleet_tv_html(), mimetype="text/html")


@app.route("/api/goal/status")
def api_goal_status():
    bus = bus_root()
    recent = _inbox_tail(bus, "fleet/bus/CPT_BRIAN_INBOX.txt", 5) or _recent_brian_lines(4)
    return jsonify({"ok": True, "recent": f"Recent:\n{recent}"})


@app.route("/goal")
@app.route("/fleet-goal")
def fleet_goal_page():
    return Response(_fleet_goal_html(), mimetype="text/html")


def _bunny_lab_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    from_bunny = _bus_full("fleet/indie_loop/FROM_BUNNY.txt")
    to_bunny = _bus_full("fleet/indie_loop/TO_BUNNY.txt")
    from_daddy = _bus_full("fleet/indie_loop/FROM_DADDY.txt")
    paste = _bus_full("fleet/indie_loop/BUNNY_PASTE.txt", 2000)
    ack = _bus_full("fleet/bus/cpt_ack_bunny.txt", 4000)
    bunny_live = not from_bunny.startswith("waiting for bunny") and "FROM_BUNNY" in from_bunny
    status = "LIVE" if bunny_live else "SILENT — loop not running on Bunny box"
    status_cls = "ok" if bunny_live else "bad"
    css = DESK_CSS + BRIAN_FIELD_CSS + """
  body { max-width: 40rem; font-size: 1.02rem; }
  .inboxbox { background: #151525; border: 2px solid #ffb347; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 1rem 0; }
  .inboxbox h2 { margin: 0 0 0.75rem; color: #ffb347; font-size: 1.2rem; border: none; }
  .inboxbox button { margin-top: 0.65rem; padding: 0.75rem 1.4rem; font-size: 1.05rem;
    background: #ffb347; color: #0a0a12; border: none; border-radius: 8px; cursor: pointer; font-weight: 700; }
  .loopbox { background: #1a1510; border: 2px solid #ffb347; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 1rem 0; }
  .loopbox h2 { color: #ffb347; margin: 0 0 0.5rem; border: none; font-size: 1.05rem; }
  .ok { color: #7bed9f; font-weight: 700; }
  .bad { color: #ff6b6b; font-weight: 700; }
  #bunnyStatus { color: #ffb347; min-height: 1.2rem; margin-top: 0.5rem; }
  .hint { color: #888; font-size: 0.88rem; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Bunny lab — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>🐰 Bunny lab</h1>"
        f'<p class="hint">CB2 indie loop · draft saved · no reload while typing · {now} · '
        f'<a href="/lab">Daddy lab</a> · <a href="/inbox">inbox</a></p>'
        f'<p>Bunny loop: <span id="bunnyLoopStatus" class="{status_cls}">{status}</span></p>'
        '<div class="inboxbox"><h2>Job → TO_BUNNY</h2>'
        '<form id="bunnyForm">'
        '<textarea id="bunnyLine" class="brian-field" rows="5" autocomplete="off" '
        'placeholder="Order for Bunny — one job, overwrite TO_BUNNY …"></textarea>'
        '<button type="submit">Send to Bunny</button></form>'
        '<p id="bunnyStatus"></p>'
        '<p class="hint">Box grows as you type · Enter = new line · Ctrl+Enter = send</p></div>'
        '<div class="loopbox"><h2>FROM_BUNNY</h2>'
        f"<pre id='fromBunny' class='full-pre panel-pre'>{_esc(from_bunny)}</pre></div>"
        '<div class="loopbox"><h2>TO_BUNNY (current job)</h2>'
        f"<pre id='toBunny' class='full-pre panel-pre'>{_esc(to_bunny)}</pre></div>"
        '<div class="loopbox"><h2>FROM_DADDY (watch)</h2>'
        f"<pre id='fromDaddy' class='full-pre panel-pre'>{_esc(from_daddy)}</pre></div>"
        '<div class="loopbox"><h2>Fetch without Drive (HTTP drop lane)</h2>'
        "<p class='hint'>Any box pulls files from penguin — no fuse · no SSH.</p>"
        "<pre class='full-pre panel-pre'>curl -fLO https://hitme.dev/keaton/jingle_short.mp3\n"
        "curl -fLO https://hitme.dev/f/drop_pile/from_bbbunny/alex_keaton_hes_so_cute_SHORT.mp3\n"
        "bash ~/GoogleDrive/MyDrive/lester/fleet_fetch.sh keaton/jingle_short.mp3</pre>"
        "<p><a href='/keaton/jingle_short.mp3'>▶ short mp3</a> · "
        "<a href='/f/drop_pile/from_bbbunny/alex_keaton_hes_so_cute_SHORT.mp3'>/f/ mirror</a> · "
        "<a href='/f/fleet/FLEET_HTTP_DROP.txt'>law</a></p></div>"
        '<div class="loopbox"><h2>Paste on Bunny terminal</h2>'
        f"<pre id='bunnyPaste' class='full-pre panel-pre'>{_esc(paste)}</pre>"
        '<button type="button" onclick="navigator.clipboard.writeText('
        "document.getElementById('bunnyPaste').textContent)\">Copy paste</button></div>"
        f'<div class="loopbox"><h2>Daddy ack</h2><pre id="bunnyAck" class="full-pre panel-pre">{_esc(ack)}</pre></div>'
        "<script>"
        "async function sendBunny(){"
        "const t=document.getElementById('bunnyLine').value.trim();if(!t)return;"
        "document.getElementById('bunnyStatus').textContent='Sending…';"
        "try{"
        "const r=await fetch('/api/bunny',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({text:t})});"
        "const d=await r.json();"
        "document.getElementById('bunnyStatus').textContent=d.ok?'→ TO_BUNNY written':'err: '+(d.error||'?');"
        "if(d.ok){document.getElementById('bunnyLine').value='';if(window.__clearBrianDraft)window.__clearBrianDraft();}"
        "}catch(x){document.getElementById('bunnyStatus').textContent='fail';}"
        "}"
        "document.getElementById('bunnyForm').onsubmit=async(e)=>{e.preventDefault();await sendBunny();};"
        "document.getElementById('bunnyLine').addEventListener('keydown',(e)=>{"
        "if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();sendBunny();}"
        "});"
        "</script>"
        f"{_brian_draft_guard_js('bunnyLine', 'bunny_draft', 15, poll_url='/api/bunny/status', poll_map={'fromBunny': 'from_bunny', 'toBunny': 'to_bunny', 'fromDaddy': 'from_daddy', 'bunnyAck': 'ack', 'bunnyLoopStatus': 'status'})}"
        f"{_textarea_autogrow_js('bunnyLine')}"
        "</body></html>"
    )


@app.route("/bunny")
@app.route("/bunny/lab")
def bunny_lab_page():
    return Response(_bunny_lab_html(), mimetype="text/html")


@app.route("/api/bunny", methods=["POST"])
def api_bunny_job():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    bus = bus_root()
    to = bus / "fleet/indie_loop/TO_BUNNY.txt"
    safe_mkdir(to.parent)
    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    body = (
        f"JOB: brian_bunny_lab\nTIME: {ts}\nFROM: Brian via Daddy · penguin · CB2\n\n"
        f"{text}\n\nWord: BUNNY · LAB · ACK\n"
    )
    try:
        to.write_text(body, encoding="utf-8")
    except OSError as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "file": "fleet/indie_loop/TO_BUNNY.txt"})


@app.route("/api/bunny/status")
def api_bunny_status():
    bus = bus_root()

    def bus_full(rel: str, cap: int = 8000) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        return safe_read_text(p).strip()[:cap] or "(empty)"

    from_bunny = bus_full("fleet/indie_loop/FROM_BUNNY.txt")
    bunny_live = not from_bunny.startswith("waiting for bunny") and "FROM_BUNNY" in from_bunny
    status = "LIVE" if bunny_live else "SILENT — loop not running on Bunny box"
    return jsonify(
        {
            "ok": True,
            "status": status,
            "from_bunny": from_bunny,
            "to_bunny": bus_full("fleet/indie_loop/TO_BUNNY.txt"),
            "from_daddy": bus_full("fleet/indie_loop/FROM_DADDY.txt"),
            "ack": bus_full("fleet/bus/cpt_ack_bunny.txt", 4000),
        }
    )


def _lab_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    def bus_snip(rel: str, n: int = 12) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        text = safe_read_text(p).strip()
        return "\n".join(text.splitlines()[:n]) or "(empty)"

    reply = _bus_full("fleet/bus/LAB_REPLY.txt", 8000)
    auto_st = _bus_full("fleet/bus/CPT_LAB_AUTO.txt", 4000)
    recent = _inbox_tail(bus, "fleet/bus/CPT_BRIAN_INBOX.txt", 12)
    css = DESK_CSS + BRIAN_FIELD_CSS + """
  body { max-width: 36rem; font-size: 1.05rem; }
  .inboxbox { background: #151525; border: 2px solid #7bed9f; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 1rem 0; }
  .inboxbox h2 { margin: 0 0 0.75rem; color: #7bed9f; font-size: 1.2rem; border: none; }
  .inboxbox button { margin-top: 0.65rem; padding: 0.75rem 1.4rem; font-size: 1.05rem;
    background: #7bed9f; color: #0a0a12; border: none; border-radius: 8px; cursor: pointer; font-weight: 700; }
  .replybox { background: #0f1a14; border: 2px solid #ffb347; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 1rem 0; }
  .replybox h2 { color: #ffb347; margin: 0 0 0.5rem; border: none; font-size: 1.1rem; }
  #labStatus { color: #7bed9f; min-height: 1.2rem; margin-top: 0.5rem; }
  .hint { color: #888; font-size: 0.88rem; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Daddy lab — {_domain()}</title><style>{css}</style></head><body>"
        "<h1>Daddy lab</h1>"
        f'<p class="hint">Type here · draft saved · no page reload while typing · {now} · '
        '<a href="/bunny">bunny lab</a> · <a href="/goal">fleet goal</a> · <a href="/george">George</a></p>'
        '<div class="inboxbox"><h2>Talk to Daddy</h2>'
        '<form id="labForm">'
        '<textarea id="labLine" class="brian-field" rows="6" autocomplete="off" '
        'placeholder="Type as much as you need — details, links, context …"></textarea>'
        '<button type="submit">Send</button></form>'
        '<p id="labStatus"></p>'
        '<p class="hint">Box grows as you type · Multi-line OK · Enter = new line · Ctrl+Enter = send · reply below polls when idle</p></div>'
        '<div class="replybox"><h2>Daddy reply</h2>'
        f'<pre id="labReply" class="full-pre panel-pre">{_esc(reply)}</pre></div>'
        '<p class="hint">Auto status</p>'
        f'<pre id="labAuto" class="full-pre panel-pre">{_esc(auto_st)}</pre>'
        f'<p class="hint">Recent CPT lines</p><pre id="labRecent" class="full-pre panel-pre">{_esc(recent)}</pre>'
        "<script>"
        "async function sendLabForm(){"
        "const t=document.getElementById('labLine').value.trim();"
        "if(!t)return;"
        "document.getElementById('labStatus').textContent='Sending…';"
        "try{"
        "const r=await fetch('/api/brian',{method:'POST',headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({text:t,lane:'cpt'})});"
        "const d=await r.json();"
        "document.getElementById('labStatus').textContent=d.ok?"
        "('Sent — Daddy waking…'):('err: '+(d.error||'?'));"
        "if(d.ok){document.getElementById('labLine').value='';if(window.__clearBrianDraft)window.__clearBrianDraft();if(window.__growBrianField)window.__growBrianField('labLine');}"
        "}catch(x){document.getElementById('labStatus').textContent='fail';}"
        "}"
        "document.getElementById('labForm').onsubmit=async(e)=>{e.preventDefault();await sendLabForm();};"
        "document.getElementById('labLine').addEventListener('keydown',(e)=>{"
        "if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();sendLabForm();}"
        "});"
        "</script>"
        f"{_brian_draft_guard_js('labLine', 'lab_draft', 15, poll_url='/api/lab/status', poll_map={'labReply': 'reply', 'labAuto': 'auto', 'labRecent': 'recent'})}"
        f"{_textarea_autogrow_js('labLine')}"
        "</body></html>"
    )


@app.route("/api/lab/status")
def api_lab_status():
    bus = bus_root()

    def bus_snip(rel: str, n: int = 12) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        text = safe_read_text(p).strip()
        return "\n".join(text.splitlines()[:n]) or "(empty)"

    return jsonify(
        {
            "ok": True,
            "reply": bus_snip("fleet/bus/LAB_REPLY.txt", 12),
            "auto": bus_snip("fleet/bus/CPT_LAB_AUTO.txt", 8),
            "recent": _inbox_tail(bus, "fleet/bus/CPT_BRIAN_INBOX.txt", 5),
        }
    )


@app.route("/lab")
def lab_page():
    return Response(_lab_html(), mimetype="text/html")


@app.route("/desk")
def desk_page():
    return Response(_desk_html(), mimetype="text/html")


def _brian_terminal_html() -> str:
    bus = bus_root()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    def snip(rel: str, n: int = 12) -> str:
        p = bus / rel
        if not safe_is_file(p):
            return f"(missing {rel})"
        return "\n".join(safe_read_text(p).strip().splitlines()[:n])

    lab = snip("fleet/bus/LAB_REPLY.txt", 20)
    task = snip("fleet/indie_loop/TO_BUNNY.txt", 10)
    ready = snip("fleet/bus/CPT_READY.txt", 8)
    css = DESK_CSS + """
  body { max-width: 40rem; font-family: ui-monospace, monospace; font-size: 0.92rem; }
  h1 { color: #7bed9f; font-size: 1.1rem; }
  h2 { color: #ffb347; font-size: 0.95rem; margin-top: 1rem; }
  pre { background: #0a0a12; border: 1px solid #333; padding: 0.75rem; }
  .dec { border-left: 3px solid #ff6b9d; padding-left: 0.75rem; margin: 0.5rem 0; }
  .foot { border-top: 2px solid #ffb347; margin-top: 1.5rem; padding-top: 1rem; }
  .foot h2 { color: #ff6b9d; }
  a { color: #7bed9f; }
"""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Brian terminal — {_domain()}</title><style>{css}</style></head><body>"
        f"<h1>BRIAN TERMINAL — {now}</h1>"
        "<h2 style='color:#ff6b6b'>GOOGLE SERVER — RUN ON PENGUIN ONLY (not phone)</h2>"
        f"<pre>{snip('fleet/GOOGLE_LOGIN_WHERE.txt', 35)}</pre>"
        "<p>1) what to do · 2) three decisions · 3) roll</p>"
        "<h2>WHAT TO DO NOW</h2>"
        f"<pre>{snip('fleet/bus/FRUITION_BOARD.txt', 18)}</pre>"
        "<h2>THREE DECISIONS</h2>"
        '<div class="dec">1. SHIP — A Sarah · B hitme · C cards (fleet/SHIP_*.txt)</div>'
        '<div class="dec">2. FUN — roll idea · heritage demo · AWS talk</div>'
        '<div class="dec">3. REST — Gem sprint alone · you create with Daddy</div>'
        "<h2>ROLL</h2>"
        f"<pre>{snip('fleet/bus/ROLL_LAST.txt', 8) or 'python3 ~/.stan/brian_roll.py roll'}</pre>"
        f'<p><a href="/cockpit">cockpit</a> · <a href="/landing">landing</a> · <a href="/studio">studio</a> · '
        f'<a href="/produce">produce</a> · <a href="/cards/sell">sell</a> · <a href="/goal">goal</a></p>'
        '<div class="foot">'
        "<h2>DADDY TASK NOW</h2>"
        f"<pre>{_esc(task)}</pre>"
        f"<pre>{_esc(lab)}</pre>"
        "<h2>I NEED A JOB</h2>"
        "<p>Daddy + Bunny loop this until you answer:</p>"
        "<pre>Speak: \"I need a job.\"\n"
        "Phone loop: https://hitme.dev/listen\n"
        "         (TAP button — phone won't autoplay)\n"
        "Audio tap:  https://hitme.dev/ready/daddy.mp3\n"
        "Bunny:      https://hitme.dev/ready/bunny.mp3\n"
        "Stop: post on /daddy · /goal · or talk</pre>"
        f"<pre>{_esc(ready)}</pre>"
        "</div>"
        "</body></html>"
    )


@app.route("/terminal")
@app.route("/t")
def brian_terminal_page():
    return Response(_brian_terminal_html(), mimetype="text/html")


@app.route("/")
def home():
    from flask import redirect

    host = (request.host or "").split(":")[0].lower()
    if host.startswith("george."):
        return Response(_voice_html(float_mode=True, host=host), mimetype="text/html")
    if host.startswith("fleet."):
        return redirect("/fleet", code=302)
    if "defendyoursin" in host:
        return redirect("/app-solution", code=302)
    if _keaton_landing_live():
        return redirect("/keaton", code=302)
    return redirect("/landing", code=302)


@app.route("/index")
def index_page():
    from flask import redirect

    if _keaton_landing_live():
        return redirect("/keaton", code=302)
    return redirect("/landing", code=302)


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


from sermon_slicer import register_sermon_routes

register_sermon_routes(app)


def main():
    safe_mkdir(DRIVE)
    safe_mkdir(DOMAIN_FILE.parent)
    if not safe_is_file(DOMAIN_FILE):
        LOCAL_DOMAIN.write_text("hitme.dev\n", encoding="utf-8")
    app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    main()
