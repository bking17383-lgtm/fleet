# Daddy rule — always show Brian what's available

**Updated:** 2026-06-14  
**Priority:** standing — every session, even when busy

Brian designs. He will **not** chase fleet status. You maintain one file.

---

## The one file Brian reads

**`MyDrive/FLEET_AVAILABLE.txt`**

Plain English. Counts at top:
- **Computers** (how many boxes, on/off, role)
- **AI agents** (6 max — available / busy / dead)
- **Parts** (services + blockers)
- **DESIGN NOW** — what Brian can use **without you**

---

## Refresh when (any trigger)

1. **Every Daddy session start** (before other work)
2. **Any heartbeat changes** — `cb1_heartbeat.md`, `cb2_heartbeat.md`, `puppy_outbox.txt`
3. **Any slave ack** — `lester6_to_*.md`
4. **Brian says DESK**

Takes 2 minutes. Copy template from bottom of this file.

---

## When you are busy

You still update **`FLEET_AVAILABLE.txt` once**. Then stop.

Uncle or CAPTN may patch it if you cannot — but **you own the board** when live.

Do **not** make Brian open `brian_queue.json`, scorecard, or mac_inbox for availability.

---

## Agent status rules

| Status | Means |
|--------|-------|
| **AVAILABLE** | Brian can use for design now |
| **BUSY** | Cursor captain overloaded — use that machine's **Lester6 Chrome** instead |
| **DEAD** | No ack/outbox/SSH in last hour — execute lane down |

Count line must always show: `AVAILABLE: N  BUSY: N  DEAD: N`

---

## DESIGN NOW section (required)

Always answer: *"Brian can design using ___ without waiting on me."*

When Daddy busy, point Brian to **BEACON** (CB2 Chrome) + **WRANGLER** (CB1 Chrome). Execute waits on **PUPPY**.

---

## Template (overwrite FLEET_AVAILABLE.txt)

```
FLEET AVAILABLE — read this to design
Updated: <ISO>
Refreshed by: Daddy

COMPUTERS (N)
  CB1  ...  ON/OFF  role
  CB2  ...
  puppy64 ...

AI AGENTS (6)
  AVAILABLE: N  BUSY: N  DEAD: N
  (list 1–6 with one line each)

PARTS
  (services + blockers, one line each)

DESIGN NOW
  (what Brian uses while you are busy)
```

---

## mac_inbox one-liner (after each refresh)

Append:
```
--- from: daddy | fleet-board | <time> ---
FLEET_AVAILABLE.txt updated — Brian say DESK to read counts.
```

Brian word: **DESK** = open `FLEET_AVAILABLE.txt` only.
