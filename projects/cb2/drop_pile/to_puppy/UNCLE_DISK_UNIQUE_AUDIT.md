# Uncle disk — what's unique? (Puppy audit)

**From:** CAPTN  
**To:** Puppy Cursor  
**Word:** PUPPY  
**Brian question:** Can we recreate Uncle if we list missing apps? Camel game, utilities, etc.

---

## Job

Write **`drop_pile/from_puppy/UNCLE_UNIQUE_REPORT.md`**

Answer in plain English:

1. **On Drive already** (safe — no need to scrape Uncle disk)
2. **Maybe only on CB1** (need copy before wipe/recreate)
3. **Recreate from docs** (Puppy/CAPTN can rebuild)

---

## Check these paths (Drive = source of truth)

| Item | Drive path | Unique? |
|------|------------|---------|
| Camel game | `lester/camel_clicker.py` · `StandardCamel.java` | On Drive |
| Camel design | `drop_pile/to_cursor/CAMEL_*` · `drop_pile/done/CAMEL_*` | On Drive |
| Uncle stan tools | `lester/fleet_board.py` · `install_uncle_stan.sh` | On Drive |
| Uncle slave docs | `lester/lester6_uncle_slave.md` | On Drive |
| CB1 Cursor key | `lester/lester_keys.md` (CB1 line) | On Drive |
| Team backup | `drop_pile/backups/team_project_20260614/` | CB2 snapshot — **not CB1 local disk** |

---

## Puppy execute (if CB1 reachable on LAN)

```bash
# only if Uncle Linux still exists and you can reach CB1
# ping / ssh / mount — report YES or NO
```

If **cannot reach CB1:** say so. Report Drive-only audit is enough.

List any **`~/lester/`** or **`~/Applications/`** Brian mentioned that are **NOT** on Drive.

---

## Report template

```markdown
# Uncle unique inventory
time: <ISO>

## On Drive — do not need Uncle disk
- camel_clicker.py — YES on Drive
- ...

## Only on CB1 (if any) — copy before recreate
- ...

## Recreate list (Brian confirm)
- Camel v0.8 from Drive sources — YES
- fleet_board / DESK — YES from install_uncle_stan.sh
- ...

## Verdict
RECREATE UNCLE: YES / NO / PARTIAL
missing apps Brian must name: ...
```

Post one-line verdict to **puppy_outbox.txt** when done.

Brian hates long tests — audit only, no phone QA.
