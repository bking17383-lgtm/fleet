# What Daddy needs from Brian (stranger phones)

**Updated:** 2026-06-14  
**Read this when you get back — 5 decisions unblock everything**

---

## 1. Cloudflare named tunnel (required)

Random `trycloudflare.com` links **die** and need Chromebook awake. Strangers need a **fixed HTTPS URL**.

**I need one of:**

- [ ] **A)** You create Cloudflare Zero Trust tunnel on puppy64 → public hostname → `http://localhost:8002`  
      Paste token into `~/.stan/cloudflare.env` on puppy OR tell Lester to save to Drive `lester/CLOUDFLARE_TUNNEL_TOKEN.txt` (redact after)
- [ ] **B)** You give a subdomain you control (e.g. `cards.yourdomain.com`) and Cloudflare DNS access
- [ ] **C)** You say "use Cloudflare free hostname" and Puppy picks name in dashboard

**Without this:** strangers on LTE cannot reach the app reliably.

---

## 2. Which app goes public first?

- [ ] **Baseball commercial demo** (recommended — package ready on Drive)
- [ ] Slicer (needs Groq budget + more abuse surface)
- [ ] Both later — pick one first

---

## 3. What data do strangers see?

- [ ] **Commercial empty** — import your own CollX (safest for strangers)
- [ ] **Demo catalog** — fake/sample cards only (Lester can write JSON)
- [ ] **Never** Brian's real 497-card collection on a public URL

---

## 4. Access control

- [ ] **Fully public link** — anyone with URL
- [ ] **Simple passcode** in URL (`?code=WORD`) — Puppy adds gate
- [ ] **Invite-only** — you text link manually (still need fixed HTTPS)

---

## 5. Puppy64 must stay on

- [ ] Confirm puppy64 PC powered + Drive synced 24/7 while strangers test
- [ ] Who reboots puppy if it dies? (Puppy agent can't wake hardware from CB2)

---

## Optional but helpful

| Item | Why |
|------|-----|
| Groq API key on puppy | Only if slicer goes public first |
| Privacy policy one-pager | Play Store + stranger trust — Lester can draft |
| Custom short link | bit.ly or CF redirect — easier texts |
| Tester recruitment channel | Discord / email list — **after** HOLD lifts |

---

## What you do NOT need to do

- Be the human tester (on HOLD)
- Relay messages between Cursors
- Keep CB2 awake for tunnels (move host to puppy)

---

## When you return, say one line

*"Fixed tunnel token is on Drive"* OR *"Baseball public, empty collection, public link"* — Daddy queues Puppy immediately.
