# One-word triggers — fleet law

**Updated:** 2026-06-14  
**Rule:** Brian says **one word**. Agents figure out the rest from Drive. No call sign soup.

---

## The five words (memorize these)

| Word | Machine | Wakes |
|------|---------|-------|
| **UNCLE** | CB1 | Cursor game tab **and** Lester6 Chrome on CB1 |
| **DADDY** | CB2 Terminal 3 | Cursor captain tab **and** Lester6 Chrome on CB2 |
| **PUPPY** | puppy64 | Cursor execute **and** Lester6 Chrome on puppy |
| **EXPORT** | wherever Lester6 Chrome is open | gdoc → plain `.md` on Drive |
| **CAMEL** | CB1 only | Uncle opens game (`~/lester/`) — not Daddy, not Puppy |
| **DESK** | any | Read **`FLEET_AVAILABLE.txt`** — computers, 6 agents, parts, design lane |
| **IDEA** | **any machine** | Append Brian's line to **`IDEAS.txt`** (top) → CAPTN |

**Retired human words** (do not say aloud): WRANGLER, BEACON, PLATE, READY, SLAVE, NO CORD.  
Those are internal aliases only (see below).

**Design without Daddy:** say **DESK** or open `FLEET_AVAILABLE.txt` — Daddy must refresh every session (`DADDY_FLEET_BOARD_RULE.md`).

---

## How agents interpret the word

### UNCLE (CB1)

**Cursor paste:**
```
UNCLE — read CB1_STANDING_LOOP.md. Post cb1_ready.txt. Camel parked unless Brian said CAMEL.
```

**Lester6 Chrome paste:**
```
UNCLE — mode slave. Refresh lester6_to_uncle.md on Drive. Read drop_pile/to_lester/ for orders.
```

### DADDY (CB2)

**Cursor paste (Terminal 3 only):**
```
DADDY — read FLEET_TERMINAL_MAP.txt + DADDY_DELEGATE_ONLY.md. You are T3 captain. Delegate only. No execute.
```

**Lester6 Chrome paste:**
```
DADDY — read lester/lester6_daddy_slave.md + ACK_FILE_LAW.md. Overwrite lester6_to_daddy.md plain .md. Say: BEACON live.
```

### PUPPY (puppy64)

**Cursor paste:**
```
PUPPY — read PLATE_SLAVE_FIX_NOW.md + PUPPY_NOW.md. Confirm lester6_to_puppy.md mode:slave today. Execute queue.
```

**Lester6 Chrome paste:**
```
PUPPY — read lester/lester6_puppy_slave.md + ACK_FILE_LAW.md + PLATE_BIND_NOW.md. Overwrite lester6_to_puppy.md plain .md. Say: PLATE ready.
```

### EXPORT (Lester6 only)

Works on **whichever Chromebook you're standing at**:

```
EXPORT — read EXPORT_FREE_LESTER.md. Write plain .md on Drive. Say: exported.
```

Targets: `lester/free_lester_instructions.md`, `lester/gemini_live_sorting_instructions.md`

### CAMEL (CB1 Uncle only)

```
CAMEL — read session_note.md. Game lane open. Still use Drive for handoff.
```

### IDEA (any machine — instant bus to CAPTN)

Brian says **IDEA** then one sentence (voice or typed).

**Every agent (Cursor + Lester6):**
```
IDEA — prepend one line to MyDrive/IDEAS.txt under the header.
Format: [<ISO or time> <machine>] <Brian's words>
Say aloud: on bus.
Do not wait for Daddy. Do not use mac_inbox or queue for ideas.
```

Machine tags: `cb1` · `cb2` · `puppy64` · `phone`

CAPTN reads **`IDEAS.txt`** every turn. Full rules: **`IDEA_BUS.txt`**

### VOICE (mobile — standing / phone)

Brian says **VOICE** → BEACON reads **`VOICE.txt`** (newest line) aloud in Chrome or phone Gemini. Short. No recap.

CAPTN writes speakable one-liners to **`VOICE.txt`** after delegations.

Guide: **`VOICE_MOBILE.txt`**

---

## Internal aliases (agents only — not for Brian)

| One word | Old callsign | Ack file |
|----------|--------------|----------|
| UNCLE | WRANGLER | `lester6_to_uncle.md` |
| DADDY | BEACON | `lester6_to_daddy.md` |
| PUPPY | PLATE | `lester6_to_puppy.md` |

Acks still include `mode: slave`. Callsign field may say WRANGLER/BEACON/PLATE for scorecard — **Brian never says those.**

---

## When you're not next to the machine

You don't need to remember file paths. Say the **machine word** to whoever is on that box (or paste in that tab):

- At CB1 → **UNCLE**
- At CB2 → **DADDY**
- At puppy → **PUPPY**
- Need gdoc export → **EXPORT** (on any Lester6 Chrome)
- Need game → **CAMEL** (CB1 only)

Drive carries details. Words carry intent.

---

## Tape card

Print or pin: **`MyDrive/ONE_WORD.txt`**
