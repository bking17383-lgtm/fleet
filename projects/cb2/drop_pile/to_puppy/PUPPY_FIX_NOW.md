# PUPPY FIX — logic bugs found (Gem scan 2026-06-16)

**Brian on puppy:** run ONE line in Linux terminal:

```bash
bash ~/GoogleDrive/MyDrive/PUPPY_FIX.sh
```

Or if Drive mounts at crostini path:

```bash
bash /mnt/home/google_drive/MyDrive/PUPPY_FIX.sh
```

---

## What was broken

| Bug | Symptom |
|-----|---------|
| **`lester/local_slave.py` missing on Drive** | `python3 ~/.stan/local_slave.py NET` → file not found |
| **SLAVE_BOOT copied from missing path** | Reload did nothing · silent `|| true` |
| **Mirror inbox** | Agent reads `/mnt/home/lester6/mac_inbox.txt` (stale) not `fleet/bus/` |
| **ONE_COMMAND `set -e`** | Any flask/Drive hiccup → whole script dies |
| **Old transcript_sink.py kept** | Reload skipped rewrite · broken sink persisted |
| **Wrong outbox path (old)** | Posted root `puppy_outbox.txt` — CPT never saw it |

---

## After PUPPY_FIX.sh

1. Refresh `drop_pile/from_lester/puppy_heartbeat.md` (today's time)
2. Cursor word: **NET**
3. CPT should see fresh `fleet/bus/puppy_outbox.txt` mtime

---

## Still wrong?

Post to `fleet/bus/puppy_needs.txt`:
```
error=<paste terminal output>
drive_path=<path from script>
```

Do NOT read lester6 mirror paths.
