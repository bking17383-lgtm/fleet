PROPOSAL — A002 — DADDY — 2026-06-17T15:10:00-07:00
title: Google Cloud NET server (fleet-net-1)
keep?: YES (if questions answered)
leader: Daddy (until Brian picks)
audit: — (waiting)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOGIC ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  penguin sleeps → hitme dies
  Puppy absent → Daddy TEMP NET is fragile
  GCP e2-standard-2 + same cloudflared token = always-on door

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUESTIONS (Daddy · need answers · not assumptions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Q1.  Which Google account email holds the $300 credit?
  Q2.  Does that credit pay Compute Engine VMs · or Gemini/Vertex only?
  Q3.  One GCP project already · or create new project for fleet?
  Q4.  After VM is live — stop penguin tunnel same day · or run both during cutover?
  Q5.  If VM fails at 2am — who flips tunnel back to penguin · and is that allowed?
  Q6.  Drive on VM: rclone sync every N minutes · or fuse mount like penguin?
  Q7.  Ship life pages only first (:8770 + tunnel) · or all 15 background watchers day one?
  Q8.  AWS keys / George Bedrock on VM · or stay on CB1 and VM calls over Tailscale?
  Q9.  Puppy name survives as edge box later · or VM replaces Puppy permanently?
  Q10. Acceptance test: Brian hits /health from phone on LTE · who confirms green?
  Q11. Wipe scope: penguin stays captain-only · or wipe penguin .stan too after VM green?
  Q12. Cost cap: ok at ~$60/mo after credit · or hard stop / shutdown at $X?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Scripts built:     YES
  VM created:        NO
  Blocker:           gcloud auth login (one Brian tap)
  hitme today:       penguin :8770 (not GCP)

Word: NOT READY · QUESTIONS · LOGIN
