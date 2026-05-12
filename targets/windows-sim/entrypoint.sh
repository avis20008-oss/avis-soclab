#!/bin/bash
set -e

WAZUH_MANAGER="${WAZUH_MANAGER:-wazuh.manager}"
WIN_HOSTNAME="${WIN_HOSTNAME:-WIN-PC-01}"
WAZUH_REGISTRATION_PASSWORD="${WAZUH_REGISTRATION_PASSWORD:-please123}"

echo "[win-sim] Starting fake Windows host: ${WIN_HOSTNAME}"

# Enroll with manager
echo "[win-sim] Waiting for Wazuh manager..."
until nc -z "${WAZUH_MANAGER}" 1515 2>/dev/null; do sleep 3; done

echo "[win-sim] Registering as ${WIN_HOSTNAME}..."
/var/ossec/bin/agent-auth \
    -m "${WAZUH_MANAGER}" \
    -A "${WIN_HOSTNAME}" \
    -P "${WAZUH_REGISTRATION_PASSWORD}" \
    -p 1515 2>&1 || echo "[win-sim] May already be registered"

# Start Wazuh agent
echo "[win-sim] Starting Wazuh agent..."
/var/ossec/bin/wazuh-control start 2>&1 || true

# Start event log generator in background
echo "[win-sim] Starting Windows event log generator..."
python3 /usr/local/bin/eventlog_generator.py &

echo "[win-sim] ${WIN_HOSTNAME} is live and generating events."

# Keep container alive
wait
