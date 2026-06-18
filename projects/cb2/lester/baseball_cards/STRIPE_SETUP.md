# Card Reader — Stripe setup

## Money flow
```
User → Stripe Checkout → your Stripe balance → bank (Dashboard → Payouts)
```
Product: **Card Reader Pro** · hello@hitme.dev receipts

## 1. Stripe Dashboard (Brian ~10 min)
1. https://dashboard.stripe.com/register
2. **Products** optional — we create prices in code
3. **Developers → API keys** → copy test keys first
4. Paste into `~/.stan/stripe.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```
5. `chmod 600 ~/.stan/stripe.env`

## 2. Pricing (wired in app)
| Plan | Price | Mode |
|------|-------|------|
| Free | $0 | 5 scans / month |
| Pro monthly | $4.99/mo | subscription |
| Pro yearly | $29/yr | one-time year unlock |

## 3. Test
```bash
bash lester/baseball_cards/start_baseball.sh
# open http://127.0.0.1:8002
# run 6 scans → upgrade prompt → Stripe test card 4242 4242 4242 4242
```

## 4. Live
- Named HTTPS URL required (cards.hitme.dev)
- Switch to `sk_live_` / `pk_live_` in stripe.env
- Stripe Dashboard → activate account → add bank

## API routes
- `GET /api/billing/status` — scans left · pro flag
- `POST /api/billing/checkout` `{plan:"monthly"|"yearly", client_id}`
- `GET /billing/success?session_id=` — activates Pro
- `POST /api/scan/grade` — blocked at free limit (402)

Data: `data/billing_usage.json` · `data/billing_pro.json` (local, not Drive secrets)
