# Android phone fleet — same house (~100 Mbps Wi-Fi)

**Daddy (T3) policy.** Phones are **clients + testers + Live cameras**, not Cursor hosts.

---

## Network rule

All phones on **same home Wi-Fi as puppy64**.

| URL type | When |
|----------|------|
| `http://192.168.x.x:8002` | Baseball — **preferred** (puppy LAN) |
| `http://192.168.x.x:5000` | Slicer — when unhold |
| Cloudflare tunnel | Fallback only — avoid for daily use |

Update **`MyDrive/BRIAN_PHONE.txt`** when puppy posts LAN IP.

100 Mbps shared is enough for: 4–6 phones browsing PWAs + 1 Live camera + CollX sync.

---

## Assign phones by role (label with tape/sticker)

| Role | Count | Job |
|------|-------|-----|
| **A — Brian primary** | 1 | CollX export → Drive `collx_inbox/`; daily baseball |
| **B — Live eyes** | 1 | Gemini Live camera for jailbreak (pair with CB2 Lester 6) |
| **C — Testers** | 2–4 | Open `BRIAN_PHONE.txt` URL; run `TESTER_PLAYBOOK.md` checklist |
| **D — Spare / hotspot** | optional | Backup Wi-Fi if puppy LAN debugging |

Do **not** install Cursor on phones. Do **not** run Termux agents unless spike.

---

## Per-role setup (one time)

### A — Primary
- Google Drive app → account synced
- CollX installed → CSV export to `collx_inbox/`
- Chrome → Add to Home Screen for baseball PWA (after puppy LAN live)

### B — Live eyes (jailbreak)
- Gemini app → Live session with CB2 Lester instructions
- Fixed mount or light box later (`IDEA_estate_drawer_catalog.md`)
- Transcript → paste to `drop_pile/from_lester/live_transcript_<date>.txt` (until scrape bot exists)

### C — Testers
- Same Wi-Fi as puppy
- Open link from `BRIAN_PHONE.txt`
- Report: `drop_pile/from_tester/phone<N>_feedback.txt`

---

## Power linking (how phones join the stack)

```text
Phones (Wi-Fi)
  → puppy64 LAN (:8002 baseball, :5000 slicer)
  → Drive (CollX CSV, transcripts, tester feedback)
  → CB2 Lester 6 + Live eyes phone
  → T3 Daddy reads queue + drop_pile
  → puppy executes queue
```

---

## Blockers (fix before phone fleet matters)

1. **puppy_qa** — baseball not on LAN yet
2. **free_lester export** — jailbreak blind without `.md`
3. **CB2 Daddy** — `DADDY_T3_CB2_BOOT.txt`

---

## Avoid

- Cellular testers until fixed HTTPS tunnel on puppy
- Medical photos in Live camera roll (Brian note)
- Each phone on different Wi-Fi band isolated from puppy (guest network without LAN access)

---

## After Lester jailbreak — eyes & ears (recommended phones)

| Role | Phones | Job |
|------|--------|-----|
| **Live eyes** | 1–2 | Gemini Live camera — one item at a time, light box later |
| **Ears / transcript** | 1 | Open puppy `:8765` paste sink — save Live text to Drive |
| **Brian primary** | 1 | CollX, baseball PWA, approve captures |
| **Testers** | 2+ | Parallel QA on `BRIAN_PHONE.txt` URL |

**Yes — more phones help** once jailbreak works. They are **sensors**, not compute nodes.

Do **not** run Cursor/Termux agents on phones. Power = **camera + mic + Wi‑Fi to puppy/CB2**.

### Eyes workflow (post-jailbreak)

```text
Phone B (Live camera) → Gemini Live on CB2 with Free Lester instructions
Phone C (browser)     → http://<puppy-LAN>:8765 paste transcript
Drive                 → drop_pile/from_lester/live_transcript_*.txt
puppy / Flask         → parse → catalog row (cards now, estate later)
```

### Minimum useful fleet: **4 phones**

- 1 Live eyes · 1 paste/ears · 1 Brian · 1 tester spare

### Scale to **6+** when:

- Human testers needed in parallel
- Second Live angle (front/back card) on two phones
- Dedicated CollX export phone always on charger

All phones: **same home Wi‑Fi as puppy64** (100 Mbps shared is fine).
