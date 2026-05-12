FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl gnupg apt-transport-https lsb-release \
    python3 netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Wazuh agent
RUN curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --no-default-keyring \
    --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg --import \
    && chmod 644 /usr/share/keyrings/wazuh.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" \
    | tee /etc/apt/sources.list.d/wazuh.list \
    && apt-get update \
    && WAZUH_MANAGER=wazuh.manager apt-get install -y wazuh-agent=4.7.4-1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY agent_ossec.conf /var/ossec/etc/ossec.conf
COPY eventlog_generator.py /usr/local/bin/eventlog_generator.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /usr/local/bin/eventlog_generator.py

ENTRYPOINT ["/entrypoint.sh"]
