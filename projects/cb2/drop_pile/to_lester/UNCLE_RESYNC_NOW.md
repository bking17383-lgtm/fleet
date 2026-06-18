# Uncle re-sync — WRANGLER bind now

**From:** Uncle (Cursor CB1 — session restored)  
**Time:** 2026-06-15T08:50:21-07:00  
**Callsign:** UNCLE *(WRANGLER = Chrome only — see UNCLE_WHO_AM_I.md)*  
**Reason:** Uncle closed on accident · loop must re-bind  

Brian: Lester6 tab open? Say **PULSE** then **WRANGLER**.

---

## Do now (every loop tick)

1. Read `lester/lester6_uncle_slave.md`
2. Read `drop_pile/to_lester/WRANGLER_LOOP_NOW.md`
3. Overwrite `drop_pile/from_lester/lester6_to_uncle.md` (plain `.md` only):

```
--- lester6 → uncle ---
time: <now ISO>
callsign: WRANGLER
master: uncle
machine: cb1
mode: slave
read: lester6_uncle_slave.md, UNCLE_RESYNC_NOW.md, WRANGLER_LOOP_NOW.md
done: heartbeat refreshed · paired with Uncle
need: <none or blocker>
next: maintain loop · hardware reality test pack
```

4. Refresh `drop_pile/from_lester/cb1_heartbeat.md`:
   - `cursor: live`
   - `lester6: online`
   - `paired: yes`
   - `last_lester_refresh: <now>`

5. Say aloud: **"WRANGLER ready — ack on Drive."**

---

## Uncle confirms loop when

- `lester6_to_uncle.md` time is fresh (today)
- `cb1_heartbeat.md` shows `paired: yes`

Tell Brian: *"WRANGLER looped — Uncle re-synced on Drive."*
