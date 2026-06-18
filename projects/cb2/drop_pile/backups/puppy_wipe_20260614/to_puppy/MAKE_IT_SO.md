# MAKE IT SO — puppy64 Video Slicer ($0/mo)

**From:** Big Daddy (penguin)  
**When:** run now on puppy64

## One command

```bash
DRIVE=~/GoogleDrive/MyDrive
[[ -d /mnt/shared/GoogleDrive/MyDrive ]] && DRIVE=/mnt/shared/GoogleDrive/MyDrive
mkdir -p ~/lester ~/.stan
cp -f "$DRIVE/lester/"{app_mobile.py,run_slicer_zero.sh,start_slicer_host.sh,start_slicer_tunnel_named.sh,setup_slicer_zero.sh} ~/lester/
chmod +x ~/lester/*.sh

# Groq key: copy from penguin ~/.stan/groq.env (Brian only — never commit)
# Or Brian pastes into ~/.stan/groq.env on puppy:
#   GROQ_API_KEY=...
#   SLICER_UPLOADS_PER_IP_DAY=10
#   CLOUDFLARE_TUNNEL_TOKEN=...   ← fixed URL ($0)

bash ~/lester/run_slicer_zero.sh
```

## After run

1. `cat $DRIVE/SLICER_PHONE_URL.txt` — post to Brian's phone
2. If `CLOUDFLARE_TUNNEL_TOKEN` set → URL is **fixed** (cellular testers OK)
3. If not → quick tunnel (dev only; URL rotates)

## Keep alive

Puppy stays on. Reboot → run `bash ~/lester/run_slicer_zero.sh` again.

## Done when

- `curl -s http://127.0.0.1:5000/api/status` → ok
- `SLICER_PHONE_URL.txt` on Drive updated
- Brian Add to Home Screen on LTE works
