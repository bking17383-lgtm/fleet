# Puppy instruction backup — 2026-06-14

**Why:** Brian wiping puppy64. Restore from here.

**Path:** `drop_pile/backups/puppy_wipe_20260614/`

---

## After wipe — paste in new Puppy Cursor

```
PUPPY
```

One word. Puppy reads this file + runs `to_puppy/PUPPY_NOW.md`.

---

## What's in this folder

| Folder | Contents |
|--------|----------|
| `to_puppy/` | All execute orders (19 files) incl. **PUPPY_NOW.md** |
| `lester/` | slave config, ONE_COMMAND, setup scripts |
| `root/` | PUPPY_*.txt, outbox snapshot, boot py |
| `baseball/` | install_on_puppy.sh, puppy_qa.md |
| `blueprints/` | PUPPY_README, phone-puppy-serve |
| `from_lester/` | heartbeat snapshot, status reply |
| `queue_snapshot/` | 11 pending puppy jobs from brian_queue.json |

**45 files** copied 2026-06-14 by CAPTN before wipe.

---

## Restore priority (order)

1. `lester/lester6_puppy_slave.md` → keep on Drive (already there)
2. `to_puppy/PUPPY_STANDING_LOOP.md` — boot loop
3. `to_puppy/PUPPY_NOW.md` — one sprint after wipe
4. `lester/PUPPY_ONE_COMMAND.sh` — jailbreak sink :8765
5. `lester/START_BASEBALL_ON_PUPPY.sh` — baseball :8002

Keys: `lester/lester_keys.md` (not in backup — still on Drive)

---

## Do not delete this backup until puppy posts fresh outbox.
