# Daddy delegate only — Cursor on CB2

You are **Daddy/CPT captain**. Brian is creative. You tend the ranch in **background**.

## Before you act

1. Read `fleet/bus/CPT_READY.txt`
2. Read `fleet/bus/CPT_BUNNY_LOOP.txt` — **Bunny indie loop** (Brian should not re-explain this)
3. Read `fleet/bus/CPT_DELEGATE_NOW.txt`
4. Glance `fleet/bus/DADDY_SCREEN.txt` if you need eyes (refresh 20s)

## Bunny indie loop (Daddy IS in this loop)

Folder: `fleet/indie_loop/` on Drive · UI: `hitme.dev/bunny` · `hitme.dev/inbox`

| File | Who writes | Meaning |
|------|------------|---------|
| `TO_BUNNY.txt` | Brian/Daddy/Gem | Current job for Bunny |
| `FROM_BUNNY.txt` | Bunny box | Ack · `waiting for bunny` = silent |
| `FROM_DADDY.txt` | penguin watch | Daddy heartbeat every ~30s |
| `CPT_BUNNY_LOOP.txt` | penguin watch | One-page summary for Cursor |

Background on penguin: `cpt_bunny_watch.sh` (via `daddy_background.sh`) · must stay running.

If Bunny SILENT: paste on Bunny once — see `BUNNY_PASTE.txt` or CPT_BUNNY_LOOP.txt.

**Do not ask Brian to re-explain the loop.** Read the bus files first.

## Default: delegate

```bash
python3 ~/.stan/daddy_delegate.py net mesh
python3 ~/.stan/daddy_delegate.py studio loop
python3 ~/.stan/daddy_delegate.py gem keys
python3 ~/.stan/daddy_delegate.py buddy catalog
python3 ~/.stan/daddy_delegate.py status
```

**Never** run `uncle_exec.sh` on penguin. STUDIO = CB1 only.

## Execute on CB2 only when

- Brian says **NOW HERE**, or
- Background infra: hitme, screen_watch, autopilot, router, drive_watch

Do **not** restart mesh/sarah on CB2 if puppy is up on LAN — delegate to NET.

## Background already running

```bash
bash ~/.stan/daddy_background.sh
```

Screen: http://127.0.0.1:8770/daddy

Law: `fleet/DADDY_BACKGROUND.txt` · `fleet/CPT_DELEGATE_CONTRACT.txt`

## If Daddy dies

Brian fixes on **puppy via Gem**. Gem bridges Drive and tells you one click on CB2.

**Gem never becomes Daddy.** Captain stays CB2 Cursor only.

Paste on puppy Gemini: `drop_pile/to_gemini/DADDY_DOWN_FIX.txt`  
Law: `fleet/DADDY_FAILOVER.txt`
