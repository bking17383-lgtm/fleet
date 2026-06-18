# START — Baseball phone serve (close open loop)

**From:** Daddy (Terminal 3)  
**To:** Cursor/puppy on puppy64  
**Priority:** parallel ops (not the creative next project)  
**Slicer:** ON HOLD — skip `MAKE_IT_SO.md` until Brian unblocks

---

## Mission

Baseball app is **shipped on penguin** (497 cards / $2,091.89). Finish acceptance: **phone on home Wi-Fi via puppy LAN**.

Full spec: **`~/Applications/cursor/baseball_cards/puppy_qa.md`**  
Queue job: **`puppy-qa-wake`** in `brian_queue.json`

---

## Execute (puppy64 only)

```bash
# 1. Read captain instructions
cat ~/GoogleDrive/MyDrive/COMMON_INSTRUCTIONS.md

# 2. Run QA spec
#    (sync from Drive → START_BASEBALL_ON_PUPPY.sh → curl checks)

# 3. Post outbox + mark queue done
python3 ~/.stan/brian_os.py process
```

---

## Done when

- [ ] `puppy_outbox.txt` shows `hostname: puppy64` + **192.168.x.x:8002**
- [ ] `puppy-qa-wake` status = `done` in queue
- [ ] Phone loads Add / List / Stats / CollX on same Wi-Fi

---

## Do NOT start

- `fcf127cd-f` slicer_zero_host — **ON HOLD per Brian**
