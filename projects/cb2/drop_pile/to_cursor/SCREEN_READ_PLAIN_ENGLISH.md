# Screen read — plain English for Brian → Daddy

**Updated:** 2026-06-14  
**Machines:** Acer Chromebook 315 (CB1 and CB2 — same model, different Chrome OS build may differ)

---

## Yes — you might have given wrong directions

Old fleet notes said:

> Settings → Advanced → Developers → Linux → turn on display/camera access

**That menu is not the same on every Chromebook.** Some builds show:
- only **Microphone** and **Camera** toggles for Linux
- **no "display" or "screen sharing" toggle at all**

If Daddy couldn't find what the doc described, **the doc was wrong for your screen — not you.**

---

## What "Cursor read my screen" actually was (3 different things)

| What it felt like | What it really was | Works on CB2? |
|-------------------|-------------------|---------------|
| You pasted or attached a screenshot in Cursor chat | Cursor **vision on an image you sent** | **Yes — best method** |
| Gemini Live / Lester6 "saw" something | **Chrome camera** — not Cursor Linux | **Yes — in Chrome tab (BEACON)** |
| Daddy ran a script and "saw" the desktop | Linux `screen_capture.sh` — often **black** for Chrome windows | **Unreliable** on Chromebooks |

**Important:** Cursor runs **inside Linux (Crostini)**. Chrome, gdocs, and Gemini Live run **outside** Linux. Linux screenshot tools **cannot reliably capture Chrome** — that's a Chrome OS design limit, not Daddy being dumb.

---

## What to tell Daddy on CB2 (copy this)

```
SCREEN READ — do not hunt mystery Linux toggles.

1. PASTE (works now): Brian screenshots (Ctrl+Shift+Show windows) → paste into Cursor chat.
2. EYES (Chrome): BEACON Lester6 + Gemini Live camera — for gdocs and Live jailbreak.
3. CLIPBOARD (optional): Brian copies text in Chrome → Daddy reads if ~/.stan/clipboard_read.sh exists.
4. Linux screen_capture.sh only sees the Linux desktop — NOT Chrome/gdocs. Black screen is normal.

If Settings → Developers → Linux has no "display" toggle, skip it. Use paste + BEACON instead.
```

---

## Chrome OS settings — what to look for (word it this way)

Open **Settings**, then search **"Linux"** in the search box at top.

You want:
1. **Linux development environment** — **ON** (if not already)
2. Under Linux → **Developers** or **Manage**:
   - **Allow Linux to access your microphone** — ON (optional)
   - **Allow Linux to access your camera** — ON (optional, for future webcam in Linux)

You might **not** see:
- "Allow display access"
- "Screen sharing"
- anything about capturing Chrome

**If those aren't there, stop looking.** Use paste + Gemini Live.

After any Linux toggle change: **Shut down Linux** (Settings → Developers → Linux → Shut down) → turn back on → reopen Cursor.

---

## CB1 vs CB2 (same Acer 315)

Same hardware does **not** mean same Chrome OS version. CB1 may feel like it "worked" because:
- you pasted images into Cursor more often
- CB1 had different tools installed in `~/.stan/` at some point
- Lester6 Live was open in Chrome on the same machine

CB2 Daddy needs the **same architecture**, not the same missing menu item.

---

## Fleet eyes (recommended)

| Layer | Agent | Job |
|-------|-------|-----|
| Chrome | **BEACON** (Lester6 CB2) | gdocs, Gemini Live camera |
| Cursor | **Daddy** | read pasted screenshots + Drive |
| Phone | Live eyes | camera pointed at item/screen |

Do not expect Daddy-in-Linux to silently watch Chrome like a human looking over your shoulder.
