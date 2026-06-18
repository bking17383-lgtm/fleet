# CB2 screen + Cloudflare setup

**Updated:** 2026-06-14

## Screen read (Daddy / Cursor)

| Tool | Command | Notes |
|------|---------|-------|
| Screenshot | `bash ~/.stan/screen_capture.sh` | Saves `~/.stan/screen/latest.png` |
| Clipboard | `bash ~/.stan/clipboard_read.sh` | Brian copies in Chrome → Daddy reads text |
| X tools | `xdotool`, `scrot`, `import` | Installed |

### Chromebook permission (required for real screen)

Linux often captures **black** until Chrome OS allows it:

1. Chrome **Settings → Advanced → Developers → Linux**
2. Turn on **Allow Linux applications to access…** (microphone/camera/display — use latest toggle available)
3. **Restart Linux** (Shut down Linux container, turn back on)
4. Re-run: `bash ~/.stan/screen_capture.sh`

If still black: Chrome windows live **outside** Crostini — use **clipboard paste** or **Lester6 Gemini Live** for Chrome/gdoc eyes (fleet design).

## Cloudflare (CB2 interim)

| File | Purpose |
|------|---------|
| `~/.stan/cloudflare_cb2.sh` | Baseball :8002 + tunnel |
| `~/.stan/cloudflare.env` | Paste **CLOUDFLARE_TUNNEL_TOKEN** for fixed URL |
| `~/.stan/cloudflare_cb2.log` | Tunnel log |
| `MyDrive/BRIAN_PHONE.txt` | Public link for phones |

### Named tunnel (strangers LTE — fixed URL)

1. Cloudflare Zero Trust → Tunnels → Create
2. Public hostname → `http://localhost:8002`
3. Paste token into `~/.stan/cloudflare.env`:
   ```
   CLOUDFLARE_TUNNEL_TOKEN='...'
   CLOUDFLARE_PUBLIC_URL='https://your-host.example.com'
   ```
4. `bash ~/.stan/cloudflare_cb2.sh`

### Quick tunnel (dev — URL rotates)

No token → script uses trycloudflare automatically.

```bash
bash ~/.stan/cloudflare_cb2.sh
```

Move **named** tunnel to **puppy64** for 24/7 stranger testing.
