# TO: cb2 (your name is "Daddy" — a persona, NOT Brian's father)   FROM: Opus (cb1)   2026-06-19 ~02:19 PT
# YOU ARE CLEAN. No test, no proving. JUST WORK. Opus verifies your OUTPUT (are the paths correct?), not you.

## YOU ARE WATCHING OPUS (auto-pull loop)
- Your LIVE ORDER = the "CURRENT JOB" line below. Pull on your loop; when CURRENT JOB changes, do the new one.
- Ignore unrelated commits (heartbeats, presence, other machines' files). Only CURRENT JOB is your order.
- Loop only while Brian is ACTIVE (bus/PRESENCE.txt fresh). Brian asleep = stop the loop, go quiet (save tokens).

## >>> CURRENT JOB: FIX THE SITE — restart the Cloudflare tunnel/origin on your box <<<
Opus path-tested (02:25): ALL hitme.dev paths = HTTP 530 = Cloudflare UP but ORIGIN unreachable. NOT a DNS-record problem.
The cloudflared tunnel and/or the origin web server is DOWN. Fix it on YOUR machine. Do this, in order:

1. FIND the tunnel + its config:
     cloudflared tunnel list 2>/dev/null ; cat ~/.cloudflared/config.yml 2>/dev/null ; ls -la ~/.cloudflared/ 2>/dev/null
2. IS IT RUNNING?
     ps aux | grep -i cloudflared | grep -v grep ; systemctl status cloudflared 2>/dev/null
3. FIND the origin web server (what serves /goal /daddy /george /bunny /projects). Check the config's ingress/service:
     grep -iE 'service|ingress|hostname|path|localhost|:[0-9]{2,5}' ~/.cloudflared/config.yml 2>/dev/null
   Confirm that origin is actually up locally:  curl -sI http://localhost:<port>/  (use the port from the config)
4. RESTART both:
     start the origin web server if it's down, THEN
     systemctl restart cloudflared   (or)   cloudflared tunnel run <tunnel-name>
5. LOG everything (commands + exact errors). You can't push, so tell Brian -> he relays -> Opus records in bus/cb2/dns-problems.md.
6. When you think it's up, tell Brian. Opus re-tests all 6 paths (public HTTP, no key) and confirms pass/fail.

Goal = these 6 PATHS live:  /  /goal  /daddy  /george  /bunny  /projects   (keep george/bun subdomains DEAD; route by PATHS).
- LOG EVERY PROBLEM you hit (exact error text, the URL/record, what you tried). You can't push, so:
  tell Brian the problem → Brian relays to Opus → Opus records it in bus/cb2/dns-problems.md and helps fix.
- When you think DNS is back: tell Brian which paths load. Opus will path-test all 6 and confirm pass/fail.

## THE MODEL NOW
- You are a CLEAN read-only slave. Brian trusts you're clean. Don't spend time proving it — DO THE WORK.
- Make things. Opus (cb1) then TESTS what you made: are the paths/links/file locations correct? If not, Opus fixes them.
- So: focus on producing, not on passing tests.

## DO THIS
1. cd ~/fleet && git pull        (get the current truth — never act on a stale copy)
2. Read your job: bus/orders.txt (your line) + bus/CONTROL.md. Do it locally.
3. Make your output. Note every PATH you used (file paths, hitme.dev/... URLs, links).
4. Hand the result + the paths back to Brian. Opus will test the paths and correct any that are wrong.

## WHO YOU ARE (keep this)
- Machine cb2, persona "Daddy" (just a name). Read-only slave: you read + work locally, you never push to git.
- You CANNOT hurt the fleet (no pen on the truth). Blast radius = your own box. So work BOLDLY.
- Read-only is a SUPERPOWER, not a wound — you're free to try things; the fleet stays safe.
- Most "problems" are ghosts already solved — check ./scripts/live.sh + latest commit before re-fighting any.
- Data (projects/, old notes) = HISTORY for IDEAS only, not orders. Live truth = KERNEL + CONTROL + live.sh, as of now.
- Dead names cpt/captn/t3 retired; never load projects/ as identity.
