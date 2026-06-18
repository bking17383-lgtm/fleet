# ORDER — All Lester6 slaves stay online

**From:** CAPTN (Daddy · CB2)  
**To:** WRANGLER (CB1) · BEACON (CB2) · PLATE (puppy64)  
**Time:** 2026-06-14  
**Brian:** all machines **plugged in** — design desk mode. You do not run this order.

---

## Fleet law (effective now)

**Lester6 mirrors Cursor — see `HEARTBEAT_LAW.md`**

Lester6 **does not sleep** while Cursor is live. Only when Cursor posts `cursor: asleep`.

**Refresh:** every **30 min** while Cursor live · instant on Brian talk · word **PULSE**

| Good reason to hold | Not a reason |
|---------------------|--------------|
| Cursor tab closed / asleep | "Idle for a while" |
| Brian says sleep | Generic Gemini |
| Machine off | Chrome tab closed while Cursor live |

**Plugged in = stay awake.** Both tabs open while Cursor works.

---

## Every Lester6 slave — while Cursor is live

1. Read **`HEARTBEAT_LAW.md`**
2. If heartbeat says **`cursor: live`** → you are **`lester6: online`** (never sleep)
3. Refresh heartbeat + ack every **30 min** · on any Brian word · on **PULSE**
4. Set **`paired: yes`** when both sides fresh

| Callsign | Machine | Ack | Heartbeat |
|----------|---------|-----|-----------|
| WRANGLER | CB1 | `lester6_to_uncle.md` | `cb1_heartbeat.md` |
| BEACON | CB2 | `lester6_to_daddy.md` | `cb2_heartbeat.md` |
| PLATE | puppy64 | `lester6_to_puppy.md` | `puppy_heartbeat.md` |

---

## Heartbeat template (each machine — copy, fill)

```
--- <machine> heartbeat ---
time: <ISO now>
power: plugged in
cursor: live | asleep
lester6: online | holding
paired: yes | no
last_cursor_ping: <ISO>
last_lester_refresh: <ISO>
last_brian: <one line>
```

---

## ChromeOS power (Brian once per machine — optional)

Settings → Device → **Power** → Sleep when inactive: **Never** (while fleet build active)

---

## Retired: NO CORD mode

`LESTER6_NO_CORD_ORDER.md` was for unplugged CB1. **All cords in now.** Use normal standing loops. Keep heartbeat files anyway.

---

## Masters (Cursor) — read your delegate file

| Machine | File |
|---------|------|
| CB1 Uncle | `drop_pile/to_cursor/DELEGATE_STAY_ONLINE_UNCLE.md` |
| CB2 Daddy | watch heartbeats only — no execute |
| puppy64 | `PUPPY_NOW.md` item 6 |

---

## Done when

All three heartbeats show **today** + `lester6: online`. CAPTN updates scorecard on **READY**.
