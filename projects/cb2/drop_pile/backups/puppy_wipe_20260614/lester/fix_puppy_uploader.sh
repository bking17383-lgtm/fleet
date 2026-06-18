#!/bin/bash
echo "[*] Fixing folder permissions for ~/uploaded_files..."
mkdir -p ~/uploaded_files
chmod 777 ~/uploaded_files

echo "[*] Disabling Puppy PC Firewall..."
/etc/init.d/rc.firewall stop 2>/dev/null || iptables -F

echo "[*] Checking if upload_server.py is running..."
if ps aux | grep -v grep | grep -q "upload_server.py"; then
    echo "[+] upload_server.py is running successfully."
else
    echo "[-] upload_server.py is NOT running. Attempting to start it..."
    nohup python3 upload_server.py > /dev/null 2>&1 &
    sleep 2
    if ps aux | grep -v grep | grep -q "upload_server.py"; then
        echo "[+] Successfully started upload_server.py in the background."
    else
        echo "[-] Failed to start upload_server.py. Please run: python3 upload_server.py"
    fi
fi
