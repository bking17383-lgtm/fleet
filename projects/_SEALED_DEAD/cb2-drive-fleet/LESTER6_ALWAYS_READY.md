# Lester6 — always ready (all machines)

**From:** Daddy T3 (CB2 Terminal 3)  
**Updated:** 2026-06-14  
**Rule:** Every Cursor master keeps a **bound Lester6 slave** at all times. No generic Gemini.  
**Ack law:** `ACK_FILE_LAW.md` — plain `.md` only, never `.gdoc`-only acks.

---

## Three bindings (non-negotiable)

| Master | Machine | Slave config | Heartbeat ack |
|--------|---------|--------------|---------------|
| Daddy | CB2 | `lester/lester6_daddy_slave.md` | `drop_pile/from_lester/lester6_to_daddy.md` |
| Uncle | CB1 | `lester/lester6_uncle_slave.md` | `drop_pile/from_lester/lester6_to_uncle.md` |
| Puppy | puppy64 | `lester/lester6_puppy_slave.md` | `drop_pile/from_lester/lester6_to_puppy.md` |

**Keys once:** `lester keys.gdoc` → `lester/lester_keys.md`

---

## Every session start (all machines)

1. Lester6 Chrome: read your slave file + `ACK_FILE_LAW.md` → **overwrite** ack `.md` with `mode: slave` + today's time
2. Cursor master: read standing loop file (below)
3. If ack missing, `mode: generic`, or **only `.gdoc` exists** → bind before any other work (`PLATE_BIND_NOW.md` / `BEACON_REBIND.md`)

| Machine | Standing loop |
|---------|---------------|
| CB2 Daddy | `DADDY_DELEGATE_ONLY.md` + design desk |
| CB1 Uncle | `drop_pile/to_cursor/CB1_STANDING_LOOP.md` |
| puppy64 | `drop_pile/to_puppy/PUPPY_STANDING_LOOP.md` |

---

## Word: **READY**

Brian or agent says **READY** → check scorecard + refresh ack file today.

---

## Daddy rule (CB2)

**Always delegate.** Daddy writes queue + drop_pile. Daddy does **not** execute servers, tunnels, or builds.

Execute → **puppy**. Game → **uncle** (when Brian says CAMEL). Design/export → **Lester6** on each machine.

---

## Scorecard

`LESTER6_SLAVE_SCORECARD.txt` — CAPTN updates when acks land.

Pass = all three ack files exist with `mode: slave` and timestamp today.

---

## Stay online (plugged in — 2026-06-14)

**Order:** `drop_pile/to_lester/LESTER6_STAY_ONLINE.md`

Each slave refreshes heartbeat + ack every **30 min while Cursor live** · word **PULSE**. Law: **`HEARTBEAT_LAW.md`**

| Machine | File |
|---------|------|
| CB1 | `cb1_heartbeat.md` |
| CB2 | `cb2_heartbeat.md` |
| puppy64 | `puppy_heartbeat.md` |

No hibernate without good reason (Brian says sleep, or battery critical without cord).
