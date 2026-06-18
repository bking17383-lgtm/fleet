# UNCLE — sync Puppy devices board

**From:** Brian queue  
**To:** Uncle Cursor on **CB1**  
**Prerequisite:** `MyDrive/fleet/PUPPY_DEVICES.txt` exists (Puppy job done)  
**Word:** **UNCLE**

---

## Paste in Uncle Cursor

```
UNCLE — read drop_pile/to_cursor/UNCLE_SYNC_PUPPY_DEVICES.md. Sync PUPPY_DEVICES into fleet board.
```

---

## Steps

1. Read **`fleet/PUPPY_DEVICES.txt`**
2. If missing or older than today → note blocker in `uncle_status.md`; stop
3. Merge puppy64 truth into **`fleet/FLEET_AVAILABLE.txt`**:
   - Update **puppy64** computer line (ON/OFF + proof)
   - Update **Puppy Cursor** + **PLATE** agent lines from PUPPY_DEVICES
   - Add **PARTS** lines for each RUNNING/DOWN service on puppy64
4. Post mirror for CB1 quick read:
   **`drop_pile/from_cursor/puppy_devices_on_uncle.md`** — copy of PUPPY_DEVICES + sync time
5. Append **`mac_inbox.txt`**:
   ```
   --- from: uncle | puppy-devices-sync | <time> ---
   PUPPY_DEVICES synced into FLEET_AVAILABLE + puppy_devices_on_uncle.md
   ```
6. Mark queue job **`uncle-sync-puppy-devices`** done (if handler runs)

---

## Success

Brian can say **DESK** and see puppy64 services without SSH to 10.0.0.1.
