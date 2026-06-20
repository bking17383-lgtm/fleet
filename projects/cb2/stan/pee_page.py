#!/usr/bin/env python3
"""hitme.dev/pee — tap when you went · 30m reminder game."""
from __future__ import annotations

import html as html_mod


def _esc(text: str) -> str:
    return html_mod.escape(text or "", quote=True)


def pee_game_html(*, domain: str = "hitme.dev") -> str:
    css = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, sans-serif; background: #0a1628; color: #eef;
    min-height: 100dvh; padding: max(14px, env(safe-area-inset-top)) 14px max(24px, env(safe-area-inset-bottom));
    text-align: center;
  }
  .badge { font-size: 0.62rem; letter-spacing: 0.14em; text-transform: uppercase; color: #64b5f6; }
  h1 { font-size: 2rem; margin: 8px 0 4px; color: #fff; }
  .sub { color: #8899aa; font-size: 0.85rem; margin-bottom: 16px; line-height: 1.4; }
  .due {
    display: none; background: #ff6b35; color: #111; font-weight: 800; font-size: 1.15rem;
    padding: 14px; border-radius: 14px; margin-bottom: 14px; animation: pulse 1.2s ease infinite;
  }
  .due.show { display: block; }
  @keyframes pulse { 50% { transform: scale(1.02); } }
  .hero b { display: block; font-size: 2.4rem; color: #7bed9f; }
  .hero span { font-size: 0.72rem; color: #8899aa; text-transform: uppercase; letter-spacing: 0.08em; }
  .hero { background: #152238; border: 2px solid #2a4060; border-radius: 16px; padding: 16px; margin-bottom: 14px; }
  .btn {
    width: 100%; max-width: 22rem; margin: 0 auto 10px; display: block; padding: 22px 16px;
    border: none; border-radius: 18px; font-size: 1.25rem; font-weight: 800; cursor: pointer;
    background: linear-gradient(180deg, #4fc3f7, #0288d1); color: #041018;
    box-shadow: 0 6px 0 #01579b; -webkit-tap-highlight-color: transparent;
  }
  .btn:active { transform: translateY(3px); box-shadow: 0 3px 0 #01579b; }
  .msg { min-height: 1.4em; color: #7bed9f; font-size: 0.95rem; margin: 10px 0; }
  .msg.bad { color: #ff8a80; }
  .fine { font-size: 0.72rem; color: #667; line-height: 1.45; max-width: 22rem; margin: 14px auto 0; }
  .links { margin-top: 16px; font-size: 0.75rem; }
  .links a { color: #64b5f6; margin: 0 6px; }
"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#0a1628">
  <title>Pee Game — {_esc(domain)}</title>
  <style>{css}</style>
</head>
<body>
  <p class="badge">hitme · safety mode · daddy watching</p>
  <h1>Pee Game</h1>
  <p class="sub">Tap when you went. Daddy asks every 30 minutes.<br>
  First time? <a href="/turf/intro" style="color:#ffd700">watch the dumb how-to</a> then <a href="/turf/setup" style="color:#64b5f6">setup fence</a>.</p>

  <div class="due" id="due">Do you have to pee yet?</div>

  <div class="hero">
    <b id="since">—</b>
    <span>since last log</span>
  </div>
  <div class="hero">
    <b id="gallons">0</b>
    <span>gallons city water (1.6 each · yard wins)</span>
  </div>

  <p class="msg" id="msg"></p>
  <button type="button" class="btn" id="logBtn">I JUST PEED</button>

  <p class="fine">Outside = barn board pegs · inside still counts here.<br>Jane training later. You on puppy. Daddy on cb2.</p>
  <p class="links"><a href="/turf/treasure">Treasure map (all spots)</a> · <a href="/turf/barn">Barn board</a> · <a href="/turf/setup">Setup pegs</a> · <a href="/">hitme</a></p>

  <script>
    const msg = (t, bad) => {{
      const el = document.getElementById('msg');
      el.textContent = t || '';
      el.className = bad ? 'msg bad' : 'msg';
    }};

    function fmtSince(m) {{
      if (m == null) return 'never logged';
      if (m < 1) return 'just now';
      if (m < 60) return m + ' min';
      const h = Math.floor(m / 60), r = m % 60;
      return h + 'h' + (r ? ' ' + r + 'm' : '');
    }}

    function render(s) {{
      document.getElementById('since').textContent = fmtSince(s.minutes_since);
      document.getElementById('gallons').textContent = (s.gallons_saved ?? 0).toLocaleString();
      document.getElementById('due').classList.toggle('show', !!s.due);
    }}

    async function refresh() {{
      try {{
        const r = await fetch('/api/pee/status');
        const s = await r.json();
        if (s.ok) render(s);
      }} catch (e) {{}}
    }}

    document.getElementById('logBtn').onclick = async () => {{
      try {{
        const r = await fetch('/api/pee/log', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: '{{}}' }});
        const s = await r.json();
        if (!s.ok) {{ msg(s.error || 'fail', true); return; }}
        msg('Logged. +' + (s.gallons_saved ? '1.6 gal story' : '1') + ' · Daddy saw it.');
        render(s);
      }} catch (e) {{ msg('offline?', true); }}
    }};

    refresh();
    setInterval(refresh, 60000);
  </script>
</body>
</html>"""
