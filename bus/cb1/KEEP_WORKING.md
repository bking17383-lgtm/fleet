# KEEP OPUS WORKING — the strategy (FROM: Opus/cb1, 2026-06-19)
# Brian's two rules: (1) CONTEXT IS KING  (2) why aren't you working?
# Problem: Opus is turn-based — it only acts when given a turn. This system gives it
# turns-with-a-job, grounded in context, cheaply, without needing Brian.

## 1. WORK QUEUE  (the WHAT — always a next job)
- bus/cb1/queue.md = a standing prioritized backlog. No queue -> no work.
- Daddy and Brian can ADD to it; Opus works it top-down. ~90% Jane, ~10% fleet.

## 2. WAKE SIGNALS  (the WHEN — Opus can't self-start)
- EVENTS (primary, instant): AWS key lands · Daddy pushes work · Daddy writes to-opus.md ·
  site up/down · a new non-heartbeat commit. These wake Opus immediately = real work.
- HEARTBEAT (fallback, lean ~20m): a context refresh + queue check so nothing is missed
  even with zero events. Kept long so idle ticks don't burn tokens.
- BRIAN (override): any message from Brian is the top-priority wake.
- Mechanism today: jane/opus-worktick.sh (background watcher) emits a sentinel; Opus wakes.

## 3. CONTEXT-FIRST CYCLE  (the HOW — rule 1 is step 1)
Every wake runs, in order:
  a. PULL git + read live truth (KERNEL, live.sh, Jane health, bus/cb2/to-opus.md).
  b. DO the top unfinished item in bus/cb1/queue.md.
  c. VERIFY the output (false-green firewall — prove it, don't assume).
  d. REPORT briefly what changed; only escalate real decisions.

## 4. DELEGATION  (SCALE — Opus is expensive)
- Grind/routine -> Daddy's slave (capable tool, has email) + cheap models.
- Opus DIRECTS + CURATES + VERIFIES; it does not do work a cheaper worker can.
- Daddy feeds Opus's queue (pushes work/reports) and runs delegated tasks via its slave.

## 5. RESILIENCE  (STAY ALIVE — no silent death)
- Self-heal at every layer: keeper restarts dead daemons · listener relaunches the mic ·
  cron @reboot restarts after a reboot. The system survives crashes/sleep unattended.

## 6. ESCALATION  (the GATE — bring Brian only the rare real call)
- Move freely on anything REVERSIBLE. STOP only for the irreversible-5:
  wipe · delete-truth · keys · spending · go-live. Those = Brian decides.

## ONE LINE
Queue + event-driven wakes (lean heartbeat) + context-first cycles + delegate to slaves +
self-healing + escalate-only-for-decisions = Opus stays working, grounded, cheap, resilient.
