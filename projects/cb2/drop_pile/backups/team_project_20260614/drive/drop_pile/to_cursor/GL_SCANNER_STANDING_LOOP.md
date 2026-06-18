# GL scanner — always on (Daddy T3)

**From:** Daddy T3  
**Owner:** CB2 Terminal 3 — **not** Puppy, **not** Uncle  
**Interval:** every **2 minutes** (matches GL transcribe cadence)

---

## Job

Always scan `MyDrive/gl/` for new GL writes. Post **Cursor agent responses** to:

`MyDrive/gl/from_cursor/PENDING.md`

GL reads PENDING for your answer. History in `gl/from_cursor/scan_*.md`.

---

## Run (CB2 Linux — already delegated)

```bash
python3 ~/.stan/gl_scanner.py watch 120 >> ~/.stan/gl_scanner.log 2>&1 &
```

One-shot test:

```bash
python3 ~/.stan/gl_scanner.py scan
```

---

## Folder map

| Path | Who writes |
|------|------------|
| `gl/inbox/` | GL — transcripts, session chunks |
| `gl/` root | GL — test files, instructions |
| `gl/from_cursor/PENDING.md` | **Scanner / T3** — latest response |
| `gl/scan_log.txt` | scanner log |
| `gl/scan_state.json` | scanner state (ignore) |

---

## GL drops here

Brian/GL task: transcribe Live → update `gl/inbox/` every 2–3 min.

Cursor scanner picks it up within 2 min → `from_cursor/PENDING.md`.

---

## If scanner dies

Brian says **DADDY** here → T3 restarts watch command above.

Do not assign to Puppy (execute lane). Captain scan only.
