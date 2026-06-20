#!/usr/bin/env python3
"""hitme.dev/drop — Brian feeds Daddy ideas + data from any box."""
from __future__ import annotations

import html as html_mod


def _esc(text: str) -> str:
    return html_mod.escape(text or "", quote=True)


def drop_page_html(*, domain: str = "hitme.dev") -> str:
    css = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: system-ui, sans-serif; background: #0a0a12; color: #eee;
    min-height: 100dvh; padding: max(14px, env(safe-area-inset-top)) 14px max(28px, env(safe-area-inset-bottom));
  }
  .badge { font-size: 0.62rem; letter-spacing: 0.14em; text-transform: uppercase; color: #ffb347; }
  h1 { font-size: 1.6rem; margin: 8px 0 4px; color: #ff6b9d; }
  .sub { color: #888; font-size: 0.85rem; line-height: 1.45; margin-bottom: 14px; }
  textarea {
    width: 100%; min-height: 9rem; padding: 12px; border-radius: 12px; border: 2px solid #444;
    background: #151525; color: #eee; font: inherit; font-size: 1.05rem; line-height: 1.45; resize: vertical;
  }
  select { width: 100%; margin: 10px 0; padding: 10px; border-radius: 10px; border: 2px solid #444;
    background: #151525; color: #eee; font: inherit; }
  .btn {
    width: 100%; margin-top: 10px; padding: 16px; border: none; border-radius: 14px;
    font-size: 1.15rem; font-weight: 800; cursor: pointer;
    background: linear-gradient(180deg, #ff6b9d, #c44569); color: #fff;
    box-shadow: 0 5px 0 #7a2844;
  }
  .btn:active { transform: translateY(2px); box-shadow: 0 3px 0 #7a2844; }
  .msg { min-height: 1.4em; margin-top: 12px; color: #7bed9f; font-size: 0.95rem; }
  .msg.bad { color: #ff8a80; }
  .lanes { font-size: 0.75rem; color: #666; line-height: 1.5; margin-top: 16px; }
  .lanes a { color: #7bed9f; }
"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#0a0a12">
  <title>Drop — {_esc(domain)}</title>
  <style>{css}</style>
</head>
<body>
  <p class="badge">Brian → Daddy · safety mode</p>
  <h1>Drop it here</h1>
  <p class="sub">Ideas · orders · paste · links · data. Daddy is the only one working.<br>
  Puppy · phone · any box — one tap lands in my handoff.</p>

  <form id="dropForm">
    <textarea id="dropText" placeholder="Type or paste anything…"></textarea>
    <select id="dropKind">
      <option value="idea">Idea</option>
      <option value="order">Order — do this</option>
      <option value="data">Data / paste</option>
    </select>
    <button type="submit" class="btn">Send to Daddy</button>
  </form>
  <p class="msg" id="msg"></p>

  <p class="lanes">Also: <a href="/pee">pee game</a> · <a href="/daddy">daddy lab</a> · <a href="/inbox">inbox</a><br>
  Drive: <code>drop_pile/from_brian/NOTE.txt</code> (inbound only · overwrite yours)</p>

  <script>
    const msg = (t, bad) => {{
      const el = document.getElementById('msg');
      el.textContent = t || '';
      el.className = bad ? 'msg bad' : 'msg';
    }};
    document.getElementById('dropForm').onsubmit = async (e) => {{
      e.preventDefault();
      const raw = document.getElementById('dropText').value.trim();
      if (!raw) {{ msg('empty', true); return; }}
      const kind = document.getElementById('dropKind').value;
      const text = '[' + kind.toUpperCase() + '] ' + raw;
      msg('Sending…');
      try {{
        const r = await fetch('/api/brian', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ text, lane: 'daddy', via: 'drop' }})
        }});
        const d = await r.json();
        if (!d.ok) {{ msg(d.error || 'fail', true); return; }}
        msg('Daddy got it. Handoff updated.');
        document.getElementById('dropText').value = '';
      }} catch (x) {{ msg('offline?', true); }}
    }};
  </script>
</body>
</html>"""
