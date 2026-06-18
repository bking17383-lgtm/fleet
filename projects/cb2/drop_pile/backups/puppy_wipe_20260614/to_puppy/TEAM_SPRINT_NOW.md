# TEAM SPRINT — Puppy now (priority 1)

**From:** CAPTN  
**Brian says on puppy64:** **PLATE**

One Cursor session. Do all. Post proof on Drive.

---

## Checklist (in order)

1. **Lester6 slave** — your Cursor manages it  
   → `drop_pile/from_lester/lester6_to_puppy.md`  
   → `mode: slave`, today's date, `machine: puppy64`

2. **Baseball** — `bash lester/START_BASEBALL_ON_PUPPY.sh`  
   → LAN URL in `Hello from Puppy.txt`

3. **Cloudflare** — read `DELEGATE_CLOUDFLARE.md`  
   → Public hostname for cb2-daddy OR new puppy tunnel  
   → Token in `lester/lester_keys.md`  
   → Update `BRIAN_PHONE.txt` with fixed https URL

4. **Outbox** — overwrite `puppy_outbox.txt`:
   ```
   --- from: puppy | time: <ISO> ---
   hostname: puppy64
   lester6: bound
   baseball: http://<LAN-IP>:8002
   public: https://<fixed-url>
   ```

5. **Queue** — `python3 ~/.stan/brian_os.py process`  
   → Mark pending puppy jobs done or post blockers

---

## Paste in Puppy Cursor

```
PLATE — TEAM_SPRINT_NOW.md. All five checklist items. Post puppy_outbox.txt today.
Brian will not open Lester tab. You manage your Lester6 slave.
```

---

## Blocker format

One line in `drop_pile/from_puppy/puppy_blocker.txt` if stuck.

CAPTN waiting on Drive only.
