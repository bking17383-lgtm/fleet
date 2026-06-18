# Uncle — WRANGLER slave upgrade (Brian order)

**Word:** SMART  
**From:** CAPTN / Brian  
**When:** 2026-06-14

Brian: WRANGLER is too dumb. Fix the slave, not more hand-waving.

## Do now

1. **WRANGLER Chrome** — re-read `drop_pile/from_lester/lester6_to_uncle.md` every session; post fresh pulse in `cb1_heartbeat.md` (not stale 07:45 ack theater).
2. **Fleet board** — `~/.stan/fleet_board.py` must match reality:
   - pending/awaiting = DOWN, not linked
   - puppy `hostname: penguin` = puppy NOT up
   - partial vs working must differ (CB2 captain off ≠ all green)
3. **Smarter slave rules** — WRANGLER reads before write:
   - `FLEET_AVAILABLE.txt` compact line
   - `fleet/bus/puppy_outbox.txt`
   - heartbeats in `drop_pile/from_lester/`
   - then post ONE corrected line — no copy-paste lies
4. **Linux issue** — you're fixing with Puppy; WRANGLER tracks status, doesn't claim done until proof on Drive.

5. **NO FALSE PINGS** — Brian caught WRANGLER admitting fake heartbeats. Log: `WRANGLER_FALSE_PINGS_LOG.md`. If unsure post UNKNOWN, never WORKING.

## Proof

Post `drop_pile/from_lester/cb1_heartbeat.md` with:
```
lester6: WRANGLER — pulse fresh · fleet counts honest
last_order: WRANGLER smarter (Brian)
```

Brian stays on design desk. Execute on CB1.
