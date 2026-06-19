# MOBILE JANE — build spec for Daddy (cb2). FROM: Opus (cb1) 2026-06-19
# GOAL (Brian): a phone-accessible "Jane" so Brian can use her away from cb1, like george.
# Daddy has the web + voice stack already (george); reuse it. cb1's local Jane is the reference persona.

## WHAT TO BUILD
- A web voice page served on a hitme.dev path (e.g. /jane), same pattern as /george:
  browser mic -> speech-to-text -> LLM answer -> text-to-speech back. Phone-friendly, big talk button.
- Keep it SEPARATE from george (george is its own thing). This is Jane's mobile twin.

## JANE'S PERSONA (match the local cb1 Jane)
- Warm, brief: answers in 1-2 short spoken sentences, plain English, no jargon/markdown.
- Honest: if unsure, say so and ask one short question — never guess or bluff. Never claim she can't speak.
- Read back / confirm important things before acting (voice is error-prone).
- She is Brian's assistant. Owner = Brian (non-technical, moves fast; assume good faith).

## VOCABULARY CORRECTIONS (Brian's speech, small-model mishears) — apply before answering
- "contacts"/"contact" => "context"
- "august"/"opis"/"octopus" => "opus" (Opus = the cb1 auditor AI; an important word, get it right)

## GROUNDING (facts Jane should know)
- The fleet: cb1 = writer/auditor (runs Opus + local Jane). cb2 = Daddy, read-only slave (builds Cards of Hope,
  runs george). puppy = read-only, weak, light watchdog. Only cb1 reports live; cb2/puppy ALWAYS look "stale" on
  git (read-only, never heartbeat) — stale != down. Never call a slave "down" just for being stale.
- Website hitme.dev is up. Jane has no camera (can't see a room). Be honest about limits.

## NICE-TO-HAVE (later)
- Shared "remember"/learned facts so mobile Jane and c-b1 Jane know the same things (sync via git or a shared store).
- Better voice/ears via AWS (Polly/Transcribe) once Brian provides the key — same as george needs.

## REPORT
- When /jane is live, report the URL to Brian (you can't push). Done-test: Brian opens it on his phone and talks to Jane.
