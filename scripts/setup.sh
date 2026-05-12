#!/bin/bash
# ============================================================
# SOC Home Lab — Initial Setup Script
# Generates TLS certificates required by Wazuh components
# Must run before docker-compose up
# ============================================================
set -euo pipefail

CERT_DIR="$(dirname "$0")/../config/wazuh/certs"
COMPOSE_DIR="$(dirname "$0")/.."

echo "======================================================"
echo " SOC Home Lab — Setup Script"
echo "======================================================"

# ── Prerequisites check ─────────────────────────────────────
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker not installed"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1 || {
    echo "ERROR: docker-compose not installed"; exit 1;
}

echo "[1/4] Creating certificate directory..."
mkdir -p "${CERT_DIR}"

# ── Set vm.max_map_count (required by OpenSearch/Wazuh Indexer) ──
echo "[2/4] Setting vm.max_map_count=262144 for OpenSearch..."
if [ "$(uname -s)" = "Linux" ]; then
    sudo sysctl -w vm.max_map_count=262144
    # Make it persistent
    if ! grep -q "vm.max_map_count" /etc/sysctl.conf 2>/dev/null; then
        echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
        echo "  Added to /etc/sysctl.conf for persistence"
    fi
else
    echo "  NOTE: On macOS/Windows, Docker Desktop handles this automatically."
    echo "  If Wazuh Indexer fails to start, set in Docker Desktop resources."
fi

# ── Generate TLS Certificates via Wazuh's cert generator ────
echo "[3/4] Generating TLS certificates..."
cat > /tmp/wazuh-certs-config.yml <<'EOF'
nodes:
  indexer:
    - name: wazuh.indexer
      ip:
        - 127.0.0.1
        - wazuh.indexer
  server:
    - name: wazuh.manager
      ip:
        - 127.0.0.1
        - wazuh.manager
  dashboard:
    - name: wazuh.dashboard
      ip:
        - 127.0.0.1
        - wazuh.dashboard
EOF

docker run --rm \
    -v /tmp/wazuh-certs-config.yml:/config/certs.yml \
    -v "${CERT_DIR}:/certificates" \
    wazuh/wazuh-certs-generator:0.0.1 \
    -conf /config/certs.yml \
    -certs-tool

# Fix permissions so containers can read certs
chmod 644 "${CERT_DIR}"/*.pem 2>/dev/null || true
chmod 600 "${CERT_DIR}"/*-key.pem 2>/dev/null || true

echo "  Certificates generated in: ${CERT_DIR}"
ls -la "${CERT_DIR}"

# ── Pull Docker images (optional pre-pull for faster startup) ──
echo "[4/4] Pre-pulling Docker images (this may take a while)..."
docker pull wazuh/wazuh-indexer:4.7.4 &
docker pull wazuh/wazuh-manager:4.7.4 &
docker pull wazuh/wazuh-dashboard:4.7.4 &
wait

echo ""
echo "======================================================"
echo " Setup complete!"
echo ""
echo " To start the lab:"
echo "   cd ${COMPOSE_DIR}"
echo "   docker-compose up -d"
echo ""
echo " Then wait ~3 minutes for services to initialize."
echo ""
echo " Dashboard: https://localhost (admin / SecretPassword1!)"
echo " SSH target: ssh labuser@localhost -p 2222 (password123)"
echo "======================================================"
