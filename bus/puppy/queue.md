# PUPPY QUEUE — Opus keeps this stocked. Work TOP-DOWN. LIGHT tasks only (weak hardware).
# Rule: do the top unfinished task -> verify it -> tell Brian -> take the next.
# If a task conflicts with something that already works, STOP and tell Brian (don't just do it).
# You can't push, so you can't check items off in git — tell Brian which you finished; Opus marks them here.
# Your lane = LIGHT watchdog/QA. Daddy does the heavy creative build; you keep watch.

## QUEUE (top = do first)
- [ ] 1. SELF HEALTH FIRST (every boot): df -h .  /  free -h  /  du -sh ~/fleet  /  ps aux --sort=-%mem | head -6
        Report any problem to Brian BEFORE other work. Low disk or a huge repo = the bloat that froze you — say so.
- [ ] 2. SITE PATH-TEST (light, no account): curl -s -o /dev/null -w '%{http_code}' each known hitme.dev path
        (e.g. /, /george, /hope when live). Report any path that is NOT 200 to Brian. This is your main QA value.
- [ ] 3. GHOST SWEEP: any OLD loops/processes running?  ps aux | grep -iE 'cpt|bunny|gemini|wake|loop' | grep -v grep
        Report findings to Brian. Don't kill anything you're unsure about — ask first.
- [ ] 4. USE THE ONE SHARED RAIL (de-dup — don't keep your own copy):
        echo puppy > ~/.fleet-name
        ln -sf ~/fleet/scripts/statusline.sh ~/.cursor/statusline.sh
        (Now your rail = the same script as cb1/cb2. One rail, machine-aware.)

## WAITING ON
- A real assigned task from Brian (this queue is the "useful" slot, ready to receive one).
- Brian removing puppy's GitHub write key = isolation becomes fully enforced.

## DONE (Opus marks here as Brian relays completions)
- (none yet)
