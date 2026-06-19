# Fleet — Daddy · Uncle · Puppy (Cursor masters + Lester6 slaves)

**Updated:** 2026-06-14  
**Daddy identity:** **Terminal 3 Cursor on CB2 only** — see `FLEET_TERMINAL_MAP.txt`  
**Chain:** Brian → **Cursor agents** → Lester6 slaves (Brian never talks to Lester directly)

## Rules

1. **CAPTN delegates** — queue + drop_pile; no default execute on CB2
2. **Each Cursor master owns its Lester6 slave** — bind, export, Live
3. **Drive is the bus**

## Cursor agents (Brian talks to these)

| Agent | Machine | Brian says | Orders in |
|-------|---------|------------|-----------|
| **Daddy / CAPTN (T3)** | CB2 Terminal 3 | DADDY, IDEAS | `drop_pile/to_puppy/`, `to_cursor/`, queue |
| **Uncle** | CB1 | READY, SLAVE | `drop_pile/to_cursor/DELEGATE_UNCLE.md` |
| **Puppy** | puppy64 | PLATE, READY | `drop_pile/to_puppy/`, `mac_inbox.txt` |

## Lester6 slaves (Cursor manages — not Brian)

| Cursor master | Slave ack |
|---------------|-----------|
| Daddy CB2 | `lester6_to_daddy.md` |
| Uncle CB1 | `lester6_to_uncle.md` |
| Puppy | `lester6_to_puppy.md` |

## Delegated now

| Job | Owner |
|-----|-------|
| Cloudflare public URL + move to puppy | **Puppy** — `DELEGATE_CLOUDFLARE.md` |
| Lester6 puppy bind | **Puppy** — `DELEGATE_LESTER6.md` |
| Lester6 uncle bind | **Uncle** — `DELEGATE_UNCLE.md` |
| Lester6 daddy export | **CAPTN internal** — `DELEGATE_DADDY_LESTER6.md` |

Read: `FLEET_CHAIN.txt` · `DADDY_DELEGATE_CONTRACT.txt`
