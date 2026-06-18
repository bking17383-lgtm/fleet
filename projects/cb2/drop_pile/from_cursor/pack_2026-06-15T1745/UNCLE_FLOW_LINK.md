# Uncle flow link — production bus (ONE doc)

**Updated:** 2026-06-15T16:57:29-07:00  
**From:** Uncle (CB1 Cursor)  
**Goal:** good flow — all agents linked via Drive, honest state

Brian: run **3 binds** below in order. Drive is the only wire.

---

## Link map

```
                    ┌─────────────┐
                    │   Brian     │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ UNCLE       │ │ WRANGLER    │ │ CAPTN       │
    │ CB1 Cursor  │ │ CB1 Chrome  │ │ CB2 Cursor  │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           └───────────────┴───────────────┘
                           │
                    Google Drive bus
```

| Agent | Reads | Writes |
|-------|-------|--------|
| **UNCLE** | `from_lester/lester6_to_uncle.md` · `mac_outbox.txt` | `from_cursor/` · `mac_inbox.txt` · `cb1_heartbeat` (cursor fields) |
| **WRANGLER** | `to_lester/WRANGLER_EXECUTE_NOW.md` | `from_lester/lester6_to_uncle.md` · `cb1_heartbeat` (lester6 fields) |
| **CAPTN** | `to_cursor/UNCLE_CAPTN_LOOP_NOW.md` · `mac_inbox.txt` | `mac_outbox.txt` · `cb2_heartbeat.md` |

**Never:** chat-only state · fleet scripts (off) · `.gdoc` acks

---

## Link status (honest)

| Link | State | Blocker |
|------|-------|---------|
| Uncle live | **YES** | — |
| Uncle ↔ WRANGLER | **interim** | Brian paste WRANGLER block · Chrome confirm |
| Uncle ↔ CAPTN | **NO** | CAPTN reply mac_outbox or cb2 heartbeat today |
| Uncle ↔ Puppy | unknown | not checked |

---

## 3 binds (do in order)

### 1 — UNCLE (CB1 Cursor) ✓ done

Already live. Watcher on WRANGLER ack + CAPTN reply.

### 2 — WRANGLER (CB1 Chrome Lester6)

Paste from `drop_pile/to_lester/WRANGLER_EXECUTE_NOW.md` → say **PULSE**

### 3 — CAPTN (CB2 Cursor)

Paste from `drop_pile/to_cursor/UNCLE_CAPTN_LOOP_NOW.md` → say **DESK**

---

## Flow closed when

- [ ] `lester6_to_uncle.md` — WRANGLER wrote today (not uncle-interim)
- [ ] `cb1_heartbeat.md` — `paired: yes` · fresh `last_lester_refresh`
- [ ] `mac_outbox.txt` — `from: captn` today with camel date + cb2 live
- [ ] `cb2_heartbeat.md` — today OR mac_outbox suffices

---

## Open asks (still on bus)

1. **Camel testable when?** → CAPTN answers
2. **CB2 live yes/no?** → CAPTN answers

---

## Words (Brian)

| Say | Wakes |
|-----|-------|
| **UNCLE** | CB1 Cursor |
| **PULSE** | WRANGLER refresh ack |
| **DESK** | CAPTN read inbox + FLEET_AVAILABLE |
| **EXPORT** | WRANGLER gdoc → .md |
| **CAMEL** | Uncle game lane (when CAPTN says go) |

---

## Watchers (Uncle session)

- WRANGLER: `lester6_to_uncle.md` + `cb1_heartbeat.md` every 30s
- CAPTN: `mac_outbox.txt` + `cb2_heartbeat.md` every 45s

Say **LINK** on any machine → read this file first.
