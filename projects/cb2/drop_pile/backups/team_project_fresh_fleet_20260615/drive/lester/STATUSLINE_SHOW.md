# CB2 status line ("show" footer)

Restores CB1-style footer above the agent prompt.

## Files (CB2)

| Path | Purpose |
|------|---------|
| `~/.cursor/statusline.sh` | CLI footer script |
| `~/.config/cursor/cli-config.json` | `statusLine` + `showStatusIndicators` |
| `~/.stan/handoff/brief.json` | Current **project** label |
| `~/.stan/handoff/gemini_usage.json` | **Gemini Ultra** estimated daily use |
| `~/.stan/handoff/session_note.md` | Fallback project (`**Active program:**`) |

## Manual

```bash
python3 ~/.stan/brian_os.py show
python3 ~/.stan/brian_os.py show 25 80   # ctx 25%, 80k tokens
```

## Footer format

```
show  design_desk  |  fleet 2/3 linked · 2/3 slaves  |  Composer ctx 18% (42k)  |  gemini ~0%
```

Fleet counts scan Drive acks + heartbeats live. Unique IDs:

| machine | callsign | master |
|---------|----------|--------|
| cb1 | WRANGLER | uncle |
| cb2 | BEACON | daddy |
| puppy64 | PLATE | puppy |

Cache: `~/.stan/handoff/fleet_status.json`

## Gemini Ultra tracking

Lester6 updates `gemini_usage.json` after voice/Live turns:

```json
{ "used_units": 12, "daily_budget_units": 100, "plan": "ultra" }
```

Rough: 1 short Lester turn ≈ 1 unit. Tune `daily_budget_units` to match your feel of Ultra daily cap.

## Apply on new machine

1. Copy `lester/cb2_statusline.sh` → `~/.cursor/statusline.sh` && chmod +x
2. Add `statusLine` block to `cli-config.json` (see statusline skill)
3. Set `showStatusIndicators: true`
4. Restart `agent` session
