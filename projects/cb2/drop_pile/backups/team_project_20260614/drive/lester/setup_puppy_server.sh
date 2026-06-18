#!/bin/bash
echo "[*] Starting SSH Server on Puppy PC..."
/etc/init.d/ssh start

echo "[*] Disabling Puppy PC Firewall..."
/etc/init.d/rc.firewall stop 2>/dev/null || iptables -F

echo "[*] Restarting WireGuard interface on Puppy PC..."
wg-quick down wg0 2>/dev/null
wg-quick up wg0

echo "[*] WireGuard Status on Puppy PC:"
wg
