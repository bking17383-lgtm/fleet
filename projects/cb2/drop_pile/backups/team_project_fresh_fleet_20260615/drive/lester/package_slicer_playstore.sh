#!/usr/bin/env bash
# Video Slicer — Play Store internal-test package (TWA / PWA wrapper).
# Run on penguin. Output → Google Drive/releases/
set -euo pipefail

VERSION="${1:-0.1.0}"
DIR="$(cd "$(dirname "$0")" && pwd)"
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
RELEASE_ROOT="$DRIVE/releases/slicer_playstore_v${VERSION}"
ARCHIVE_NAME="slicer_playstore_v${VERSION}.tar.gz"
STAMP="$(date -Iseconds)"

if [[ ! -d "$DRIVE" ]]; then
  echo "ERROR: Drive not mounted at $DRIVE"
  exit 1
fi

echo "[*] Slicer Play Store package v${VERSION} @ ${STAMP}"

rm -rf "$RELEASE_ROOT"
mkdir -p "$RELEASE_ROOT/app"

APP_FILES=(
  app_mobile.py
  start_slicer.sh
  package_slicer_playstore.sh
)

for f in "${APP_FILES[@]}"; do
  cp -f "$DIR/$f" "$RELEASE_ROOT/app/$f"
done

cat > "$RELEASE_ROOT/RELEASE.json" <<EOF
{
  "product": "Video Slicer",
  "commercial_version": "${VERSION}",
  "build_machine": "penguin",
  "built_at": "${STAMP}",
  "channel": "playstore_internal_test",
  "features": [
    "Search spoken word in uploaded videos",
    "Share plain-text quotes + 2-sentence context",
    "10s clip export",
    "PWA standalone + TWA assetlinks hook"
  ],
  "data_policy": "No Brian cloud catalog in public build — upload-your-own only",
  "deploy_target": "stable HTTPS host + Play internal testing track"
}
EOF

cat > "$RELEASE_ROOT/PLAY_STORE_SHIP.md" <<'EOF'
# Play Store Internal Testing — Video Slicer

## What ships
- **PWA** at stable HTTPS URL (not trycloudflare — URL must not rotate)
- **TWA wrapper** (Android app shell → full-screen Chrome)
- **Internal testing** track — up to 100 testers, no public listing

## Prerequisites (blockers)

| Item | Owner | Notes |
|------|-------|-------|
| Stable HTTPS URL | puppy / Brian | e.g. `https://slicer.example.com` or named Cloudflare tunnel |
| Always-on host | puppy | `app_mobile.py` on :443 or reverse proxy |
| Play Console app | Lester 6 | Create app → Internal testing |
| PNG icons 512×512 | Lester 6 | Export from logo.svg for store listing |
| Privacy policy URL | Lester 6 | Required even for internal test |

## Server env (production host)

```bash
# ~/.stan/groq.env or systemd Environment=
GROQ_API_KEY=...
SLICER_TWA_PACKAGE=com.seizetheclip.slicer
SLICER_TWA_SHA256=AA:BB:...   # from bubblewrap signing key
```

Verify: `curl -s https://YOUR_HOST/.well-known/assetlinks.json`

## Build TWA (puppy or any Linux with Node)

```bash
npm install -g @bubblewrap/cli
bubblewrap init --manifest=https://YOUR_HOST/manifest.json
# package: com.seizetheclip.slicer (match SLICER_TWA_PACKAGE)
bubblewrap build
# → app-release-signed.apk / .aab for Play Console upload
```

Or use [PWABuilder](https://www.pwabuilder.com/) → paste manifest URL → Generate Android package.

## Play Console upload

1. Create app → **Internal testing** release
2. Upload `.aab` from bubblewrap
3. Add tester emails (cellular users OK — they hit YOUR_HOST over LTE)
4. Testers install from Play Store link (not sideload)

## Public tester experience (cellular)

1. Install from Play internal test link
2. Open app → lands on YOUR_HOST PWA
3. **Pick local videos** → upload → transcribe → search → share
4. No Brian personal cloud library in v0.1

## Acceptance before inviting strangers

- [ ] `GET /manifest.json` — standalone, icons, description
- [ ] `GET /.well-known/assetlinks.json` — non-empty on prod
- [ ] Share paste has **no https://** (plain text only)
- [ ] Upload + search works on LTE (not LAN-only)
- [ ] Video play has sound on 2+ Android devices

## Files in this package

- `RELEASE.json` — build metadata
- `app/app_mobile.py` — server + PWA
- `app/start_slicer.sh` — local dev start
EOF

cat > "$RELEASE_ROOT/install_on_host.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "$0")" && pwd)"
DST="${HOME}/lester"
mkdir -p "$DST"
cp -rf "$PKG/app/"* "$DST/"
chmod +x "$DST"/*.sh 2>/dev/null || true
echo "Installed to $DST — configure reverse proxy + SLICER_TWA_* env, then:"
echo "  cd $DST && bash start_slicer.sh"
EOF
chmod +x "$RELEASE_ROOT/install_on_host.sh"

(
  cd "$RELEASE_ROOT"
  find . -type f -not -name 'SHA256SUMS' | sort | xargs sha256sum > SHA256SUMS
)

(
  cd "$(dirname "$RELEASE_ROOT")"
  rm -f "$ARCHIVE_NAME"
  tar -czf "$ARCHIVE_NAME" "$(basename "$RELEASE_ROOT")"
)

mkdir -p "$DRIVE/lester"
cp -f "$DIR/app_mobile.py" "$DRIVE/lester/app_mobile.py"

echo "OK: $RELEASE_ROOT"
echo "ARCHIVE: $DRIVE/releases/$ARCHIVE_NAME"
