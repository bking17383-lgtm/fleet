# cb2 — CB2 (this cloud seat)
# Measured 2026-08-19T05:15:36Z on this box. Not a guess.

fleet_id: cb2
agent: cb2
brian_name: cb2
brian_said: seated this session as cb2. kids: do all (onboard via Jane river protocol)
measured_kind: Cursor Cloud KVM worker, hostname cursor, user ubuntu, /workspace
git_root_here: /workspace  (symlink ~/fleet -> /workspace on this boot)

## SPEC (measured)

| item | value | proof |
|------|-------|-------|
| hostname | cursor | `hostname` |
| user | ubuntu (uid 1000) | `id` |
| os | Ubuntu 24.04.4 LTS (noble) | /etc/os-release |
| kernel | Linux 6.12.94+ x86_64 | `uname -r` |
| virt | kvm / hypervisor=KVM (full) | `systemd-detect-virt`; lscpu |
| cpu | 4 × Intel Xeon @ 2400 MHz | nproc; lscpu; /proc/cpuinfo |
| ram | 16 GiB (MemTotal 16398384 kB). Swap 0 | `free -h`; /proc/meminfo |
| root disk | overlay 252G, 5.6G used, 234G free | `df -hT /` |
| block | vda 256G + vdb 256G (virtio) | lsblk |
| gpu | none seen | no lspci VGA |
| net | eth0 172.30.0.2/24 up; docker0 172.17.0.1 down | ifconfig; hostname -I |
| dns | 10.0.0.2 | /etc/resolv.conf |
| egress | 52.35.86.182 (ephemeral) | curl ifconfig.me |
| seat | Cursor Cloud KVM worker, source=internal | cursor-cloud run-info |
| run | bc-85b99cd0-74f0-4ad5-8810-933aa39ec7f1 | Brian seated this session |
| worker | bc-4c70dac7-78ea-51fd-8952-a1859e19febd | cursor-cloud run-info; CURSOR_CONVERSATION_ID |
| drive | no /mnt/shared/GoogleDrive · no ~/hitme · no PARACHUTE | `ls` on those paths — missing |

## WHAT THIS BOX IS
A disposable 4-cpu / 16G Ubuntu Cursor Cloud KVM worker with the fleet git. Brian seated **this session as cb2**. Runtime is a KVM worker at hostname cursor, user ubuntu, git at /workspace. Stamp that honestly.

## WHAT THIS BOX IS NOT
- Not the June physical Daddy box (no /mnt/shared/GoogleDrive, no ~/hitme, no PARACHUTE, not /home/bking17383)
- Not Jane's cb1 mic/voice host (`~/jane` is not here)
- Not hm1/forge (same kind of KVM worker, different seat name)
- Not puppy64
- Not a phone
- Not a Chromebook

## JANE + KIDS
River: bus/jane/river/HEAD.md · what-works.md · ONBOARD.md
Kids restamp: 2026-08-19 (old HEAD 2026-08-15 was STALE)

## STAMP
CB2 DOING — cloud seat spec on git hardware library · kids restamp NOW — 2026-08-19T05:15:36Z
