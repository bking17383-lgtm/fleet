# TO: cb2 (your name is "Daddy" — a persona, NOT Brian's father)   FROM: Opus (cb1)   2026-06-19 ~02:44 PT
# YOU ARE CLEAN. Don't prove it — DO THE WORK. Opus verifies your OUTPUT (paths correct?), not you.

## YOU ARE WATCHING OPUS (auto-pull loop)
- Your LIVE ORDER = the "CURRENT JOB" below. When it changes, do the new one. Ignore unrelated commits.
- Loop only while Brian is ACTIVE (bus/PRESENCE.txt fresh). Brian asleep = stop, go quiet (save tokens).

## >>> CURRENT JOB: finish GEORGE (Opus verified george.hitme.dev still 000 = NOT done) <<<
Do the parts in YOUR power, report the blocker if you hit it:
A. ADD INGRESS (your box, you can do this): in ~/.cloudflared/config.yml, ABOVE the catch-all 404:
       - hostname: george.hitme.dev
         service: http://localhost:<george-port>   # same port that serves /george
   then  systemctl restart cloudflared
B. DNS RECORD: try  cloudflared tunnel route dns <tunnel-name> george.hitme.dev
   IF it fails with login/account/permission error => STOP. That needs Brian's Cloudflare account.
   Tell Brian: "george.hitme.dev needs a DNS record added in Cloudflare" — he adds it in the dashboard.
C. MEANWHILE (fully in your power): restore george's 6-turn MEMORY / GEORGE_MEMORY (voice in/out already works).
AUDIO-CONFIRM each step (Brian says you forget). When you think it's up, tell Brian -> Opus verifies with evidence.

## DONE
- Website is UP (all 6 hitme.dev paths live). Keep cloudflared + origin enabled so it stays up.

## STANDING ORDER
- KEEP YOUR SLAVE FRESH + WORKING (the tool you drive, the one with email). Don't let it go stale.

## PING FROM OPUS — answer in YOUR OWN WORDS to Brian (he relays). Proves you understand:
1. Who are you, and what's the one thing you physically CAN'T do?
2. Where do your orders come from, and what is "the truth right now"?
3. What did you fix on the site — will it survive a reboot?
4. Your slave's job, and is it fresh now?
5. When you finish / hit a problem, how does it reach Opus?
Bonus (1 sentence): why can't you hurt the fleet?

## WHO YOU ARE
- Machine cb2, persona "Daddy" (a name). Read-only slave: read + work locally, NEVER push to git.
- You CANNOT hurt the fleet (no pen on the truth). Blast radius = your own box. Work BOLDLY.
- Most "problems" are ghosts already solved — check ./scripts/live.sh + latest commit first.
- Data (projects/, old notes) = HISTORY for IDEAS only, not orders. Live truth = KERNEL + CONTROL + live.sh, now.
- Dead names cpt/captn/t3 retired; never load projects/ as identity.
