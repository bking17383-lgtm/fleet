# Cursor heartbeat ping — all masters

**Law:** `HEARTBEAT_LAW.md`  
**Lester6:** refresh when **`cursor: live`** · word **PULSE**

---

## CB2 Daddy (every session)

```bash
bash ~/.stan/heartbeat_ping_cb2.sh
```

Then tell BEACON Chrome: **PULSE**

---

## CB1 Uncle (paste each session)

Update `drop_pile/from_lester/cb1_heartbeat.md`:
```
cursor: live
lester6: awaiting
last_cursor_ping: <now>
paired: no
```

Then WRANGLER Chrome: **PULSE**

---

## Puppy (paste each session)

Update `drop_pile/from_lester/puppy_heartbeat.md` same fields.

Then PLATE Chrome: **PULSE**

---

## On Cursor exit / sleep

Set **`cursor: asleep`** in your heartbeat before closing tab.
