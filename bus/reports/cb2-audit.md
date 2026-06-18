# Audit: cb2  (2026-06-18T00:25:36-07:00)

## OS
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
NAME="Debian GNU/Linux"
VERSION_ID="13"
VERSION="13 (trixie)"
VERSION_CODENAME=trixie

## Cron jobs (old loops?)
*/2 * * * * /home/bking17383/.stan/url_keeper.sh >/dev/null 2>&1
@reboot sleep 30 && /home/bking17383/.stan/url_keeper.sh >/dev/null 2>&1

## Suspicious processes (agents/loops/drive/gemini/bus)
message+     216  0.0  0.1   8296  3832 ?        Ss   Jun16   0:00 /usr/bin/dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
bking17+     293  0.0  0.1   7756  2992 ?        Ss   Jun16   0:00 /usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
bking17+     320  0.0  0.0   7732  1608 ?        Ss   Jun16   0:00 /opt/google/cros-containers/bin/../lib/ld-linux-x86-64.so.2 --argv0 /usr/bin/sommelier --library-path /opt/google/cros-containers/bin/../lib --inhibit-rpath  /opt/google/cros-containers/bin/sommelier.elf -X --x-display=0 --sd-notify=READY=1 --no-exit-with-child --x-auth=/home/bking17383/.Xauthority --stable-scaling --enable-xshape --enable-linux-dmabuf /bin/sh -c systemctl --user set-environment DISPLAY=${DISPLAY};                     systemctl --user set-environment XCURSOR_SIZE=${XCURSOR_SIZE};                     systemctl --user import-environment SOMMELIER_VERSION;                     touch /home/bking17383/.Xauthority;                     xauth -f /home/bking17383/.Xauthority add :0 . $(xxd -l 16 -p /dev/urandom);                     . /etc/sommelierrc
bking17+     325  0.0  0.0   7728  1608 ?        Ss   Jun16   0:00 /opt/google/cros-containers/bin/../lib/ld-linux-x86-64.so.2 --argv0 /usr/bin/sommelier --library-path /opt/google/cros-containers/bin/../lib --inhibit-rpath  /opt/google/cros-containers/bin/sommelier.elf -X --x-display=1 --sd-notify=READY=1 --no-exit-with-child --x-auth=/home/bking17383/.Xauthority --stable-scaling --enable-xshape --enable-linux-dmabuf /bin/sh -c systemctl --user set-environment DISPLAY_LOW_DENSITY=${DISPLAY};                     systemctl --user set-environment XCURSOR_SIZE_LOW_DENSITY=${XCURSOR_SIZE};                     systemctl --user import-environment SOMMELIER_VERSION;                     touch /home/bking17383/.Xauthority;                     xauth -f /home/bking17383/.Xauthority add :1 . $(xxd -l 16 -p /dev/urandom);                     . /etc/sommelierrc
bking17+   32604  0.0  0.0   7480  2668 ?        S    Jun17   0:03 bash /home/bking17383/.stan/drive_watch.sh
bking17+  261859  7.6 24.7 35918404 693912 pts/0 Rl+  Jun17  59:44 /home/bking17383/.local/bin/cursor-agent --use-system-ca /home/bking17383/.local/share/cursor-agent/versions/2026.06.15-03-48-54-da23e37/index.js
bking17+  341926  0.1  1.9  69244 54500 ?        S    Jun17   1:05 python3 /home/bking17383/.stan/cpt_daddy_ready_loop.py watch
bking17+  343078  0.0  0.6  27972 17056 ?        S    Jun17   0:11 python3 /mnt/shared/GoogleDrive/MyDrive/fleet/bootstrap/box_slave_loop.py daddy
bking17+  357117  0.0  0.1  10024  5220 ?        Ss   Jun17   0:00 /bin/bash -O extglob -c snap=$(command cat <&3) && builtin shopt -s extglob && builtin eval -- "$snap" && { builtin set +u 2>/dev/null || true; builtin eval "${__CURSOR_SANDBOX_ENV_RESTORE:-}" 2>/dev/null; builtin export PWD="$(builtin pwd)"; builtin shopt -s expand_aliases 2>/dev/null; alias sudo='sudo -A'; builtin eval "$1"; }; COMMAND_EXIT_CODE=$?; dump_bash_state >&4; builtin exit $COMMAND_EXIT_CODE -- /home/bking17383/.stan/gcloud auth login --no-launch-browser 2>&1 | head -8 || true
bking17+  543655  2.1  0.2  10024  5884 ?        Ss   00:25   0:00 /bin/bash -O extglob -c snap=$(command cat <&3) && builtin shopt -s extglob && builtin eval -- "$snap" && { builtin set +u 2>/dev/null || true; builtin eval "${__CURSOR_SANDBOX_ENV_RESTORE:-}" 2>/dev/null; builtin export PWD="$(builtin pwd)"; builtin shopt -s expand_aliases 2>/dev/null; alias sudo='sudo -A'; builtin eval "$1"; }; COMMAND_EXIT_CODE=$?; dump_bash_state >&4; builtin exit $COMMAND_EXIT_CODE -- cd ~/fleet && chmod +x scripts/audit.sh 2>/dev/null; ./scripts/audit.sh cb2 2>&1
bking17+  543674 70.5  7.3 228332 206092 ?       R    00:25   0:01 tesseract /mnt/shared/GoogleDrive/MyDrive/convert_inbox/20260617_111508.jpg stdout -l eng

