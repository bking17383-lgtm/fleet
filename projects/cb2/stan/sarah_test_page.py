#!/usr/bin/env python3
"""Mobile test page for Sarah — seminary preview + studio links."""
from __future__ import annotations

from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def for_sarah_html(sarah_voice_url: str = "/sarah") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Sarah — test page</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #0b0b0f;
    color: #eee;
    padding: max(1rem, env(safe-area-inset-top)) 1rem 2rem;
    line-height: 1.45;
  }}
  h1 {{ font-size: 1.35rem; font-weight: 600; margin-bottom: 0.25rem; }}
  .hi {{ color: #ff6b9d; }}
  .sub {{ color: #888; font-size: 0.9rem; margin-bottom: 1.25rem; }}
  .card {{
    display: block;
    background: #16161c;
    border: 1px solid #2a2a32;
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.75rem;
    text-decoration: none;
    color: inherit;
  }}
  .card:active {{ border-color: #ff6b9d; }}
  .card b {{ display: block; font-size: 1rem; margin-bottom: 0.25rem; }}
  .card span {{ font-size: 0.85rem; color: #999; }}
  .tag {{ display: inline-block; font-size: 0.65rem; letter-spacing: 0.06em; text-transform: uppercase;
    color: #7bed9f; margin-bottom: 0.35rem; }}
  .section {{ font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase; color: #666;
    margin: 1.25rem 0 0.5rem; }}
  footer {{ margin-top: 1.5rem; font-size: 0.8rem; color: #555; }}
</style>
</head>
<body>
  <p class="tag">For Sarah · phone test</p>
  <h1><span class="hi">Hi Sarah</span> — start here.</h1>
  <p class="sub">Updated {_now()[:16]}</p>

  <a class="card" href="/seminary-app" style="border-color:#ff6b9d;background:#1a1020">
    <b>Seminary Application</b>
    <span>You asked for this — Canvas · afternoon · online submit · 2 courses</span>
  </a>

  <p class="section">Also on this phone</p>
  <a class="card" href="/seminary">
    <b>Afternoon Queue</b>
    <span>Shorter preview of the same idea</span>
  </a>
  <a class="card" href="/handoff">
    <b>Handoff / QR</b>
    <span>If links break — Brian opens this</span>
  </a>

  <p class="section">Other builds (Brian lane)</p>
  <a class="card" href="/studio">
    <b>Studio deck</b>
    <span>Sell sheet, cockpit, dossier — cards stay illiquid until ready</span>
  </a>
  <a class="card" href="{sarah_voice_url}">
    <b>Sarah voice app</b>
    <span>Snap a post-it · hear it back · confirm</span>
  </a>
  <a class="card" href="/sarah">
    <b>Sarah pitch page</b>
    <span>Appointment product one-pager</span>
  </a>

  <footer>Tell Brian what works. Seminary app is the main test.</footer>
</body>
</html>"""


def seminary_application_html() -> str:
    """What Sarah asked for — seminary app concept (Canvas · afternoon · online submit)."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Seminary Application</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #0a0a12;
    color: #eee;
    padding: max(1rem, env(safe-area-inset-top)) 1rem 2.5rem;
    line-height: 1.5;
    max-width: 420px;
    margin: 0 auto;
  }}
  .badge {{ display: inline-block; font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: #ff6b9d; border: 1px solid #ff6b9d44; padding: 0.25rem 0.5rem; border-radius: 4px; margin-bottom: 0.5rem; }}
  h1 {{ font-size: 1.45rem; color: #7bed9f; margin-bottom: 0.35rem; }}
  .sub {{ color: #888; font-size: 0.9rem; margin-bottom: 1.25rem; }}
  .box {{ background: #161622; border: 1px solid #333; border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem; }}
  .box h2 {{ font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; color: #ffb347; margin-bottom: 0.5rem; }}
  .box p, .box li {{ font-size: 0.9rem; color: #ccc; }}
  .box ul {{ padding-left: 1.1rem; margin-top: 0.35rem; }}
  .row {{ background: #161622; border: 1px solid #333; border-radius: 12px; padding: 0.9rem; margin-bottom: 0.65rem; }}
  .due {{ color: #ff6b9d; font-size: 0.75rem; font-weight: 600; }}
  .course {{ color: #888; font-size: 0.8rem; }}
  .title {{ font-size: 0.95rem; margin: 0.25rem 0; }}
  .read {{ font-size: 0.8rem; color: #aaa; }}
  .chk {{ margin-top: 0.5rem; font-size: 0.75rem; color: #666; }}
  .cta {{ display: block; text-align: center; margin-top: 1.25rem; padding: 1rem;
    background: #ff6b9d; color: #0a0a12; font-weight: 700; border-radius: 999px; text-decoration: none; }}
  a {{ color: #7bed9f; }}
  footer {{ margin-top: 1.5rem; font-size: 0.8rem; color: #555; text-align: center; }}
</style>
</head>
<body>
  <span class="badge">Sarah · seminary</span>
  <h1>Seminary Application</h1>
  <p class="sub">Canvas readings · afternoon blocks · online submissions · 2 courses</p>

  <div class="box">
    <h2>What you asked for</h2>
    <ul>
      <li>Readings live in <strong>Canvas</strong></li>
      <li>Done = <strong>submission posted</strong> online</li>
      <li>You consume in the <strong>afternoon</strong></li>
      <li>Two courses — one queue, not four tabs</li>
    </ul>
  </div>

  <div class="box">
    <h2>Afternoon block (90 min)</h2>
    <p>Open queue → skim map → read what’s due → draft in Canvas → submit.</p>
  </div>

  <p style="font-size:0.75rem;color:#666;margin:1rem 0 0.5rem;text-transform:uppercase;letter-spacing:0.1em">This week (preview)</p>

  <div class="row">
    <div class="due">Wed 11:59 PM · Canvas</div>
    <div class="course">Course A · Discussion 2</div>
    <div class="title">Submit online · text box ~250 words</div>
    <div class="read">Read: Module 3 · est. 45 min · afternoon Tue</div>
    <div class="chk">☐ Read · ☐ Draft · ☐ Submitted</div>
  </div>
  <div class="row">
    <div class="due">Fri 5:00 PM · Canvas</div>
    <div class="course">Course B · Reflection 1</div>
    <div class="title">Submit online · upload or text</div>
    <div class="read">Read: Ch. 1–2 · est. 35 min · afternoon Thu</div>
    <div class="chk">☐ Read · ☐ Draft · ☐ Submitted</div>
  </div>

  <a class="cta" href="/for-sarah">← Back to test home</a>
  <footer>Tell Brian: too much · too little · or ship it · {_now()[:16]}</footer>
</body>
</html>"""


def seminary_preview_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Afternoon Queue — preview</title>
<style>
  body {{ font-family: system-ui,sans-serif; background:#0a0a12; color:#eee; padding:1rem; max-width:420px; margin:0 auto; }}
  h1 {{ font-size:1.2rem; color:#7bed9f; }}
  .sub {{ color:#888; font-size:0.85rem; margin-bottom:1rem; }}
  .row {{ background:#161622; border:1px solid #333; border-radius:12px; padding:0.9rem; margin-bottom:0.65rem; }}
  .due {{ color:#ff6b9d; font-size:0.75rem; font-weight:600; }}
  .course {{ color:#888; font-size:0.8rem; }}
  .title {{ font-size:0.95rem; margin:0.25rem 0; }}
  .read {{ font-size:0.8rem; color:#aaa; }}
  .chk {{ margin-top:0.5rem; font-size:0.75rem; color:#666; }}
  a {{ color:#7bed9f; }}
</style>
</head>
<body>
  <h1>Afternoon Queue</h1>
  <p class="sub">Preview · 2 courses · online submit · not wired to Canvas yet</p>

  <div class="row">
    <div class="due">Wed 11:59 PM</div>
    <div class="course">Course A · Discussion 2</div>
    <div class="title">Submit: Canvas text box (~250 words)</div>
    <div class="read">Read: Module 3 PDF · est. 45 min</div>
    <div class="chk">☐ Reading skimmed · ☐ Post drafted · ☐ Submitted online</div>
  </div>
  <div class="row">
    <div class="due">Fri 5:00 PM</div>
    <div class="course">Course B · Reflection 1</div>
    <div class="title">Submit: file upload or text</div>
    <div class="read">Read: Ch. 1–2 · est. 35 min</div>
    <div class="chk">☐ Reading skimmed · ☐ Draft started · ☐ Submitted online</div>
  </div>

  <p style="margin-top:1rem;font-size:0.85rem">Afternoon block: pick one row → pre-class card → read → submit in Canvas.</p>
  <p><a href="/for-sarah">← Back to Sarah test</a></p>
</body>
</html>"""
