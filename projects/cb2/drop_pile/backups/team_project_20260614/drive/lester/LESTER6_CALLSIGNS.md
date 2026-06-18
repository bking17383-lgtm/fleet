# Lester6 call signs — fleet roster

**Updated:** 2026-06-14  
**Human words:** see **`ONE_WORD.txt`** — Brian says UNCLE | DADDY | PUPPY only.

Internal aliases below (agents/scorecard — not for Brian to memorize).

---

## One word → one machine (Brian)

| Word | Machine | Wakes Cursor + Lester6 |
|------|---------|------------------------|
| **UNCLE** | CB1 | game tab + Chrome |
| **DADDY** | CB2 | captain tab + Chrome |
| **PUPPY** | puppy64 | execute + Chrome |

Plus: **EXPORT** (any Lester6) · **CAMEL** (CB1 game only)

---

## Internal aliases (scorecard / ack field)

| Word (Brian) | Alias (ack) | Ack file |
|--------------|-------------|----------|
| UNCLE | WRANGLER | `lester6_to_uncle.md` |
| DADDY | BEACON | `lester6_to_daddy.md` |
| PUPPY | PLATE | `lester6_to_puppy.md` |

---

## Roster (detail)

| Callsign | Master | Machine | Chrome Lester6 | Slave config | Ack file |
|----------|--------|---------|----------------|--------------|----------|
| **WRANGLER** | Uncle | CB1 | Gemini on CB1 Chrome | `lester/lester6_uncle_slave.md` | `drop_pile/from_lester/lester6_to_uncle.md` |
| **BEACON** | Daddy T3 | CB2 | Gemini on CB2 Chrome | `lester/lester6_daddy_slave.md` | `drop_pile/from_lester/lester6_to_daddy.md` |
| **PLATE** | Puppy | puppy64 | Gemini on puppy Chrome | `lester/lester6_puppy_slave.md` | `drop_pile/from_lester/lester6_to_puppy.md` |

---

## Wake words (Brian)

| Say | Wakes |
|-----|-------|
| **WRANGLER** | Uncle's Lester6 (CB1) — export, heartbeat, game sync |
| **BEACON** | Daddy's Lester6 (CB2) — gdoc export, delegate voice |
| **PLATE** | Puppy's Lester6 (puppy64) — QA, tester copy, human-test |
| **READY** | All masters check scorecard + refresh acks today |

---

## Ack must include

```
callsign: WRANGLER | BEACON | PLATE
mode: slave
```

No callsign in ack = generic session = failed bind.

---

## Cursor masters (for clarity)

| Name | Machine | Role |
|------|---------|------|
| Uncle | CB1 | Game / Camel |
| Daddy T3 | CB2 Terminal 3 | Delegate / queue |
| Puppy | puppy64 | Execute / serve |

Lester6 slaves are **Chrome only**. Cursor masters read Drive; they are not Lester6.
