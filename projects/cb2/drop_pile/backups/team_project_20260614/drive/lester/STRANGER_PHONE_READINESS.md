# Stranger phones (LTE / any network) — readiness plan

**Updated:** 2026-06-14  
**Daddy CB2 — LIVE prep track**  
**Human testing:** ON HOLD (`drop_pile/HOLD_HUMAN_TEST.md`)

---

## Target

Strangers open **one HTTPS link** on Android/iPhone (cellular OK). No Brian relay. No same Wi-Fi. No Chromebook awake.

---

## Why today fails for strangers

| Gap | Current state | Stranger requirement |
|-----|---------------|----------------------|
| URL | Random `trycloudflare.com` (rotates, CB2 tunnel) | **Fixed HTTPS** on puppy64 24/7 |
| Host | Often penguin / Chromebook | **puppy64 always on** |
| Network | LAN `192.168.x.x:8002` only | **Public tunnel** → localhost:8002 |
| Data | Brian's 497-card collection on old demos | **Commercial v1** empty/demo (no personal CollX) |
| Invite | SARAH_TESTER.txt + Brian awake | **Public link + 2-min script** on Drive |
| Legal | Privacy policy missing for public | **Privacy URL** (Lester draft OK) |
| Abuse | No rate limits on uploads | **Caps** on upload/API (slicer pattern) |

---

## App priority for strangers

| # | App | Stranger-ready? | Notes |
|---|-----|-----------------|-------|
| **1** | **Baseball commercial v1** | closest | Read-only demo + CollX import story; package on Drive |
| 2 | Video slicer | later | Needs Groq key + CF token; was ON HOLD for other reasons |
| 3 | Camel PWA | later | Uncle/CB1 game — not public yet |
| 4 | Jailbreak Live | **HOLD** | Human test frozen |

**First public link should be baseball commercial demo** unless Brian picks slicer.

---

## Puppy must ship (execute)

See `drop_pile/to_puppy/STRANGER_PHONE_PREP.md`:

1. Install `releases/baseball_cards_v1.0.0` on puppy64
2. Run `:8002` with **commercial** empty collection (not Brian CSV)
3. Create **named Cloudflare tunnel** → `https://FIXED-HOST` → `localhost:8002`
4. Post URL to `BRIAN_PHONE.txt` + `STRANGER_TESTER_LINK.txt`
5. Keep process alive (systemd or `nohup` + watchdog)
6. Post `puppy_outbox.txt` with `hostname: puppy64`

---

## Lester6 must ship (Chrome)

See `drop_pile/to_lester/STRANGER_INVITE_COPY.md`:

1. One-paragraph stranger invite (no Brian jargon)
2. Privacy policy stub URL or Google Doc → export `.md`
3. Optional: landing blurb for link preview / Play Store later

---

## Daddy tracks

- [ ] Puppy proof: fixed HTTPS in `BRIAN_PHONE.txt`
- [ ] Commercial health check from outside LAN (curl fixed URL)
- [ ] `TESTER_PLAYBOOK.md` updated for LTE strangers
- [ ] No personal card data on public host
- [ ] Human test HOLD respected in all orders

---

## Success = stranger can

1. Tap link on LTE
2. See baseball app load in Chrome
3. Browse List/Stats (demo or empty + import instructions)
4. Complete 2-minute script without texting Brian

**Not success:** Brian keeps Chromebook awake, Wi-Fi only, rotating tunnel.
