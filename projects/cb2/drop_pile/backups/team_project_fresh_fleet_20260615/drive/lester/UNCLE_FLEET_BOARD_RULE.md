# Uncle rule — show Brian which devices are alive (CB1)

**Updated:** 2026-06-14  
**Machine:** CB1 · Uncle Cursor

Daddy had a manual board rule (`DADDY_FLEET_BOARD_RULE.md`).  
Uncle has the **same output file** plus an auto-refresh script on this box.

---

## One command (this computer)

```bash
bash ~/.stan/fleet_desk.sh
```

Or:

```bash
python3 ~/.stan/fleet_board.py
```

---

## What it reads (Drive)

- `drop_pile/from_lester/*_heartbeat.md`
- `drop_pile/from_lester/lester6_to_*.md`
- `fleet/bus/puppy_outbox.txt`
- `fleet/FLEET_BROADCAST.txt`

---

## What it writes

| File | Purpose |
|------|---------|
| `fleet/FLEET_AVAILABLE.txt` | Same board Brian reads with **DESK** |
| `drop_pile/from_cursor/cb1_devices_board.md` | CB1-friendly view |
| `~/.stan/handoff/fleet_snapshot.json` | Terminal status line (under ctx) |

---

## Brian words

- **DESK** → open `fleet/FLEET_AVAILABLE.txt`
- **UNCLE** → standing loop + auto refresh board

Terminal status line refreshes the board every ~5 minutes while Cursor is open.
