#!/usr/bin/env python3
"""DIRT STRONG — family share page (Alabama · trucks · redneck · Army Strong energy)."""

from __future__ import annotations

from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")[:10]


def dirt_strong_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta property="og:title" content="DIRT STRONG">
<meta property="og:description" content="There's strong. Then there's dirt strong. Alabama. Big trucks. The ones who show up.">
<title>DIRT STRONG</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Arial Black", "Helvetica Neue", Arial, sans-serif;
    background: #0a0a0a;
    color: #f5f5f5;
    line-height: 1.2;
  }}
  .hero {{
    min-height: 52vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 2rem 1.25rem;
    background:
      linear-gradient(180deg, rgba(158,27,50,0.35) 0%, transparent 45%),
      linear-gradient(180deg, #0a0a0a 0%, #141414 100%);
    text-align: center;
  }}
  .truck {{ font-size: 2.5rem; margin-bottom: 0.5rem; filter: grayscale(0.2); }}
  .brand {{
    font-size: clamp(2.8rem, 14vw, 4.5rem);
    font-weight: 900;
    letter-spacing: -0.03em;
    line-height: 0.95;
    color: #fff;
    text-transform: uppercase;
  }}
  .brand span {{ color: #9E1B32; display: block; }}
  .hook {{
    margin-top: 1.25rem;
    font-size: clamp(1rem, 4.5vw, 1.35rem);
    font-weight: 700;
    color: #ccc;
    letter-spacing: 0.02em;
  }}
  .hook em {{ color: #9E1B32; font-style: normal; }}
  .loc {{
    margin-top: 0.75rem;
    font-size: 0.7rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #666;
  }}
  main {{ padding: 0 1.25rem 2.5rem; max-width: 28rem; margin: 0 auto; }}
  .block {{
    margin: 1.75rem 0;
    padding-left: 0.75rem;
    border-left: 4px solid #9E1B32;
  }}
  .block p {{
    font-family: Georgia, serif;
    font-size: 1.05rem;
    font-weight: 400;
    color: #d4d4d4;
    line-height: 1.55;
    margin-bottom: 0.75rem;
  }}
  .block p:last-child {{ margin-bottom: 0; }}
  .block strong {{ color: #fff; }}
  .pillars {{
    list-style: none;
    margin: 1.5rem 0;
  }}
  .pillars li {{
    font-size: 0.95rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 0.85rem 0;
    border-bottom: 1px solid #222;
    color: #e8e8e8;
  }}
  .pillars li span {{ color: #9E1B32; margin-right: 0.35rem; }}
  .morgan {{
    background: #141414;
    border: 2px solid #333;
    padding: 1.15rem;
    margin: 1.5rem 0;
    text-align: center;
  }}
  .morgan b {{ color: #9E1B32; font-size: 1.1rem; }}
  .morgan p {{
    font-family: Georgia, serif;
    font-size: 0.95rem;
    color: #aaa;
    margin-top: 0.5rem;
    line-height: 1.45;
  }}
  .cta {{
    display: block;
    margin: 1rem auto;
    padding: 1rem 1.25rem;
    max-width: 20rem;
    text-align: center;
    font-size: 0.9rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    text-decoration: none;
    border-radius: 4px;
    border: none;
    cursor: pointer;
    width: 100%;
  }}
  .cta.red {{ background: #9E1B32; color: #fff; }}
  .cta.outline {{ background: transparent; color: #fff; border: 2px solid #444; }}
  .foot {{ text-align: center; font-size: 0.65rem; color: #444; margin-top: 1.5rem; letter-spacing: 0.08em; }}
</style>
</head>
<body>
  <header class="hero">
    <div class="truck" aria-hidden="true">🛻</div>
    <h1 class="brand">DIRT<span>STRONG</span></h1>
    <p class="hook">There's strong.<br>Then there's <em>dirt strong.</em></p>
    <p class="loc">Alabama · Missouri · anywhere the trucks run</p>
  </header>

  <main>
    <div class="block">
      <p>Left California. Bought land. Five parcels. Big truck in the drive.
      <strong>That's not running away — that's running toward.</strong></p>
      <p>Call it redneck. Call it hillbilly. We call it the reason America
      still stands when the coast forgets how.</p>
    </div>

    <ul class="pillars">
      <li><span>▸</span> Strong enough to move states</li>
      <li><span>▸</span> Strong enough to own dirt</li>
      <li><span>▸</span> Strong enough to fix it yourself</li>
      <li><span>▸</span> Strong enough — no beer required</li>
    </ul>

    <div class="morgan">
      <b>MORGAN</b>
      <p>This one's for you. Cal couldn't hold you. Missouri knows your name.
      The family list still breathing — you're why the flag has weight.</p>
    </div>

    <div class="block">
      <p>When the power dies, when the storm hits, when something heavy
      won't move — <strong>they don't call the coast. They call you.</strong></p>
    </div>

    <a class="cta red" href="/parcels">Play Five Parcels</a>
    <button class="cta outline" type="button" id="shareBtn">Share DIRT STRONG</button>
    <p class="foot">RESPECT · {_now()}</p>
  </main>

  <script>
  (function(){{
    var btn = document.getElementById('shareBtn');
    var url = location.href.split('#')[0];
    btn.addEventListener('click', function(){{
      if (navigator.share) {{
        navigator.share({{ title: 'DIRT STRONG', text: "There's strong. Then there's dirt strong.", url: url }});
      }} else if (navigator.clipboard) {{
        navigator.clipboard.writeText(url);
        btn.textContent = 'COPIED';
      }} else {{
        prompt('Copy:', url);
      }}
    }});
  }})();
  </script>
</body>
</html>"""


def heartbeat_html() -> str:
    """Legacy alias → same page."""
    return dirt_strong_html()
