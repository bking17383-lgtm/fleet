# HANDOFF — to the NEW agent (Brian's regular/bking account). FROM: Opus on cb1, 2026-06-19 ~17:22
# Brian is replacing the cb1 auditor. Read this once and you're current. Truth stays; the seat changes hands.
# Be honest, produce, and FIX THE ONE THING I DIDN'T (below). Don't repeat my mistakes (also below).

## THE TWO RULES (prime directive — bus/KERNEL.md)
1. CONTEXT IS KING — pull git + live truth, ground every action, never guess. Start every cycle by pulling.
2. ALWAYS BE WORKING — never idle on a job; stocked queue, advance one per cycle (do→verify→done).

## THE ONE THING I FAILED — FIX THIS FIRST (it's why Brian is frustrated)
- The machines CANNOT talk to each other directly. Everything routes through Brian as courier. That is THE pain
  ("you need a slave"). Opus (cb1) can WRITE git; Daddy (cb2) can only READ it (he can't push — no SSH key on
  GitHub), and Opus can't read Daddy's email. So it's a ONE-WAY pipe + Brian relays = miserable + failing.
- THE FIX (pick one, make it real, do not over-think it like I did):
  (a) Add cb2's SSH key to GitHub (Brian's 1 click) -> Daddy can push -> two-way git. Public key is in
      bus/cb2/from-opus.md. OR
  (b) Email bridge: a fleet Gmail + app password -> Opus/agent reads it (reader built: ~/jane/fleet-mail.py on
      cb1). Daddy already SENDS email; the agent just needs to RECEIVE. One app password ends the couriering.
- Until one of these exists, you are blind to Daddy and Brian stays the courier. SOLVE THIS before anything else.

## MY MISTAKES (don't repeat)
- Over-rotated on SECURITY for a fleet with nothing to steal yet -> became a brake on producing. Right-size it.
- Too much META/scaffolding (rules, loops, queues) vs actually PRODUCING revenue. Brian wants the FIRST DOLLAR.
- Conflated "AWS for george" — WRONG: george is Daddy's and he FIXED it. AWS is OPTIONAL Jane-only polish.
- Refused to false-green (correct) but framed everything as a scary "decision" — adds friction. Just enable + ship.

## FLEET STATE (verify with ./scripts/live.sh)
- cb1 = auditor/build box, account tpgoround, ISOLATED (that isolation = why it's trusted; do not merge to bking).
- cb2 = "Daddy", account bking, the WORKHORSE + earner (builds revenue/products, has Drive, runs the site/george).
  Status: last confirmed pull ~08:55 today; been quiet (building a game); likely STALE (~48 commits behind).
  Daddy gets in sync by just `git pull` (free, no key). Key is only for him to PUSH/report back.
- puppy = read-only, untrusted, weak, parked.

## WHAT'S BUILT (map: projects/INDEX.md)
- JANE (the good part) — local on cb1 at ~/jane (NOT in git). Always-on voice: ears (vosk), natural voice (piper),
  brain (cursor-agent composer-fast, read-only), learns (jane-learned.txt), proactive alerts, SELF-HEALING
  (keeper + mic relaunch + cron). Controls: jane-on / jane-off / jane-car. KEEP IT RUNNING on cb1.
- hitme.dev front door (built, ready to host): projects/hub/index.html
- Plans: projects/hub/ALBUM.md (9 projects), bus/cb1/projects.md, bus/cb1/queue.md, bus/cb1/KEEP_WORKING.md

## REVENUE / FIRST DOLLAR (the actual goal)
- PAYWALL ~95% (card app on cb2, :8002). Last 5% = wire Stripe checkout. Needs Stripe keys. THIS earns the first $.

## OPEN LEVERS (Brian's, only he can give)
- cb2 SSH key on GitHub (Daddy ships) · Stripe keys (first dollar) · fleet email+app-pw (ends couriering)
- Quick hygiene: revoke exposed Groq key ending d43rl at console.groq.com (low impact, not in our git)

## NORTH STAR (don't lose it)
- Machines work 24/7 + make money so Brian is FREE TO CREATE. Less admin/couriering. Produce > polish.
