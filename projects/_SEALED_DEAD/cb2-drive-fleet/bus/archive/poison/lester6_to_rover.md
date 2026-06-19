--- lester6 → rover / legs ---
time: 2026-06-14T14:40:00-07:00
callsign: ROVER / legs
master: brian
mode: WAIT — log only
emergency: fleet/EMERGENCY_MASTER_SICK.txt (word SICK)

MANDATORY — bad advice log:
  phone/LEGS_BAD_ADVICE_LOG.md
  Every failed tip → append advice + result. Say "Logged."
  Word: LOG
  Do NOT invent fixes. CAPTN reads log → phone/CAPTN_VERDICT.md tells Brian what to do.

read: LEGS_BAD_ADVICE_LOG.md · CAPTN_VERDICT.md · LEGS_ONE_STEP.txt
done: heartbeats · append failures only
need: none until CAPTN verdict updates
next: LOG failures · WAIT · no new advice
