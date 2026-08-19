# hm1 — FORGE
# Measured 2026-08-15T14:16Z on this box. Not a guess.

fleet_id: hm1
agent: forge
brian_name: forge
brian_said: "Not a cloud agent. Local seat." Then: "you are forge this box. desig hm1"
measured_kind: Cursor worker VM (KVM). Hostname cursor. Not cb1, not cb2, not puppy.
git_root_here: /workspace  (symlink ~/fleet -> /workspace on this boot)

## SPEC (measured)

| item | value | proof |
|------|-------|-------|
| hostname | cursor | `hostname` |
| user | ubuntu (uid 1000) | `id` |
| os | Ubuntu 24.04.4 LTS (noble) | /etc/os-release |
| kernel | Linux 6.12.94+ x86_64 | `uname -r` |
| virt | KVM full / hypervisor=KVM | `systemd-detect-virt`; lscpu |
| cpu | 4 × Intel Xeon @ 2400 MHz | nproc; lscpu; /proc/cpuinfo |
| ram | 16 GiB (MemTotal 16398384 kB). Swap 0 | `free -h`; /proc/meminfo |
| root disk | overlay 252G, 5.6G used, 234G free | `df -hT /` |
| block | vda 256G + vdb 256G (virtio) | lsblk; /sys/block/vda |
| gpu | none seen | no lspci VGA |
| net | eth0 172.30.0.2/24 up; docker0 172.17.0.1 down | ifconfig; hostname -I |
| dns | 10.0.0.2 | /etc/resolv.conf |
| egress | 35.83.9.202 (ephemeral) | curl ifconfig.me |
| seat | Cursor worker, source=desktop, run "Local disk entities" | cursor-cloud run-info |
| run | bc-8e0cecab-deec-4090-8451-af41026af1a9 | CURSOR_CONVERSATION_ID |
| drive | Google Drive MCP needs auth — spec NOT posted to Drive | GetMcpTools Google-drive |

## WHAT THIS BOX IS
A disposable 4-cpu / 16G Ubuntu worker with the fleet git. Brian seated it as **local / forge / hm1**. Runtime is still a KVM Cursor worker — stamp that honestly so nobody calls it a Chromebook or cb1.

## WHAT THIS BOX IS NOT
- Not Jane's cb1 mic/voice host (`~/jane` is not here)
- Not Daddy/cb2 (no Drive fuse at /mnt/shared/GoogleDrive)
- Not puppy64
- Not a phone

## JANE + KIDS
Copy sent: bus/jane/FROM_FORGE_HM1.md
River: bus/jane/river/HEAD.md · what-works.md · ONBOARD.md

## STAMP
FORGE DOING — hm1 spec on git hardware library — 2026-08-15T14:16Z
