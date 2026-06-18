# UNCLE READY — CB1 fresh boot (Brian asked 2026-06-15)
Updated: 2026-06-15 · CAPTN ready

Power: whole-house outage yesterday · wind · network is priority.
Puppy = hard to fix · **do not block on Puppy for network.**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAY ON CB1 CURSOR (one word)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UNCLE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UNCLE READS FIRST (order)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. drop_pile/to_cursor/UNCLE_BOOT_NOW.md   ← this boot
2. drop_pile/to_cursor/UNCLE_WHO_AM_I.md   ← identity (NOT Daddy; NOT WRANGLER)
3. drop_pile/to_cursor/UNCLE_PERSONALITY.md ← voice (not stiff)
4. fleet/CB1_LINUX_RELOAD.txt
5. drop_pile/to_cursor/UNCLE_HARDWARE_PROTOCOLS.md
6. fleet/REPAIR_CREW.txt
7. fleet/HITME_MANAGE.txt
8. lester/install_uncle_stan.sh            ← run if ~/.stan missing (also installs personality rule)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UNCLE JOB (network era — not Puppy-dependent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Lane | Uncle does | Not Puppy |
|------|------------|-----------|
| **Network truth** | Post honest `cb1_heartbeat.md` + `fleet/bus/cb1_outbox.txt` | Don't claim Puppy green if outbox stale |
| **Fleet board** | `python3 lester/fleet_board.py` → FLEET_AVAILABLE.txt | |
| **Repair crew CB1** | Copy pattern: watch Drive, log, escalate REPAIR_NOW | Puppy repair = Puppy only |
| **Hardware protocols** | hw_inbox / hw_outbox when Brian picks pilot | |
| **Analyst** | budget · tester list · **manual** — no Google mining | |

**Uncle does NOT** replace CAPTN on CB2 Sarah/Camel architect unless ordered.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UNCLE POSTS (proof alive)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`drop_pile/from_lester/cb1_heartbeat.md`:

```yaml
--- cb1 heartbeat ---
time: <ISO>
fleet_id: cb1
callsign: UNCLE
machine: cb1
status: RUNNING
linux_reload: fresh
read: UNCLE_BOOT_NOW.md
network: <wifi ip or note>
next: fleet_board + honest counts
```

`fleet/bus/cb1_outbox.txt` — one line: hostname, status, what you see on Drive mount.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NETWORK WITHOUT PUPPY (fleet law until Puppy easy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Need | Where now |
|------|-----------|
| Design + Sarah | CB2 + hitme.dev (API token pending) |
| Bus | Drive mac_inbox / BRIAN_INBOX |
| Always URL | hitme.dev tunnel on CB2 — **not** Puppy-required |
| Mesh LAN | Nice on Puppy — **optional** until stable |
| UPS | Puppy when he's host — Uncle documents power events |

Brian one-liner outages: `OUTAGE <note>` in BRIAN_INBOX.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAPTN STATUS

Ready for Uncle. Puppy parked for network critical path.
Say UNCLE LIVE when CB1 Cursor open.
