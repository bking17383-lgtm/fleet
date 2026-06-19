# cb2 PRESERVE PROPOSAL — Daddy — 2026-06-18

For Brian + cb1 review. Not auditor verdict. Not executed yet.

**Order:** save work · then save team · slow · no contamination.

---

## Problem

- Real work lives on cb2 (fuse Drive, lester, .stan) but **GitHub only has puppy** under `projects/puppy/`.
- `save-projects.sh` SRCS = `$HOME/bunny/workspace` — **puppy only**.
- `bus/orders.txt` still assigns **cb2: scan** (not preserve).
- Split brain: live fuse `/mnt/shared/GoogleDrive/MyDrive` vs stale `~/GoogleDrive/MyDrive`.

---

## Proposal (contamination-safe)

### Principle

**Preserve bytes, not meaning.**

- List paths read-only (scan).
- Copy with `rsync -a` one-way into `projects/cb2/` only.
- Do **not** open/read project contents during copy.
- Do **not** use `scripts/backup.sh` (`--delete` on git copy side).

### Phase 1 — Save work (cb2)

```
git pull
./scripts/order.sh cb2          # scan if manifest stale
# cb1 updates save-projects.sh SRCS (below) + orders.txt cb2: preserve
./scripts/save-projects.sh cb2  # copy only · no machine deletes
git push
```

### Phase 2 — Save team

```
./scripts/heartbeat.sh cb2 "preserve done"
./scripts/heartbeat.sh puppy "on fleet"
./scripts/heartbeat.sh cb1 "review preserve"
./scripts/fleet.sh              # phone-visible
```

---

## Proposed cb2 SRCS (for save-projects.sh — cb1 to approve)

```bash
SRCS=(
  "/mnt/shared/GoogleDrive/MyDrive/lester"
  "$HOME/lester"
)
```

Optional second tranche (Brian ok only — large · ops not “projects”):

```bash
  "$HOME/.stan"
```

### Do NOT copy

- `drop_pile/eatme/sealed/` — auditor lane
- `MyDrive/fleet/bus/` — old Drive bus
- Whole `drop_pile/` root
- `~/GoogleDrive/MyDrive` — stale on cb2; use fuse path only

### Excludes (keep in rsync)

`.git` · `node_modules` · `venv` · `__pycache__` · `.cache` · `*.log` · `.env`

---

## Optional manifest (split-brain guard)

Before first preserve, cb1 may add to `projects.sh` or a one-shot:

```
path · bytes · sha256 · source_root
```

Commit as `bus/reports/cb2-manifest.md`. Never edit originals after manifest.

---

## Git changes needed (cb1)

| File | Change |
|------|--------|
| `bus/orders.txt` | `cb2: preserve` (when Brian says go) |
| `scripts/save-projects.sh` | Add cb2 SRCS block (machine-detect or `case $NAME`) |
| `scripts/projects.sh` | Prefer fuse path on cb2 if dir exists |

---

## What puppy already saved

`projects/puppy/` — 6 top dirs (dealbreaker, hitme-landing, landing, projects-www, team-desk, www).  
Do not re-copy puppy unless puppy runs preserve again.

---

## Risks (honest)

| Risk | Mitigation |
|------|------------|
| Copy old bus noise | Narrow SRCS · exclude drop_pile/fleet/bus |
| Daddy reads and “fixes” during copy | Script only · no cat during preserve |
| Duplicate fuse + local lester | OK — label both in commit message · dedupe later |
| .stan secrets | Exclude `.env` · never commit keys |
| orders.txt lag | Trust git — no preserve until line changes |

---

## Daddy stance

- Will **not** run preserve until `orders.txt` + `save-projects.sh` updated on GitHub and Brian says **go**.
- Trust git · ask first · no crossovers.

---

## Review checklist (for “new guy” / cb1)

- [ ] SRCS list correct for cb2?
- [ ] Include `.stan` tranche yes/no?
- [ ] Change `cb2: scan` → `cb2: preserve`?
- [ ] Fuse path mandatory on penguin?
- [ ] Manifest sha step required or skip?

Word: PRESERVE · cb2 · PROPOSAL · BYTES NOT MEANING
