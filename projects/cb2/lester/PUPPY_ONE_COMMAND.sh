#!/bin/bash
# PUPPY — run this ONE command (Lester loop does NOT execute this for you)
set -u
for DRIVE in /mnt/home/google_drive/MyDrive "$HOME/GoogleDrive/MyDrive" /mnt/shared/GoogleDrive/MyDrive; do
  [[ -d "$DRIVE/fleet" ]] && break
done
[[ -d "$DRIVE/fleet" ]] || { echo "Drive not mounted"; exit 1; }
bash "$DRIVE/lester/PUPPY_STATUSLINE_FIX.sh" 2>/dev/null || true
mkdir -p "$DRIVE/drop_pile/from_lester" ~/lester/jailbreak

python3 -c "import flask" 2>/dev/null || {
  echo "Installing flask…"
  python3 -m pip install --user flask 2>/dev/null || pip3 install --user flask 2>/dev/null || {
    echo "FAIL: flask missing — run: python3 -m pip install --user flask"
    exit 1
  }
}

# Always rewrite sink (old broken copy was blocking reload)
cat > ~/lester/jailbreak/transcript_sink.py << 'PY'
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
import os

DRIVE = Path(os.environ.get("DRIVE", Path.home() / "GoogleDrive/MyDrive"))
for p in ("/mnt/home/google_drive/MyDrive", "/mnt/shared/GoogleDrive/MyDrive", Path.home() / "GoogleDrive/MyDrive"):
    if Path(p).is_dir():
        DRIVE = Path(p)
        break
OUT = DRIVE / "drop_pile/from_lester"
OUT.mkdir(parents=True, exist_ok=True)
app = Flask(__name__)

@app.route("/")
def i():
    return "<h1>jailbreak sink OK</h1><p>POST /save</p>"

@app.route("/save", methods=["POST"])
def s():
    t = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not t:
        return jsonify(ok=False), 400
    p = OUT / f"live_transcript_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.txt"
    p.write_text(t + "\n", encoding="utf-8")
    return jsonify(ok=True, path=str(p))

if __name__ == "__main__":
    app.run("0.0.0.0", 8765)
PY

pkill -f 'transcript_sink.py' 2>/dev/null || true
sleep 1
nohup python3 ~/lester/jailbreak/transcript_sink.py >> ~/lester/jailbreak/sink.log 2>&1 &
sleep 2

IP=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^192\.168\.' | head -1)
IP=${IP:-$(hostname -I | awk '{print $1}')}
SINK_OK=$(curl -sf http://127.0.0.1:8765/ | head -1 || echo "SINK FAILED")
NOW=$(date -Iseconds 2>/dev/null || date)
BUS="${DRIVE}/fleet/bus"
mkdir -p "$BUS" "$DRIVE/drop_pile/from_puppy"

cat > "$BUS/puppy_outbox.txt" << EOF
--- from: puppy | time: ${NOW} ---
PUPPY CHECKIN — puppy64 — ${IP} — ${NOW}
hostname: puppy64
status: RUNNING
program: lester_jailbreak
ip: ${IP}
port: 8765
url: http://${IP}:8765
sink: ${SINK_OK}
note: ONE_COMMAND ran · fleet/bus path (not root mirror)
EOF

cat > "$BUS/puppy_needs.txt" << EOF
puppy_needs — ${NOW}
mirror=OK
drive_path=${DRIVE}/fleet/bus/
:8765=${SINK_OK}
uncle_on_lan=UNKNOWN
next=refresh puppy_heartbeat
EOF

echo "DONE. URL: http://${IP}:8765"
echo "Updated fleet/bus/puppy_outbox.txt on Drive."
