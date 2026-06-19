# DADDY QUEUE — Opus keeps this stocked. Work TOP-DOWN. Each task is safe + must NOT break what already works.
# Rule: do the top unfinished task -> verify it -> AUDIO-confirm + tell Brian -> mark [x] -> take the next.
# If a task conflicts with something that already works, STOP and tell Brian (don't just do it).
# You can't push, so you can't check items off in git — tell Brian which you finished; Opus marks them here.

## QUEUE (top = do first)
- [ ] 0b. MOBILE JANE (Brian's order 2026-06-19 ~07:53, SOON): host a phone-accessible "Jane" voice page on a
        hitme.dev path (e.g. /jane), reusing the george web+voice stack. Full spec: bus/jane/MOBILE_JANE_SPEC.md.
        Done-test: Brian opens hitme.dev/jane on his phone and talks to Jane. Report the URL.
- [~] 0. BASEBALL CARDS OF HOPE (Brian's order 2026-06-19 ~04:15, TOP NOW): slave scrubs a person's Facebook
        (face + facts; creds LOCAL never git). Reuse dealbreaker card engine (face+stat-bars+flip). Make ~10 cards =
        their face + HOPEFUL/aspirational stats (encouraging, NOT satire). Serve on a hitme.dev path. Report URL.
        Done-test: live path shows ~10 cards with real face + hope stats.
- [x] 1. DRIVE-MIRROR GHOST — DONE (2026-06-19, Daddy reported via email relay):
        Finding: Google Drive mirror = ARCHIVE ONLY, no live sync daemon running. No split-brain risk. Nothing to stop.
- [~] 2. GEORGE SUBDOMAIN — BLOCKED (awaiting Brian): adding ingress + `cloudflared tunnel route dns` for
        george.hitme.dev needs a Cloudflare ORIGIN CERT / account login. Correctly STOPPED per the task rule.
        -> Brian decision needed (his Cloudflare account). Until then /george PATH already works (200); use that.
- [~] 3. GEORGE MEMORY (IN PROGRESS, assigned 2026-06-19 ~03:58): restore the 6-turn memory / GEORGE_MEMORY self-update on /george (voice in/out already works).
        NOTE (2026-06-19): Daddy reports Polly TTS = 503, needs aws_sandbox.env (AWS creds = a SECRET). Text/memory logic
        can be restored without it, but spoken output stays 503 until Brian provides the AWS key. Surface, don't guess.
- [ ] 4. SITE STAYS UP: confirm cloudflared + the origin server are enabled as services (systemctl is-enabled). Report.
- [ ] 5. GHOST SWEEP: any OLD loops/processes running? (cpt / bunny / gemini / old wake-loops)
        check:  ps aux | grep -iE 'cpt|bunny|gemini|wake|loop' | grep -v grep
        Report findings to Brian. Don't kill anything you're unsure about — ask first.
- [ ] 6. USE THE ONE SHARED RAIL (de-dup — don't keep your own copy):
        echo cb2 > ~/.fleet-name
        ln -sf ~/fleet/scripts/statusline.sh ~/.cursor/statusline.sh
        (Now your rail = the same script as cb1/puppy. One rail, machine-aware.)

## DONE (Opus marks here as Brian relays completions)
- 2026-06-19: Task 1 (Drive-mirror ghost) — confirmed archive-only, no sync daemon = no split-brain. Accepted.
