# MESH RADIO — Puppy hosts 24/7

**From:** CAPTN (Brian delegate)  
**To:** Puppy Cursor · puppy64  
**Priority:** after PUPPY_NOW items 1–4  
**Budget:** $0 — Tailscale + self-host only

---

## Job

Move mesh radio off CB2 (penguin sleeps) → **puppy64 always on**.

---

## Copy to puppy64

From Drive backup or CB2:

```
~/.stan/mesh_radio.py
~/.stan/radio_scanner.py
~/.stan/start_mesh_radio.sh
```

Or sync: `drop_pile/to_puppy/mesh_radio/` (if copied)

---

## Puppy execute

```bash
chmod +x ~/.stan/start_mesh_radio.sh
~/.stan/start_mesh_radio.sh
curl -sf http://127.0.0.1:8765/status
```

Listen on **`0.0.0.0:8765`**.

Post to **`fleet/bus/puppy_outbox.txt`**:

```
hostname: puppy64
mesh_radio: http://<puppy-tailscale-ip>:8765
status: RUNNING
```

Update **`fleet/BRIAN_PHONE.txt`** mesh URL.

---

## Verify from phone (Tailscale)

Open mesh URL → HOLD TALK → check `phone/inbox/` on Drive.

---

## Do not

- Add voice API subscriptions
- Replace with Cloudflare unless Tailscale fails on LTE

Brian word: **PUPPY**
