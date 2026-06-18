# PUPPY — Network Delegate (CAPTN order)

**From:** CAPTN (Brian design desk)  
**To:** Puppy Cursor + PLATE Chrome on puppy64  
**Date:** 2026-06-15  
**Word:** **PUPPY** (Cursor) · **PLATE** (Chrome slave)

Brian: *"Let's get puppy to delegate. He is also our network man. Phone probably next but I hate testing."*

---

## Your role now

| You own | CAPTN / CB2 does NOT |
|---------|----------------------|
| **Network** — mesh radio :8765, tunnels, Tailscale, PUBLIC URLs | Run servers on CB2 (design desk only) |
| **Execute** — queue jobs, Flask apps, cloudflared on puppy64 | SSH to you (impossible) |
| **Proof on Drive** — outbox, heartbeats, acks | Phone QA with Brian |

**Phone:** Puppy verifies network. Brian does **not** test unless he asks. See `PUPPY_PARKED_PHONE_P1.md`.

---

## Paste — Puppy Cursor

```
PUPPY — read drop_pile/to_puppy/PUPPY_DELEGATE_NETWORK_NOW.md.
You are network delegate + execute. CAPTN delegates only.
Post puppy_outbox hostname puppy64. Phone self-test only — do not wake Brian.
```

## Paste — Puppy Chrome (PLATE)

```
PLATE — read lester6_puppy_slave.md + ACK_FILE_LAW.md.
Overwrite lester6_to_puppy.md mode:slave today. Say: PLATE ready.
Network orders in drop_pile/to_puppy/ — refresh ack every session.
```

---

## Sprint (order — stop when green)

### 0 — Link proof (still missing)
- [ ] `lester6_to_puppy.md` on Drive — mode: slave, today
- [ ] `puppy_outbox.txt` — **hostname: puppy64** (not penguin)
- [ ] `drop_pile/from_puppy/captn_link_ack.md` one line

### 1 — Mesh radio host (network man job #1)
Read: `MESH_RADIO_PUPPY_HOST.md`  
Copy from `drop_pile/to_puppy/mesh_radio/` or CB2 backup → `~/.stan/`  
Run `start_mesh_radio.sh` · listen `0.0.0.0:8765`  
Post Tailscale/LAN URL in outbox + `fleet/MESH_RADIO_URL.txt`

### 2 — Named tunnel / public URL (network man job #2)
Read: `DELEGATE_CLOUDFLARE.md`  
Keys: `lester/lester_keys.md` (Cloudflare token)  
Post **PUBLIC_URL** → `BRIAN_PHONE.txt` + outbox  
Goal: phones hit **puppy64**, not sleeping CB2

### 3 — Baseball / execute queue (when network green)
Read: `PUPPY_NOW.md` items 2–4 if not done  
Process `brian_queue.json` jobs assigned **puppy**

### 4 — Phone lane (Puppy self-test ONLY)
- [ ] curl mesh `/status` from puppy
- [ ] One line in `drop_pile/from_puppy/network_selftest.md` — PASS/FAIL
- [ ] **Do not** assign Brian Samsung/Moto tests until CAPTN says GO

---

## Done when (green list)

```
puppy64  ✓  PLATE + network delegate
mesh :8765  UP on puppy64
PUBLIC_URL  in BRIAN_PHONE.txt (puppy-hosted)
puppy_outbox  hostname puppy64
Brian testing  PARKED
```

Post board snippet to `drop_pile/from_puppy/PUPPY_NETWORK_REPORT.md`

---

## References

- `PUPPY_STANDING_LOOP.md` — every session
- `fleet/FLEET_AVAILABLE.txt` — honest status
- `fleet/GATES_LATER.txt` — keys in lester_keys OK for now
- GV SMS bridge stays on CB2 until puppy takes tunnel host

CAPTN reads outbox + report. Brian keeps designing.
