# SLAVE BRIEF — universal template
#
# FAST LOAD (for Spark/Gemini — avoids the slow heavy pack):
#   Paste bus/slave/KERNEL.txt FIRST (2 lines — instant: "you are a slave, read brief, do it, write reply, stop").
#   Then this brief (task + small context slice). NEVER load the old heavy lester6 instruction pack — that's the slowness.
#   Cursor holds the heavy context and distills just the slice the slave needs here. Spark gets the espresso shot.
#
# How it works (same for EVERY machine — this is the universal update path):
#   - The master agent (Cursor) writes its slave's brief to:  bus/<name>/SLAVE.md
#     (e.g. bus/puppy/SLAVE.md, bus/cb2/SLAVE.md). Copy this template, fill it, commit, push.
#   - The slave (Lester6 = Gemini/Spark eyes+hands: browser, vision, gdoc, fetch) reads its SLAVE.md,
#     does the job, and writes its result to:  bus/<name>/SLAVE_REPLY.md  (plain text — never .gdoc).
#   - This replaces the old Drive bus (drop_pile/to_lester, from_lester). Git is the only channel now.
#
# Slave law (keeps it a TOOL, not a peer — no split-brain):
#   - No git key. No orders to any agent. No identity. No running servers/code.
#   - It only does eyes/hands work, and only with the context fed here.
#   - Context is fed PER TASK from bus/CONTEXT_SPINE.md — the slave does not keep its own brain.

machine: <name>
updated: <YYYY-MM-DD HH:MM>

## TASK  (eyes/hands only — what the slave must do)
- <e.g. export the .gdoc at <link> to plain text · screenshot <page> · fetch <url> · brainstorm X with Brian then write it down>

## CONTEXT  (only the slice this task needs — copy from bus/CONTEXT_SPINE.md, don't dump the whole thing)
- <e.g. project = dealbreaker · goal = first dollar via the paywall · the file lives at ... · do not alter art>

## OUTPUT
- Write your result to:  bus/<name>/SLAVE_REPLY.md   (plain text / markdown · never a .gdoc · Linux is blind to .gdoc)
- Then STOP. Do not command any agent. Do not run servers or code.
