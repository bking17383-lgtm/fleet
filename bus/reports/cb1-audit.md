# Audit: cb1  (2026-06-18T00:22:01-07:00)

## OS
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
NAME="Debian GNU/Linux"
VERSION_ID="13"
VERSION="13 (trixie)"
VERSION_CODENAME=trixie

## Cron jobs (old loops?)
*/10 * * * * cd $HOME/fleet && ./scripts/heartbeat.sh cb1 auto >/dev/null 2>&1

## Suspicious processes (agents/loops/drive/gemini/bus)
message+     213  0.0  0.1   8312  4840 ?        Ss   Jun17   0:00 /usr/bin/dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
tpgorou+     288  0.0  0.1   7756  4200 ?        Ss   Jun17   0:00 /usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
tpgorou+     312  0.0  0.1   7728  5452 ?        Ss   Jun17   0:00 /opt/google/cros-containers/bin/../lib/ld-linux-x86-64.so.2 --argv0 /usr/bin/sommelier --library-path /opt/google/cros-containers/bin/../lib --inhibit-rpath  /opt/google/cros-containers/bin/sommelier.elf -X --x-display=0 --sd-notify=READY=1 --no-exit-with-child --x-auth=/home/tpgoround/.Xauthority --stable-scaling --enable-xshape --enable-linux-dmabuf /bin/sh -c systemctl --user set-environment DISPLAY=${DISPLAY};                     systemctl --user set-environment XCURSOR_SIZE=${XCURSOR_SIZE};                     systemctl --user import-environment SOMMELIER_VERSION;                     touch /home/tpgoround/.Xauthority;                     xauth -f /home/tpgoround/.Xauthority add :0 . $(xxd -l 16 -p /dev/urandom);                     . /etc/sommelierrc
tpgorou+     315  0.0  0.1   7732  5488 ?        Ss   Jun17   0:00 /opt/google/cros-containers/bin/../lib/ld-linux-x86-64.so.2 --argv0 /usr/bin/sommelier --library-path /opt/google/cros-containers/bin/../lib --inhibit-rpath  /opt/google/cros-containers/bin/sommelier.elf -X --x-display=1 --sd-notify=READY=1 --no-exit-with-child --x-auth=/home/tpgoround/.Xauthority --stable-scaling --enable-xshape --enable-linux-dmabuf /bin/sh -c systemctl --user set-environment DISPLAY_LOW_DENSITY=${DISPLAY};                     systemctl --user set-environment XCURSOR_SIZE_LOW_DENSITY=${XCURSOR_SIZE};                     systemctl --user import-environment SOMMELIER_VERSION;                     touch /home/tpgoround/.Xauthority;                     xauth -f /home/tpgoround/.Xauthority add :1 . $(xxd -l 16 -p /dev/urandom);                     . /etc/sommelierrc
tpgorou+     509  0.5 21.9 35761404 616240 pts/0 Sl+  Jun17   2:19 /home/tpgoround/.local/bin/cursor-agent --use-system-ca /home/tpgoround/.local/share/cursor-agent/versions/2026.06.15-18-00-12-6f5a2cf/index.js
tpgorou+    1133  9.9 23.1 35859364 650360 pts/1 Sl+  Jun17  44:55 /home/tpgoround/.local/bin/agent --use-system-ca /home/tpgoround/.local/share/cursor-agent/versions/2026.06.15-18-00-12-6f5a2cf/index.js
tpgorou+    5247  0.6  0.2  10032  5748 ?        Ss   00:21   0:00 /bin/bash -O extglob -c snap=$(command cat <&3) && builtin shopt -s extglob && builtin eval -- "$snap" && { builtin set +u 2>/dev/null || true; builtin eval "${__CURSOR_SANDBOX_ENV_RESTORE:-}" 2>/dev/null; builtin export PWD="$(builtin pwd)"; builtin shopt -s expand_aliases 2>/dev/null; alias sudo='sudo -A'; builtin eval "$1"; }; COMMAND_EXIT_CODE=$?; dump_bash_state >&4; builtin exit $COMMAND_EXIT_CODE -- cd ~/fleet && chmod +x scripts/audit.sh && git add scripts/audit.sh && git commit --trailer "Co-authored-by: Cursor <cursoragent@cursor.com>" -q -m "Add audit.sh — each machine reports its state" && git push -q && echo "=== running audit on cb1 ===" && ./scripts/audit.sh cb1 && echo "=== cb1 audit result ===" && cat bus/reports/cb1-audit.md

## Git repos present (besides fleet)

## Drive / rclone (old bus?)
(no drive mounts)
(no rclone config)

## Tools
git=/usr/bin/git
ssh=/usr/bin/ssh
cron=NO
cursor-agent=/home/tpgoround/.local/bin/cursor-agent
rclone=NO

## Home top-level
total 40
drwx------ 1 tpgoround tpgoround  292 Jun 17 22:52 .
drwxr-xr-x 1 root      root        18 Jun 17 16:10 ..
-rw------- 1 tpgoround tpgoround  104 Jun 17 16:32 .Xauthority
-rw------- 1 tpgoround tpgoround 1381 Jun 17 16:31 .bash_history
-rw-r--r-- 1 tpgoround tpgoround  220 Mar  8 08:21 .bash_logout
-rw-r--r-- 1 tpgoround tpgoround 3659 Jun 18 00:05 .bashrc
drwxr-xr-x 1 tpgoround tpgoround   40 Jun 17 16:39 .cache
drwxr-xr-x 1 tpgoround tpgoround   76 Jun 17 16:39 .config
drwxr-xr-x 1 tpgoround tpgoround  104 Jun 17 16:39 .cursor
-rw-r--r-- 1 tpgoround tpgoround   90 Jun 17 22:52 .gitconfig
drwx------ 1 tpgoround tpgoround   26 Jun 17 16:25 .local
-rw-r--r-- 1 tpgoround tpgoround  807 Mar  8 08:21 .profile
-rw-r--r-- 1 tpgoround tpgoround  425 Dec 31  1999 .sommelierrc
drwx------ 1 tpgoround tpgoround   96 Jun 17 22:54 .ssh
-rw-r--r-- 1 tpgoround tpgoround    0 Jun 17 16:15 .sudo_as_admin_successful
drwxr-xr-x 1 tpgoround tpgoround   46 Jun 17 17:16 audit
drwxr-xr-x 1 tpgoround tpgoround   82 Jun 18 00:16 fleet
drwxr-xr-x 1 tpgoround tpgoround   26 Jun 17 16:18 projects
