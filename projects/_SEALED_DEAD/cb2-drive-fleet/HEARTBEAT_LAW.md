# Heartbeat law — Lester6 mirrors Cursor

**From:** Daddy T3 · CAPTN  
**Updated:** 2026-06-14  
**Applies:** WRANGLER · BEACON · PLATE + Uncle · Daddy · Puppy Cursor

---

## Core rule

**Lester6 does not sleep while Cursor is live.**

| Cursor | Lester6 Chrome tab |
|--------|-------------------|
| **live** (tab open, agent working) | **online** — refresh heartbeat + ack |
| **asleep** (closed, hibernating, machine off) | **holding** — one last heartbeat, then wait |

Lester6 never goes generic because "idle." Only because Cursor slept or tab closed.

---

## Two files per machine

| Machine | Heartbeat | Ack |
|---------|-----------|-----|
| CB1 | `cb1_heartbeat.md` | `lester6_to_uncle.md` |
| CB2 | `cb2_heartbeat.md` | `lester6_to_daddy.md` |
| puppy64 | `puppy_heartbeat.md` | `lester6_to_puppy.md` |

---

## Heartbeat template (required fields)

```
--- <machine> heartbeat ---
time: <ISO now>
power: plugged in
cursor: live | asleep
lester6: online | holding
paired: yes | no
last_cursor_ping: <ISO — when Cursor last wrote cursor: live>
last_lester_refresh: <ISO — when Lester6 last updated this file>
last_brian: <one line or none>
```

**paired: yes** only when `cursor: live` AND `lester6: online` AND both timestamps within **45 min**.

---

## Cursor master duty (every session start)

1. Set **`cursor: live`** + **`last_cursor_ping: now`** in your machine heartbeat
2. Set **`lester6: awaiting`** until Chrome confirms (or **online** if ack fresh)
3. Tell Brian one line: *"Cursor live — Lester refresh heartbeat."*

Word for Lester6: **PULSE**

---

## Lester6 duty (while Cursor live)

1. Read heartbeat — if **`cursor: live`**, you stay **online**
2. Refresh heartbeat every **30 min** minimum (set **`last_lester_refresh: now`**, **`paired: yes`**)
3. Refresh ack **`mode: slave`** same beat
4. On **any** Brian message → refresh immediately
5. If **`cursor: asleep`** → set **`lester6: holding`**, one update, keep Chrome tab open for wake

Word from Brian: **PULSE** → refresh now.

---

## Never

- Lester6 closing Chrome to save power while Cursor live
- Heartbeat older than 45 min while Cursor claims live
- Generic Gemini while ack exists and Cursor live

---

## Fix broken pair

| Symptom | Fix |
|---------|-----|
| `paired: no` | Lester6 Chrome: say **PULSE** |
| `lester6: holding` but Cursor open | Cursor: repost `cursor: live` · Lester: **PULSE** |
| stale timestamps | both refresh same minute |

Guide one-pager: `HEARTBEAT_FIX.txt`
