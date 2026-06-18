# PUPPY — Reboot Rule Fix (review WITH Brian before applying)

Date: 2026-06-18
From: auditor (cb1) · For: puppy
Rule: Puppy reads this, compares with Brian, then applies. No silent change.

---

## The dangerous rule (current — REMOVE)

Right now puppy's local rules say that on "reboot" / "restart puppy" he runs:
- `/root/puppy-server/bin/puppy-reboot.sh`
- `/root/puppy-server/bin/puppy-clean-reboot.sh`  ← **wipe + no agents**

Problem: the everyday word **"reboot" also triggers a WIPE.** A casual restart
could erase the machine. That is the "wipe without verify" risk.

---

## The safe replacement (USE THIS)

**1. Plain restart (safe, normal):**
- Triggers: `reboot`, `restart`, `restart puppy`, `puppy reboot`
- Action: run ONLY `/root/puppy-server/bin/puppy-reboot.sh`
- NEVER run any wipe/clean-reboot script on these words.

**2. Wipe (separate, deliberate, rare):**
- Trigger: ONLY the exact explicit order `WIPE PUPPY CONFIRM` (all caps, exact).
- Pre-checks REQUIRED before it may run:
  - Projects confirmed saved on GitHub under `projects/puppy/`.
  - Brian says go, in the same breath.
- Plain "reboot" must NEVER reach the wipe script.

**3. Before ANY restart:**
- Confirm projects are preserved on GitHub first.

---

## Note for puppy

- Before trusting `puppy-clean-reboot.sh` at all, we should read what it actually
  deletes. Until then, do not let it run automatically on any word.

Word: PUPPY · REBOOT-SAFE · WIPE-NEEDS-CONFIRM · SAVE-FIRST
