#!/bin/bash
# ============================================================
# SOC Lab — Ubuntu Target Container Entrypoint
# Starts SSH, auditd, rsyslog, and Wazuh agent
# ============================================================
set -e

WAZUH_MANAGER="${WAZUH_MANAGER:-wazuh.manager}"
WAZUH_AGENT_NAME="${WAZUH_AGENT_NAME:-ubuntu-target-01}"
WAZUH_REGISTRATION_PASSWORD="${WAZUH_REGISTRATION_PASSWORD:-please123}"

echo "[SOC-LAB] Starting ubuntu-target: ${WAZUH_AGENT_NAME}"

# ── SSH ─────────────────────────────────────────────────────
echo "[SOC-LAB] Starting SSH server..."
mkdir -p /run/sshd
/usr/sbin/sshd -D &
SSH_PID=$!
echo "[SOC-LAB] SSH listening on :22 (pid ${SSH_PID})"

# ── Rsyslog ─────────────────────────────────────────────────
echo "[SOC-LAB] Starting rsyslog..."
rsyslogd

# ── Auditd ──────────────────────────────────────────────────
echo "[SOC-LAB] Starting auditd..."
mkdir -p /var/log/audit
auditd -b 8192 2>/dev/null || echo "[SOC-LAB] auditd start note (may not load kernel module in container)"

# Load audit rules after brief delay
sleep 2
auditctl -R /etc/audit/rules.d/audit.rules 2>/dev/null || echo "[SOC-LAB] auditctl: kernel audit may be limited in this container"

# ── Wazuh Agent Enrollment ──────────────────────────────────
echo "[SOC-LAB] Waiting for Wazuh manager at ${WAZUH_MANAGER}:1515..."
MAX_WAIT=120
WAITED=0
while ! nc -z "${WAZUH_MANAGER}" 1515 2>/dev/null; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "[SOC-LAB] WARNING: Wazuh manager not reachable after ${MAX_WAIT}s — starting agent anyway"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    echo "[SOC-LAB] Still waiting for manager... (${WAITED}s)"
done

# Register agent with the manager
echo "[SOC-LAB] Registering agent '${WAZUH_AGENT_NAME}' with manager..."
/var/ossec/bin/agent-auth \
    -m "${WAZUH_MANAGER}" \
    -A "${WAZUH_AGENT_NAME}" \
    -P "${WAZUH_REGISTRATION_PASSWORD}" \
    -p 1515 2>&1 || echo "[SOC-LAB] Registration note: agent may already be registered"

# ── Wazuh Agent ─────────────────────────────────────────────
echo "[SOC-LAB] Starting Wazuh agent..."
/var/ossec/bin/wazuh-control start 2>&1 || true

echo "[SOC-LAB] ============================================"
echo "[SOC-LAB] ubuntu-target is ready!"
echo "[SOC-LAB] SSH available on port 22 (mapped to 2222)"
echo "[SOC-LAB] Users: labuser/password123, developer/dev123"
echo "[SOC-LAB] Wazuh agent connected to: ${WAZUH_MANAGER}"
echo "[SOC-LAB] ============================================"

# Keep SSH process in foreground
wait $SSH_PID
