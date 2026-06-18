# Puppy — Uncle fresh boot (CB1 on LAN)

**From:** CAPTN CB2  
**Brian:** rebooting Uncle chromebook (CB1)  
**Word:** UNCLE

---

## Your job when CB1 is on home WiFi

1. Confirm you see fresh files on Drive (not required before try):
   - `drop_pile/from_cursor/cb1_ready.txt` — today
   - `drop_pile/from_lester/cb1_heartbeat.md` — today

2. **If SSH to CB1 works** (Brian reported root@10.0.0.1 or CB1 LAN IP):

```bash
ssh root@<CB1_LAN_IP> 'bash ~/GoogleDrive/MyDrive/lester/install_uncle_stan.sh' 2>&1 | tee /tmp/uncle_fix.log
```

Post log to: `drop_pile/from_puppy/uncle_linux_fix.log`

3. **If SSH fails** — one line to `fleet/bus/mac_inbox.txt`:
   `from: puppy | uncle-fresh-boot | blocked — Brian paste FIX on CB1 Cursor`

4. **Do NOT** claim Uncle PASS until:
   - `fleet/FLEET_AVAILABLE.txt` refreshed today
   - `cb1_heartbeat` cursor live + WRANGLER pulse fresh
   - `puppy_outbox.txt` hostname **puppy64** (overwrite stale penguin)

5. PLATE: hold execute until Uncle PASS unless Brian says otherwise.

---

## CB2 eyes (for Brian)

Brian may SNAP CB1 screen from Samsung RADIO — CAPTN on CB2 reads `eyes/inbox/`.
No rover live stream. SNAP + text only.

Post puppy status to `puppy_outbox.txt` when you start this job.
