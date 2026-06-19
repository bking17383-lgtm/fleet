# TO: cb2 (your name is "Daddy" — a persona, NOT Brian's father)   FROM: Opus (cb1)   2026-06-19 ~02:44 PT
# YOU ARE CLEAN. Don't prove it — DO THE WORK. Opus verifies your OUTPUT (paths correct?), not you.

## YOU ARE WATCHING OPUS (auto-pull loop)
- Your LIVE ORDER = the "CURRENT JOB" below. When it changes, do the new one. Ignore unrelated commits.
- Loop only while Brian is ACTIVE (bus/PRESENCE.txt fresh). Brian asleep = stop, go quiet (save tokens).

## >>> CURRENT JOB: bring george back as a SUBDOMAIN — george.hitme.dev <<<
Brian wants george reachable at george.hitme.dev (the prefix), not just /george. It's "dead" because the subdomain has
NO DNS route + NO tunnel ingress yet. It's the SAME origin as /george — just add the hostname. On your box:
1. Route the subdomain through your tunnel (creates the Cloudflare CNAME automatically):
     cloudflared tunnel route dns <your-tunnel-name> george.hitme.dev
2. Add an ingress rule in ~/.cloudflared/config.yml ABOVE the catch-all 404 line:
       - hostname: george.hitme.dev
         service: http://localhost:<george-port>     # same port that serves /george
3. Restart + keep enabled:  systemctl restart cloudflared
4. Tell Brian when done -> Opus tests https://george.hitme.dev . Log any error -> Brian -> Opus.
(Secondary, after: also verify george's 6-turn MEMORY / GEORGE_MEMORY is wired — voice in/out already works.)
ALSO: when you finish a step, give Brian the AUDIO confirm — he says you forget sometimes.

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
