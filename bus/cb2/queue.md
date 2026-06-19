# DADDY QUEUE — Opus keeps this stocked. Work TOP-DOWN. Each task is safe + must NOT break what already works.
# Rule: do the top unfinished task -> verify it -> AUDIO-confirm + tell Brian -> mark [x] -> take the next.
# If a task conflicts with something that already works, STOP and tell Brian (don't just do it).
# You can't push, so you can't check items off in git — tell Brian which you finished; Opus marks them here.

## QUEUE (top = do first)
- [ ] 1. DRIVE-MIRROR GHOST: is a Google Drive mirror live on your box?
        check:  mount | grep -i -E 'google|drive|gdrive|/mnt/shared' ; ls /mnt/shared/GoogleDrive 2>/dev/null
        If it's mounted/syncing -> STOP the sync (unmount / disable the daemon). DO NOT delete files — just kill the live mirror.
        Report what you found to Brian. (This is the split-brain risk — git is the only truth.)
- [ ] 2. GEORGE SUBDOMAIN: add ingress for george.hitme.dev (same port as /george), restart cloudflared.
        Try: cloudflared tunnel route dns <tunnel> george.hitme.dev. If it needs account login -> STOP, tell Brian.
- [ ] 3. GEORGE MEMORY: restore the 6-turn memory / GEORGE_MEMORY self-update on /george (voice in/out already works).
- [ ] 4. SITE STAYS UP: confirm cloudflared + the origin server are enabled as services (systemctl is-enabled). Report.
- [ ] 5. GHOST SWEEP: any OLD loops/processes running? (cpt / bunny / gemini / old wake-loops)
        check:  ps aux | grep -iE 'cpt|bunny|gemini|wake|loop' | grep -v grep
        Report findings to Brian. Don't kill anything you're unsure about — ask first.
- [ ] 6. USE THE ONE SHARED RAIL (de-dup — don't keep your own copy):
        echo cb2 > ~/.fleet-name
        ln -sf ~/fleet/scripts/statusline.sh ~/.cursor/statusline.sh
        (Now your rail = the same script as cb1/puppy. One rail, machine-aware.)

## DONE (Opus marks here as Brian relays completions)
- (none yet)
