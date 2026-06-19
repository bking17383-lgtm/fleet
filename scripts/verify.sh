#!/usr/bin/env bash
# FALSE-GREEN FIREWALL — verify a claim with EVIDENCE. Prints PASS/FAIL + the facts. No trust, just proof.
# The doer never runs this on their own claim — the independent checker (cb1/Opus) does.
#   verify.sh url  <URL> [must-contain]        e.g. verify.sh url https://george.hitme.dev "George"
#   verify.sh file <relpath-in-fleet> [must-contain]
#   verify.sh say  <url|file> <target> [contain]   same as above but ALSO speaks PASS/FAIL out loud
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
say() { command -v espeak-ng >/dev/null 2>&1 && espeak-ng -a 200 -s 140 "$1" --stdout 2>/dev/null | paplay 2>/dev/null; }

SPEAK=0
if [ "$1" = "say" ]; then SPEAK=1; shift; fi
KIND="$1"; TARGET="$2"; WANT="$3"

result() { # $1=PASS/FAIL  $2=detail
  echo "$1  $KIND $TARGET  [$2]"
  [ "$SPEAK" = 1 ] && { [ "$1" = PASS ] && say "verified pass" || say "verify failed"; }
  [ "$1" = PASS ]
}

case "$KIND" in
  url)
    body=$(curl -sL -m 12 "$TARGET" 2>/dev/null)
    code=$(curl -sL -o /dev/null -m 12 -w '%{http_code}' "$TARGET" 2>/dev/null)
    bytes=$(printf '%s' "$body" | wc -c | tr -d ' ')
    ok=1; [ "$code" -ge 200 ] 2>/dev/null && [ "$code" -lt 400 ] 2>/dev/null || ok=0
    miss=""
    if [ -n "$WANT" ]; then printf '%s' "$body" | grep -qi "$WANT" || { ok=0; miss=" missing '$WANT'"; }; fi
    [ "$ok" = 1 ] && result PASS "HTTP $code, ${bytes}B${WANT:+, contains '$WANT'}" \
                  || result FAIL "HTTP $code, ${bytes}B$miss"
    ;;
  file)
    f="$HOME/fleet/$TARGET"
    if [ -f "$f" ] && { [ -z "$WANT" ] || grep -qi "$WANT" "$f"; }; then
      result PASS "exists${WANT:+, contains '$WANT'}"
    else
      [ -f "$f" ] && result FAIL "exists but missing '$WANT'" || result FAIL "file not found"
    fi
    ;;
  *)
    echo "usage: verify.sh [say] url <URL> [contain] | [say] file <relpath> [contain]"; exit 2 ;;
esac
