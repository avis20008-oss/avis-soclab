# ============================================================
# SOC Home Lab — Vulnerable Ubuntu Target
# Intentionally misconfigured for lab/training purposes only.
# DO NOT use these settings in production environments.
# ============================================================
FROM ubuntu:22.04

LABEL maintainer="SOC-Lab"
LABEL description="Vulnerable Ubuntu target with Wazuh agent for SOC training"
LABEL warning="For authorized lab use only — intentionally insecure"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install dependencies
RUN apt-get update && apt-get install -y \
    # SSH server (intentionally weakly configured)
    openssh-server \
    # Wazuh agent dependencies
    curl \
    gnupg \
    apt-transport-https \
    lsb-release \
    # Audit framework for syscall monitoring
    auditd \
    audispd-plugins \
    # Useful for attack simulation
    netcat-openbsd \
    nmap \
    wget \
    python3 \
    python3-pip \
    sudo \
    vim \
    net-tools \
    iputils-ping \
    tcpdump \
    # Log shipping utilities
    rsyslog \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Wazuh Agent Installation
# ============================================================
RUN curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --no-default-keyring \
    --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import \
    && chmod 644 /usr/share/keyrings/wazuh.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" \
    | tee /etc/apt/sources.list.d/wazuh.list \
    && apt-get update \
    && WAZUH_MANAGER=wazuh.manager WAZUH_AGENT_GROUP=ubuntu-targets apt-get install -y wazuh-agent=4.7.4-1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# SSH Configuration — Intentionally weak for lab attack sims
# WARNING: These settings are deliberately insecure for training
# ============================================================
RUN mkdir -p /run/sshd /var/run/sshd

COPY ssh_config /etc/ssh/sshd_config

# Create lab user accounts with weak passwords (intentional for lab)
RUN useradd -m -s /bin/bash labuser \
    && echo "labuser:password123" | chpasswd \
    && useradd -m -s /bin/bash developer \
    && echo "developer:dev123" | chpasswd \
    && useradd -m -s /bin/bash svcaccount \
    && echo "svcaccount:svc2024" | chpasswd \
    && echo "root:toor" | chpasswd \
    && usermod -aG sudo labuser

# ============================================================
# Auditd Configuration — captures syscall events for Wazuh
# ============================================================
COPY audit.rules /etc/audit/rules.d/audit.rules

# ============================================================
# Wazuh Agent Configuration
# ============================================================
COPY agent_ossec.conf /var/ossec/etc/ossec.conf

# ============================================================
# Entrypoint
# ============================================================
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]
