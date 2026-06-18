# PUPPY — working devices board

**From:** Uncle (Brian queue)  
**To:** Puppy Cursor on **puppy64**  
**Word:** **PUPPY**  
**Output:** `MyDrive/fleet/PUPPY_DEVICES.txt`

Daddy keeps **`fleet/FLEET_AVAILABLE.txt`** (fleet-wide design board).  
You keep **`fleet/PUPPY_DEVICES.txt`** — what is actually working **on this box**.

---

## Paste in Puppy Cursor

```
PUPPY — read drop_pile/to_puppy/PUPPY_DEVICES_BOARD.md. Post fleet/PUPPY_DEVICES.txt today.
```

---

## What to list (honest counts)

| Section | Include |
|---------|---------|
| **Machine** | hostname, LAN IP, Tailscale IP if up |
| **Services** | :8002 baseball, :8765 jailbreak, mesh radio, cloudflare — RUNNING / DOWN |
| **Processes** | one line each with port + proof (curl or ss) |
| **Slaves** | PLATE ack in `lester6_to_puppy.md` — PASS / FAIL |
| **Blockers** | one line each |

Use **RUNNING / DOWN / UNKNOWN**. Stale outbox ≠ working.

---

## Template (overwrite `fleet/PUPPY_DEVICES.txt`)

```
PUPPY DEVICES — working on puppy64
Updated: <ISO>
Hostname: puppy64
Posted by: Puppy Cursor

MACHINE
  hostname: puppy64
  lan_ip: <192.168.x.x>
  tailscale: <100.x.x.x or DOWN>

SERVICES (N up / M down)
  baseball :8002     RUNNING|DOWN  url: http://<lan>:8002
  jailbreak :8765    RUNNING|DOWN  url: http://<lan>:8765
  mesh_radio         RUNNING|DOWN
  cloudflare tunnel  RUNNING|DOWN  url: ...

SLAVES
  PLATE Chrome       PASS|FAIL  proof: lester6_to_puppy.md

BLOCKERS
  (none | list)

PROOF
  puppy_outbox.txt refreshed today: yes|no
  ss -tlnp | grep -E '8002|8765': (paste one line)
```

---

## After post

1. Refresh **`fleet/bus/puppy_outbox.txt`** — `hostname: puppy64`
2. Mark queue job **`puppy-devices-board`** done:
   ```bash
   python3 ~/.stan/brian_os.py process
   ```
3. Append **`mac_inbox.txt`**:
   ```
   --- from: puppy | devices-board | <time> ---
   PUPPY_DEVICES.txt posted — Uncle sync next.
   ```

Uncle pulls this file next (queue job on CB1).
