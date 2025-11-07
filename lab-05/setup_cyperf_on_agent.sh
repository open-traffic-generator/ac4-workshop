#!/bin/bash
set -e

export DEBIAN_FRONTEND=noninteractive

# Wait for apt lock
while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
    echo "Waiting for apt lock..."
    sleep 5
done

# Preconfigure tshark to avoid interactive prompt
echo "wireshark-common wireshark-common/install-setuid boolean false" | sudo debconf-set-selections

# Update & install dependencies
sudo apt-get update -qq
DEBIAN_FRONTEND=noninteractive sudo -E dpkg --configure -a
sudo apt-get install -y -qq --no-install-recommends \
    python3 python3-pip python3-venv libcap2-bin iproute2 ethtool tshark \
    ca-certificates curl gpg software-properties-common

# Upgrade pip and install Python packages with --break-system-packages
pip3 install --upgrade pip --break-system-packages
pip3 install --no-cache-dir scapy numpy pandas requests PyYAML --break-system-packages

echo "====== Installing Cyperf =========="
# Add CyPerf repo and install
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://cyperfce.cyperf.io/cyperf-ce-public.gpg | sudo gpg --yes --dearmor -o /etc/apt/keyrings/cyperf-ce-public.gpg

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/cyperf-ce-public.gpg] https://cyperfce.cyperf.io/debian stable main" \
    | sudo tee /etc/apt/sources.list.d/cyperf-ce.list > /dev/null

sudo apt-get update -qq
KEYSIGHT_EULA_ACCEPTED=true sudo -E apt install -y cyperf

echo "Provisioning complete"