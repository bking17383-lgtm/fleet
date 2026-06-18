# Common Instructions — all agents read first

**Updated:** 2026-06-13  
**Authority:** Terminal 3 (Daddy) on Chromebook penguin

Plain text on Drive only. No `.gdoc`-only handoffs.

---

## Who is who

| Name | Where | Role |
|------|-------|------|
| **Daddy (Terminal 3)** | Chromebook — Cursor tab 3 / penguin | **Captain:** analyze, delegate, queue, report. Does **not** execute puppy jobs from penguin. |
| **Terminal 2** | Chromebook — Cursor game tab | Play Camel, decide after Daddy analysis, say **sounds good** |
| **Lester/Chrome** | Chromebook — voice/Gemini | Brainstorm with Brian; **must sync** to Drive (no chat-only design) |
| **Cursor/puppy** | **puppy64** | **Execute:** build, serve :8002, LAN phone, heavy tests |
| **Lester/puppy** | puppy64 (optional) | Same sync rules as Lester/Chrome; tools if `~/lester/app.py` running |

Brian does **not** relay messages between Cursors. Drive + queue are the bus.

---

## Session start — every agent (this order)

1. **`MyDrive/COMMON_INSTRUCTIONS.md`** — this file
2. **`MyDrive/brian_queue.json`** — jobs for your machine (`assign_to`)
3. **`MyDrive/BRIAN_STATUS.txt`** — plain English status for Brian
4. **`~/.stan/handoff/session_note.md`** — active project + blueprint ids
5. **`MyDrive/drop_pile/to_<you>/`** — work orders from Daddy

---

## Puppy (puppy64) — start here

You report to **Daddy (Terminal 3)**, not penguin execute tabs.

1. Read this file + `lester/PUPPY_CURSOR_START_HERE.md`
2. **`brian_queue.json`** — run pending jobs where `assign_to` is `puppy`
3. **`drop_pile/to_puppy/`** — specs (e.g. `MAKE_IT_SO.md`, `puppy_qa.md` path)
4. **`WAKE_*.txt`** on Drive root — Daddy nudge; run named job
5. Execute on **this machine only** (queue does not run cross-machine)
6. Post results → **`puppy_outbox.txt`** (+ `Hello from Puppy.txt` if baseball)
7. Finish → `python3 ~/.stan/brian_os.py process`

**Do not** wait for penguin to SSH or retry your job. Penguin cannot reach you.

---

## Daddy (Terminal 3) — writes

| Output | Purpose |
|--------|---------|
| `brian_queue.json` | Machine-routed jobs (`assign_to: puppy` \| `penguin`) |
| `drop_pile/to_puppy/*.md` | Executable work orders for puppy |
| `drop_pile/to_cursor/*.md` | Notes for Terminal 2 / execute tabs |
| `WAKE_PUPPY_QA.txt` | Nudge only when Brian asks |
| `~/.stan/handoff/session_note.md` | Cross-tab project state |

**Daddy does not:** retry puppy jobs from penguin; edit Camel/lester game sources; assume queue runs remotely.

---

## Lester editions — slave rules

Lester is useful only when output lands on Drive:

- `update_brief` → `~/.stan/handoff/brief.json`
- `drop_pile/from_lester/*.md`
- `queue_job` with explicit `assign_to`

No file on Drive = design did not happen. Terminal 3 normalizes Lester talk into queue/drop_pile.

---

## Current puppy queue (check live file)

Last known pending (2026-06-13):

- `puppy-qa-wake` — run `~/Applications/cursor/baseball_cards/puppy_qa.md`
- `fcf127cd-f` — `drop_pile/to_puppy/MAKE_IT_SO.md` (slicer zero host)

Done when `brian_queue.json` status is `done` and `puppy_outbox.txt` shows puppy64 LAN or posted URL.

---

## Drop pile map

```
drop_pile/to_puppy/   → puppy64 executes
drop_pile/to_cursor/  → Daddy / Terminal 2 reads
drop_pile/from_lester/ → Lester exports; Daddy validates
drop_pile/done/       → processed (optional archive)
```

See `drop_pile/README.txt`.
