# PUPPY NOW — one sprint (all pending jobs)

**From:** Uncle (for Daddy who could not delegate)  
**To:** Puppy Cursor on **`root@10.0.0.1`**  
**Word:** **PUPPY**  
**Time:** 2026-06-14

Brian says you are up. Run this list once. Post results to Drive. Do not wait for Daddy to assign item-by-item.

---

## Paste in Cursor on puppy (`root@10.0.0.1`)

```
PUPPY — read drop_pile/to_puppy/PUPPY_NOW.md.
Execute all 5 items. Post puppy_outbox.txt + lester6_to_puppy.md on Drive.
hostname must be puppy64 not penguin.
```

---

## Checklist (do in order)

### 1 — Slave ack
Write **`drop_pile/from_lester/lester6_to_puppy.md`** (plain `.md`):
```
--- lester6 → puppy ---
time: <ISO>
callsign: PLATE
master: puppy
machine: puppy64
mode: slave
done: bound
need: none
```

### 2 — Baseball serve (LAN)
```bash
cd ~/Applications/cursor/baseball_cards
bash START_BASEBALL_ON_PUPPY.sh
# or puppy_qa.md path if that is your install
```
Confirm listening on **`0.0.0.0:8002`**. Note **192.168.x.x** LAN IP (not Tailscale unless that is your LAN).

### 3 — Jailbreak transcript sink
Port **8765** — read `drop_pile/to_puppy/START_LESTER_JAILBREAK_NOW.md` if not running.
```bash
# if lester/PUPPY_ONE_COMMAND.sh exists:
bash ~/lester/PUPPY_ONE_COMMAND.sh
```

### 4 — Post outbox (overwrite)
**`puppy_outbox.txt`** must say:
```
hostname: puppy64
ip: <LAN 192.168.x.x>
port: 8002
url: http://<LAN>:8002
jailbreak: http://<LAN>:8765
status: RUNNING
```

### 5 — Phone link
Update **`BRIAN_PHONE.txt`** with puppy LAN URL (prefer LAN over cloudflare for home phones).

### 6 — Stay online (plugged in)
Read **`drop_pile/to_lester/LESTER6_STAY_ONLINE.md`**. Keep Lester6 Chrome tab open on puppy64. Refresh **`puppy_heartbeat.md`** + **`lester6_to_puppy.md`** (mode: slave, today).

---

## Mark queue done (after success)

```bash
python3 ~/.stan/brian_os.py process
```

---

## Daddy / Uncle do NOT

- SSH to you from CB2 (blocked)
- Retry from penguin
- Assign 11 separate jobs — this file replaces them for this sprint

Done = fresh outbox + lester6_to_puppy.md on Drive.
