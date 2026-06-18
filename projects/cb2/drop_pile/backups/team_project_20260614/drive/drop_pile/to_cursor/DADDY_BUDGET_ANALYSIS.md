# Daddy analysis — Brian budget + GL build decision

**From:** Uncle · CB1  
**To:** Captain / whoever holds design desk (T3 killed — read anyway)  
**Time:** 2026-06-14  
**Brian rule:** **$20 AI + $20 tools** until apps make money. Ultra → Pro in days.

---

## Executive summary

Brian is at **~$200/mo Google Ultra** today — **10×** his target AI spend. Cursor (~$20) is the lane that ships. Fleet infra (Cloudflare, Tailscale, Groq, puppy64) is **~$0** on paper. **Do not** add voice APIs, custom GL servers, or OCR pipelines — that breaks the cap and repeats “never had good hear/speak we built.”

**Amen alignment:** Kill Ultra. Pro + Cursor + Drive = whole GL v0. Delegate execute to Puppy when Drive proves it — not new subscriptions.

---

## Bill picture (network-visible)

See **`fleet/BRIAN_MONTHLY_BILLS.txt`** for the table Brian can edit.

| Bucket | Now | Target |
|--------|-----|--------|
| Google AI | ~$200 Ultra | **~$20 Pro** |
| Cursor | ~$20 | ~$20 (keep) |
| Cloudflare / Tailscale / Groq | ~$0 | ~$0 |
| CollX / Readsy / other | **unknown** | Brian fill in |
| **Fleet AI+tools target** | **~$220+** | **~$40 + ?** |

**Savings from Ultra → Pro:** ~**$180/mo** — use that as runway, not new SaaS.

---

## What “simple GL” costs under Brian’s cap

| Approach | Fits $40 cap? | Verdict |
|----------|---------------|---------|
| Gemini **Pro** app Live + `gl/instructions for AI.md` + IDEA bus | **Yes** | **Ship this** |
| Hosted voice API (Realtime, Vapi, …) | **No** | Per-minute blank check |
| Self-host voice on puppy64 | **Marginal** | Time cost; OK home-only, not walking LTE |
| Phone video OCR off-network | **No** | Hardest layer + variable cost |

**Compare to others:** Everyone else uses **vendor Live app (A)** or **voice SaaS (B)**. Custom (C/D) is startup territory. Puppy “found on web” must be classified A or B — reject C/D for v0.

---

## Fleet spend policy (enforce on delegate)

1. **No new recurring line** without fixed $/mo OR hard API cap (see `FINANCE_TREE_SLICER.txt` rule).
2. **No captain execute** that adds API meters (voice, vision OCR).
3. **Pass line before new tools:** puppy_outbox `hostname: puppy64`, PLATE ack confirmed, exports not stub — **free work first**.
4. **Ultra cancel** is P0 — bigger win than any GL engineering sprint.

---

## What Daddy / desk should do (not build)

| Do | Don’t |
|----|-------|
| Remind Brian: Ultra cancel → Pro | Start GL scanner loops that burn context |
| Keep **`BRIAN_MONTHLY_BILLS.txt`** updated | Add OpenAI Realtime / OCR spike |
| Queue **PUPPY** + **EXPORT** only | Second captain tab |
| Capture IDEAS → `fleet/bus/IDEAS.txt` | Custom hear/speak device v0 |

---

## Unknown bills (Brian to remember)

Fleet **cannot** see bank/Gmail from here. Likely candidates Brian forgot:

- CollX subscription (baseball app)
- Readsy (IDEAS spike)
- Old Google One tier if stacked with Ultra
- YouTube Premium (may have been bundled in Ultra)

**Action:** Brian fills **`fleet/BRIAN_MONTHLY_BILLS.txt`** bottom section → one true **ACTUAL TOTAL**.

---

## One paragraph for Brian

You’re right: **$20 + $20 until money**. Ultra is the leak. Cursor + Pro Gemini + Drive docs **is** the product until baseball/slicer/GL earns the next dollar. Don’t jailbreak, don’t rebuild Gemini, don’t OCR while walking — **cancel Ultra, fill the bill sheet, walk and say IDEA.**

---

Append to `mac_inbox.txt` when captain live.
