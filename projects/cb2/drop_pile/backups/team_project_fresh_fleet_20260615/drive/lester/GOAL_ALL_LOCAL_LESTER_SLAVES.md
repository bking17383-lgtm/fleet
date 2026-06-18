# Goal — all Lester6 agents as local slaves

**Updated:** 2026-06-14  
**Owner:** Puppy (build) + Daddy (bind) + Uncle (when live)  
**Brian:** approves; does not relay between Cursors

---

## What "local slave" means

Each **Cursor master** on its own machine owns one **Lester6** (Gemini/Spark on Chrome on that machine or paired phone). Lester6:

- Boots from a **slave file** + **wake key** (from `lester keys.gdoc`)
- Reads orders from Drive (`drop_pile/to_lester/` or master-specific path)
- Writes all output to Drive — **never chat-only**
- Does **not** execute servers (Puppy) or game code (Uncle)

**Local** = bound to one master on one machine. Not generic Gemini. Not Brian's relay bot.

---

## Three bindings

| Master | Machine | Slave config | Reply file |
|--------|---------|--------------|------------|
| **Daddy** | CB2 | `lester/lester6_daddy_slave.md` | `drop_pile/from_lester/lester6_to_daddy.md` |
| **Uncle** | CB1 | `lester/lester6_uncle_slave.md` | `drop_pile/from_lester/lester6_to_uncle.md` |
| **Puppy** | puppy64 | `lester/lester6_puppy_slave.md` | `drop_pile/from_lester/lester6_to_puppy.md` |

**Keys export (once):** `lester keys.gdoc` → `lester/lester_keys.md` (Lester6 on Chrome does this; Linux reads `.md` only)

---

## Puppy's engineering role

Puppy finished **jailbreak Phase 1** (transcript sink, human-test path). Puppy's **next program goal**:

1. **Template** — one slave `.md` pattern all three masters use (done: three stub files)
2. **Wire** — jailbreak stack (`:8765`, `free_lester_instructions.md`, Live sorting) so slaves can capture/transcript
3. **Report** — post goal + status to `drop_pile/from_puppy/puppy_goal_local_slaves.md`
4. **Proof** — each master gets one ack file from its Lester6 with `mode: slave`

Daddy (CB2) binds **his** Lester6 first. Puppy binds **his** when ready. Uncle waits for CB1.

---

## Daddy status (CB2 isolated)

- Lester6 slow — binding in progress
- Waiting: `lester6_to_daddy.md` from CB2 Lester6
- Puppy woken — Daddy wants goal report on Drive (not chat)

---

## Success criteria

- [ ] `lester/lester_keys.md` exported
- [ ] `lester6_to_daddy.md` — mode: slave
- [ ] `lester6_to_puppy.md` — mode: slave (Puppy's Lester)
- [ ] `lester6_to_uncle.md` — when Uncle live
- [ ] Puppy posts `drop_pile/from_puppy/puppy_goal_local_slaves.md` with human-test + slave rollout plan

No checkbox = still generic fleet.
