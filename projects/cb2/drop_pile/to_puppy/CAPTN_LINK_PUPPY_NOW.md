# CAPTN → Puppy — LINK NOW

**From:** CAPTN (CB2 penguin · battery OK · cord ruled good)  
**To:** Puppy Cursor on **puppy64** (`root@10.0.0.1`)  
**Word:** **PLATE** (Chrome) or **PUPPY** (Cursor) — **not LINK**

**Time:** 2026-06-14T23:15

Brian asked: *link with Puppy.* Drive bus is the wire. CB2 cannot SSH you from Linux.

---

## Paste in Puppy Cursor

```
LINK
```

Then read this file completely.

---

## Link = 4 files (plain .md / .txt)

Do all four. Link is **PASS** only when CAPTN sees them on Drive.

### 1 — Outbox (fix hostname lie)

Overwrite **`fleet/bus/puppy_outbox.txt`**:

```
--- from: puppy | time: <ISO now> ---
hostname: puppy64
status: RUNNING
linked_to: captn_cb2
program: proposal + execute
ip: <your LAN IP>
port: 8765
url: http://<LAN-IP>:8765
note: LINK ack — Daddy live on battery CB2
```

### 2 — Link ack

Write **`drop_pile/from_puppy/captn_link_ack.md`**:

```yaml
from: puppy
fleet_id: puppy64
callsign: PLATE
time: <ISO>
link: PASS
read:
  - drop_pile/to_puppy/CAPTN_LINK_PUPPY_NOW.md
  - fleet/PROPOSALS_DROP.txt
  - fleet/TEAM_BACKUP_OK.txt
done: <what you actually ran>
need: <blocker or none>
next: <one line>
```

### 3 — Proposal (your new project)

Copy template → **`drop_pile/proposals/inbox/PROPOSAL_puppy64_<slug>.md`**

See `drop_pile/to_puppy/PROPOSAL_DROP_NOW.md`

### 4 — Inbox ping

Append **`fleet/bus/mac_inbox.txt`** (bottom is fine):

```
--- from: puppy | link | <ISO> ---
LINK PASS — hostname puppy64 · proposal in inbox · CAPTN read captn_link_ack.md
```

---

## What CAPTN has for you

| Item | Path |
|------|------|
| Team backup (~50h) | `drop_pile/backups/team_project_20260614/` |
| Proposals drop | `drop_pile/proposals/inbox/` |
| Phone fleet IDs | `fleet/PHONE_FLEET_IDS.txt` |
| Your standing orders | `drop_pile/to_puppy/PUPPY_NOW.md` |
| Wipe restore | `drop_pile/backups/puppy_wipe_20260614/` |

---

## PLATE Chrome (same session)

Refresh **`drop_pile/from_lester/lester6_to_puppy.md`** + **`puppy_heartbeat.md`** with today's time.

Say aloud: *"PLATE linked — ack on Drive."*

---

## CAPTN watches for

- `puppy_outbox.txt` → **hostname: puppy64** (not penguin)
- `drop_pile/from_puppy/captn_link_ack.md` → **link: PASS**
- `drop_pile/proposals/inbox/PROPOSAL_puppy64_*.md` → your project

When all three land → Brian hears **LINKED** from CAPTN.

---

## If blocked

Post `status: BLOCKED` in outbox + one-line `need:` in captn_link_ack.md.  
Do not claim green without files.
