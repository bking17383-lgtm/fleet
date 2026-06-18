# Proposal — Sarah appointment lane (web-first)
**From:** CAPTN · Brian relay  
**For:** Sarah + others like her  
**Date:** 2026-06-15  
**Status:** concept — not built

Sarah asked: help making appointments. She is **not alone**.  
Cell web = same price as desktop for most portals. **Calling is fallback, not default.**

---

## Scenario — open slots + bundling (Brian 2026-06-15)

**Example:** 10 open spots for Sarah · 8 for doctor(s) → agent **matches** and **offers** combinations.

### Application theme question (core UX)

> **"Do you want them bundled to one day?"**

| Answer | Agent behavior |
|--------|----------------|
| **Yes, one day** | Pack compatible appts into single day · minimize trips · show timeline |
| **No / spread out** | Offer best individual slots · still show gentle day context |
| **Ask me each time** | Default for Sarah-like users (not hyper-busy) |

### If not bundled — gentle itinerary (opt-in depth)

Parallel to **other objectives that day** — without intrusion:

- Seminary block? → don't stack doctor across long commute before class  
- Already has coffee with friend? → suggest slot **before** or **after**, not "we moved your life"  
- **Offer, don't override** — busy executives love auto-pack; Sarah (seminary 2yr) gets **lighter touch**

**Invasive line:** agent rearranges her whole week without asking.  
**Good line:** *"You have chapel 2pm. These two lab slots fit 9am–11am same day — bundle?"*

### Sarah persona (not generic "busy CEO")

| Trait | Product tuning |
|-------|----------------|
| Seminary 2 years | Respect study rhythm · predictable weekly anchors |
| Not so busy | **Fewer nudges** · no executive-density packing |
| Still wants help | Web booking + missed-appt guard + optional bundle question |
| Not alone | Same engine · **per-user** "intrusion level" slider |

### Matching logic (concept)

```
INPUT:  sarah_slots[10]  doctor_slots[8]  sarah_day_objectives[]  bundle_preference

MATCH:  feasible pairs where travel + duration + portal rules OK

OFFER:  ranked list
  1) bundled day plans (if yes or maybe)
  2) best single appt
  3) "parallel itinerary" — soft note only ("class at 3 — these fit morning")

Sarah taps to confirm — never silent book.
```

### Intrusion slider (settings)

| Level | Who |
|-------|-----|
| **Minimal** | Sarah default — bundle question + reminders only |
| **Standard** | day-context hints |
| **Executive** | aggressive pack + transit buffers (opt-in) |

Some users find day-context invasive · busy users love it · **Sarah starts Minimal.**

---

## What Sarah needs (mapped)

| Need | Agent can help? | How |
|------|-----------------|-----|
| **Medical test / chart / follow-up** (web) | **YES — best case** | Portal login → schedule → confirm → calendar + reminders |
| **Web appointments generally** | **YES** | Find booking URL, fill forms, pick slot from her rules |
| **Missed appointment → penalties/fees** | **Guard, not magic** | Reminders + confirm loop + “you must tap GO” — agent does not skip human ack for medical |
| **In-person “scan phones” + business cards** | **YES — separate feature** | QR / NFC vCard handshake at events (see below) |
| **Jury duty check-in** | **Probably NO** | Government, identity-bound, often in-person or strict gov portal — case-by-case, no promises |

---

## Design principles (Brian security rules)

1. **Web before phone** — no robocall unless Sarah explicitly approves that tier  
2. **Sarah owns credentials** — agent never stores passwords on Drive in plain text  
3. **No mining Google** for contacts or “friends who could help” (`TESTERS_NO_GOOGLE_MINING.txt`)  
4. **Human ack before book** — agent prepares slot; Sarah one-tap **BOOK** or **CALL**  
5. **Missed-appt protection** — calendar hold + 24h / 2h reminders; log confirmations  

---

## Lane A — Web appointment assist (Sarah’s main ask)

### Flow

```
Sarah (or Brian types for her) → APPOINTMENT_REQUEST.txt
        ↓
Agent finds: portal URL · guest schedule · phone-only flag
        ↓
Agent drafts: APPOINTMENT_READY.md (slots, forms prefilled where safe)
        ↓
Sarah taps BOOK or opens link on **her phone** (same price as desktop)
        ↓
Agent adds calendar event + reminder chain
        ↓
Day-of: "Leave now?" ping (SMS or notification — Sarah picks channel)
```

### Medical specifically

- MyChart / patient portal / lab follow-up — **all computer-possible** ✓  
- Agent can: check results posted, schedule follow-up, request callback  
- Agent cannot: practice medicine, interpret labs, bypass HIPAA portals without her login  
- **Credential vault:** Sarah’s phone password manager or one-time paste — not fleet Drive  

### Missed appointment problem

Sarah’s fear: human misses slot → fees / lost follow-ups / “only get a few chances.”

**Mitigations:**
| Layer | What |
|-------|------|
| Confirm twice | Agent proposes → Sarah confirms → agent books |
| Calendar block | Auto `.ics` with travel buffer |
| Reminders | 7d · 1d · 2h (configurable) |
| Escalation | If Sarah doesn’t ack 1d reminder → text Brian or designated helper **only if she opted in** |
| Audit log | `fleet/bus/APPOINTMENT_LOG.txt` — who booked what when |

