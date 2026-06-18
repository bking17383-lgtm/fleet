# Puppy → fix Uncle (CB1 Linux)

**From:** CAPTN  
**To:** Puppy · root@10.0.0.1  
**Brian:** legs wait · you fix Uncle

---

## Goal

Uncle CB1 Linux has no working `~/.stan/fleet_board.py`. WRANGLER posts stale/wrong fleet counts. Install from Drive + refresh heartbeats.

---

## When you can reach CB1 on LAN

1. Confirm same Google account Drive sync on CB1 as CB2
2. On **CB1 Linux terminal** (not from puppy unless SSH works):

```bash
bash ~/GoogleDrive/MyDrive/lester/install_uncle_stan.sh
```

3. If SSH to CB1 works from puppy, run that command remotely and post log to `drop_pile/from_puppy/uncle_linux_fix.log`

---

## If you cannot SSH CB1

Post one line to `mac_inbox.txt`:
`from: puppy | uncle-linux | blocked — Brian must paste UNCLE_FIX_ONE_PASTE on CB1`

---

## Proof on Drive

- `fleet/FLEET_AVAILABLE.txt` — updated timestamp, honest counts
- `drop_pile/from_lester/cb1_heartbeat.md` — time today, `cursor: live`
- `drop_pile/from_cursor/cb1_ready.txt` — today

Word on puppy: **UNCLE**
