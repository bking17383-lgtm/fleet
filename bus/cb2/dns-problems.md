# DNS PROBLEMS LOG — Daddy's DNS-recovery blockers, recorded by Opus (cb1)
# Daddy is read-only (can't push). Flow: Daddy hits a problem -> tells Brian -> Brian relays -> Opus logs it HERE and diagnoses.
# Format per entry: [time] WHERE (url/record) | EXACT ERROR | what Daddy tried | Opus diagnosis/fix.

## TARGET (what "DNS back" means)
These 6 hitme.dev PATHS must resolve:  /  /goal  /daddy  /george  /bunny  /projects
Dead-on-purpose (leave dead): bun.hitme.dev.  Known: hitme.dev/keaton was 503.
NOTE (2026-06-19): george.hitme.dev is now WANTED (Brian reversed it) — being revived. Was "dead-on-purpose"; no longer.

## PROBLEMS (newest first)
- [2026-06-19 03:44, Daddy via email relay] george.hitme.dev (subdomain) | BLOCKED: needs a Cloudflare ORIGIN CERT /
  account login to add the ingress + `cloudflared tunnel route dns`. Daddy correctly STOPPED (can't touch Brian's CF account).
  -> AWAITING BRIAN: provide the CF origin cert / do the account-side DNS route. /george PATH already works (200) meanwhile.
- [2026-06-19 02:39, Opus re-test] RESOLVED ✅ — Daddy got the site back up. /goal /daddy /george /bunny /projects = 200,
  / = 302 (working redirect). 530s gone. Tunnel/origin live. (Confirm it STAYS up = services enabled per the job.)
- [2026-06-19 02:25, Opus path-test] ALL hitme.dev paths return HTTP 530 (Cloudflare up, ORIGIN unreachable):
    / · /goal · /daddy · /george · /bunny · /projects · /keaton  -> all 530
    bun.hitme.dev -> 530 ;  george.hitme.dev -> 000 (DNS dead, as intended)
  DIAGNOSIS: 530 = Cloudflare answers but can't reach the origin = the NAMED TUNNEL / origin server is DOWN.
  This is NOT a DNS-record problem (lookups resolve). REAL FIX = restart/reconnect the Cloudflare tunnel to the origin.
  -> Daddy: get the cloudflared tunnel running again and pointing hitme.dev paths at the live origin. Then tell Brian; Opus re-tests.

- [2026-06-19T02:53:32-07:00] site-guard: state changed unknown -> up

- [2026-06-19T16:52:15-07:00] site-guard: state changed up -> partial
