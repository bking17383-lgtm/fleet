#!/usr/bin/env python3
"""
Puppy Linux Bootloader Repair Script (fix_puppy_boot.py)
Automated repair tool for UNetbootin and CD-ROM boot errors on Puppy Linux USBs.
Diagnoses and resolves:
1. Missing main ramdisk (initrd.gz) in syslinux.cfg (Legacy Boot)
2. CD-ROM media setting (pmedia=cd) instead of USB flash in grub.cfg (EFI Boot)
"""

import os
import re
import subprocess
import sys

MOUNT_DIR = "/tmp/puppy_repair_mount"

def run_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def find_usb_partitions():
    print("[*] Scanning for connected USB storage partitions...")
    partitions = []
    # Read /proc/partitions to find sd* devices
    if not os.path.exists("/proc/partitions"):
        return partitions
    
    with open("/proc/partitions", "r") as f:
        lines = f.readlines()
        
    for line in lines[2:]:
        parts = line.split()
        if len(parts) >= 4:
            name = parts[3]
            # Match sda1, sdb1, sdc1 etc. (exclude main system disks like nvme or sda if it is the only disk)
            if re.match(r"^sd[a-z]\d+$", name):
                partitions.append(f"/dev/{name}")
    return partitions

def repair_partition(dev_path):
    print(f"\n[*] Attempting to mount and inspect {dev_path}...")
    os.makedirs(MOUNT_DIR, exist_ok=True)
    
    # Mount the partition
    ret, out, err = run_cmd(f"sudo mount {dev_path} {MOUNT_DIR}")
    if ret != 0:
        if "already mounted" in err:
            # Try to read directly or find where it is mounted
            print(f"[!] {dev_path} is already mounted. Proceeding with inspection...")
        else:
            print(f"[!] Failed to mount {dev_path}: {err}")
            return False
            
    try:
        repaired = False
        syslinux_path = os.path.join(MOUNT_DIR, "syslinux.cfg")
        grub_path = os.path.join(MOUNT_DIR, "grub.cfg")
        
        # 1. Repair syslinux.cfg (Missing initrd.gz)
        if os.path.exists(syslinux_path):
            print(f"[+] Found legacy bootloader: {syslinux_path}")
            with open(syslinux_path, "r") as f:
                content = f.read()
                
            # Pattern to match initrd=/ucode.cpio without /initrd.gz
            buggy_pattern = r"(initrd=/ucode\.cpio)(?!,/initrd\.gz)"
            if re.search(buggy_pattern, content):
                print("[!] Detected missing main ramdisk (/initrd.gz) bug in syslinux.cfg!")
                # Replace initrd=/ucode.cpio with initrd=/ucode.cpio,/initrd.gz
                fixed_content = re.sub(buggy_pattern, r"\1,/initrd.gz", content)
                with open(syslinux_path, "w") as f:
                    f.write(fixed_content)
                print("[+] Successfully appended ,/initrd.gz to all boot entries.")
                repaired = True
            else:
                print("[~] syslinux.cfg looks already healthy or clean.")
                
        # 2. Repair grub.cfg (pmedia=cd instead of usbflash)
        if os.path.exists(grub_path):
            print(f"[+] Found EFI bootloader: {grub_path}")
            with open(grub_path, "r") as f:
                content = f.read()
                
            if "pmedia=cd" in content:
                print("[!] Detected incorrect pmedia=cd configuration in grub.cfg!")
                fixed_content = content.replace("pmedia=cd", "pmedia=usbflash")
                with open(grub_path, "w") as f:
                    f.write(fixed_content)
                print("[+] Successfully updated boot media setting to pmedia=usbflash.")
                repaired = True
            else:
                print("[~] grub.cfg looks already healthy or clean.")
                
        if repaired:
            print(f"[SUCCESS] {dev_path} boot parameters repaired successfully!")
        else:
            print(f"[~] No boot issues found on {dev_path}.")
            
    finally:
        # Cleanly unmount
        run_cmd(f"sudo umount {MOUNT_DIR}")
        
    return True

def main():
    if os.getuid() != 0:
        # Re-run with sudo if needed
        print("[*] Re-running script with root privileges to access partitions...")
        args = [sys.executable] + sys.argv
        os.execvp("sudo", ["sudo"] + args)
        
    partitions = find_usb_partitions()
    if not partitions:
        print("[!] No USB storage partitions (/dev/sd*) found. Please plug in the USB drive.")
        sys.exit(1)
        
    print(f"[+] Found partitions to scan: {', '.join(partitions)}")
    success_count = 0
    for part in partitions:
        if repair_partition(part):
            success_count += 1
            
    if success_count > 0:
        print("\n[✔] Diagnostic and repair process completed.")
    else:
        print("\n[!] No partitions were successfully repaired.")

if __name__ == "__main__":
    main()
