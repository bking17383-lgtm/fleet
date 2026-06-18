# AFK / night stack — Brian away

**Daddy (T3) policy.** Slicer on hold unless Brian unblocks.

---

## Who runs while Brian sleeps

| Machine | Run | Do NOT |
|---------|-----|--------|
| **puppy64** | Queue watcher, baseball LAN serve, agent mail poll | Mass video batch jobs |
| **Chromebook** | Keep awake only if tunnel fallback needed | Extra Lester, slicer, new Cursors |
| **Gemini Live** | Slave mode: sync to Drive only | Design without `drop_pile/` output |

---

## puppy64 — start before AFK

```bash
# Queue + status (every 20s)
nohup python3 ~/.stan/brian_os.py watch 20 >> ~/brian_os_watch.log 2>&1 &

# Agent mail (puppy_outbox ↔ mac_inbox)
nohup python3 ~/.stan/agent_mail.py watch 8 >> ~/agent_mail.log 2>&1 &

# Baseball phone (priority over slicer while on hold)
bash ~/GoogleDrive/MyDrive/lester/START_BASEBALL_ON_PUPPY.sh
python3 ~/.stan/brian_os.py process
```

Post URL → `puppy_outbox.txt` + `BRIAN_PHONE.txt` on Drive.

---

## Chromebook — minimal AFK

- **Terminal 2 / 3:** close or leave idle (no marathon chats)
- **Optional tunnel:** only if puppy LAN down — costs RAM + must stay awake
- **Do not start** second Lester (`~/lester/app.py`) — RAM ~166MB free

---

## Gemini Live slave (Chrome)

Allowed outputs only:

1. `drop_pile/from_lester/*.md`
2. `update_brief` → brief.json (if tool wired)
3. `queue_job` with `assign_to`

**30TB rule:** Gemini cannot browse Drive mount. It must **export plain .md/.txt** to `drop_pile/`. Linux agents read the mount at `/mnt/shared/GoogleDrive/` or `~/GoogleDrive/MyDrive/`.

---

## Morning check (Brian or T3)

1. `BRIAN_STATUS.txt`
2. `brian_queue.json` — any `failed`?
3. `puppy_outbox.txt` — LAN URL live?
4. `drop_pile/from_cursor/` — T2 memo if analysis ran
