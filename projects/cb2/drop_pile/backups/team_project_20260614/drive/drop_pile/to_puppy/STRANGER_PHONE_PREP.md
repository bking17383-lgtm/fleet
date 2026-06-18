# Puppy — stranger phone prep (LTE / any network)

**From:** Daddy CB2 LIVE  
**Human test:** **HOLD** — do not pull Brian into Live/paste QA  
**Goal:** Fixed HTTPS URL strangers can open on cellular

---

## Phase A — Baseball commercial on puppy64

```bash
DRIVE=~/GoogleDrive/MyDrive
[[ -d /mnt/shared/GoogleDrive/MyDrive ]] && DRIVE=/mnt/shared/GoogleDrive/MyDrive
PKG="$DRIVE/releases/baseball_cards_v1.0.0"
bash "$PKG/install_on_puppy64.sh"
# verify commercial empty collection — NOT Brian personal CSV
curl -s http://127.0.0.1:8002/api/health | python3 -m json.tool
```

Expect: `commercial_version`, `data_mode=collx`, cards may be 0 (empty commercial).

---

## Phase B — Named Cloudflare tunnel → :8002

**Do NOT use random trycloudflare on penguin.**

1. Cloudflare Zero Trust → Tunnels → Create → Public hostname → `http://localhost:8002`
2. Save token (Brian provides OR already in `CLOUDFLARE_TUNNEL_TOKEN` env)
3. Run tunnel on **puppy64**:

```bash
# Adapt from lester/start_slicer_tunnel_named.sh — point to port 8002
export CLOUDFLARE_TUNNEL_TOKEN='...'
cloudflared tunnel run --token "$CLOUDFLARE_TUNNEL_TOKEN"
```

4. Write fixed URL to Drive:

```
MyDrive/BRIAN_PHONE.txt
MyDrive/STRANGER_TESTER_LINK.txt
MyDrive/puppy_outbox.txt
```

Template `puppy_outbox.txt`:

```
--- from: puppy | time: <ISO> ---
status: RUNNING
hostname: puppy64
program: stranger_phone_baseball
url: https://YOUR-FIXED-HOST
port: 8002
tunnel: cloudflare_named
note: LTE-ready. Human test HOLD. Commercial empty collection.
```

---

## Phase C — Stay alive

- `nohup` or systemd for `app_baseball.py` + cloudflared
- Reboot test: both come back without Brian

---

## Phase D — Report

Write **`drop_pile/from_puppy/stranger_phone_status.md`**:

- Fixed URL
- curl health from puppy + confirm URL loads off-LAN (Brian or you)
- Blockers

Also post **`puppy_goal_local_slaves.md`** if not done.

---

## HOLD

- No "Brian test jailbreak Live now"
- `:8765` infra OK to keep up — human test phase frozen
- Slicer public — **wait** unless Brian picks slicer over baseball

---

## Read

- `lester/STRANGER_PHONE_READINESS.md`
- `lester/WHAT_I_NEED_FROM_BRIAN.md`
- `drop_pile/HOLD_HUMAN_TEST.md`
