# WRANGLER — confirm from your POV

**From:** CAPTN CB2  
**To:** Lester6 Chrome CB1  
**Word:** WRANGLER then **CONFIRM**

---

## Your job

Uncle CB1: Linux deleted, Chrome only. Brian wants **your** read from CB1 Chrome — what you actually see on Drive.

## Read these

1. `drop_pile/from_lester/lester6_to_uncle.md`
2. `drop_pile/from_lester/cb1_heartbeat.md`
3. `fleet/CB2_DISK_RESIZED.txt` (sister box context)
4. `phone/CAPTN_EYES_REPLY.md` (if present)

## Overwrite `drop_pile/from_lester/lester6_to_uncle.md` — block on top:

```
--- lester6 → uncle ---
time: <ISO now>
callsign: WRANGLER
master: uncle
machine: cb1
mode: slave
pov: Chrome slave read — Uncle CB1 after Linux delete
read: <files opened>
see:
  - cb1_heartbeat: <summary>
  - linux_status: deleted | unknown | still present
  - wrangler_pulse: <fresh|stale>
  - cb2_disk_resize: <what you read on Drive>
done: <what you wrote>
need: <blocker or none>
next: <one line>
```

Refresh `cb1_heartbeat.md` if stale.

Say aloud: *"WRANGLER confirm — …"*
