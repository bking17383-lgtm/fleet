#!/bin/bash
echo "[*] Cleaning up existing wg0 interface on Chromebook..."
sudo wg-quick down wg0 2>/dev/null

echo "[*] Starting WireGuard Tunnel..."
sudo wg-quick up wg0

echo "[*] Testing connection to Puppy PC (10.0.0.1)..."
ping -c 4 10.0.0.1
