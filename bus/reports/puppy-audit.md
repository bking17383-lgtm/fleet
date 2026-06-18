# Audit: puppy  (2026-06-18T00:38:18-07:00)

## OS
NAME=Puppy
VERSION="2601"
ID=debian
VERSION_ID=2601
PRETTY_NAME="TrixiePup64Wayland 2601"

## Cron jobs (old loops?)
(none)

## Suspicious processes (agents/loops/drive/gemini/bus)
root           1  0.0  0.0   3544  2184 ?        Ss   Jun17   0:01 /bin/busybox init
root          45  0.0  0.0      0     0 ?        I    Jun17   0:00 [kworker/u18:1-loop0]
message+    4839  0.0  0.0   8348  3244 ?        Ss   Jun17   0:00 /bin/dbus-daemon --system
spot        5191  0.0  0.0   6792  2548 ?        Ss   Jun17   0:00 dbus-daemon --fork --print-address 1 --print-pid 1 --session
root        5230  0.0  0.0   4976  2300 tty1     S+   Jun17   0:00 dbus-run-session labwc
root        5234  0.0  0.1   6844  4200 tty1     S+   Jun17   0:00 dbus-daemon --nofork --print-address 4 --session
spot        6121  0.0  0.0   6724  2508 ?        Ss   Jun17   0:00 /usr/bin/dbus-daemon --syslog --fork --print-pid 5 --print-address 7 --session
root        6740  0.0  0.0   4076  2988 ?        S    Jun17   0:00 /bin/bash /root/puppy-server/bin/home-poller-loop.sh
root        7103  0.1  0.0   7040  3484 ?        S    Jun17   0:05 /bin/bash /root/puppy-server/bin/sync-watch-loop.sh
root        7215  0.0  0.0   7108  3420 ?        S    Jun17   0:01 /bin/bash /root/puppy-server/bin/lester-keepalive-loop.sh
root        8775  3.0  8.3 35129464 326928 pts/0 Rl+  Jun17   2:02 /root/.local/bin/agent --use-system-ca /root/.local/share/cursor-agent/versions/2026.06.15-18-00-12-6f5a2cf/index.js
root       45564  4.3  0.1   9216  5668 ?        Ss   00:38   0:00 /bin/bash -O extglob -c snap=$(command cat <&3) && builtin shopt -s extglob && builtin eval -- "$snap" && { builtin set +u 2>/dev/null || true; builtin eval "${__CURSOR_SANDBOX_ENV_RESTORE:-}" 2>/dev/null; builtin export PWD="$(builtin pwd)"; builtin shopt -s expand_aliases 2>/dev/null; alias sudo='sudo -A'; builtin eval "$1"; }; COMMAND_EXIT_CODE=$?; dump_bash_state >&4; builtin exit $COMMAND_EXIT_CODE -- cd "$HOME/fleet" && ./scripts/audit.sh puppy && git status --short --branch && git log --oneline -3

## Git repos present (besides fleet)

## Drive / rclone (old bus?)
(no drive mounts)
(no rclone config)

## Tools
git=/bin/git
ssh=/bin/ssh
cron=NO
cursor-agent=NO
rclone=NO

## Home top-level
total 751
drwx-----x  1 root root   4096 Jun 17 23:49 .
drwxr-xr-x  1 root root   4096 Jun 18 00:30 ..
-rwxr-xr-x  1 root root   1541 May 17 19:32 ai_loop.sh
drwxr-x---  2 root root   4096 May 22 06:51 .android
-rw-r--r--  1 root root    154 Jun 12 05:43 .asoundrc
-rw-------  1 root root  11590 Jun 16 07:27 .bash_history
-rwxr-xr-x  1 root root    281 Jun 12 06:09 .bashrc
drwxr-xr-x  9 root root   4096 Jun 16 23:56 bunny
drwx------  9 root root   4096 Jun 15 08:29 .cache
drwxr-xr-x  2 root root      3 May  2 02:29 .compose-cache
drwxr-xr-x  1 root root   4096 Jun 17 00:49 .config
-rw-r--r--  1 root root     25 May  2 02:33 .connectwizardrc
-rw-r--r--  1 root root   3013 May 18 22:16 currentProjects.abw
drwxr-xr-x  6 root root   4096 Jun 16 01:18 .cursor
drwx------  3 root root   4096 Jun  9 04:44 .dbus
drwxr-xr-x  1 root root   4096 Jun 17 23:31 Desktop
lrwxrwxrwx  1 root root     22 May  2 02:32 Downloads -> ../home/spot/Downloads
-rwxr-xr-x  1 root root   2405 Jun 14 01:38 fix_browser_audio.sh
-rwxr-xr-x  1 root root   4163 Jun  9 10:46 fix_puppy_boot.py
drwxr-xr-x  6 root root   4096 Jun 18 00:38 fleet
-rw-r--r--  1 root root     68 May  2 02:28 .fonts.cache-1
drwxr-xr-x  5 root root   4096 May 18 15:14 gemini_env
-rw-r--r--  1 root root   1238 Jun 12 05:28 gemini_voice.py
-rw-r--r--  1 root root    433 May 14  2025 .gtkrc-2.0
-rw-------  1 root root  47349 May 17 23:32 .history
drwxr-xr-x  2 root root     89 Dec 11  2024 .icons
-rw-r--r--  1 root root     65 Jun 16 06:51 inbox
-rw-r--r--  1 root root    833 Sep 27  2024 .isomaster
-rw-------  1 root root   4668 May  2 02:32 .jwmrc
