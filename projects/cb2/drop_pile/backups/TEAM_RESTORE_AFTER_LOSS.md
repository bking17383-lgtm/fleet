# Team restore — after CB death / soul swap / wipe

**Use when:** one box goes black, Puppy can't reach projects, or Brian considers CB1↔CB2 swap.

**Latest backup folder:** see `fleet/TEAM_BACKUP_OK.txt`

---

## One word per machine

| Machine | Say | Reads |
|---------|-----|-------|
| **CB2 CAPTN** | `RESTORE` | this file + backup folder |
| **puppy64 PLATE** | `PUPPY` | `puppy_wipe_20260614/` OR team backup drive/lester |
| **CB1 Uncle** | `UNCLE` | `drop_pile/to_cursor/UNCLE_FIX_ONE_PASTE.md` |

---

## Restore priority (CB2 — new Daddy)

1. **Drive is king** — if Google Drive sync works, live `fleet/` + `drop_pile/` may already be current. Backup = point-in-time proof.

2. **Local code** — copy from backup:
   ```
   backup/local/stan/*     → ~/.stan/
   backup/local/lester/*   → ~/lester/
   backup/local/cursor/skills-cursor → ~/.cursor/skills-cursor/
   ```

3. **Secrets** — copy `backup/local/secrets/cloudflare.env` → `~/.stan/cloudflare.env` (never paste in chat)

4. **Agent memory** — `backup/local/cursor/agent-transcripts/` is the ~50h session archive. Reference only; don't overwrite live transcripts.

5. **Services** — after files land:
   ```
   ~/.stan/start_mesh_radio.sh
   ~/.stan/start_mesh_radio_tunnel.sh
   ```
   Then refresh `fleet/MESH_RADIO_URL.txt` — old phone bookmarks → 1033.

6. **Verify** — `free -h`, `df -h /`, BEACON heartbeat, Puppy outbox.

---

## Restore priority (Puppy)

1. `drop_pile/backups/puppy_wipe_20260614/PUPPY_RESTORE_AFTER_WIPE.md`
2. Team backup `drive/lester/` + `drive/drop_pile/to_puppy/` for anything newer

---

## Do not delete backup until

- Fresh `cb2_heartbeat.md` + `puppy_outbox.txt` today
- CAPTN confirms mesh_radio 200
- Brian says OK

---

## Linkage rule (CB1 lesson)

**One box must not kill the fleet.** Read `LINKAGE_ISOLATION_LAW.md` in the backup folder.

Quick version:
- Named tunnel for stable URLs; quick tunnel reboot ≠ fleet reboot
- Drive files are async — never assume another box is live because a heartbeat says so
- Each machine must boot alone from backup without needing CB2
