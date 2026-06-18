#!/bin/bash
# PUPPY JAILBREAK — run ON puppy64 keyboard only
# RADIO stays :8765 · transcript sink :8766 · baseball :8002 with live/capture
set -u
for DRIVE in /mnt/shared/GoogleDrive/MyDrive "$HOME/GoogleDrive/MyDrive" /mnt/home/google_drive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "Drive not mounted"; exit 1; }

HOST="$(hostname 2>/dev/null || echo unknown)"
if [[ "$HOST" == "penguin" ]]; then
  echo "REFUSE: run on puppy64, not Chromebook ($HOST)"
  exit 2
fi

mkdir -p ~/lester/jailbreak "$DRIVE/drop_pile/from_lester"
python3 -c "import flask" 2>/dev/null || python3 -m pip install --user flask

# Transcript sink on 8766 (8765 = mesh RADIO)
cat > ~/lester/jailbreak/transcript_sink.py << 'PY'
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
import os, re

DRIVE = Path(os.environ.get("DRIVE", Path.home() / "GoogleDrive/MyDrive"))
for p in ("/mnt/shared/GoogleDrive/MyDrive", "/mnt/home/google_drive/MyDrive", Path.home() / "GoogleDrive/MyDrive"):
    if Path(p).is_dir():
        DRIVE = Path(p)
        break
OUT = DRIVE / "drop_pile/from_lester"
OUT.mkdir(parents=True, exist_ok=True)
app = Flask(__name__)

PAGE = """<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:640px;margin:1rem">
<h2>Jailbreak sink :8766</h2><p>Paste Gemini Live transcript</p>
<textarea id=t rows=12 style="width:100%;font-size:16px"></textarea><br>
<button onclick="fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({text:document.getElementById('t').value})}).then(r=>r.json()).then(j=>{alert(JSON.stringify(j));if(j.ok)document.getElementById('t').value=''})">Save</button></body></html>"""

@app.route("/")
def home():
    return PAGE

@app.route("/save", methods=["POST"])
def save():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify(ok=False, error="empty"), 400
    tag = re.sub(r"[^\w\-]", "_", (data.get("tag") or "live")[:40])
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUT / f"live_transcript_{tag}_{ts}.txt"
    path.write_text(f"# jailbreak sink :8766\n# saved: {ts}\n\n{text}\n", encoding="utf-8")
    return jsonify(ok=True, path=str(path), bytes=path.stat().st_size)

if __name__ == "__main__":
    app.run("0.0.0.0", 8766, debug=False)
PY

pkill -f 'transcript_sink.py' 2>/dev/null || true
sleep 1
nohup python3 ~/lester/jailbreak/transcript_sink.py >> ~/lester/jailbreak/sink.log 2>&1 &
sleep 2

# Baseball app with live/capture (current Drive copy)
if [[ -f "$DRIVE/lester/START_BASEBALL_ON_PUPPY.sh" ]]; then
  bash "$DRIVE/lester/START_BASEBALL_ON_PUPPY.sh" || true
fi

IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.' | head -1)
IP=${IP:-$(hostname -I | awk '{print $1}')}
NOW=$(date -Iseconds 2>/dev/null || date)
SINK=$(curl -sf http://127.0.0.1:8766/ | head -c 20 || echo FAIL)
LIVE=$(curl -sf -o /dev/null -w '%{http_code}' http://127.0.0.1:8002/live/capture 2>/dev/null || echo 000)
GEM_URL=$(grep -E '^http' "$DRIVE/lester/gemini_live_url.txt" 2>/dev/null | head -1)

BUS="$DRIVE/fleet/bus"
mkdir -p "$BUS"
cat > "$BUS/puppy_outbox.txt" << EOF
--- from: puppy | jailbreak | time: ${NOW} ---
PUPPY CHECKIN — puppy64 — ${IP} — ${NOW}
hostname: puppy64
status: RUNNING
program: JAILBREAK
ports:
  mesh_radio: 8765
  jailbreak_sink: 8766 (${SINK})
  baseball: 8002 (live/capture HTTP ${LIVE})
urls:
  sink: http://${IP}:8766
  cards: http://${IP}:8002
  live_capture: http://${IP}:8002/live/capture
  gem_gate: ${GEM_URL:-see lester/gemini_live_url.txt}
next: one card test · Live → sink → grade
EOF

echo "JAILBREAK puppy OK"
echo "  sink  http://${IP}:8766"
echo "  cards http://${IP}:8002/live/capture"
echo "  gem   ${GEM_URL:-(Gem gate on CB1/CB2 LAN)}"
