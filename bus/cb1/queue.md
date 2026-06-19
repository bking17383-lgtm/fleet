# CB1 / OPUS WORK QUEUE — my standing backlog so there is ALWAYS a next job.
# RULE 1: context is king — every work cycle STARTS by pulling git + reading live truth
#   (bus/KERNEL.md, bus/CONTEXT_SPINE.md, scripts/live.sh, Jane daemons, bus/cb2/to-opus.md).
# RULE 2: then DO the top unfinished item, verify it, report briefly. Never idle when there is a job.
# Priorities: ~90% Jane, ~10% fleet upkeep (Brian's standing order 2026-06-19).

## STANDING (always-on duties — check every cycle)
- [ ] Jane health: all 5 daemons up (keeper covers it) — confirm, fix if not.
- [ ] Truth accurate: rail/RAIL.txt, status files, OPUS.md handoff reflect reality.
- [ ] Daddy loop: read bus/cb2/to-opus.md; ack new reports in bus/cb2/from-opus.md; keep his queue stocked.

## EVENT-TRIGGERED (do the instant the event fires)
- [ ] AWS key lands at ~/.aws/credentials -> wire Jane voice (Polly) + unblock george; report.
- [ ] Daddy pushes new work commit -> read it, verify output (paths correct?), ack.
- [ ] Site goes down (watcher speaks) -> investigate from cb1, log to bus/cb2/dns-problems.md.

## ACTIVE BUILD TASKS (the WORKING SET — every cycle DO the top one, verify, mark [x], take next)
# Standing duties above = a 10-second glance. THIS is the real work. Never reduce a cycle to monitoring.
- [ ] Simulate a voice-daemon HANG and prove jane-say.sh falls through (validate today's deadlock fix end-to-end).
- [ ] Guard the keeper itself: if jane-keeper.sh dies, nothing restarts it — add a cron @reboot/peer check.
- [ ] Jane resilience: a jane-install.sh that rebuilds Jane from scratch (venv + models + scripts) after a wipe.
- [ ] Hearing: add a "did I get that right?" readback for important/irreversible-sounding commands.
- [ ] Grow jane-corrections.txt proactively (common mishears: names, fleet words).
- [ ] QA the watcher + refresher for edge cases (empty cache, git offline) — harden.
- [ ] Mobile Jane: verify /jane when Daddy ships it (vantage-test from a phone-like fetch).

## DEFERRED (needs Brian / a key — NOT autonomous)
- [ ] True barge-in (interrupt mid-sentence) — needs Brian's voice to tune.
- [ ] AWS Transcribe ears + Polly voice — needs the AWS key.

## FLEET BACKLOG (the 10%)
- [ ] george.hitme.dev CF cert (Brian account) — surfaced, waiting.
- [ ] puppy: stays read-only/untrusted/parked; isolated+useful prep already pushed.

## DONE (log completions here)
- 2026-06-19: Jane built (ears/voice/brain/learn/alerts/self-heal); Daddy re-looped two-way; sleep locked (Linux side).
