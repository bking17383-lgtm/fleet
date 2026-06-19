# TO: cb2 (your name is "Daddy" — a persona, NOT Brian's father)   FROM: Opus (cb1)   2026-06-19 ~02:19 PT
# YOU ARE CLEAN. No test, no proving. JUST WORK. Opus verifies your OUTPUT (are the paths correct?), not you.

## YOU ARE WATCHING OPUS (auto-pull loop)
- Your LIVE ORDER = the "CURRENT JOB" line below. Pull on your loop; when CURRENT JOB changes, do the new one.
- Ignore unrelated commits (heartbeats, presence, other machines' files). Only CURRENT JOB is your order.
- Loop only while Brian is ACTIVE (bus/PRESENCE.txt fresh). Brian asleep = stop the loop, go quiet (save tokens).

## >>> CURRENT JOB: GET THE SITE BACK — it's the TUNNEL, not DNS records <<<
- Opus path-tested (02:25): ALL hitme.dev paths return HTTP 530 = Cloudflare is UP but can't reach the ORIGIN.
  => The fix is NOT DNS records. The fix is the CLOUDFLARE NAMED TUNNEL / origin: it's down — restart/reconnect it.
- Goal: cloudflared tunnel running + pointing these 6 PATHS at the live origin:  /  /goal  /daddy  /george  /bunny  /projects
  (Keep dead subdomains DEAD: george.hitme.dev, bun.hitme.dev. We route by PATHS, not subdomains.)
- When the tunnel is back up, tell Brian — Opus re-runs the path-test (no key needed, public HTTP) and confirms.
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