## Git repos present (besides fleet)

## Drive / rclone (old bus?)
(no drive mounts)
(no rclone config)

## Tools
git=/usr/bin/git
ssh=/usr/bin/ssh
cron=NO
cursor-agent=/home/bking17383/.local/bin/cursor-agent
rclone=NO

## Home top-level
total 1104
drwx------ 1 bking17383 bking17383    814 Jun 17 23:29 .
drwxr-xr-x 1 root       root           20 Jun 13 21:43 ..
drwxr-xr-x 1 bking17383 bking17383     12 Jun 14 03:33 .Applications
-rw------- 1 bking17383 bking17383    104 Jun 16 22:41 .Xauthority
-rw------- 1 bking17383 bking17383  10470 Jun 14 16:04 .bash_history
-rw-r--r-- 1 bking17383 bking17383    220 Jan  2 06:01 .bash_logout
-rw-r--r-- 1 bking17383 bking17383   1375 Jun 15 00:32 .bashrc
drwxr-xr-x 1 bking17383 bking17383     84 Jun 17 06:12 .cache
drwxr-xr-x 1 bking17383 bking17383    102 Jun 16 03:50 .cloudflared
drwxr-xr-x 1 bking17383 bking17383     98 Jun 17 14:56 .config
drwxr-xr-x 1 bking17383 bking17383    288 Jun 17 11:04 .cursor
drwx------ 1 bking17383 bking17383      0 Jun 13 23:53 .cursor-user
-rw-r--r-- 1 bking17383 bking17383     69 Jun 18 00:25 .daddy_slave_state.json
drwx------ 1 bking17383 bking17383     32 Jun 17 06:13 .local
drwx------ 1 bking17383 bking17383     10 Jun 13 23:00 .pki
-rw-r--r-- 1 bking17383 bking17383    844 Jun 13 23:55 .profile
-rw-r--r-- 1 bking17383 bking17383    425 Dec 31  1999 .sommelierrc
drwx------ 1 bking17383 bking17383    108 Jun 17 23:29 .ssh
drwxr-xr-x 1 bking17383 bking17383   5580 Jun 17 17:15 .stan
-rw-r--r-- 1 bking17383 bking17383      0 Jun 13 21:48 .sudo_as_admin_successful
-rw------- 1 bking17383 bking17383    924 Jun 15 00:06 .viminfo
-rw-r--r-- 1 bking17383 bking17383    204 Jun 13 22:03 .wget-hsts
drwxr-xr-x 1 bking17383 bking17383     12 Jun 13 22:09 Applications
drwxr-xr-x 1 bking17383 bking17383     14 Jun 15 19:48 GoogleDrive
-rw-r--r-- 1 bking17383 bking17383  81232 Jun 15 18:11 Screenshot 2026-06-15 6.11.31 PM.png
-rw-r--r-- 1 bking17383 bking17383 490955 Jun 15 19:48 Screenshot 2026-06-15 7.48.26 PM.png
-rw-r--r-- 1 bking17383 bking17383 507099 Jun 15 19:50 Screenshot 2026-06-15 7.50.56 PM.png
-rwxr-xr-x 1 bking17383 bking17383      0 Jun 13 22:14 cursor.AppImage
drwxr-xr-x 1 bking17383 bking17383     66 Jun 18 00:25 fleet
