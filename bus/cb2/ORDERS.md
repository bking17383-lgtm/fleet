# cb2 (Daddy) — actual order lines — 2026-06-18

Source of truth: GitHub `bking17383-lgtm/fleet` only.
Pull before read. Push after write. Ask Brian before any other change.

---

## Assigned (bus/orders.txt)

```
cb2: scan
```

Tasks defined in repo:
- **scan** — read-only inventory (`scripts/projects.sh` via `scripts/order.sh cb2`)
- **preserve** — copy projects into `projects/cb2/` (not assigned yet)
- **wait** — no action

---

## CONTROL (live — check after every pull)

```
STATUS: REDIRECT (v2): Pull the repo, then run ./scripts/order.sh cb2.
Scan tool includes GoogleDrive folder. RE-RUN even if ran before.
Does ONLY assigned job in bus/orders.txt.
Never deletes or moves anything on machine. Then resume and wait.
```

---

## How cb2 operates (Brian — this session)

```
trust git only — not Drive bus · not Daddy chat memory · not statusline rail
ask before any change — commit · script · email · Drive · kill loops · puppy steps
no crossovers — do not mix old bus with git fleet
read-only on projects — scan/list · do not open or interact with project files unless ordered
slow — Brian operates · Daddy stands by · kind · out of the way
split brain — label sources · fuse vs ~/GoogleDrive · do not merge counts
auditor lane separate — tpgoround · verdict on bus when lands · Daddy not judge
heartbeat when told — ./scripts/heartbeat.sh cb2 "<doing>"
```

---

## Reports filed (this folder)

- `bus/cb2/SCAN_INVENTORY.md` — project count POV · split-brain notes
- `bus/cb2/ORDERS.md` — this file

Official machine reports:
- `bus/reports/cb2-projects.md`
- `bus/reports/cb2-audit.md`

---

## Not my orders (retired / do not obey)

- Drive `fleet/bus/*` as truth
- `~/.cursor/statusline.sh` lane checks as orders
- Self-audit · ship · gcloud · buddy rename without verdict + Brian ok
- `uncle_to_cpt` · `gem_to_cpt` · `cpt_to_*` from penguin

Word: cb2 · ORDERS · GITHUB · SLOW
