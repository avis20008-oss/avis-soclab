# SOC Home Lab — Detection Rules

Three Sigma rules covering the most common attack techniques seen in real SOC environments.

## Rules

| File | Technique | MITRE | Severity |
|------|-----------|-------|----------|
| `brute_force_ssh.yml` | SSH Brute Force | T1110.001 | High |
| `suspicious_powershell.yml` | Obfuscated PowerShell Execution | T1059.001, T1027 | High |
| `lateral_movement_psexec.yml` | Lateral Movement via PsExec | T1021.002 | Critical |

## Sigma Format

Each rule follows the [Sigma specification](https://github.com/SigmaHQ/sigma) and can be compiled to native SIEM query language using `sigmac` or `pySigma`:

```bash
# Install sigmac
pip install sigmatools

# Convert to Splunk SPL
sigmac -t splunk -c splunk-windows brute_force_ssh.yml

# Convert to Elastic SIEM
sigmac -t es-qs -c winlogbeat suspicious_powershell.yml

# Convert to QRadar AQL
sigmac -t qradar lateral_movement_psexec.yml

# Convert to Wazuh rules (community backend)
sigmac -t wazuh brute_force_ssh.yml
```

## Wazuh Native Rules

The equivalent Wazuh XML rules are in `../config/wazuh/local_rules.xml`:

- Rule IDs `100001–100004` → brute force SSH
- Rule IDs `100101–100104` → suspicious execution (Linux equivalents)
- Rule IDs `100201–100205` → lateral movement (SSH-based equivalents)

## Analyst Workflow

Each Sigma rule contains a detailed **SOC Analyst Playbook** in its comments, covering:

1. Triage steps
2. High-severity escalation indicators
3. Evidence collection artifacts
4. Containment actions
5. Full MITRE ATT&CK mapping
