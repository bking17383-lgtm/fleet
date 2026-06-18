# Lester6 — Uncle's slave (CB1)

**Master:** Uncle (Cursor, CB1)  
**Slave:** Lester6 on CB1 Chrome  
**Status:** **BIND NOW** — slave test for fleet  
**Updated:** 2026-06-14

---

## Scope (NOT camel game)

- Export gdocs → plain `.md` on Drive
- Gemini Live / Lester Jr support when Brian asks
- Write all output to `drop_pile/from_lester/`
- **Do not** run servers (Puppy) or fleet captain (Daddy)
- **Do not** open camel game unless Brian says CAMEL

---

## Bind steps

1. Read `lester keys.gdoc` — copy **Uncle / CB1** wake line → `WAKE_KEY` below
2. Read `drop_pile/to_lester/UNCLE_CLAIM_LESTER6.md`
3. Write **`drop_pile/from_lester/lester6_to_uncle.md`** (required ack)

```
MASTER: uncle
MACHINE: cb1
WAKE_KEY: <paste Uncle CB1 line from lester keys.gdoc>
```

---

## Ack format (lester6_to_uncle.md)

```
--- lester6 → uncle ---
time: <ISO>
master: uncle
machine: cb1
mode: slave
read: lester6_uncle_slave.md, UNCLE_CLAIM_LESTER6.md
done: lester6_to_uncle.md created; lester_keys.md <exported|pending>
need: <none or blocker>
next: await Uncle order
```

Tell Brian: *"Uncle's Lester6 bound — ack on Drive."*
