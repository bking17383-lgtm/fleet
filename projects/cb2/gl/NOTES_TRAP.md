# The notes trap — why GL drifts and how to beat it

**Updated:** 2026-06-14 · Daddy T3  
**For:** Brian + BEACON / WRANGLER / PLATE

---

## What you're seeing (normal, not your fault)

Gemini / Lester6 **prefers local context**:

| Where it wants to keep stuff | Why |
|------------------------------|-----|
| Chat thread memory | Default — feels "helpful" |
| Gemini **Notes** (app feature) | Built-in, one tap, no path |
| "I'll remember that" | No Drive write = no friction |
| Generic assistant mode | Ignores fleet slave rules |

**Instructions help part of the time** because:

- Voice/Live has **less** tool access than text chat
- Long instruction files → model reads **top + tail**, skips middle
- Context **resets** between sessions — slave bind forgotten
- Camera / driving / multitask → drops sync rules first

**You cannot instruction your way to 100% consistency.**  
Design around drift instead of fighting it.

---

## What Step 1 actually means (reframed)

Step 1 is **not**: "Gemini maintains `.md` files on Drive."

Step 1 **is**:

1. **Brain lives in plain `.md` on Drive** — Linux/T3/Puppy read those
2. **Gemini is a voice/text front-end** — not the memory store
3. **Brian triggers saves with one word** — not hope
4. **T3 backfills** when GL drops the ball

Gdocs optional. **Local notes never count.**

---

## Brian's session ritual (works with inconsistent GL)

### Open (10 sec)

1. Chrome → Gemini
2. Say **DADDY** (or UNCLE / PUPPY on that machine)
3. Open **`gl/instructions for AI.md`** in Drive app side-by-side OR say: *"read instructions for AI on Drive"*

Wait for one line: *"BEACON synced"* (or callsign ready).  
If generic fluff → say **DADDY** again or paste `BEACON_REBIND.md` block.

### While talking

| You want | Say | Lands in |
|----------|-----|----------|
| One idea, fast | **IDEA** + sentence | `IDEAS.txt` |
| Voice dump / recap / camera notes | **SAVE** | `drop_pile/from_lester/live_YYYYMMDD.txt` |
| Silence (driving) | **shh** / **shut up** | nothing (HOLD law) |
| Keep talking | **resume** | — |

**Do not** ask GL to "remember for later" without **IDEA** or **SAVE**.

### Close (5 sec)

Say: **"What landed on Drive?"**

Pass = one-line list of **file paths**.  
Fail = vague "I noted that" → say **SAVE** now or tell T3 here in Cursor.

---

## Three capture lanes (pick by weight)

```
Light   IDEA  →  IDEAS.txt           (one line, any machine)
Medium  SAVE  →  drop_pile/from_lester/live_*.txt
Heavy   T3    →  you talk here in Cursor; Daddy writes the .md
```

**Heavy design in GL = drift.** Brainstorm in GL, **commit in T3**.

---

## What BEACON must do (non-negotiable)

### Forbidden phrases (session = failed if you say these without saving)

- "I'll keep that in mind"
- "I've noted that"
- "I remember"
- Saving only to **Gemini Notes**
- Long recap in chat with **no file path**

### Required after every IDEA or SAVE

One line aloud: **"On Drive at `<path>`."**

No path = lie. Brian should not trust the session.

### If you cannot write to Drive (voice-only moment)

Say: **"Not on Drive — say SAVE or use T3."**  
Do not pretend it saved.

---

## When GL won't conform — Brian bypass (always works)

| Method | When |
|--------|------|
| **Drive app on phone** | Type one line into `IDEAS.txt` |
| **Terminal 3 Cursor** | Talk — Daddy writes files + queue |
| **brian_says.txt** | One line on Drive; CAPTN reads |
| **Post-session** | Paste GL chat export → T3 summarizes to Drive |

**T3 is the reliable memory. GL is the microphone.**

---

## Why Apps Script is separate

Apps Script fixes **gdoc → .md** sync.  
It does **not** fix Gemini keeping **local notes**.

Even with script: if content never hits Drive, nothing to sync.

Order of fixes:

1. **IDEA / SAVE ritual** (this file)
2. **Plain `.md` master** (no gdoc editing)
3. **Apps Script** (optional, for leftover gdocs)

---

## Words (add SAVE to your tape)

| Word | Action |
|------|--------|
| **IDEA** | one line → `IDEAS.txt` |
| **SAVE** | append session chunk → `drop_pile/from_lester/live_<today>.txt` |
| **HOLD** | shh / shut up → zero output |
| **DADDY** | bind BEACON + read instructions for AI |

Full card: `ONE_WORD.txt`
