# Video Slicer — $0/mo stack (pre-customers)

Brian rule: **fixed monthly costs only** until paying customers. No Gemini cloud backend. No VPS yet.

## Monthly bill

| Item | Cost |
|------|------|
| Puppy PC (already owned) | $0 |
| Cloudflare named tunnel | $0 |
| PWA / Add to Home Screen | $0 |
| Play Store | **Deferred** ($25 one-time later) |
| Groq transcribe | Usage only — **capped** (see below) |
| Gemini cloud | **Not used** for slicer |

## Architecture

```
Phone (LTE or Wi-Fi)
    → https://FIXED-URL (Cloudflare named tunnel)
    → puppy:5000 app_mobile.py
    → Groq API (transcribe uploads only)
```

Brian's 180 cloud videos: **dev only on penguin** — not shipped to strangers.

## Puppy setup (one time)

1. Copy lester from Drive:
   ```bash
   mkdir -p ~/lester
   cp -f ~/GoogleDrive/MyDrive/lester/app_mobile.py ~/lester/
   cp -f ~/GoogleDrive/MyDrive/lester/start_slicer*.sh ~/lester/
   cp -f ~/GoogleDrive/MyDrive/lester/setup_slicer_zero.sh ~/lester/
   chmod +x ~/lester/*.sh
   ```

2. Groq key on puppy:
   ```bash
   mkdir -p ~/.stan
   echo 'GROQ_API_KEY=...' >> ~/.stan/groq.env
   echo 'SLICER_UPLOADS_PER_IP_DAY=10' >> ~/.stan/groq.env
   ```

3. Named Cloudflare tunnel (stable URL — not random trycloudflare):
   - Cloudflare Zero Trust → Tunnels → Create → copy token
   - Public hostname → `http://localhost:5000`
   ```bash
   export CLOUDFLARE_TUNNEL_TOKEN='eyJ...'
   bash ~/lester/setup_slicer_zero.sh
   ```

4. Post URL to Drive:
   ```bash
   echo "https://YOUR-FIXED-HOST" > ~/GoogleDrive/MyDrive/SLICER_PHONE_URL.txt
   echo "slicer RUNNING $(date -Iseconds)" >> ~/GoogleDrive/MyDrive/puppy_outbox.txt
   ```

## Phone test

1. Open `SLICER_PHONE_URL.txt` on LTE
2. Add to Home Screen
3. Pick local video → search → share (plain text, no ugly links)

## Groq cap (no blank check)

Default: **10 uploads per IP per day** (`SLICER_UPLOADS_PER_IP_DAY` in groq.env).

## When customers exist

Then add fixed lines: VPS ~$6/mo, Play $25 once, Groq budget line item.

## Files

- `setup_slicer_zero.sh` — puppy install + tunnel + systemd hint
- `start_slicer_host.sh` — app only
- `start_slicer_tunnel_named.sh` — tunnel only (needs token)
- `package_slicer_playstore.sh` — deferred Play packaging
