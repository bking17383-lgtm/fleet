# START NOW — Lester jailbreak (puppy64)

**From:** Daddy T3 (CB1)  
**Priority:** #1 — start immediately  
**Slicer:** ON HOLD — do not run MAKE_IT_SO.md  
**Baseball phone:** after jailbreak Phase 1 spike (or parallel if quick)

---

## Puppy boot (paste in Cursor on puppy64)

```
Read MyDrive/COMMON_INSTRUCTIONS.md and MyDrive/drop_pile/to_puppy/START_LESTER_JAILBREAK_NOW.md.
Execute Phase 1–2 now. Post status to puppy_outbox.txt. Slicer on hold.
```

---

## Phase 1 — Transcript sink (start without Free Lester export)

Create on puppy64:

```bash
DRIVE=~/GoogleDrive/MyDrive
[[ -d /mnt/shared/GoogleDrive/MyDrive ]] && DRIVE=/mnt/shared/GoogleDrive/MyDrive
mkdir -p "$DRIVE/drop_pile/from_lester" "$DRIVE/drop_pile/from_tester"
mkdir -p ~/lester/jailbreak
```

**Minimal paste server** — save Live transcripts to Drive:

```bash
cat > ~/lester/jailbreak/transcript_sink.py << 'PY'
#!/usr/bin/env python3
"""Paste Gemini Live transcript → Drive drop_pile/from_lester/"""
import os, re
from datetime import datetime, timezone
from pathlib import Path

DRIVE = Path(os.environ.get("DRIVE", Path.home() / "GoogleDrive/MyDrive"))
if Path("/mnt/shared/GoogleDrive/MyDrive").is_dir():
    DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
OUT = DRIVE / "drop_pile/from_lester"
OUT.mkdir(parents=True, exist_ok=True)

from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/")
def home():
    return """<html><body style="font-family:sans-serif;max-width:640px;margin:1rem">
<h2>Lester jailbreak — transcript sink</h2>
<p>Paste Gemini Live transcript. Saves to Drive <code>drop_pile/from_lester/</code></p>
<textarea id="t" rows="12" style="width:100%"></textarea><br>
<input id="tag" placeholder="tag (optional)" style="width:100%;margin:0.5rem 0">
<button onclick="go()">Save to Drive</button>
<pre id="out"></pre>
<script>
async function go(){
  const r=await fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:document.getElementById('t').value,tag:document.getElementById('tag').value})});
  document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2);
}
</script></body></html>"""

@app.route("/save", methods=["POST"])
def save():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty"}), 400
    tag = re.sub(r"[^\w\-]", "_", (data.get("tag") or "live")[:40])
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUT / f"live_transcript_{tag}_{ts}.txt"
    path.write_text(f"# Lester jailbreak transcript\n# saved: {ts}\n\n{text}\n", encoding="utf-8")
    return jsonify({"ok": True, "path": str(path), "bytes": path.stat().st_size})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
PY
chmod +x ~/lester/jailbreak/transcript_sink.py
```

Run + post LAN URL:

```bash
nohup python3 ~/lester/jailbreak/transcript_sink.py >> ~/lester/jailbreak/sink.log 2>&1 &
hostname -I | awk '{print $1}'
curl -s http://127.0.0.1:8765/ | head -3
```

Write **`puppy_outbox.txt`**:

```
status: RUNNING
program: lester_jailbreak
hostname: puppy64
port: 8765
url: http://<LAN_IP>:8765
note: Transcript sink live. Paste Gemini Live text here. Phase 2 after free_lester export.
```

---

## Phase 2 — Wire baseball Live bridge (when Drive sync has files)

```bash
DRIVE=~/GoogleDrive/MyDrive
[[ -d /mnt/shared/GoogleDrive/MyDrive ]] && DRIVE=/mnt/shared/GoogleDrive/MyDrive
# sync baseball app if needed
SRC="$DRIVE/lester/baseball_cards"
DST="$HOME/Applications/cursor/baseball_cards"
mkdir -p "$DST"
cp -f "$SRC"/*.py "$SRC"/*.html "$DST/" 2>/dev/null || true

# When free_lester_instructions.md has real body (not AWAITING_EXPORT):
# create scan_cheats.json global_prompt from that file

echo "http://$(hostname -I | awk '{print $1}'):8002/live/capture" > "$DRIVE/lester/gemini_live_url.txt"
```

Start baseball only if Brian wants phone test same session:

```bash
bash "$DRIVE/lester/START_BASEBALL_ON_PUPPY.sh"
```

---

## Phase 3 — Night watch (keep running)

```bash
nohup python3 ~/.stan/brian_os.py watch 20 >> ~/brian_os_watch.log 2>&1 &
```

Process queue **except slicer**:

```bash
python3 ~/.stan/brian_os.py process
# skip fcf127cd-f slicer_zero_host until Brian unblocks
```

---

## Done when (report in puppy_outbox)

- [ ] `:8765` transcript sink reachable on LAN
- [ ] Test save creates `drop_pile/from_lester/live_transcript_*.txt`
- [ ] `gemini_live_url.txt` posted when baseball up
- [ ] `brian_os watch` running

---

## Read on Drive

- `drop_pile/to_puppy/START_LESTER_JAILBREAK.md` (full spec)
- `lester/free_lester_instructions.md` (stub until Lester exports on CB2)
