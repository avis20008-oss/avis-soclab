# SOC Home Lab — Mock Attack Playbook

Three-phase attack simulation against the `ubuntu-target` container.
Open the Wazuh dashboard at **https://localhost** before you start.

---

## Prerequisites

```powershell
# Install Python SSH library (one-time)
pip install paramiko
```

---

## Phase 1 — SSH Brute Force

**Goal:** Trigger brute-force detection, then a successful login.  
**Alerts expected:** Rule 100001 (level 10), Rule 100003 (level 14 CRITICAL)

```powershell
python attacks/phase1_brute_force.py
```

What happens:
1. Script sends 10 wrong passwords → fires rule 100001 (8+ failures in 2 min)
2. Then logs in with `labuser:password123` → fires rule 100003 (success after brute force)

---

## Phase 2 — Post-Exploitation

**Goal:** Simulate attacker living off the land inside the target.  
**Alerts expected:** Rules 100101, 100102, 100104, 100204

```powershell
# SSH into the target first
ssh labuser@127.0.0.1 -p 2222
# password: password123

# Then inside the shell, run:
bash -s < attacks/phase2_post_exploitation.sh
```

What happens:
- Encoded command via `base64 -d | bash` → rule 100101
- `curl | bash` download-exec pattern → rule 100102
- `nc` (netcat) execution → rule 100104
- `sudo` escalation → rule 100204

---

## Phase 3 — Persistence & Lateral Movement

**Goal:** Establish persistence and simulate lateral movement indicators.  
**Alerts expected:** Rules 100202, 100205, 100201

```powershell
# Quickest method — run via docker exec as root:
docker exec -it ubuntu-target bash -c "bash /tmp/phase3.sh"

# Or copy the script in first:
docker cp attacks/phase3_persistence.sh ubuntu-target:/tmp/phase3.sh
docker exec -it ubuntu-target bash /tmp/phase3.sh
```

What happens:
- Adds SSH key to `authorized_keys` → Wazuh FIM fires rule 100202
- Creates backdoor user account → rule 100205
- Instructions for SSH tunnel trigger → rule 100201

---

## Watching Alerts in Wazuh

**Dashboard:** https://localhost  
**Login:** admin / (see `.env` file for `WAZUH_INDEXER_PASSWORD`)

Useful filters in Security Events:
| Filter | Shows |
|--------|-------|
| `rule.id: 100003` | Critical: brute force success |
| `rule.groups: soc_lab_alert` | All lab alerts |
| `rule.level: >= 10` | High severity and above |
| `agent.name: ubuntu-target-01` | All events from the target |

---

## Cleanup After Lab

```bash
# Inside ubuntu-target:
docker exec -it ubuntu-target bash
userdel -r backdoor
sed -i '/attacker@c2server/d' /home/labuser/.ssh/authorized_keys
rm -f /tmp/pwned
```
