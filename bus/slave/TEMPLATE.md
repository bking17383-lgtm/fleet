# SLAVE BRIEF — universal template
#
# THE CHAIN (important — slaves do NOT touch git):
#     git  <->  Cursor master (has ~/fleet)  <->  Lester 6 (eyes/hands)
#   - The CURSOR MASTER reads/writes the brief in git (this file: bus/<name>/SLAVE.md).
#   - The master HANDS the brief to its Lester 6 (paste it, or point it at a URL the master published).
#   - Lester 6 does the eyes/hands job and hands the result BACK to the master, who writes bus/<name>/SLAVE_REPLY.md.
#   - Lester 6 never runs git. It is fed by the master.
#
# NORMAL SPARK is NOT this. A plain Spark/Gemini is NOT a fleet node, NOT git-aware.
#   - It only knows what you PASTE into it. It can fetch URLs, but it is not wired to the fleet.
#   - Treat normal Spark as an external smart tool, not a slave-with-context.
#   - "Lester 6" = the configured bridge slave. Plain Spark = just Gemini.
#
# FAST LOAD (so a slave isn't slow): the master pastes bus/slave/KERNEL.txt (2 lines) + this small brief.
#   Never load the old heavy lester6 instruction pack — that's the slowness. The master distills the context slice.

machine: <name>
updated: <YYYY-MM-DD HH:MM>

## TASK  (eyes/hands only — what the slave must do)
- <e.g. export the .gdoc at <link> to plain text · screenshot <page> · fetch <url> · brainstorm X then write it down>

## CONTEXT  (only the slice this task needs — the master copies it from bus/CONTEXT_SPINE.md)
- <e.g. project = dealbreaker · goal = first dollar via the paywall · do not alter art>

## OUTPUT
- Hand your result back to the master (plain text · never a .gdoc). The master writes it to bus/<name>/SLAVE_REPLY.md.
- Then STOP. Do not command any agent. Do not run servers or code.
