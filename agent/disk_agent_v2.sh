#!/bin/bash
# Disk Monitoring Agent - Collect folder size and report to central server
# Deploy on VMs at each site and execute periodically via cron
# Version: 2.0 - Added SSH tunnel support for restricted networks

# ==================== Configuration (Please modify the following settings) ====================
# These can be set via environment variables (for Docker) or edited directly (for cron)

# Connection method: "direct" or "ssh_tunnel"
CONNECTION_METHOD="${CONNECTION_METHOD:-direct}"

# Direct connection settings (used when CONNECTION_METHOD="direct")
# CHANGE THIS to your actual central server IP and port
CENTRAL_SERVER_URL="${CENTRAL_SERVER_URL:-http://YOUR_CENTRAL_SERVER_IP:5100/api/report}"

# SSH tunnel settings (used when CONNECTION_METHOD="ssh_tunnel")
# CHANGE THESE to match your SSH server configuration
SSH_TUNNEL_HOST="${SSH_TUNNEL_HOST:-YOUR_SSH_HOST_IP}"          # The server where dashboard is running
SSH_TUNNEL_USER="${SSH_TUNNEL_USER:-your_ssh_username}"         # SSH username
SSH_TUNNEL_PORT=${SSH_TUNNEL_PORT:-22}                           # SSH port (usually 22)
SSH_LOCAL_PORT=${SSH_LOCAL_PORT:-15100}                         # Local port for tunnel
DASHBOARD_PORT=${DASHBOARD_PORT:-5100}                          # Dashboard port on remote server

# API Token - IMPORTANT: Change this to match API_TOKEN in central server's .env file
API_TOKEN="${API_TOKEN:-your-api-token-from-central-server}"

# Site information (modify according to actual situation)
SITE="${SITE:-Site_A}"           # Main site name: Site_A or Site_B
SUB_SITE="${SUB_SITE:-SubSite_1}"        # Sub-site name: SubSite_1, SubSite_2, SubSite_3, etc.
SERVER_TYPE="${SERVER_TYPE:-log_server}"  # Server type: log_server, backup_log_server

# Monitor path
MONITOR_PATH="${MONITOR_PATH:-/data}"

# ==================== SSH Tunnel Functions ====================

# Setup SSH tunnel
setup_ssh_tunnel() {
    # Check if tunnel already exists
    if check_ssh_tunnel; then
        echo "[INFO] SSH tunnel already exists"
        return 0
    fi
    
    echo "[INFO] Setting up SSH tunnel to ${SSH_TUNNEL_HOST}..."
    
    # Create SSH tunnel in background
    # -f: go to background
    # -N: don't execute remote command
    # -L: local port forwarding
    ssh -f -N -L ${SSH_LOCAL_PORT}:localhost:${DASHBOARD_PORT} \
        -p ${SSH_TUNNEL_PORT} \
        ${SSH_TUNNEL_USER}@${SSH_TUNNEL_HOST} 2>/dev/null
    
    if [ $? -eq 0 ]; then
        # Wait a moment for tunnel to establish
        sleep 2
        
        # Verify tunnel is working
        if check_ssh_tunnel; then
            echo "[INFO] SSH tunnel established successfully"
            return 0
        else
            echo "[ERROR] SSH tunnel failed to establish"
            return 1
        fi
    else
        echo "[ERROR] Failed to create SSH tunnel"
        return 1
    fi
}

# Check if SSH tunnel is active
check_ssh_tunnel() {
    # Check if local port is listening
    if lsof -Pi :${SSH_LOCAL_PORT} -sTCP:LISTEN -t >/dev/null 2>&1 || \
       netstat -tuln 2>/dev/null | grep -q ":${SSH_LOCAL_PORT}"; then
        return 0
    else
        return 1
    fi
}

# Cleanup SSH tunnel
cleanup_ssh_tunnel() {
    if [ "$TUNNEL_CREATED" = "true" ]; then
        echo "[INFO] Cleaning up SSH tunnel..."
        # Find and kill SSH tunnel process
        PID=$(lsof -ti:${SSH_LOCAL_PORT} 2>/dev/null)
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null
            echo "[INFO] SSH tunnel closed"
        fi
    fi
}

# ==================== Main Program ====================

# Get folder size in MB
get_folder_size_mb() {
    local path=$1
    if [ -d "$path" ]; then
        # Use du to get size in KB, then convert to MB
        local size_kb=$(du -sk "$path" 2>/dev/null | cut -f1)
        if [ -n "$size_kb" ]; then
            echo "scale=2; $size_kb / 1024" | bc
        else
            echo "0"
        fi
    else
        echo "0"
    fi
}

# Send data to central server
send_report() {
    local size_mb=$1
    local api_url="$CENTRAL_SERVER_URL"
    
    # If using SSH tunnel, modify URL to use localhost
    if [ "$CONNECTION_METHOD" = "ssh_tunnel" ]; then
        api_url="http://localhost:${SSH_LOCAL_PORT}/api/report"
    fi
    
    local json_data=$(cat <<EOF
{
    "token": "${API_TOKEN}",
    "site": "${SITE}",
    "sub_site": "${SUB_SITE}",
    "server_type": "${SERVER_TYPE}",
    "path": "${MONITOR_PATH}",
    "size_mb": ${size_mb}
}
EOF
)
    
    # Send POST request
    response=$(curl -s -w "\n%{http_code}" -X POST "$api_url" \
        -H "Content-Type: application/json" \
        -d "$json_data" \
        --connect-timeout 10 \
        --max-time 30)
    
    # Parse response
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Report successful: ${size_mb} MB"
        return 0
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Report failed (HTTP ${http_code}): ${body}"
        return 1
    fi
}

# Main function
main() {
    echo "========================================"
    echo "Disk Monitoring Agent - Folder Size Tracking"
    echo "Site: ${SITE} / ${SUB_SITE}"
    echo "Server Type: ${SERVER_TYPE}"
    echo "Monitor Path: ${MONITOR_PATH}"
    echo "Connection: ${CONNECTION_METHOD}"
    echo "========================================"
    
    # Setup trap to cleanup on exit
    trap cleanup_ssh_tunnel EXIT
    
    # Setup SSH tunnel if needed
    TUNNEL_CREATED="false"
    if [ "$CONNECTION_METHOD" = "ssh_tunnel" ]; then
        if ! setup_ssh_tunnel; then
            echo "[ERROR] Cannot establish connection to central server"
            exit 1
        fi
        TUNNEL_CREATED="true"
    fi
    
    # Check if path exists
    if [ ! -d "$MONITOR_PATH" ]; then
        echo "[ERROR] Path ${MONITOR_PATH} does not exist"
        exit 1
    fi
    
    # Get folder size
    size_mb=$(get_folder_size_mb "$MONITOR_PATH")
    echo "[INFO] Folder Size: ${size_mb} MB"
    
    # Send report
    send_report "$size_mb"
    
    exit_code=$?
    
    # Manual cleanup (trap will also run)
    cleanup_ssh_tunnel
    
    exit $exit_code
}

# Execute main function
main "$@"
