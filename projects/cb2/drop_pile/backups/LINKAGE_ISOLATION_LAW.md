# Linkage isolation law — learned on CB1, proven on CB2

**Updated:** 2026-06-14  
**Problem:** One computer brought the others down. CB1 fixed it when CB1 was first Daddy. CB2 blackout repeated the lesson harder.

---

## What "linkage" means

A **shared dependency** where one box failing looks like everyone failed:

| Linkage | CB1 symptom | CB2 symptom (Jun 14) |
|---------|-------------|----------------------|
| Quick tunnel URL | Reboot radio → all phones 1033 | Same — stale ROVER bookmark |
| False heartbeat | Slave says `cursor: live` when Linux dead | BEACON 18:01 ack while CAPTN gone since 17:29 |
| Queue cascade | One stale job re-run on wrong host | brian_queue puppy jobs from penguin |
| Drive as live bus | Puppy waits for CB2 proof that never comes | 5h blackout — no sync, no projects |
| Power coupling | Uncle hibernates → WRANGLER stale | Garage plug → whole CB black |

---

## Isolation rules (fleet law)

### 1. URLs are not permanent unless named

- **Baseball / Daddy:** named Cloudflare token → fixed hostname
- **Mesh radio / ROVER:** quick tunnel → **new URL every reboot**
- **Fix:** `fleet/MESH_RADIO_URL.txt` is canonical. Delete old Home Screen icons. Say **1033** not "radio broken."

### 2. Heartbeats are claims, not proof

- Chrome slave `cursor: live` ≠ Linux running
- **Pass** = today's plain `.md` + CAPTN ping + service HTTP 200
- Never chain actions: "BEACON said live so start tunnel on Puppy"

### 3. Each box boots alone

Every machine must restore from Drive backup **without** needing another machine up:

| Box | Boot artifact |
|-----|---------------|
| CB2 | `drop_pile/backups/team_project_*/` |
| puppy64 | `drop_pile/backups/puppy_wipe_20260614/` |
| CB1 | `drop_pile/to_cursor/UNCLE_FIX_ONE_PASTE.md` |

### 4. Execute stays local

- CAPTN **delegates** by default (`DADDY_DELEGATE_CONTRACT.txt`)
- Rebooting CB2 radio must not trigger Puppy job retries from CB2 shell
- Puppy cannot SSH from Crostini — don't queue SSH from CB2 expecting it to run here

### 5. Power is per-box

- Wall power on CB1 ≠ CB2 powered
- Plug-in can **hang** EC — treat black screen as hardware, not "Daddy hibernating"
- `keep_awake` on one box doesn't keep siblings awake

### 6. No soul swap without backup

Before CB1 ↔ CB2 role swap:
1. Run `~/.stan/team_backup.sh` on live box
2. Confirm `fleet/TEAM_BACKUP_OK.txt` updated
3. Then swap roles

---

## What CB1 fixed (carry forward)

- Separated **stable Daddy URL** from **expiring radio URL**
- Stopped treating Drive acks as cross-machine execute triggers
- Uncle/CB1 can run Chrome-only while Linux deleted — fleet continues on Puppy + Drive

---

## What CB2 added (Jun 14)

- Full host blackout ≠ Linux sleep — Gemini can't diagnose EC/firmware
- Team backup must include **local** `.stan` + **agent transcripts** (Drive alone misses ~50h)
- Puppy loyalty ≠ access — backup is how he reaches projects when CB2 is black
