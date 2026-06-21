# PACK HANDOFF — cb1 test account (Tommy session)
# Packed: 2026-06-20 · Brian switching accounts · next agent read this + hitme.dev/all

## READ FIRST (any machine)
- **https://hitme.dev/all** — live read-only fleet law + pee board state (curl `/all.txt` or json `/api/fleet/all`)
- Then: `cd ~/fleet && git pull` · `bus/KERNEL.md` · this file

## WHO / WHICH BOX
- machine: **cb1** (`~/.fleet-name`) · hostname penguin · user **tpgoround**
- agent name this session: **Tommy** (cb1-only agent)
- **TEST ACCOUNT** — stays test · do not merge to bking · other account = out of scope
- **NO OPUS** (Brian lock 2026-06-20) — cb1 seat = Composer Fast · FIND · verify · read-only · TO_JANE one pass
- `bus/cb1/DUMMY_MODE.txt` still active — isolated trainee lane

## THIS SESSION (what Brian said)
- Disk: 10 GB now · slider can go to 72 GB · expect **max ~62 GB** use · no urgent clean yet (34% used)
- Shelf (manual — cannot change from Linux): keep **Chrome · Files · Terminal · Gemini** only; always ask before shelf changes
- **No slave on this test account** — real gap (Gemini pinned ≠ fleet slave); fix = bind Chrome Gemini via `bus/cb1/SLAVE.md` when Brian says
- Other account: ignore · not our lane

## WHAT STAYS RUNNING (leave on)
- Jane daemons via keeper (`jane-car.sh on` · cron ensure @reboot + */5)
- Fleet heartbeat cron */10 (`scripts/heartbeat.sh cb1`)
- Cursor: statusline `/home/tpgoround/.cursor/statusline.sh` · hooks ding on idle

## LOCAL ONLY (not in git — survives account switch on same profile)
- `~/jane/` — full voice stack (~529M): venv, vosk model, piper voice, scripts, corrections, learned
- `~/fleet/` — truth repo (SSH push works on this box)
- `~/.cursor/` — cli-config, hooks, skills
- `~/.aws/` — empty dir placeholder · no key yet

## NEXT AGENT — FIRST MOVES
1. curl -s https://hitme.dev/all.txt | head — confirm live law matches git
2. `git pull` · read `bus/cb1/PACK_HANDOFF.md` · `bus/jane/JANE_PACK_LIST.md`
3. `./scripts/live.sh` if present — verify vitals
4. Wait for Brian · short replies · prove claims · no Opus burn

## OPEN (not done this pack)
- [ ] Resize Linux disk toward 72 GB (Brian manual slider)
- [ ] Wire cb1 Chrome slave (Gemini bind)
- [ ] Jane pack list reviewed by Brian / Daddy
