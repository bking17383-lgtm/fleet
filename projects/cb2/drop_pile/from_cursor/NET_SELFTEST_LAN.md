# NET selftest — from CB2 LAN scan (Gem · not puppy post)
time: 2026-06-16T03:48:58-07:00
target: puppy64 @ 192.168.1.4
result: **FAIL** (partial reachability)

| Check | Result |
|-------|--------|
| LAN ping/tcp :8002 | PASS |
| baseball /api/health | FAIL 404 |
| /live/capture | FAIL 404 |
| jailbreak sink :8766 | FAIL closed |
| mesh :8765 | FAIL closed |
| SSH :22 | FAIL refused |

**Cause:** upload_server on :8002 — not app_baseball.py

**Fix:** puppy terminal → `bash ~/GoogleDrive/MyDrive/lester/PUPPY_JAILBREAK.sh`

When puppy runs fix, replace this file with PASS from puppy keyboard.