Agent **does not** silently no-show. Human still responsible — we reduce forget, not liability.

---

## Lane B — In-person scan / business card (handshake)

**Different product surface — complements appointments.**

At event / clinic lobby / networking:

| Mechanism | What exchanges |
|-----------|----------------|
| **QR on phone** | vCard + optional “book with me” link |
| **NFC tap** (Android) | same payload |
| **CAPTN card** | stable URL → Sarah’s scheduling page or Brian’s service |

Not Google scraping — **opt-in scan**. Both parties choose to exchange.

Fleet tie-in later: Puppy **stable URL** hosts lightweight `/sarah` or `/book` PWA.

---

## Lane C — What we don’t promise

| Item | Why |
|------|-----|
| Jury duty automation | Gov systems, legal identity, often not delegatable |
| Agent impersonating Sarah on phone | Cost, law, error rate |
| Mining her contacts for helpers | Invasive — Sarah names people explicitly |
| Booking without confirmation | Medical + penalty risk |

---

## Sarah v2 — voice · scan · integrity · plugins (Brian 2026-06-15)

Sarah wants:
- **Voice activated**
- **Scan schedule** → learn pattern (seminary Tue/Thu, etc.)
- **Short interview** → basic needs once
- **Personality shifts slightly per user** — not one generic bot
- **Prerequisites as plugins** — school function → what to bring → allowed items (no peanuts)
- **Integrity:** *"How do I know it understood me, not assumed like Gemini?"*

### Integrity protocol (core — not a plugin)

Every booking attempt:

1. **Echo** what was heard  
2. **2–3 confirm questions** — including "did I get this wrong?"  
3. **List assumptions** before showing slot offers ("I assumed mornings because…")  
4. **No match/offers until Sarah says yes to echo**

This is Sarah's trust layer. Without it, product is Gemini-with-calendar.

### Voice (KISS)

- Short commands in · short confirm out  
- Capped turns — integrity Qs count  
- Same backend as `APPOINTMENT_REQUEST.txt` text fallback  
- Not Ultra Live burn loops

### Schedule scan

- Sarah **opts in**: photo of schedule · ICS export · calendar paste  
- **No Google life mining** — she hands the schedule  
- Output: **pattern anchors** for match + gentle itinerary only

### Prerequisites plugin chain

```
plugin_school_event     → recital, parent night, seminary function
plugin_school_bring     → what to bring
plugin_school_rules     → allowed items (no peanuts, nut-free room)
```

Medical prerequisites = future plugins (fasting, etc.) — **don't build until asked**.

### Personality (slight per user)

| Sarah | Gentle · minimal intrusion · seminary-aware |
| Busy user | Terse · bundle-aggressive (opt-in) |

`personality.json` per user — slight tone delta on one core engine.

### KISS + plugins always

**Core:** voice/text in → integrity loop → interview store → match → bundle question → BOOK tap  

**Everything else:** plugin. See `concepts/SARAH_APPOINTMENT_PLUGINS.txt`

### Probes for Sarah (she has no more yet — hold)

When ready, ask her:
- fasting before labs?
- ride / parking?
- telehealth vs in-person?
- companion allowed?

---

## Build phases (when Brian says go)

| Phase | Ship | Cost |
|-------|------|------|
| **0** | Core + **integrity echo/confirm** + interview + text request | $0 |
| **1** | Schedule scan (photo/ICS) → pattern | $0 |
| **2** | Match + bundle question + reminders + log | $0 |
| **3** | Voice in/out (capped) | $0–low |
| **4** | plugin_medical_web (one portal) | time |
| **5** | plugin_school_event → bring → rules | time |
| **6** | Stable `/book` on puppy + QR | $0 |
| **7** | Outbound phone voice | **$** — later |

---

## Sarah onboarding (interview — once)

1. Portals / doctors she uses  
2. Reminder channel (voice · sms · calendar)  
3. **Intrusion level** (minimal for Sarah)  
4. **Bundle preference** (yes / no / ask)  
5. Schedule scan opt-in (how she'll share pattern)  
6. School/allergy plugins needed? (peanuts, etc.)  
7. Escalation if miss reminder (none default for Sarah)

Every session still runs **integrity echo** — interview ≠ skip confirm.

---

## Fleet assignment (when un-parked)

| Who | Role |
|-----|------|
| **CAPTN** | appointment architect · templates · medical web playbooks |
| **Puppy** | stable `/book` URL · QR host |
| **Brian** | Sarah relationship · credential handoff · pricing |
| **Sarah** | confirm · tap BOOK · show up |

Camel art + CB1 reload stay priority until Brian lifts HOLD.

---

## One line for Sarah

*"I echo back what I heard, ask two questions so you know I didn't assume, then offer slots — you tap BOOK. Voice or text. Plugins handle school stuff like peanuts when you need them."*

Proposal: `drop_pile/proposals/inbox/PROPOSAL_sarah_appointment_lane.md`  
Plugins: `concepts/SARAH_APPOINTMENT_PLUGINS.txt`
