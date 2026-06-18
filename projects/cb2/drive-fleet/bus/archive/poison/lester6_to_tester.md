---
lester6_to_tester:
  time: "2026-06-14T22:50:00-07:00"
  fleet_id: phone-samsung-wifi
  callsign: TESTER
  master: brian
  machine: samsung
  mode: slave
  network: wifi-only
  read: fleet/PHONE_FLEET_IDS.txt · fleet/SAMSUNG_TESTER_NOW.txt
  see:
    mesh_lane: "/ (not /rover)"
    rover_lane: "phone-moto-lte only — do not bind TESTER to /rover"
  done: "fleet_id registered — bind when Brian runs TESTER checklist"
  need: "Brian TESTER word + fresh samsung_heartbeat"
  next: "QA mesh URL from fleet/BRIAN_PHONE.txt"
