# WHO — fleet roster (bulk)
Updated: 2026-06-16T03:17:52-07:00

Regenerate: `python3 lester/plate_who.py`

| fleet_id | callsign | role | network | url |
|----------|----------|------|---------|-----|
| cb1 | WRANGLER | Analyst · hardware protocols · budget | reload paused |  |
| cb2 | BEACON | CAPTN desk · architect · Sarah host | Tailscale 100.115.92.26 | http://127.0.0.1:8766/sarah |
| puppy64 | PLATE | Network · art lane · 24/7 host | wlan0 192.168.1.4 · wg0 10.0.0.1 | http://192.168.1.4:8765 |
| phone-moto-lte | ROVER | Brian road phone · cellular | LTE | /rover on mesh |
| phone-samsung-wifi | TESTER | QA · Sarah trials | WiFi only | mesh home / |
| human-sarah | — | Appointment tester · minimal intrusion | HTTPS or home WiFi | fleet/SARAH_SEND_WHEN_READY.txt |
| human-brian | DADDY | Steer · art · inbox one-line | — | fleet/bus/BRIAN_INBOX.txt |

## Live status

```
FLEET AVAILABLE — read this to design
Updated: 2026-06-16T03:17:52.170850-07:00
Refreshed by: fleet_board.py on penguin

COMPUTERS (3 + Puppy host)
  CB1      ✗ DOWN      WRANGLER + Uncle
  CB2      ✗ DOWN      BEACON + CAPTN/Daddy
  puppy64  ✗ DOWN      Puppy + PLATE

PHONES (2) — fleet_id is stable · see fleet/PHONE_FLEET_IDS.txt
  phone-moto-lte      ✗ DOWN      ROVER   Moto Play · cellular · /rover
  phone-samsung-wifi  ✗ DOWN      TESTER  Samsung · wifi/dongle only · /

AI AGENTS — see heartbeats in drop_pile/from_lester/

PARTS / SERVICES (CB2 host check)
  baseball :8002  DOWN
  mesh radio :8765  UP
  Daddy public URL  fleet/DADDY_BASEBALL_URL.txt
  RADIO public URL  fleet/MESH_RADIO_URL.txt

DESIGN NOW
  Brian say DESK — honest board from heartbeats
  Uncle: bash ~/GoogleDrive/MyDrive/lester/install_uncle_stan.sh
  Puppy: drop_pile/to_puppy/UNCLE_LINUX_FIX.md

Compact: CB1✗ CB2✗ puppy64✗ moto✗ samsung✗ | 0 up · 0 partial · 5 down
```
