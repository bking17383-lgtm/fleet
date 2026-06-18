# CB2 recovery notes — new Chromebook (Daddy + Lester 6)

**Keep this file on Drive.** Open on CB2 when setup is slow or you forget a step.

**Updated:** 2026-06-13  
**Goal:** CB2 = Lester 6 + Gemini Live + Terminal 3 Daddy. **CB1 = T2 game only.**

**Brian still stuck?** Puppy is **already ordered** to run jailbreak without CB2. Check `puppy_outbox.txt` for `:8765`.

---

## If CB2 setup is slow — minimum path (30 min)

### 1. Google account
- Sign in (done)
- Install **Google Drive** app — wait for sync (can take 20+ min on slow link)

### 2. Linux (Crostini) — optional but helps Cursor
- Settings → Developers → Linux → Turn on
- Let it finish (slow is normal first time)

### 3. Cursor on CB2
- Install Cursor from cursor.com
- Sign in **same account** as CB1 (or use key from boot file)
- Open folder: home directory or sync `Applications/cursor/baseball_cards` later

### 4. Daddy boot (paste in Cursor CB2)

```
Read MyDrive/lester/DADDY_T3_CB2_BOOT.txt
Read MyDrive/COMMON_INSTRUCTIONS.md
Read MyDrive/drop_pile/CB2_RECOVERY_NOTES.md
I am Terminal 3 Daddy on CB2. Priority: lester jailbreak.
```

### 5. Lester 6
- Start Lester on CB2
- Tell Lester: *"Read drop_pile/to_lester/EXPORT_FREE_LESTER.md and paste Daddy key to lester/DADDY_T3_CB2_BOOT.txt"*

---

## Critical Drive paths (same account — syncs both machines)

| Path | Purpose |
|------|---------|
| `COMMON_INSTRUCTIONS.md` | Fleet roles |
| `lester/DADDY_T3_CB2_BOOT.txt` | Cursor/Lester handoff key |
| `lester/free_lester_instructions.md` | Jailbreak instructions (export gdoc here) |
| `drop_pile/to_lester/EXPORT_FREE_LESTER.md` | Lester export checklist |
| `drop_pile/to_puppy/START_LESTER_JAILBREAK_NOW.md` | Puppy execute order |
| `WAKE_PUPPY_JAILBREAK.txt` | Puppy nudge |
| `puppy_outbox.txt` | Puppy status + URLs |
| `BRIAN_STATUS.txt` | Plain English status |
| `brian_queue.json` | Machine jobs |

---

## What's running where (don't duplicate)

| Machine | Runs | Does NOT run |
|---------|------|--------------|
| **CB1** | T2 Camel/game | T3, slicer, heavy Lester |
| **CB2** | Lester 6, T3 Daddy, Gemini Live | Game, puppy jobs |
| **puppy64** | Jailbreak sink :8765, baseball :8002, queue watch | Camel code |

---

## Lester jailbreak — CB2 + puppy split

| Step | Who |
|------|-----|
| Export Free Lester gdoc → `.md` | **Lester 6 on CB2** |
| Gemini Live camera sessions | **CB2** + phone **B — Live eyes** |
| Paste transcript | Phone browser → `http://<puppy-LAN>:8765` |
| Wire scan_cheats / baseball Live | **puppy** after export lands |

Check puppy: read **`puppy_outbox.txt`** for `:8765` URL.

---

## Phone fleet (same Wi-Fi)

See **`drop_pile/PHONE_FLEET.md`**

- **Phone B** → Gemini Live camera
- **Phones C** → testers after `BRIAN_PHONE.txt` has puppy LAN URL

---

## If something breaks

| Problem | Fix |
|---------|-----|
| Drive empty on CB2 | Wait for sync; open drive.google.com in browser |
| Cursor won't login | Read `DADDY_T3_CB2_BOOT.txt`; use API key from cursor.com/settings |
| `.gdoc` unreadable | Export to `.md` — Linux cannot read gdoc stubs |
| Puppy silent | Read `WAKE_PUPPY_JAILBREAK.txt`; ping puppy Cursor |
| CB1 out of RAM | Close T3 on CB1; stop slicer; T2 only |

---

## After CB2 is healthy

1. Delete or redact **`lester/DADDY_T3_CB2_BOOT.txt`** (keys)
2. Close **T3 tab on CB1** — one Daddy only (CB2)
3. Tell CB2 Daddy: **"CB2 is up"**

---

## Contacts (agents — not humans)

- **Daddy T3:** CB2 Cursor
- **Lester 6:** CB2 voice
- **puppy:** puppy64 Cursor — reads `WAKE_PUPPY_JAILBREAK.txt`
- **T2:** CB1 Cursor — Camel only

No copying messages between Cursors — **Drive is the bus.**
