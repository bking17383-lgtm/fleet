# Uncle → Puppy clean report

**Time:** 2026-06-16T00:16:00-07:00  
**From:** Uncle (CB2 scan while Brian heartbeats puppy)  
**Word:** NET

## Found on network

| Host | IP | Proof |
|------|-----|-------|
| puppy64 | 192.168.1.4 | :8002 baseball UP · :80 nginx UP |
| CB2 penguin | 100.115.92.26 | this scan |
| CB1 Uncle | not seen | no ping on 192.168.1.x except .1 .4 .16 .104 |

## Mirror bug (root cause)

`lester/PUPPY_ONE_COMMAND.sh` wrote to **wrong file**:

- Wrote: `MyDrive/puppy_outbox.txt` (nobody reads)
- Team reads: `MyDrive/fleet/bus/puppy_outbox.txt`
- Used `hostname: $(hostname)` → could post **penguin** on wrong box

Also: agents reading `/mnt/home/lester6/mac_inbox.txt` see stale mirror, not fleet bus.

## Fixed on Drive (Uncle)

1. `PUPPY_ONE_COMMAND.sh` → writes `fleet/bus/puppy_outbox.txt` · hostname **puppy64**
2. `fleet/bus/puppy_outbox.txt` → NET clean line + scan truth
3. `fleet/bus/puppy_needs.txt` → mirror + path guidance

## Puppy execute (Brian heartbeat then one command)

```bash
bash ~/GoogleDrive/MyDrive/lester/PUPPY_ONE_COMMAND.sh
```

Then refresh `puppy_heartbeat.md` on Drive.

## Team link

When puppy re-runs ONE_COMMAND, CPT sees fresh mtime on `fleet/bus/puppy_outbox.txt` → NET bar goes green.
