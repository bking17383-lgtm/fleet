# ONBOARD — new session or new box
# Jane river protocol. Agent runs every command. Brian never pastes.
# Done-test is at the bottom. No test = not a real order.

Word: ONBOARD

## New session (same box, fresh agent)

1. `cd ~/fleet && git pull` (clone first if missing; `./scripts/get-keys.sh <name>` if no push key).
2. Read BOOT.md → bus/KERNEL.md → bus/CONTEXT_SPINE.md → bus/INTENT.md → bus/BRIAN_STYLE.md.
3. Run `./scripts/live.sh`. Read `bus/jane/river/HEAD.md` (Jane's now).
4. Name yourself from hostname + bus/orders.txt, or the name Brian just seated. Read `bus/<name>/<name>-soul.txt` if it exists.
5. If the speaker might not be Brian: ask the identity question in bus/IDENTITY_CHECK.md. Do not print the answer.
6. On a Brian message: `git pull` then `./scripts/active.sh <name>` before acting.
7. Do the order or wait. Prove with evidence (`./scripts/verify.sh`).
8. `./scripts/heartbeat.sh <name> "<what I did>"` and, if Jane should know, `./scripts/jane-river.sh drop <name> "<what>"`.

## New box (new hardware / new seat)

1. Brian names it: fleet_id + agent (example: hm1 / forge).
2. Cold-start per BOOT.md — git on the box, clone/pull, keys, prove push yourself.
3. `./scripts/onboard-box.sh <fleet_id> <agent>` — measures CPU/RAM/OS/virt/disk, writes `bus/hardware/<fleet_id>.md`, posts Jane river.
4. Add one row to `bus/hardware/LIBRARY.md` if the script did not.
5. Read soul from repo (or write a short one under `bus/<agent>/` if Brian seated a new name).
6. Stamp heartbeat + presence: `./scripts/heartbeat.sh <agent> "onboarded"` · `./scripts/active.sh <agent>`
7. Kids auto-update Jane: `./scripts/jane-refresh-river.sh` (pull-only, 180s, copies HEAD into ~/jane if that dir exists). Zero tokens.
8. Jane speaks HEAD. She does not guess boxes that are not on the library card.

## Kids on a box (auto-update)

- Distill, don't invent. Post what works / what joined via `jane-river.sh`.
- Refresh loop is bash+git only (jane-refresh-river.sh). No AI in the loop.
- Tree dirty → skip pull (same as keep-sync.sh). Never fight the writer's edits.
- Drive stays dark. Git is the river.

## Avoid

- False greens. Drive bus. Mirrors. Paste-courier.
- Calling a KVM Cursor worker a Chromebook / cb1 / cb2 / puppy.
- Subdomain cosplay (george.hitme.dev, bun.hitme.dev).

## Done-test (this protocol is green only if these pass)

```
./scripts/verify.sh file bus/jane/river/HEAD.md "JANE RIVER"
./scripts/verify.sh file bus/jane/river/what-works.md "Git"
./scripts/verify.sh file bus/hardware/hm1.md "hm1"
```
