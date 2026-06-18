# STABLE URL — Puppy execute (Play Store pipe)

**Brian needs:** fixed HTTPS for 12 Play Store testers.  
**You own:** puppy64 24/7 + named Cloudflare (not trycloudflare).

---

## Paste — Puppy Cursor

```
STABLE URL — read fleet/PLAY_STABLE_URL_FIX.txt
Ensure ~/.stan/cloudflare.env has CLOUDFLARE_TUNNEL_TOKEN + CLOUDFLARE_PUBLIC_URL
Run: bash lester/cloudflare_puppy.sh
Post fleet/STABLE_PUBLIC_URL.txt + puppy_outbox RUNNING
```

---

## Checklist

- [ ] App up locally (`curl http://127.0.0.1:5000/api/status` slicer OR :8002 baseball)
- [ ] Named tunnel running (`cloudflared tunnel run --token`)
- [ ] `fleet/STABLE_PUBLIC_URL.txt` written
- [ ] `fleet/PLAY_TESTER_URL.txt` written
- [ ] Public URL loads on **LTE** (not just LAN)

Token: `lester/lester_keys.md` — do not ask Brian to paste.

---

## If PUBLIC_URL not set yet

Brian/Uncle must finish Cloudflare dashboard **Public Hostname** once.  
See `fleet/CLOUDFLARE_PASTE.txt` — click Continue, set localhost:5000, copy https URL.

Quick tunnel is **NOT** acceptable for Play.
