#!/usr/bin/env python3
"""hitme.dev — who roster + fleet links (port 8770)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, send_file

from design_links import DESK_SECTIONS

DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
WHO_JSON = DRIVE / "fleet/WHO.json"
CARD_DEMO = DRIVE / "lester/heritage/card_demo.html"
DOMAIN_FILE = DRIVE / "fleet/HITME_DOMAIN.txt"
PORT = int(__import__("os").environ.get("HITME_PORT", "8770"))

app = Flask(__name__)


def _domain() -> str:
    if DOMAIN_FILE.is_file():
        return DOMAIN_FILE.read_text(encoding="utf-8").strip().splitlines()[0] or "hitme.dev"
    return "hitme.dev"


def _who() -> dict:
    if WHO_JSON.is_file():
        return json.loads(WHO_JSON.read_text(encoding="utf-8"))
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
"""


def _desk_html() -> str:
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>Design desk — {_domain()}</title><style>{DESK_CSS}</style></head><body>",
        f"<h1>Design desk</h1>",
        '<p class="sub">Click — no hunting paths. '
        '<span class="top"><a href="/">← hitme</a></span></p>',
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


@app.route("/card")
@app.route("/heritage/card_demo.html")
def card_demo():
    if CARD_DEMO.is_file():
        return send_file(CARD_DEMO, mimetype="text/html")
    return Response("card demo missing on Drive", status=404)


@app.route("/desk")
def desk_page():
    return Response(_desk_html(), mimetype="text/html")


@app.route("/")
def home():
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
    return home()


@app.route("/who.json")
@app.route("/api/who")
def who_json():
    return jsonify(_who())


@app.route("/health")
def health():
    return jsonify({"ok": True, "domain": _domain(), "port": PORT})


def main():
    DRIVE.mkdir(parents=True, exist_ok=True)
    DOMAIN_FILE.write_text("hitme.dev\n", encoding="utf-8")
    app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    main()
