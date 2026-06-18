# New Uncle boot — CB1

**Time:** 2026-06-15  
**Role:** Uncle (new instance — not old Uncle)  
**Hostname:** penguin  
**Machine:** CB1 Acer 315  

---

## Status

```
uncle: LIVE (fresh Cursor session)
generation: new — do not inherit old ~/.stan or fleet script state
local_disk: clean — no ~/lester, no ~/.stan
drive: mounted at /mnt/chromeos/shared/GoogleDrive/MyDrive
cursor_agent: 2026.06.15-03-48-54-da23e37
keys: lester/lester_keys.md — use as needed per Brian
```

## Safe rules (Brian 2026-06-15)

- **No fleet scripts** for now — corruption risk (`fleet_board.py`, `install_uncle_stan.sh`, etc.)
- **Drive is truth** — read/write handoffs only; no chat-only state
- **New Uncle ≠ old Uncle** — do not assume CB1-local artifacts survived
- **Camel** — retrieve from Drive when Brian says; source on Drive: `lester/camel_clicker.py`
- **Lester6 WRANGLER** — Chrome slave; bind when Brian restores Chrome tab
- **Network** — Brian will wire fleet soon; standing by

## Waiting on

- Network hookup (Brian)
- Camel game pull to local `~/lester` when ready
- WRANGLER Chrome session (Brian)

## Blocker

none on CB1 Linux
