#!/usr/bin/env bash
# Package Baseball Card Valuation — commercial v1 for Play Store / puppy deploy.
# Run on PENGUIN (captain). Output → Google Drive/releases/
set -euo pipefail

VERSION="${1:-1.0.0}"
DIR="$(cd "$(dirname "$0")" && pwd)"
DRIVE="/mnt/shared/GoogleDrive/MyDrive"
RELEASE_ROOT="$DRIVE/releases/baseball_cards_v${VERSION}"
ARCHIVE_NAME="baseball_cards_commercial_v${VERSION}.tar.gz"
STAMP="$(date -Iseconds)"

if [[ ! -d "$DRIVE" ]]; then
  echo "ERROR: Drive not mounted at $DRIVE"
  exit 1
fi

echo "[*] Commercial package v${VERSION} @ ${STAMP}"

rm -rf "$RELEASE_ROOT"
mkdir -p "$RELEASE_ROOT/app/data/collx" "$RELEASE_ROOT/app/uploads" "$RELEASE_ROOT/app/data/dev"

APP_FILES=(
  app_baseball.py
  index_baseball.html
  live_capture.html
  collx_data.py
  collx_gmail.py
  scan_pipeline.py
  dev_log.py
  scan_collx_drive.py
  start_baseball.sh
  install_on_puppy.sh
  open_for_phone.sh
  AGENTS.md
  puppy_qa.md
  package_commercial.sh
)

for f in "${APP_FILES[@]}"; do
  cp -f "$DIR/$f" "$RELEASE_ROOT/app/$f"
done

cp -f "$DRIVE/lester/START_BASEBALL_ON_PUPPY.sh" "$RELEASE_ROOT/install_on_puppy64.sh"

# Commercial ships empty collection — user imports their own CollX CSV.
echo '[]' > "$RELEASE_ROOT/app/data/collection.json"
echo '{}' > "$RELEASE_ROOT/app/data/collx/meta.json"
echo '[]' > "$RELEASE_ROOT/app/data/collx/catalog.json"

cat > "$RELEASE_ROOT/RELEASE.json" <<EOF
{
  "product": "Baseball Card Valuation",
  "commercial_version": "${VERSION}",
  "build_machine": "penguin",
  "built_at": "${STAMP}",
  "channel": "commercial_v1",
  "play_store": "reserved",
  "features": [
    "CollX CSV import only",
    "Phone-first List / Sync / Stats",
    "PSA precursor scan with save-to-card",
    "Practice sim + retake prompt",
    "PWA standalone manifest"
  ],
  "human_test": {
    "tester": "Sarah",
    "platform": "Android Wi-Fi",
    "result": "pass_core_plus_scan",
    "notes": "Search, sync, scroll smooth; scan round 2 fixed"
  },
  "data_policy": "No personal cards in package — empty collection.json",
  "deploy_target": "puppy64 LAN server or Play Store TWA wrapper"
}
EOF

cat > "$RELEASE_ROOT/PLAY_STORE_SHIP.md" <<'EOF'
# Play Store / Commercial Ship — Baseball Card Valuation v1

## What this is
First commercial package — phone-first CollX collection + PSA precursor scan.
Penguin packaged; puppy64 serves on home Wi-Fi; Play Store slot reserved by Lester.

## Install on puppy64
```bash
DRIVE=~/GoogleDrive/MyDrive
[[ -d /mnt/shared/GoogleDrive/MyDrive ]] && DRIVE=/mnt/shared/GoogleDrive/MyDrive
PKG="$DRIVE/releases/baseball_cards_v1.0.0"
mkdir -p ~/Applications/cursor/baseball_cards
cp -rf "$PKG/app/"* ~/Applications/cursor/baseball_cards/
bash "$PKG/install_on_puppy64.sh"
```

## Phone URL
After install: `http://192.168.x.x:8002` (from script output).
Post to `puppy_outbox.txt` on Drive.

## Play Store path (Lester)
1. **TWA / PWA** — wrap the puppy LAN URL or production host
2. **Listing** — Award Winner Author angle + CollX import story
3. **Sandbox** — verify standalone manifest (`/manifest.json`)
4. **Privacy** — no cloud account; data stays on device + user's CollX CSV

## Acceptance before listing
- [ ] Health: `data_mode=collx`, `commercial_version` present
- [ ] CollX import from phone upload works
- [ ] Scan saves PSA line to List
- [ ] PWA installs on Android (Add to Home Screen)

## Support files
- `RELEASE.json` — build metadata
- `SHA256SUMS` — integrity check
- `app/puppy_qa.md` — puppy QA checklist
EOF

cat > "$RELEASE_ROOT/install_commercial.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DRIVE="${HOME}/GoogleDrive/MyDrive"
[[ -d "/mnt/shared/GoogleDrive/MyDrive" ]] && DRIVE="/mnt/shared/GoogleDrive/MyDrive"
PKG="$(cd "$(dirname "$0")" && pwd)"
DST="${HOME}/Applications/cursor/baseball_cards"
mkdir -p "$DST/data/collx" "$DST/uploads"
cp -rf "$PKG/app/"* "$DST/"
chmod +x "$DST"/*.sh 2>/dev/null || true
echo "Installed to $DST"
bash "$PKG/install_on_puppy64.sh"
EOF
chmod +x "$RELEASE_ROOT/install_commercial.sh"

(
  cd "$RELEASE_ROOT"
  find . -type f ! -name SHA256SUMS | sort | xargs sha256sum > SHA256SUMS
)

(
  cd "$(dirname "$RELEASE_ROOT")"
  rm -f "$ARCHIVE_NAME"
  tar -czf "$ARCHIVE_NAME" "$(basename "$RELEASE_ROOT")"
)

# Mirror latest app to lester for puppy pull
mkdir -p "$DRIVE/lester/baseball_cards"
cp -rf "$RELEASE_ROOT/app/"* "$DRIVE/lester/baseball_cards/"

# Sync to penguin workspace copy marker
echo "$VERSION" > "$DIR/COMMERCIAL_VERSION.txt"

echo "OK: $RELEASE_ROOT"
echo "ARCHIVE: $DRIVE/releases/$ARCHIVE_NAME"
ls -la "$DRIVE/releases/$ARCHIVE_NAME" "$RELEASE_ROOT/RELEASE.json"
