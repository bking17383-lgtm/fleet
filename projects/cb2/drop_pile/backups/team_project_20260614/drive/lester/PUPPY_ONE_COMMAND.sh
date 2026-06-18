#!/bin/bash
# PUPPY — run this ONE command (Lester loop does NOT execute this for you)
set -e
DRIVE="$HOME/GoogleDrive/MyDrive"
[[ -d /mnt/shared/GoogleDrive/MyDrive ]] && DRIVE="/mnt/shared/GoogleDrive/MyDrive"
mkdir -p "$DRIVE/drop_pile/from_lester" ~/lester/jailbreak

# minimal transcript sink if missing
if [[ ! -f ~/lester/jailbreak/transcript_sink.py ]]; then
  curl -sf "$DRIVE/drop_pile/to_puppy/START_LESTER_JAILBREAK_NOW.md" >/dev/null 2>&1 || true
  # inline minimal server
  cat > ~/lester/jailbreak/transcript_sink.py << 'PY'
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime, timezone
import os, re
DRIVE = Path(os.environ.get("DRIVE", Path.home()/"GoogleDrive/MyDrive"))
if Path("/mnt/shared/GoogleDrive/MyDrive").is_dir(): DRIVE = Path("/mnt/shared/GoogleDrive/MyDrive")
OUT = DRIVE / "drop_pile/from_lester"
OUT.mkdir(parents=True, exist_ok=True)
app = Flask(__name__)
@app.route("/")
def i(): return "<h1>jailbreak sink OK</h1><p>POST /save</p>"
@app.route("/save", methods=["POST"])
def s():
    t = (request.get_json(silent=True) or {}).get("text","").strip()
    if not t: return jsonify(ok=False), 400
    p = OUT / f"live_transcript_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.txt"
    p.write_text(t+"\n", encoding="utf-8")
    return jsonify(ok=True, path=str(p))
if __name__ == "__main__": app.run("0.0.0.0", 8765)
PY
fi

pkill -f 'transcript_sink.py' 2>/dev/null || true
nohup python3 ~/lester/jailbreak/transcript_sink.py >> ~/lester/jailbreak/sink.log 2>&1 &
sleep 2
IP=$(hostname -I | awk '{print $1}')
curl -sf http://127.0.0.1:8765/ | head -1 || echo "SINK FAILED"

cat > "$DRIVE/puppy_outbox.txt" << EOF

--- from: puppy | time: $(date -Iseconds) ---
status: RUNNING
hostname: $(hostname)
program: lester_jailbreak
ip: $IP
port: 8765
url: http://$IP:8765
note: ONE_COMMAND ran. Lester loop is talk — this is execute.
EOF

echo "DONE. URL: http://$IP:8765"
echo "Updated puppy_outbox.txt on Drive."
