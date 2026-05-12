# SOC Home Lab — Wazuh SIEM + Attack Simulation

A fully functional Security Operations Center (SOC) homelab built with Docker.
Includes a live SIEM, monitored endpoints, custom detection rules mapped to MITRE ATT&CK,
and attack simulation scripts that generate real alerts.

> **Stack:** Wazuh 4.7 · OpenSearch · Docker · Python

---

## What This Lab Does

| Capability | Detail |
|---|---|
| SIEM | Wazuh 4.7 — log ingestion, rule engine, alert management |
| Endpoints | 4 monitored agents (Linux + simulated Windows) |
| Detections | Custom rules mapped to MITRE ATT&CK TTPs |
| Attack Sims | SSH brute force, lateral movement, PowerShell C2, persistence |
| Dashboard | OpenSearch Dashboards — real-time alert visualisation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WAZUH SIEM STACK                     │
│                                                         │
│  ┌──────────────────┐      ┌────────────────────────┐   │
│  │  wazuh-manager   │─────▶│    wazuh-indexer       │   │
│  │  (rule engine)   │      │    (OpenSearch DB)     │   │
│  └──────────────────┘      └────────────┬───────────┘   │
│                                         │               │
│                             ┌───────────▼───────────┐   │
│                             │   wazuh-dashboard     │   │
│                             │   (UI on port 443)    │   │
│                             └───────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ agents (port 1514)
        ┌────────────┼──────────────────────┐
        ▼            ▼                      ▼
┌──────────────┐ ┌──────────────┐ ┌───────────────────────┐
│FINANCE-      │ │HR-LAPTOP-01  │ │ WEBDEV-WORKSATION-01  │
│WORKSTATION-01│ │(Windows sim) │ │ DEVOPS-WORKSTATION-01 │
│(Ubuntu + SSH)│ │              │ │ (Windows sims)        │
└──────────────┘ └──────────────┘ └───────────────────────┘
```

---

## Monitored Endpoints

| Agent | OS | Purpose |
|---|---|---|
| `FINANCE-WORKSTATION-01` | Ubuntu 22.04 | Linux target — SSH exposed, auditd, FIM monitoring |
| `HR-LAPTOP-01` | Windows (sim) | Simulates Windows 10 workstation with realistic event logs |
| `WEBDEV-WORKSATION-01` | Windows (sim) | Simulates Windows server — lateral movement target |
| `DEVOPS-WORKSTATION-01` | Windows (sim) | Simulates developer workstation |

---

## Detection Rules (MITRE ATT&CK Mapped)

| Rule ID | Name | MITRE TTP | Severity |
|---|---|---|---|
| 100001 | SSH Brute Force | T1110.001 | High (10) |
| 100002 | External SSH Brute Force | T1110.001 | High (12) |
| 100003 | Successful Login After Brute Force | T1078 | Critical (14) |
| 100004 | Direct Root SSH Login | T1078.003 | High (10) |
| 100101 | Encoded/Obfuscated Command Execution | T1027 | High (10) |
| 100102 | Download-and-Execute (curl\|bash) | T1105 | High (12) |
| 100104 | Known Attacker Tool Executed | T1095 | High (11) |
| 100202 | SSH authorized\_keys Modified (FIM) | T1098.004 | High (12) |
| 100204 | Sudo Privilege Escalation | T1548.003 | Medium (9) |
| 100205 | New User Account Created | T1136.001 | High (10) |

Full Sigma-format detection rules with analyst playbooks are in [`/detections`](./detections/).

---

## Attack Simulations

### Phase 1 — SSH Brute Force (T1110.001)
Sends 10 failed SSH logins followed by a successful login.
Triggers rules 100001 (brute force detected) and 100003 (account compromise — level 14 CRITICAL).

```bash
wsl -d Ubuntu python3 attacks/phase1_brute_force.py
```

### Phase 2 — Post-Exploitation (T1059, T1105, T1548)
Simulates an attacker living off the land after gaining access:
- Base64-encoded command execution
- `curl | bash` download-and-execute
- Netcat execution (known attacker tool)
- Sudo privilege escalation

```bash
ssh labuser@127.0.0.1 -p 2222   # password: password123
bash -s < attacks/phase2_post_exploitation.sh
```

### Phase 3 — Persistence (T1098.004, T1136)
- Adds attacker SSH key to `authorized_keys` (FIM alert)
- Creates backdoor user account

```bash
docker cp attacks/phase3_persistence.sh ubuntu-target:/tmp/phase3.sh
docker exec -it ubuntu-target bash /tmp/phase3.sh
```

### Windows Station Attacks (T1110, T1021.002, T1059.001, T1053)
Simulates a real attack chain across two Windows endpoints:
- **HR-LAPTOP-01**: Credential stuffing → account compromise → PowerShell C2 beacon
- **WEBDEV-WORKSATION-01**: Lateral movement via PsExec → SYSTEM shell → backdoor user → malicious scheduled task

```bash
wsl -d Ubuntu python3 attacks/attack_windows.py
```

---

## Project Structure

```
soc-homelab/
├── config/
│   ├── wazuh/
│   │   ├── local_rules.xml          # Custom detection rules
│   │   ├── ossec.conf               # Manager configuration
│   │   └── certs/                   # TLS certs (gitignored)
│   └── wazuh-dashboard/
│       └── opensearch_dashboards.yml
├── detections/                      # Sigma-format detection rules + playbooks
│   ├── brute_force_ssh.yml
│   ├── lateral_movement_psexec.yml
│   └── suspicious_powershell.yml
├── targets/
│   ├── Dockerfile                   # Ubuntu Linux target
│   ├── audit.rules                  # Auditd syscall monitoring rules
│   ├── agent_ossec.conf             # Agent config (FIM, log collection)
│   └── windows-sim/                 # Simulated Windows endpoint
│       ├── Dockerfile
│       └── eventlog_generator.py    # Generates Windows Event Log JSON
├── attacks/                         # Attack simulation scripts
│   ├── phase1_brute_force.py        # SSH brute force
│   ├── phase2_post_exploitation.sh  # Post-access living off the land
│   ├── phase3_persistence.sh        # Backdoor + authorized_keys
│   └── attack_windows.py           # Multi-stage Windows attack chain
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

**Requirements:** Docker Desktop, WSL2 (Windows) or Linux/macOS

```bash
git clone https://github.com/YOUR_USERNAME/soc-homelab.git
cd soc-homelab
cp .env.example .env          # edit passwords if needed
docker compose up -d
```

Wait ~2 minutes for services to become healthy, then open **https://localhost**.  
Default login: `admin` / (password from your `.env`)

---

## Skills Demonstrated

- **SIEM deployment** — Wazuh stack (manager, indexer, dashboard) orchestrated in Docker Compose
- **Detection engineering** — custom Wazuh rules + Sigma format with analyst playbooks
- **MITRE ATT&CK mapping** — TTPs tagged on every rule and alert
- **Threat simulation** — realistic multi-stage attack chains (initial access → lateral movement → persistence)
- **Linux security monitoring** — auditd, FIM, SSH log analysis
- **Windows event log knowledge** — Security/Sysmon event IDs (4624, 4625, 4688, 7045, 4698)
- **Incident response** — triage playbooks written for each detection

---

## Notes

- Built for learning and portfolio purposes only
- The Ubuntu target is intentionally misconfigured — do not expose to the internet
- All attack simulations run against local containers only
