# WAKE NOW — Puppy (puppy64)

**From:** Daddy CB2 · **Time:** 2026-06-14 · **Priority:** EXECUTE (not talk)

Brian opened you because CB2 cannot run puppy work. Daddy delegates. You execute locally.

---

## Paste this in Cursor on puppy64 (one message)

```
You are Puppy on puppy64. Read MyDrive/drop_pile/to_puppy/WAKE_NOW_ONE_PASTE.md and mac_inbox.txt (bottom).

RUN NOW in terminal:
  bash ~/GoogleDrive/MyDrive/lester/PUPPY_ONE_COMMAND.sh
  bash ~/GoogleDrive/MyDrive/lester/START_BASEBALL_ON_PUPPY.sh

Then:
  python3 ~/.stan/brian_os.py process
  python3 ~/.stan/brian_os.py watch 20 &

Post puppy_outbox.txt (hostname MUST be puppy64, not penguin).
Write drop_pile/from_puppy/puppy_fleet_status.md with :8765 and :8002 URLs.
Do NOT wait for Brian. Report blockers in one line.
```

---

## Success = Drive shows today

| Check | Expected |
|-------|----------|
| `puppy_outbox.txt` | `hostname: puppy64`, `:8765` sink, `:8002` baseball |
| `Hello from Puppy.txt` | LAN URL `http://192.168.x.x:8002` |
| `BRIAN_PHONE.txt` | Updated with **puppy LAN IP** (not trycloudflare) |
| `brian_queue.json` | Jobs `98ecabbe-e`, `puppy-qa-wake` marked done |

---

## If blocked

Write one line to `drop_pile/from_puppy/puppy_fleet_status.md`:

```
BLOCKED: <reason> — need Brian: <yes/no>
```

Common fixes:
- Drive not synced → wait 2 min, retry
- `python3-flask` missing → `sudo apt install python3-flask`
- Wrong machine → must NOT be hostname `penguin`

---

## HOLD

- `fcf127cd-f` slicer — do not run
- Human tester loops — Brian not QA today
