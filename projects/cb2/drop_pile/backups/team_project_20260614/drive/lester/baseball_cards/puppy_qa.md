# Puppy QA — puppy agent on puppy64

Run this on **puppy64** (not penguin). Workspace: `~/Applications/cursor/baseball_cards`

**Big Daddy** (penguin Cursor) shipped CollX + commercial package. **puppy** job: serve phone on home Wi-Fi.

## 1. Sync latest app from Drive

```bash
DRIVE="${HOME}/GoogleDrive/MyDrive"
[[ -d "/mnt/shared/GoogleDrive/MyDrive" ]] && DRIVE="/mnt/shared/GoogleDrive/MyDrive"
SRC="$DRIVE/lester/baseball_cards"
DST="$HOME/Applications/cursor/baseball_cards"
mkdir -p "$DST/data/collx" "$DST/uploads"
cp -f "$SRC"/*.py "$SRC"/*.html "$SRC"/*.sh "$SRC"/AGENTS.md "$DST/" 2>/dev/null || true
cp -rf "$SRC/data/"* "$DST/data/" 2>/dev/null || true
cp -f "$SRC/collx_export.csv" "$DST/" 2>/dev/null || true
```

## 2. Start baseball server

```bash
bash "$DRIVE/lester/START_BASEBALL_ON_PUPPY.sh"
```

Must report `status: RUNNING` and a **192.168.x.x** LAN URL (not 100.x Tailscale).

## 3. Acceptance checks

```bash
curl -s http://127.0.0.1:8002/api/health | python3 -m json.tool
curl -s http://127.0.0.1:8002/api/cards | python3 -c "
import sys, json
d=json.load(sys.stdin)
print('cards:', d.get('count'), 'total_mid:', d.get('total_mid'))
assert d.get('count',0) >= 490, 'expected ~497 cards'
"
```

Expect:
- `data_mode`: `collx`
- `count`: **497** (or close)
- `total_mid`: **~2091.89**

## 4. Post status to Drive

Write `MyDrive/puppy_outbox.txt`:

```
status: RUNNING
ip: <your 192.168.x.x>
port: 8002
url: http://<ip>:8002
hostname: puppy64
cards: 497
total: 2091.89
```

Also update `Hello from Puppy.txt` (START script does this automatically).

## 5. Process queue

```bash
python3 ~/.stan/brian_os.py process
```

Marks `puppy_qa` job done in `brian_queue.json`.

## 6. Phone test

On phone (same home Wi-Fi): open the LAN URL from step 2.

- Bottom tabs: Add / List / Stats / CollX
- Stats shows **497 cards** and **~$2,092**
- No mismatch banner

## Done when

- [ ] Health 200 with `data_mode=collx`
- [ ] 497 cards / $2091.89 on API
- [ ] `puppy_outbox.txt` has 192.168 LAN URL
- [ ] Phone loads app on Wi-Fi

Penguin tunnel is fallback only — puppy LAN is preferred.
