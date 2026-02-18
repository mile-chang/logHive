# Lightweight Agent Container for LogHive
# Simulates a remote server that monitors disk usage and reports to central server
FROM alpine:3.19

# Install required tools
RUN apk add --no-cache \
    bash \
    curl \
    bc \
    coreutils

# Create app directory
WORKDIR /opt/agent

# Copy agent scripts
COPY disk_agent.sh .
COPY file_generator.sh .
COPY entrypoint.sh .

# Make scripts executable
RUN chmod +x disk_agent.sh file_generator.sh entrypoint.sh

# Create data directory
RUN mkdir -p /data

# Default environment variables
ENV CENTRAL_SERVER_URL=http://loghive:5100/api/report \
    API_TOKEN=change-me \
    SITE=Site_A \
    SUB_SITE=SubSite_1 \
    SERVER_TYPE=log_server \
    MONITOR_PATH=/data \
    MAX_SIZE_MB=500 \
    FILE_GEN_INTERVAL=86400 \
    REPORT_INTERVAL=3600 \
    MIN_FILE_KB=1 \
    MAX_FILE_KB=20480

ENTRYPOINT ["/opt/agent/entrypoint.sh"]
