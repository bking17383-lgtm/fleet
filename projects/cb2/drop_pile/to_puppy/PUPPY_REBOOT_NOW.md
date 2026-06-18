# Puppy reboot — screenshot read (Gem · convert_inbox 20260616_003946)

**What the picture shows:** Debian puppy64 after reboot. **Desktop crashed** (dio-wayland / Wayland broken pipe, pixman bug, dconf/dbus spam). **You are at root `#` — that's enough.**

nginx started. Audio init ran. **Ignore GUI errors for now.**

---

## At the `#` prompt — paste ONE line

```bash
bash ~/GoogleDrive/MyDrive/PUPPY_REBOOT_RECOVERY.sh
```

Try these if path fails:

```bash
bash /mnt/home/google_drive/MyDrive/PUPPY_REBOOT_RECOVERY.sh
bash /root/GoogleDrive/MyDrive/PUPPY_REBOOT_RECOVERY.sh
```

---

## What it does

1. Finds Drive mount
2. Runs PUPPY_FIX (stan + :8765 sink + bus post)
3. Logs reboot state to `fleet/bus/puppy_needs.txt`

---

## Not broken (ignore on screen)

| Message | Truth |
|---------|-------|
| dconf-WARNING / dbus-launch | Root session has no GUI dbus — noise |
| dio-wayland Broken pipe | Desktop dead · terminal fleet still works |
| pixman invalid rectangle | Display bug · skip GUI |
| connman-ui-gtk not found | Missing UI package · network may still work |

---

## After script OK

Refresh `puppy_heartbeat.md` · say **NET** in Cursor when up.

Do **not** fight the desktop tonight unless you need a browser — terminal + bus is the wire.
