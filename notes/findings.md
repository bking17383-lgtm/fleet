# cb1 agent notebook  (cb1 writes only — single writer, no split-brain)
Persisted in the fleet so context survives across sessions. Read this first.

## 2026-06-18 — GHOST HUNT (evidence from audits)

### cb1 = CLEAN
No old loops, no Drive, no rclone, no ghosts. (fresh auditor box.)

### cb2 (daddy) = GHOSTS CONFIRMED. The OLD system is FULLY RUNNING next to the new fleet.
Still-live old machinery (THIS is the split-brain, not a theory):
- CRON every 2 min:  ~/.stan/url_keeper.sh   (+ @reboot)   -> keeps old tunnel/URL alive
- PROC:  ~/.stan/drive_watch.sh                              -> OLD Google-Drive "bus" watcher
- PROC:  ~/.stan/cpt_daddy_ready_loop.py watch               -> old captain loop
- PROC:  python3 /mnt/shared/GoogleDrive/MyDrive/fleet/bootstrap/box_slave_loop.py daddy
         ^^^ THE OLD SLAVE LOOP — runs a SECOND "fleet" that lives on GOOGLE DRIVE
- PROC:  tesseract ... /GoogleDrive/MyDrive/convert_inbox/*.jpg   -> old OCR/convert pipeline
- ~/.stan/         = the whole old system's home (large)
- ~/.daddy_slave_state.json, ~/GoogleDrive, ~/.cloudflared

### ROOT CAUSE OF THE SPLIT-BRAIN (evidence-backed):
There are TWO fleets running at once:
  (A) NEW = git repo  github:bking17383-lgtm/fleet    (what we built tonight)
  (B) OLD = /mnt/shared/GoogleDrive/MyDrive/fleet      (on Google Drive, still served by box_slave_loop.py)
Daddy is STILL serving the OLD Drive fleet. Adding the git fleet did NOT remove the old one.
=> Mirrors persist until the old loops on cb2 are stopped.

### KILL LIST (cb2 — only with Brian's go; archive, don't delete):
- crontab -r the url_keeper lines
- stop/disable: drive_watch.sh, cpt_daddy_ready_loop.py, box_slave_loop.py
- retire ~/.stan/ (archive first)
- stop writing to /MyDrive/fleet (old source of truth)

### puppy = audit pending (likely similar ghosts)
