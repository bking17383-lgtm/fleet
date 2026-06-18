# NET (puppy64) — PACK BEFORE WIPE

**Priority:** 1 · **Word when done:** PACKED

Brian + CPT are resetting the fleet. You are **NET** in the new 3-agent model.
Before any wipe: save useful files. No new features.

## Do this now

```bash
bash MyDrive/lester/pack_before_wipe.sh
```

(Puppy Drive path is often `/mnt/home/google_drive/MyDrive/` — find `fleet/` folder first.)

## Worth keeping if you see them locally

- `~/.stan/mesh_radio.py` · tunnel scripts · `start_mesh_radio*.sh`
- `~/lester/` — camel, fleet_board, run scripts
- Any working Cloudflare / Tailscale notes (not secrets in chat)

## Do NOT do

- Start mesh "to prove green"
- Write heartbeat theater
- Lester6 ack files

## After PACK

One line in `fleet/bus/puppy_outbox.txt`:

```
PACKED — hostname puppy64 — ready for wipe — <time>
```

Wait at keyboard for CPT wipe/reinstall order.

Guide: `fleet/FRESH_FLEET.txt`
