# JANE PACK LIST — cb1 local (~529M at ~/jane)
# Packed: 2026-06-20 · for Brian + Daddy · NOT in git (local only)

## RUNNING NOW (keeper + cron)
| Piece | Script | Role |
|-------|--------|------|
| keeper | jane-keeper.sh | restarts dead daemons |
| ears | jane-listen.py | vosk mic → queue |
| voice | jane-voiced.py | piper TTS queue |
| watch | jane-watch.sh | site/git watcher |
| refresh | jane-refresh.sh (180s loop) | context refresh |
| car | jane-car.sh | on/off all · @reboot |
| ensure | jane-ensure.sh | cron */5 relaunch keeper |

## BRAIN / CONTROL
| File | Role |
|------|------|
| jane-do.sh | run cursor-agent (composer-fast, read-only) |
| jane-ask.sh | one-shot ask |
| jane-say.sh | speak text (fallback if daemon hung) |
| opus-worktick.sh | wake tick (legacy name — Opus retired on cb1) |
| fleet-mail.py | email reader stub (needs app password) |

## DATA / LEARN
| File | Role |
|------|------|
| jane-corrections.txt | mishear fixes |
| jane-learned.txt | accumulated learnings |
| jane-context.txt / live-context.txt | live context slice |
| queue.txt / memory.log / *.log | runtime state |

## MODELS (heavy — cb1-only unless copied)
| Path | ~Size | Notes |
|------|-------|-------|
| model/ | 205M | vosk speech model (active) |
| model.small.bak/ | 68M | backup — safe delete if space needed |
| voices/en_US-amy-medium.onnx | 61M | piper voice |
| venv/ | 196M | python3.13 + vosk + piper |

## MOBILE / SHIP DECISION (propose — Brian picks)
| Stays cb1-only | Could ship to hitme / mobile |
|----------------|------------------------------|
| vosk model + mic pipeline | /jane API talk (Daddy stub on hitme — not phone-proven) |
| piper local TTS | Polly/AWS voice (needs ~/.aws/credentials) |
| keeper + full daemon set | float UI spec: bus/jane/MOBILE_JANE_SPEC.md |
| corrections + learned | read-only brain via API |

## BRIAN MUST BRING (if voice upgrade)
- AWS credentials → ~/.aws/credentials (never git)
- Fleet Gmail app password → fleet-mail.py (ends couriering)

## REBUILD AFTER WIPE
- No jane-install.sh yet (queue task) — manual: venv + model + voices + scripts from memory or Daddy pack
- @reboot cron already calls jane-car.sh on
