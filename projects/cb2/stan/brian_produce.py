#!/usr/bin/env python3
"""Brian produce lane — ship artifacts, not bus docs.

  python3 ~/.stan/brian_produce.py sell|story|sarah|hitme|bundles|studio|setlist|mick|invent|all
"""
from __future__ import annotations

import html as html_mod
import json
import random
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import bus_root, safe_mkdir

STAN = Path.home() / ".stan"
COLLECTION = STAN / "parked/baseball_cards_cb2/data/collection.json"
OUT = bus_root() / "drop_pile/from_daddy/produced"
LATEST = OUT / "LATEST.txt"
CATALOG = OUT / "INVENT_CATALOG.json"

STAGE_WORDS = (
    "electric", "midnight", "swagger", "raw", "legend", "rebel", "gold", "thunder",
    "velvet", "fire", "ghost", "honky", "satisfaction", "jumpin", "wild", "soul",
)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _esc(t: str) -> str:
    return html_mod.escape(str(t or ""), quote=True)


def _load_cards() -> list[dict]:
    data = json.loads(COLLECTION.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("collection.json must be a list")
    return data


def _mid(card: dict) -> float:
    v = card.get("valuation") or {}
    raw = v.get("estimate_mid")
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def _write(name: str, body: str) -> Path:
    safe_mkdir(OUT)
    p = OUT / name
    p.write_text(body, encoding="utf-8")
    return p


def _manifest(entries: list[tuple[str, Path]]) -> None:
    lines = [f"PRODUCED {_now()}", ""]
    for label, path in entries:
        lines.append(f"{label}\t{path.name}\t{path}")
    manifest = OUT / f"manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    prev = {}
    if CATALOG.is_file():
        try:
            prev = json.loads(CATALOG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = {}
    items = prev.get("items") or []
    for label, path in entries:
        items.append({"id": label, "file": path.name, "path": str(path), "at": _now()})
    CATALOG.write_text(
        json.dumps({"updated": _now(), "count": len(items), "items": items[-80:]}, indent=2),
        encoding="utf-8",
    )
    LATEST.write_text(
        "\n".join(f"{label}: {path.name}" for label, path in entries) + f"\nupdated: {_now()}\n",
        encoding="utf-8",
    )


def _shell_css() -> str:
    return """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #0c0c14; color: #eee; padding: 1.25rem; max-width: 900px; margin: 0 auto; line-height: 1.5; }
  h1 { font-size: 1.7rem; margin-bottom: 0.35rem; }
  h2 { font-size: 1rem; color: #ffb347; margin: 1.25rem 0 0.5rem; }
  .sub { color: #888; margin-bottom: 1.25rem; }
  a { color: #7bed9f; }
  .btn { display: inline-block; margin: 0.35rem 0.5rem 0.35rem 0; padding: 0.55rem 0.9rem; background: #1a1a2e; border: 1px solid #444; border-radius: 999px; text-decoration: none; font-size: 0.9rem; }
  .btn.hot { border-color: #ff6b9d; color: #ff6b9d; }
  .grid { display: grid; gap: 0.75rem; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
  .tile { background: #161622; border: 1px solid #333; border-radius: 12px; padding: 1rem; }
  .tile b { color: #c9a227; display: block; margin-bottom: 0.35rem; }
  .tile p { font-size: 0.85rem; color: #aaa; }
"""


def _sell_sheet(cards: list[dict]) -> str:
    total = sum(_mid(c) for c in cards)
    priced = sum(1 for c in cards if _mid(c) > 0)
    rookies = [c for c in cards if c.get("rookie")]
    top = sorted(cards, key=_mid, reverse=True)[:24]
    decades: dict[str, float] = {}
    for c in cards:
        y = str(c.get("year") or "?")[:3] + "0s"
        decades[y] = decades.get(y, 0) + _mid(c)

    def row(c: dict) -> str:
        img = c.get("image_url") or ""
        return (
            f'<article class="card">'
            f'<img src="{_esc(img)}" alt="{_esc(c.get("player",""))}" loading="lazy">'
            f'<div class="meta">'
            f'<strong>{_esc(c.get("player",""))}</strong>'
            f'<span>{_esc(str(c.get("year","")))} · {_esc(c.get("set",""))} #{_esc(str(c.get("card_number","")))}</span>'
            f'<em>${_mid(c):.2f}</em>'
            f"</div></article>"
        )

    decade_rows = "".join(
        f"<li><span>{_esc(d)}</span><span>${v:,.0f}</span></li>"
        for d, v in sorted(decades.items(), key=lambda x: -x[1])[:8]
    )
    extra = """
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem; }
  .stat { background: #161622; border: 1px solid #333; border-radius: 10px; padding: 1rem; text-align: center; }
  .stat b { display: block; font-size: 1.5rem; color: #c9a227; }
  .cols { display: grid; grid-template-columns: 1fr 280px; gap: 1.5rem; }
  @media (max-width: 800px) { .cols { grid-template-columns: 1fr; } }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 0.75rem; }
  .card { background: #161622; border-radius: 10px; overflow: hidden; border: 1px solid #2a2a3a; }
  .card img { width: 100%; aspect-ratio: 2/3; object-fit: cover; }
  .meta { padding: 0.5rem; font-size: 0.75rem; }
  aside ul { list-style: none; }
  aside li { display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #222; font-size: 0.85rem; }
"""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>497 Cards — Sell Sheet</title><style>{_shell_css()}{extra}</style></head><body>
<h1 style="color:#7bed9f">497 Cards · CollX Market Sheet</h1>
<p class="sub">{_esc(_now())}</p>
<div class="stats">
  <div class="stat"><b>{len(cards)}</b><span style="color:#888;font-size:0.75rem">CARDS</span></div>
  <div class="stat"><b>${total:,.0f}</b><span style="color:#888;font-size:0.75rem">MID</span></div>
  <div class="stat"><b>{priced}</b><span style="color:#888;font-size:0.75rem">PRICED</span></div>
  <div class="stat"><b>{len(rookies)}</b><span style="color:#888;font-size:0.75rem">ROOKIES</span></div>
</div>
<div class="cols"><section><h2 style="color:#ccc">Top 24</h2><div class="grid">{"".join(row(c) for c in top)}</div></section>
<aside><h2 style="color:#c9a227">Decades</h2><ul>{decade_rows}</ul></aside></div>
<p style="margin-top:1rem"><a href="/bundles">Bundle lots →</a></p>
</body></html>"""


def _story_card(cards: list[dict], lore: str = "") -> tuple[str, dict]:
    c = random.choice([x for x in cards if x.get("image_url")] or cards)
    player = c.get("player") or "Unknown"
    year = c.get("year") or "?"
    img = c.get("image_url") or ""
    val = _mid(c)
    lore_block = lore.strip() or (
        f"In {year}, this card waited in the stack like a B-side nobody played — "
        f"until tonight it jumped the queue."
    )
    slug = f"story_{c.get('id','x')}_{datetime.now().strftime('%H%M%S')}"
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Story — {_esc(player)}</title>
<style>
  body {{ font-family: Georgia, serif; background: radial-gradient(ellipse at 30% 20%, #2a1520, #0a0a0f); color: #f5e6c8;
    min-height: 100dvh; display: flex; align-items: center; justify-content: center; padding: 1rem; }}
  .frame {{ max-width: 420px; border: 3px double #c9a227; border-radius: 16px; padding: 1rem; text-align: center; background: rgba(0,0,0,0.45); }}
  .frame img {{ width: 100%; border-radius: 8px; margin-bottom: 1rem; }}
  h1 {{ font-size: 1.15rem; color: #c9a227; }}
  .lore {{ font-style: italic; line-height: 1.55; margin: 1rem 0; }}
  a {{ color: #c9a227; }}
</style></head><body><div class="frame">
<img src="{_esc(img)}" alt="">
<h1>{_esc(player)}</h1>
<p>{_esc(str(year))} · #{_esc(str(c.get('card_number','')))}</p>
<p class="lore">{_esc(lore_block)}</p>
<p style="color:#7bed9f">${_esc(f'{val:.2f}')} mid</p>
<p><a href="/cards/story?new=1">Another →</a></p>
</div></body></html>"""
    return slug, {"html": html, "card": c, "slug": slug}


def _sarah_pitch() -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sarah — snap your appointment</title><style>
  body {{ font-family: system-ui,sans-serif; background: linear-gradient(160deg,#0f0a1a,#1a1028); color:#eee;
    min-height:100dvh; display:flex; align-items:center; justify-content:center; padding:1.5rem; }}
  .card {{ max-width:420px; background:#161622; border:2px solid #ff6b9d; border-radius:20px; padding:1.75rem; }}
  h1 {{ color:#ff6b9d; font-size:1.5rem; }}
  .tag {{ color:#888; margin:0.5rem 0 1.25rem; }}
  ol {{ padding-left:1.2rem; color:#ccc; line-height:1.7; }}
  .cta {{ display:block; margin-top:1.5rem; padding:1rem; text-align:center; background:#ff6b9d; color:#0a0a12;
    border-radius:999px; font-weight:700; text-decoration:none; }}
  .note {{ margin-top:1rem; font-size:0.85rem; color:#888; }}
</style></head><body>
<div class="card">
  <h1>Sarah</h1>
  <p class="tag">Post-it → voice confirm → done</p>
  <ol>
    <li>Snap a photo of your appointment note</li>
    <li>Sarah reads it back out loud</li>
    <li>You confirm or fix — one tap</li>
  </ol>
  <a class="cta" href="http://100.115.92.26:8766/sarah">Try Sarah on your phone</a>
  <p class="note">Ship A · {_esc(_now())} · no fleet signup · just the link</p>
</div></body></html>"""


def _hitme_landing() -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>hitme.dev — Brian's studio on the road</title><style>
  body {{ font-family: system-ui,sans-serif; background:#0a0a12; color:#eee; margin:0; }}
  .hero {{ min-height:70dvh; display:flex; flex-direction:column; align-items:center; justify-content:center;
    text-align:center; padding:2rem 1.5rem; background: radial-gradient(circle at 50% 0%, #2a1530, #0a0a12 60%); }}
  h1 {{ font-size: clamp(2rem,8vw,3.2rem); color:#ff6b9d; letter-spacing:-0.02em; margin:0; }}
  .line {{ font-size:1.15rem; color:#ccc; max-width:28rem; margin:1rem auto 1.5rem; }}
  .links {{ display:flex; flex-wrap:wrap; gap:0.6rem; justify-content:center; }}
  .links a {{ padding:0.6rem 1.1rem; border-radius:999px; background:#151525; border:1px solid #444; color:#7bed9f; text-decoration:none; }}
  .links a.primary {{ background:#ff6b9d; color:#0a0a12; border-color:#ff6b9d; font-weight:600; }}
  footer {{ text-align:center; padding:2rem; color:#666; font-size:0.85rem; }}
  footer a {{ color:#888; }}
</style></head><body>
<section class="hero">
  <h1>hitme.dev</h1>
  <p class="line">Voice · cards · ideas · one link for the garage.<br>Say hello: <strong>hello@hitme.dev</strong></p>
  <div class="links">
    <a class="primary" href="/checkout">Enter studio</a>
    <a href="/cards/sell">497 cards</a>
    <a href="/sarah">Sarah</a>
    <a href="/studio">Preview studio</a>
  </div>
</section>
<footer>hitme.dev · landing · {_esc(_now())}</footer>
</body></html>"""


def _bundles(cards: list[dict]) -> str:
    by_decade: dict[str, list[dict]] = defaultdict(list)
    for c in cards:
        d = str(c.get("year") or "?")[:3] + "0s"
        by_decade[d].append(c)
    rows = []
    for decade in sorted(by_decade.keys()):
        chunk = by_decade[decade]
        total = sum(_mid(c) for c in chunk)
        top = sorted(chunk, key=_mid, reverse=True)[:3]
        thumbs = "".join(
            f'<img src="{_esc(c.get("image_url",""))}" alt="" style="width:48px;height:68px;object-fit:cover;border-radius:4px">'
            for c in top if c.get("image_url")
        )
        rows.append(
            f'<tr><td>{_esc(decade)}</td><td>{len(chunk)}</td><td>${total:,.0f}</td>'
            f'<td>${total/max(len(chunk),1):.2f}</td><td>{thumbs}</td></tr>'
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bundle Lots</title><style>{_shell_css()}
  table {{ width:100%; border-collapse:collapse; font-size:0.9rem; }}
  th,td {{ text-align:left; padding:0.6rem; border-bottom:1px solid #333; vertical-align:middle; }}
  th {{ color:#c9a227; }}
  td img {{ margin-right:4px; }}
</style></head><body>
<h1 style="color:#7bed9f">Sellable Bundle Lots</h1>
<p class="sub">Split the 497 by decade · {_esc(_now())}</p>
<table><tr><th>Decade</th><th>Cards</th><th>Mid total</th><th>Avg</th><th>Preview</th></tr>
{"".join(rows)}</table>
<p><a href="/cards/sell">Full sell sheet →</a></p>
</body></html>"""


def _studio() -> str:
    tiles = [
        ("Sell sheet", "497 cards priced · photos", "/cards/sell"),
        ("Bundle lots", "Decade splits for eBay", "/bundles"),
        ("Story cards", "Random heritage draw", "/cards/story?new=1"),
        ("Sarah", "Post-it appointments", "/sarah"),
        ("Midnight index", "Stage energy roulette", "/mick"),
        ("Setlist", "Top 10 poster", "/setlist"),
        ("Fortune", "Garage post-it oracle", "/fortune"),
        ("Garage radio", "FM 497 playlist", "/radio"),
        ("Encore meter", "Satisfaction clicker", "/encore"),
        ("Cockpit", "Porsche tach · ship RPM", "/cockpit"),
        ("Dossier", "Sherlock evidence brief", "/dossier"),
        ("Brochure", "No.1 card spec sheet", "/brochure"),
        ("9·1·1", "Nine proofs · one goal", "/911"),
        ("Scan proof", "Ship C one-pager", "/scan"),
        ("Team", "Fleet goal board", "/goal"),
    ]
    grid = "".join(
        f'<a class="tile" href="{u}"><b>{_esc(t)}</b><p>{_esc(d)}</p></a>' for t, d, u in tiles
    )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brian Studio</title><style>{_shell_css()}
  .grid {{ grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }}
  .tile {{ text-decoration:none; color:inherit; transition: border-color 0.15s; }}
  .tile:hover {{ border-color: #ff6b9d; }}
  h1 {{ color:#ff6b9d; }}
</style></head><body>
<h1>Studio</h1>
<p class="sub">Everything we built while you weren't looking · {_esc(_now())}</p>
<div class="grid">{grid}</div>
<p style="margin-top:1.5rem"><a href="/landing">← hitme.dev</a></p>
</body></html>"""


def _setlist(cards: list[dict]) -> str:
    top = sorted(cards, key=_mid, reverse=True)[:10]
    lines = []
    for i, c in enumerate(top, 1):
        lines.append(
            f'<li><span class="n">{i}</span><span class="t">{_esc(c.get("player",""))}</span>'
            f'<span class="v">${_mid(c):.0f}</span></li>'
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tonight's Setlist — Top 10 Cards</title><style>
  body {{ font-family: Georgia, serif; background:#0a0a0f; color:#f5e6c8; padding:2rem; max-width:480px; margin:0 auto; }}
  h1 {{ color:#c9a227; font-size:1.4rem; text-transform:uppercase; letter-spacing:0.15em; }}
  .sub {{ color:#666; font-size:0.85rem; margin-bottom:1.5rem; }}
  ul {{ list-style:none; }}
  li {{ display:grid; grid-template-columns:2rem 1fr auto; gap:0.5rem; padding:0.65rem 0; border-bottom:1px solid #222; }}
  .n {{ color:#ff6b9d; font-weight:bold; }}
  .v {{ color:#7bed9f; }}
</style></head><body>
<h1>Tonight's Setlist</h1>
<p class="sub">Top 10 by CollX mid · encore: the other 487</p>
<ul>{"".join(lines)}</ul>
<p><a href="/cards/sell" style="color:#c9a227">Full collection →</a></p>
</body></html>"""


def _mick_index(cards: list[dict]) -> str:
    picks = random.sample([c for c in cards if c.get("image_url")] or cards, min(12, len(cards)))
    cards_html = []
    for c in picks:
        energy = random.randint(72, 99)
        word = random.choice(STAGE_WORDS)
        cards_html.append(
            f'<article><img src="{_esc(c.get("image_url",""))}" alt="">'
            f'<h3>{_esc(c.get("player",""))}</h3>'
            f'<p class="e">{energy}% {word}</p></article>'
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Midnight Index</title><style>
  body {{ background:#0a0a0f; color:#eee; font-family:system-ui,sans-serif; padding:1.25rem; }}
  h1 {{ color:#ff6b9d; font-size:1.6rem; }}
  .sub {{ color:#888; margin-bottom:1rem; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:0.75rem; }}
  article {{ background:#161622; border-radius:12px; overflow:hidden; border:1px solid #333; }}
  img {{ width:100%; aspect-ratio:2/3; object-fit:cover; }}
  h3 {{ font-size:0.75rem; padding:0.4rem 0.5rem 0; }}
  .e {{ font-size:0.7rem; color:#c9a227; padding:0 0.5rem 0.5rem; text-transform:uppercase; letter-spacing:0.06em; }}
  .roll {{ display:inline-block; margin-top:1rem; padding:0.75rem 1.25rem; background:#ff6b9d; color:#0a0a12;
    border-radius:999px; text-decoration:none; font-weight:700; }}
</style></head><body>
<h1>Midnight Index</h1>
<p class="sub">Stage energy ratings for cardboard legends · refresh for new draw · {_esc(_now())}</p>
<div class="grid">{"".join(cards_html)}</div>
<a class="roll" href="/mick?new=1">Re-roll the night</a>
<p style="margin-top:1rem"><a href="/studio" style="color:#7bed9f">Studio →</a></p>
</body></html>"""


def _fortune() -> str:
    fortunes = [
        "The post-it says Tuesday. Your calendar says maybe. Sarah wins.",
        "Sell the 1970s lot before the encore.",
        "One human tries Sarah today. That's the whole chart.",
        "hello@hitme.dev rings once — answer it like a headline act.",
        "Lou Brock steals third. You steal twenty minutes and ship.",
        "The garage wants a voice. Give it one sentence on /goal.",
        "497 cards hum at midnight. A buyer is tuning in.",
        "Don't start the show with fleet law. Start with one link.",
    ]
    f = random.choice(fortunes)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Garage Fortune</title><style>
  body {{ min-height:100dvh; display:flex; align-items:center; justify-content:center; background:#0f0a18;
    color:#f5e6c8; font-family:Georgia,serif; padding:1.5rem; text-align:center; }}
  .f {{ max-width:24rem; font-size:1.35rem; line-height:1.55; border:2px dashed #ff6b9d; padding:2rem; border-radius:16px; }}
  a {{ color:#7bed9f; display:block; margin-top:1.5rem; font-family:system-ui,sans-serif; font-size:0.9rem; }}
</style></head><body>
<div><p class="f">{_esc(f)}</p>
<a href="/fortune?new=1">Another fortune</a>
<a href="/studio">Studio</a></div>
</body></html>"""


def _scan_one_pager() -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scan One Card — Proof</title><style>{_shell_css()}
  .step {{ background:#161622; border-left:4px solid #7bed9f; padding:1rem; margin:0.75rem 0; border-radius:0 8px 8px 0; }}
  .step b {{ color:#7bed9f; }}
</style></head><body>
<h1 style="color:#7bed9f">Scan One Card</h1>
<p class="sub">Ship C proof · 20 minutes · {_esc(_now())}</p>
<div class="step"><b>1</b> Open <a href="http://100.115.92.26:8002">:8002</a> on phone (same wifi)</div>
<div class="step"><b>2</b> Scan a physical card · match CollX mid</div>
<div class="step"><b>3</b> Screenshot · compare one eBay comp</div>
<div class="step"><b>4</b> Show <a href="/cards/sell">sell sheet</a> — 497 already priced</div>
<p class="sub">Pitch: inventory + tool, not vapor.</p>
</body></html>"""


def _garage_radio(cards: list[dict]) -> str:
    picks = random.sample(cards, min(8, len(cards)))
    tracks = []
    for i, c in enumerate(picks, 1):
        tracks.append(
            f'<li><span class="t">{i:02d}</span> {_esc(c.get("player",""))[:40]} '
            f'<span class="v">${_mid(c):.2f}</span></li>'
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Garage Radio FM 497</title><style>
  body {{ background:#0a0a0f; color:#eee; font-family:ui-monospace,monospace; padding:1.5rem; max-width:520px; margin:0 auto; }}
  h1 {{ color:#ff6b9d; font-size:1.2rem; }}
  .now {{ background:#161622; border:1px solid #333; padding:1rem; border-radius:8px; margin:1rem 0; }}
  .blink {{ animation: blink 1.2s step-end infinite; color:#7bed9f; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  ul {{ list-style:none; font-size:0.85rem; }}
  li {{ padding:0.35rem 0; border-bottom:1px solid #222; display:flex; gap:0.5rem; }}
  .t {{ color:#666; width:2rem; }}
  .v {{ margin-left:auto; color:#c9a227; }}
  a {{ color:#7bed9f; }}
</style></head><body>
<h1>▶ GARAGE RADIO FM 497</h1>
<div class="now"><span class="blink">● LIVE</span> Now playing: {_esc(picks[0].get("player","")) if picks else "static"}</div>
<ul>{"".join(tracks)}</ul>
<p><a href="/radio?new=1">Shuffle playlist</a> · <a href="/studio">Studio</a></p>
</body></html>"""


def _top_card(cards: list[dict]) -> dict:
    return max(cards, key=_mid)


def _precision_css() -> str:
    return """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0b0b0d; color: #e8e8ea;
    min-height: 100dvh; }
  .silver { color: #a8a8ad; }
  .red { color: #d5001c; }
  a { color: #e8e8ea; text-decoration: none; border-bottom: 1px solid #444; }
  a:hover { border-color: #d5001c; color: #fff; }
"""


def _cockpit(cards: list[dict]) -> str:
    total = sum(_mid(c) for c in cards)
    top = _top_card(cards)
    rookies = sum(1 for c in cards if c.get("rookie"))
    # Ship needle: blend of priced ratio + top-heavy liquidity (0–9000 like a tach)
    priced = sum(1 for c in cards if _mid(c) > 0)
    needle = int(min(9000, max(1200, (priced / max(len(cards), 1)) * 5500 + min(total, 5000) / 5000 * 2800)))
    deg = -130 + (needle / 9000) * 260
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Garage Cockpit</title><style>{_precision_css()}
  .wrap {{ max-width: 420px; margin: 0 auto; padding: 1.5rem 1rem 2rem; }}
  h1 {{ font-size: 0.75rem; letter-spacing: 0.35em; text-transform: uppercase; color: #666; margin-bottom: 0.25rem; }}
  .model {{ font-size: 1.75rem; font-weight: 300; letter-spacing: -0.02em; margin-bottom: 1.5rem; }}
  .model span {{ font-weight: 600; }}
  .tach {{ position: relative; width: 280px; height: 280px; margin: 0 auto 1.5rem; }}
  .tach svg {{ width: 100%; height: 100%; }}
  .readouts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
  .r {{ background: #141416; border: 1px solid #222; border-radius: 8px; padding: 0.85rem 1rem; }}
  .r label {{ display: block; font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: #666; }}
  .r b {{ font-size: 1.35rem; font-weight: 400; font-variant-numeric: tabular-nums; }}
  .action {{ margin-top: 1.25rem; padding: 1rem 1.1rem; border-left: 3px solid #d5001c; background: #121214; }}
  .action b {{ display: block; font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: #d5001c; margin-bottom: 0.35rem; }}
  .foot {{ margin-top: 1.5rem; font-size: 0.8rem; color: #555; text-align: center; }}
</style></head><body>
<div class="wrap">
  <h1>Garage · Cockpit</h1>
  <p class="model">hitme<span>.dev</span> · same garage as the Porsche</p>
  <div class="tach">
    <svg viewBox="0 0 200 200">
      <circle cx="100" cy="100" r="88" fill="none" stroke="#222" stroke-width="8"/>
      <circle cx="100" cy="100" r="88" fill="none" stroke="#333" stroke-width="2" stroke-dasharray="4 8"/>
      <line x1="100" y1="100" x2="100" y2="32" stroke="#d5001c" stroke-width="3" stroke-linecap="round"
        transform="rotate({deg:.1f} 100 100)"/>
      <circle cx="100" cy="100" r="6" fill="#d5001c"/>
      <text x="100" y="118" text-anchor="middle" fill="#888" font-size="11">{needle}</text>
      <text x="100" y="132" text-anchor="middle" fill="#555" font-size="8">SHIP RPM</text>
    </svg>
  </div>
  <div class="readouts">
    <div class="r"><label>Collection mid</label><b>${total:,.0f}</b></div>
    <div class="r"><label>Cards cataloged</label><b>{len(cards)}</b></div>
    <div class="r"><label>Top asset</label><b>${_mid(top):,.0f}</b></div>
    <div class="r"><label>Rookie flags</label><b>{rookies}</b></div>
  </div>
  <div class="action">
    <b>Today's one move</b>
    Send one human the sell sheet or Sarah link. Engine's warm — clutch out.
  </div>
  <p class="foot"><a href="/dossier">Deduction dossier</a> · <a href="/brochure">Top card brochure</a> · <a href="/studio">Studio</a></p>
</div></body></html>"""


def _dossier(cards: list[dict]) -> str:
    total = sum(_mid(c) for c in cards)
    top10 = sorted(cards, key=_mid, reverse=True)[:10]
    top10_sum = sum(_mid(c) for c in top10)
    pct = (top10_sum / total * 100) if total else 0
    by70 = [c for c in cards if str(c.get("year") or "").startswith("197")]
    d70 = sum(_mid(c) for c in by70)
    rows = []
    facts = [
        ("F1", f"{len(cards)} cards · CollX mid on every row", "Inventory is real, not a spreadsheet fantasy."),
        ("F2", f"${total:,.2f} total mid · top card ${_mid(_top_card(cards)):,.2f}", "Liquidity concentrates at the head."),
        ("F3", f"Top 10 = {pct:.0f}% of value ({top10_sum:,.0f})", "Sell singles first or lead with highlights."),
        ("F4", f"1970s decade: {len(by70)} cards · ${d70:,.0f} mid", "Natural eBay lot bundle."),
        ("F5", "Sarah LIVE · sell sheet LIVE · scan :8002 LIVE", "Three doors open. Pick one human."),
    ]
    for fid, fact, ded in facts:
        rows.append(
            f'<tr><td class="id">{fid}</td><td>{_esc(fact)}</td><td class="ded">{_esc(ded)}</td></tr>'
        )
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deduction Dossier</title><style>{_precision_css()}
  .wrap {{ max-width: 720px; margin: 0 auto; padding: 1.5rem 1rem 2.5rem; }}
  h1 {{ font-family: Georgia, serif; font-size: 1.5rem; font-weight: 400; margin-bottom: 0.25rem; }}
  .sub {{ font-size: 0.85rem; color: #666; margin-bottom: 1.5rem; font-style: italic; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
  th {{ text-align: left; font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase; color: #666;
    padding: 0.5rem 0.6rem; border-bottom: 1px solid #333; }}
  td {{ padding: 0.75rem 0.6rem; border-bottom: 1px solid #1a1a1c; vertical-align: top; }}
  .id {{ color: #d5001c; font-variant-numeric: tabular-nums; width: 2.5rem; }}
  .ded {{ color: #a8a8ad; }}
  .verdict {{ margin-top: 1.5rem; padding: 1rem; background: #121214; border: 1px solid #28282a; }}
  .verdict b {{ color: #d5001c; }}
</style></head><body>
<div class="wrap">
  <h1>The Deduction Dossier</h1>
  <p class="sub">Elementary. The data speaks; the fleet does not.</p>
  <table>
    <tr><th>Ref</th><th>Observation</th><th>Therefore</th></tr>
    {"".join(rows)}
  </table>
  <div class="verdict">
    <b>Verdict (confidence 0.91):</b> Ship lane C this week — sell sheet + one 1970s lot.
    Lane A if a human is in hand. Ignore bus until money moves.
  </div>
  <p style="margin-top:1rem;font-size:0.85rem"><a href="/cockpit">Cockpit</a> · <a href="/cards/sell">Sell sheet</a></p>
</div></body></html>"""


def _brochure(cards: list[dict]) -> str:
    c = _top_card(cards)
    img = c.get("image_url") or ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(c.get('player',''))} — Spec Sheet</title><style>{_precision_css()}
  .hero {{ min-height: 100dvh; display: grid; grid-template-rows: 1fr auto; }}
  .img {{ background: #000 center/cover no-repeat; min-height: 55vh;
    background-image: url('{_esc(img)}'); }}
  .spec {{ padding: 2rem 1.5rem 3rem; max-width: 520px; }}
  h1 {{ font-size: 1.1rem; letter-spacing: 0.2em; text-transform: uppercase; color: #666; }}
  h2 {{ font-size: 1.75rem; font-weight: 300; margin: 0.35rem 0 1.25rem; line-height: 1.2; }}
  dl {{ display: grid; grid-template-columns: auto 1fr; gap: 0.35rem 1.5rem; font-size: 0.9rem; }}
  dt {{ color: #666; text-transform: uppercase; font-size: 0.65rem; letter-spacing: 0.08em; }}
  dd {{ margin: 0; font-variant-numeric: tabular-nums; }}
  .price {{ font-size: 2rem; color: #d5001c; margin-top: 1.5rem; font-weight: 300; }}
  .tag {{ margin-top: 2rem; font-size: 0.75rem; color: #555; letter-spacing: 0.15em; text-transform: uppercase; }}
</style></head><body>
<div class="hero">
  <div class="img"></div>
  <div class="spec">
    <h1>Specification · No. 1</h1>
    <h2>{_esc(c.get('player',''))}</h2>
    <dl>
      <dt>Year</dt><dd>{_esc(str(c.get('year','')))}</dd>
      <dt>Set</dt><dd>{_esc(c.get('set',''))}</dd>
      <dt>Card</dt><dd>#{_esc(str(c.get('card_number','')))}</dd>
      <dt>Condition</dt><dd>{_esc(c.get('condition','RAW'))}</dd>
      <dt>CollX mid</dt><dd>${_mid(c):.2f}</dd>
    </dl>
    <p class="price">${_mid(c):.2f}</p>
    <p class="tag">Heritage inventory · brochure grade · {_esc(_now())[:10]}</p>
    <p style="margin-top:1rem;font-size:0.85rem"><a href="/cards/sell">Full collection</a> · <a href="/cockpit">Cockpit</a></p>
  </div>
</div></body></html>"""


def _bundles_csv(cards: list[dict]) -> str:
    from collections import defaultdict

    by_decade: dict[str, list[dict]] = defaultdict(list)
    for c in cards:
        d = str(c.get("year") or "?")[:3] + "0s"
        by_decade[d].append(c)
    lines = ["lot_id,decade,card_count,mid_total,avg_mid,notes"]
    for decade in sorted(by_decade.keys()):
        chunk = by_decade[decade]
        total = sum(_mid(c) for c in chunk)
        avg = total / max(len(chunk), 1)
        lot_id = f"LOT-{decade.replace('s','').replace('?','X')}"
        lines.append(
            f'{lot_id},{decade},{len(chunk)},{total:.2f},{avg:.2f},"Vintage Topps {decade} bundle"'
        )
    return "\n".join(lines) + "\n"


def _nine_one_one(cards: list[dict]) -> str:
    total = sum(_mid(c) for c in cards)
    proofs = [
        "497 cards in CollX JSON — verified count",
        f"${total:,.0f} mid total — priced inventory",
        "Sell sheet with photos — shippable link",
        "Bundle CSV — eBay lot splits ready",
        "Sarah voice — one human test path",
        "Scan :8002 — physical proof loop",
        "Top card brochure — lead with Lou Brock tier",
        "Deduction dossier — evidence not opinions",
        "hello@hitme.dev — public contact face",
    ]
    lis = "".join(f"<li>{_esc(p)}</li>" for p in proofs)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>9 · 1 · 1</title><style>{_precision_css()}
  .wrap {{ max-width: 480px; margin: 0 auto; padding: 2rem 1.25rem; text-align: center; }}
  .nums {{ font-size: 4rem; font-weight: 200; letter-spacing: 0.08em; line-height: 1; margin-bottom: 0.5rem; }}
  .nums span {{ color: #d5001c; }}
  h1 {{ font-size: 0.8rem; letter-spacing: 0.3em; text-transform: uppercase; color: #666; margin-bottom: 2rem; }}
  ol {{ text-align: left; font-size: 0.88rem; color: #a8a8ad; line-height: 1.6; padding-left: 1.2rem; margin-bottom: 2rem; }}
  .one {{ font-size: 1.15rem; color: #fff; padding: 1.25rem; border: 1px solid #333; border-radius: 12px; }}
  .one b {{ color: #d5001c; }}
</style></head><body>
<div class="wrap">
  <p class="nums">9<span>·</span>1<span>·</span>1</p>
  <h1>Daily precision · Porsche not party bus</h1>
  <ol>{lis}</ol>
  <div class="one"><b>1 goal today:</b> one person opens <a href="/cards/sell">/cards/sell</a> or <a href="/sarah">/sarah</a>.</div>
  <p style="margin-top:1.5rem;font-size:0.8rem"><a href="/cockpit">Cockpit</a></p>
</div></body></html>"""


def _encore(cards: list[dict]) -> str:
    total = sum(_mid(c) for c in cards)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Encore Meter</title><style>
  body {{ min-height:100dvh; display:flex; flex-direction:column; align-items:center; justify-content:center;
    background:#0a0a0f; color:#eee; font-family:system-ui,sans-serif; text-align:center; padding:1.5rem; }}
  h1 {{ color:#ff6b9d; }}
  .bar {{ width:min(320px,90vw); height:24px; background:#222; border-radius:999px; overflow:hidden; margin:1rem 0; }}
  .fill {{ height:100%; width:0%; background:linear-gradient(90deg,#c9a227,#ff6b9d); transition:width 0.3s; }}
  button {{ padding:1rem 2rem; font-size:1.1rem; border:none; border-radius:999px; background:#ff6b9d;
    color:#0a0a12; font-weight:700; cursor:pointer; }}
  p {{ color:#888; max-width:22rem; line-height:1.5; }}
</style></head><body>
<h1>Encore Meter</h1>
<p>${total:,.0f} on stage · 497 cards · how loud is the crowd?</p>
<div class="bar"><div class="fill" id="fill"></div></div>
<p id="pct">0%</p>
<button id="btn">I can't get no — click</button>
<p style="margin-top:1.5rem"><a href="/studio" style="color:#7bed9f">Studio</a></p>
<script>
let n=0; const btn=document.getElementById('btn'), fill=document.getElementById('fill'), pct=document.getElementById('pct');
btn.onclick=()=>{{ n=Math.min(100,n+7+Math.floor(Math.random()*8)); fill.style.width=n+'%'; pct.textContent=n+'% satisfaction';
  if(n>=100){{ btn.textContent='ENCORE! Ship one link today.'; btn.style.background='#7bed9f'; }} }};
</script></body></html>"""


def _aws_lore(player: str, val: float) -> str:
    try:
        r = subprocess.run(
            [
                sys.executable,
                str(STAN / "aws_lane.py"),
                "talk",
                f"Two sentences vintage baseball lore about {player} card worth ${val:.0f}. Poetic. No fleet.",
            ],
            capture_output=True,
            text=True,
            timeout=45,
        )
        for ln in (r.stdout or "").splitlines():
            if ln.strip() and not ln.startswith("→"):
                return ln.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ""


def cmd_sell(cards: list[dict]) -> Path:
    return _write("sell_sheet.html", _sell_sheet(cards))


def cmd_story(cards: list[dict], lore: str = "", aws: bool = False) -> tuple[Path, dict]:
    if aws and not lore:
        c0 = random.choice(cards)
        lore = _aws_lore(c0.get("player") or "a player", _mid(c0))
    slug, meta = _story_card(cards, lore=lore)
    p = _write(f"{slug}.html", meta["html"])
    (OUT / "story_latest.json").write_text(
        json.dumps({"slug": slug, "player": meta["card"].get("player"), "path": str(p)}, indent=2),
        encoding="utf-8",
    )
    return p, meta


def cmd_sarah() -> Path:
    _write(
        "sarah_sms.txt",
        "Try Sarah — snap a post-it, she reads it back: http://100.115.92.26:8766/sarah\n",
    )
    return _write("sarah_pitch.html", _sarah_pitch())


def cmd_hitme() -> Path:
    return _write("hitme_landing.html", _hitme_landing())


def cmd_bundles(cards: list[dict]) -> Path:
    return _write("bundles.html", _bundles(cards))


def cmd_studio() -> Path:
    return _write("studio.html", _studio())


def cmd_setlist(cards: list[dict]) -> Path:
    return _write("setlist.html", _setlist(cards))


def cmd_mick(cards: list[dict]) -> Path:
    return _write("mick_index.html", _mick_index(cards))


def cmd_fortune() -> Path:
    return _write("fortune.html", _fortune())


def cmd_scan() -> Path:
    return _write("scan_one_pager.html", _scan_one_pager())


def cmd_radio(cards: list[dict]) -> Path:
    return _write("garage_radio.html", _garage_radio(cards))


def cmd_encore(cards: list[dict]) -> Path:
    return _write("encore.html", _encore(cards))


def cmd_cockpit(cards: list[dict]) -> Path:
    return _write("cockpit.html", _cockpit(cards))


def cmd_dossier(cards: list[dict]) -> Path:
    return _write("dossier.html", _dossier(cards))


def cmd_brochure(cards: list[dict]) -> Path:
    return _write("brochure.html", _brochure(cards))


def cmd_export(cards: list[dict]) -> Path:
    return _write("bundles_ebay.csv", _bundles_csv(cards))


def cmd_nine(cards: list[dict]) -> Path:
    return _write("nine_one_one.html", _nine_one_one(cards))


def cmd_craft(cards: list[dict]) -> list[tuple[str, Path]]:
    out = []
    for label, fn in (
        ("cockpit", cmd_cockpit),
        ("dossier", cmd_dossier),
        ("brochure", cmd_brochure),
        ("bundles_ebay", cmd_export),
        ("nine_one_one", cmd_nine),
    ):
        p = fn(cards)
        out.append((label, p))
    return out


COMMANDS = {
    "sell": lambda cards: [("sell_sheet", cmd_sell(cards))],
    "story": lambda cards: [("story_card", cmd_story(cards, aws=True)[0])],
    "sarah": lambda cards: [("sarah_pitch", cmd_sarah())],
    "hitme": lambda cards: [("hitme_landing", cmd_hitme())],
    "bundles": lambda cards: [("bundles", cmd_bundles(cards))],
    "studio": lambda cards: [("studio", cmd_studio())],
    "setlist": lambda cards: [("setlist", cmd_setlist(cards))],
    "mick": lambda cards: [("mick_index", cmd_mick(cards))],
    "fortune": lambda cards: [("fortune", cmd_fortune())],
    "scan": lambda cards: [("scan_one_pager", cmd_scan())],
    "radio": lambda cards: [("garage_radio", cmd_radio(cards))],
    "encore": lambda cards: [("encore", cmd_encore(cards))],
    "cockpit": lambda cards: [("cockpit", cmd_cockpit(cards))],
    "dossier": lambda cards: [("dossier", cmd_dossier(cards))],
    "brochure": lambda cards: [("brochure", cmd_brochure(cards))],
    "export": lambda cards: [("bundles_ebay", cmd_export(cards))],
    "nine": lambda cards: [("nine_one_one", cmd_nine(cards))],
    "craft": lambda cards: cmd_craft(cards),
}


def main() -> None:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "invent").lower()
    lore = ""
    if "--lore" in sys.argv:
        i = sys.argv.index("--lore")
        if i + 1 < len(sys.argv):
            lore = sys.argv[i + 1]

    cards = _load_cards()
    entries: list[tuple[str, Path]] = []

    if cmd == "all" or cmd == "invent":
        for name in (
            "hitme", "sarah", "sell", "bundles", "studio", "setlist", "mick", "fortune",
            "scan", "radio", "encore", "craft", "story",
        ):
            for label, path in COMMANDS[name](cards):
                entries.append((label, path))
                print(f"{name} → {path}")
    elif cmd == "story":
        p, meta = cmd_story(cards, lore=lore, aws=not lore)
        entries.append(("story_card", p))
        print(f"story → {p} ({meta['card'].get('player')})")
    elif cmd in COMMANDS:
        for label, path in COMMANDS[cmd](cards):
            entries.append((label, path))
            print(f"{cmd} → {path}")
    else:
        raise SystemExit(f"unknown: {cmd} · use {' | '.join(COMMANDS)} | invent | all")

    if entries:
        _manifest(entries)


if __name__ == "__main__":
    main()
