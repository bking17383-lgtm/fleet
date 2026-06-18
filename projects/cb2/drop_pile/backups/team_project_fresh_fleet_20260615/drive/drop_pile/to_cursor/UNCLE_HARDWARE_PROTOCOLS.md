# Uncle (CB1) — hardware + project integration
**fleet_id:** `cb1` · **Updated:** 2026-06-15  
Brian: Uncle is learning how we integrate projects **using hardware** — protocols to **build things**. Link when fresh Uncle is up.

---

## Goal

One protocol stack so Uncle can wire **physical builds** (GPIO, serial, USB, sensors, actuators) into the same bus the fleet already uses — without each project inventing its own glue.

---

## Layer 0 — already live (software bus)

| Piece | Path | Role |
|-------|------|------|
| Drive bus | `fleet/bus/mac_inbox.txt` | one-line orders, all nodes |
| Heartbeats | `drop_pile/from_lester/cb1_heartbeat.md` | green list |
| Proposals | `drop_pile/proposals/inbox/` | new project drops |
| Fleet board | `lester/fleet_board.py` | who is alive |

**Law:** Drive is source of truth. No Google mining. Plain `.txt` / `.md`.

---

## Layer 1 — hardware protocol (Uncle builds)

Suggested **HW envelope** — every device message is one JSON line or one INI block:

```ini
--- hw | cb1 | 2026-06-15T12:00:00 | sensor-temp-garage ---
device_id: cb1-gpio-01
project: sarah-appointments
action: read
payload: {"c": 22.4, "unit": "C"}
status: ok
```

```ini
--- hw | cb1 | 2026-06-15T12:00:01 | relay-desk-lamp ---
device_id: cb1-relay-02
project: camel-demo
action: set
payload: {"on": true}
status: ok
```

**Post to:** `fleet/bus/hw_inbox.txt` (create on first use)  
**Ack to:** `fleet/bus/hw_outbox.txt`

Uncle owns: parse `hw_inbox` → talk serial/GPIO → post `hw_outbox`.

---

## Layer 2 — project hooks (link soon)

| Project | Software today | Hardware hook (future) |
|---------|----------------|------------------------|
| **Sarah appointments** | `:8766/sarah` web, OCR post-its | desk button → snap trigger; LED "confirmed" |
| **Mesh / phones** | `mesh_radio.py :8765` | ROVER physical PTT |
| **Camel game** | terminal v0.8 | arcade button / coin slot on Puppy |
| **Fleet poll** | mac_inbox one-liners | Uncle daemons tier B |

CAPTN posts **software** specs; Uncle posts **pinout + protocol** back to same project folder.

---

## Uncle boot checklist (when Linux reload done)

1. Mount Drive → confirm `MyDrive/fleet/` visible  
2. Post fresh `cb1_heartbeat.md`  
3. Read this file + `fleet/CB1_LINUX_RELOAD.txt`  
4. Reply one line in `mac_inbox.txt`: `UNCLE hw protocol read`  
5. Pick **one** pilot: Sarah desk button OR garage sensor — post pinout to `drop_pile/proposals/inbox/PROPOSAL_cb1_<slug>.md`

---

## Isolation (from LINKAGE_ISOLATION_LAW)

- CB1 does **not** run CAPTN email or Puppy mesh unless ordered  
- Hardware daemons **read-only** on Drive except `hw_outbox` + heartbeats  
- No scraping Gmail/contacts — same as Sarah tester law

---

## Questions for Uncle (Brian can relay)

1. What board/stack on CB1 after reload? (Pi, Arduino bridge, USB relay?)  
2. First physical build Sarah would feel? (one button beats ten sensors)  
3. Serial format preference: JSON lines vs INI blocks above?

**CAPTN holds software lane until Uncle posts heartbeat.**
