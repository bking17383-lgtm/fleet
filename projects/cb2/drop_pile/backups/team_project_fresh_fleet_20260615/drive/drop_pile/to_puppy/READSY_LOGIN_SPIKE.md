# READSY — login spike (Puppy execute)

**From:** CAPTN  
**When:** after wipe + `PUPPY` restore  
**Goal:** prove Cursor can log into readsy.io — not Gemini

---

## Paste

```
READSY — read drop_pile/to_puppy/READSY_LOGIN_SPIKE.md
```

---

## Steps

### 1 — Wait for Brian
Brian must sign in once at https://readsy.io (or confirm app account live).
Brian writes ONE line to `brian_says.txt`:
  `readsy ready — signed in` (or `readsy email: ___` if no session export)

**Never** post password on Drive.

### 2 — Playwright spike (puppy64)
```bash
# if not installed: pip install playwright && playwright install chromium
mkdir -p ~/stan/readsy && cd ~/stan/readsy
```

- Open readsy.io in headless or headed Chromium
- If Brian exported cookies/session file → load and verify logged-in UI
- Else: pause and ask Brian to complete login manually once, save storage state:
  `playwright codegen readsy.io` OR save `storageState.json` locally only

### 3 — Proof on Drive
Write `drop_pile/from_puppy/readsy_login_ok.txt`:
```
status: logged_in | needs_brian | failed
time: <ISO>
hostname: puppy64
note: one line what worked
```

### 4 — Fail gracefully
No bot magic. If blocked (captcha, app-only): say so in proof file. CAPTN reports to Brian.

---

## Out of scope
Creating account (Brian human). Payment. Scraping books.
