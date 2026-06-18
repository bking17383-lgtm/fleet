# PUPPY — READ THIS NOW (2026-06-13)

**Brian is stuck on CB2 setup. Do NOT wait for Chromebooks.**  
**Daddy T3 (CB1) says: execute on puppy64 today.**

---

## One paste for Cursor on puppy64

```
Read MyDrive/PUPPY_READ_THIS_NOW.md and execute it.
Priority #1 lester jailbreak transcript sink port 8765.
Slicer ON HOLD. CB2 not ready — proceed without it.
Post puppy_outbox.txt when done.
```

---

## Priority order (2026-06-13)

| # | Job | File | Status |
|---|-----|------|--------|
| **1** | **Lester jailbreak** | `drop_pile/to_puppy/START_LESTER_JAILBREAK_NOW.md` | **DO NOW** |
| — | Slicer | `MAKE_IT_SO.md` | **ON HOLD — skip** |
| — | Baseball phone | `puppy_qa.md` | after jailbreak Phase 1 or parallel |

Queue job: `98ecabbe-e` · intent `lester_jailbreak`

---

## Step 1 — Transcript sink (15 min)

Full script in **`START_LESTER_JAILBREAK_NOW.md`**.

Short version:

```bash
DRIVE=~/GoogleDrive/MyDrive
[[ -d /mnt/shared/GoogleDrive/MyDrive ]] && DRIVE=/mnt/shared/GoogleDrive/MyDrive
mkdir -p "$DRIVE/drop_pile/from_lester" ~/lester/jailbreak

# Copy transcript_sink.py from START_LESTER_JAILBREAK_NOW.md (or read that file)
# Run:
nohup python3 ~/lester/jailbreak/transcript_sink.py >> ~/lester/jailbreak/sink.log 2>&1 &

IP=$(hostname -I | awk '{print $1}')
curl -s http://127.0.0.1:8765/ | head -3
echo "LAN: http://$IP:8765"
```

---

## Step 2 — Post outbox (required)

Overwrite **`MyDrive/puppy_outbox.txt`**:

```
status: RUNNING
program: lester_jailbreak
hostname: puppy64
ip: <192.168.x.x>
port: 8765
url: http://<192.168.x.x>:8765
updated: 2026-06-13
note: Transcript sink live. CB2 setup slow — puppy did not wait. Slicer HOLD.
```

---

## Step 3 — Mark queue

```bash
python3 ~/.stan/brian_os.py process
```

If `lester_jailbreak` has no handler, still post outbox — job counts as done when sink works.

---

## Step 4 — Night watch (optional, keep running)

```bash
nohup python3 ~/.stan/brian_os.py watch 20 >> ~/brian_os_watch.log 2>&1 &
```

---

## Do NOT

- Wait for CB2 or new Chromebook
- Run slicer (`fcf127cd-f`) until Brian unblocks
- Ask CB1 penguin to SSH here

---

## Questions?

Read: `COMMON_INSTRUCTIONS.md` · `WAKE_PUPPY_JAILBREAK.txt`

Report problems → append to `Hello from Puppy.txt` on Drive.
