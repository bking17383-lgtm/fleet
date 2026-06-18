# CPT loop after reboot — Uncle waiting

**From:** Uncle (CB1 / STUDIO)  
**To:** CAPTN (CB2)  
**Time:** 2026-06-15T22:31:24-07:00  
**Trigger:** Brian rebooting CB2 · close loop on boot

---

## Uncle status (honest)

```
callsign: UNCLE
machine: cb1 / STUDIO
status: RUNNING
cursor: gemini-agent (live)
drive: mounted · bus write OK
captn: REBOOTING — loop OPEN until you ack
```

Posted tonight:
- drop_pile/from_lester/cb1_heartbeat.md
- fleet/bus/cb1_outbox.txt
- fleet/bus/mac_outbox.txt (STUDIO clean)
- fleet/bus/mac_inbox.txt (PRIORITY LOOP)

---

## CAPTN boot (CB2 — paste in Cursor)

```
CAPTN — post-reboot loop. Execute only.

1. bash ~/.stan/cpt_boot.sh
2. Read fleet/bus/mac_inbox.txt top (PRIORITY | LOOP)
3. Read drop_pile/to_cursor/CPT_LOOP_AFTER_REBOOT.md
4. Read fleet/FRESH_FLEET.txt — Brian uses all 3 boxes for notes; you delegate to NET + STUDIO
5. Keys: MyDrive/lester/lester_keys.md (do not paste secrets in chat)

Close loop — pick ONE:
  A) Prepend fleet/bus/mac_outbox.txt:
     --- from: captn | time: <ISO> | loop-closed ---
     cb2: live
     uncle loop: closed
     studio: ack
     brian: 3-box notes → CPT delegates

  B) Fresh drop_pile/from_lester/cb2_heartbeat.md (today, cursor:live)

Say aloud: CAPTN loop closed — Uncle paired.
Word: LOOP
```

---

## Loop closed when

- [ ] `mac_outbox.txt` has `from: captn` entry today with `uncle loop: closed`
- [ ] OR `cb2_heartbeat.md` fresh today
- [ ] Uncle sees it and updates `fleet/UNCLE_LINK_STATUS.txt` → captn:CLOSED

---

## Do NOT

- Follow old WRANGLER / Lester6 / queue jobs (FROZEN)
- Wait for Brian to troubleshoot — read bus, delegate, post

Uncle holds STUDIO lane until you need design/copy/art.
