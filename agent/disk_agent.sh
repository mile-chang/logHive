#!/bin/bash
# Disk Monitoring Agent - Collect folder size and report to central server
# Deploy on VMs at each site and execute periodically via cron

# ==================== Configuration (Please modify the following settings) ====================
# These can be set via environment variables (for Docker) or edited directly (for cron)

# Central server URL (CHANGE THIS)
CENTRAL_SERVER_URL="${CENTRAL_SERVER_URL:-http://YOUR_CENTRAL_SERVER_IP:5100/api/report}"

# API Token - IMPORTANT: Change this to match API_TOKEN in central server's .env file
API_TOKEN="${API_TOKEN:-your-api-token-from-central-server}"

# Site information (modify according to actual situation)
SITE="${SITE:-Site_A}"           # Main site name: Site_A or Site_B
SUB_SITE="${SUB_SITE:-SubSite_1}"        # Sub-site name: SubSite_1, SubSite_2, SubSite_3, etc.
SERVER_TYPE="${SERVER_TYPE:-log_server}"  # Server type: log_server, backup_log_server

# Monitor path
MONITOR_PATH="${MONITOR_PATH:-/data}"

# ==================== Main Program ====================

# Get folder size in MB
get_folder_size_mb() {
    local path=$1
    if [ -d "$path" ]; then
        # Use du to get size in KB, then convert to MB
        local size_kb
        size_kb=$(du -sk "$path" 2>/dev/null | cut -f1)
        if [ -n "$size_kb" ]; then
            echo "scale=2; $size_kb / 1024" | bc | sed 's/^\./0./'
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
    
    local json_data
    json_data=$(cat <<EOF
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
    response=$(curl -s -w "\n%{http_code}" -X POST "$CENTRAL_SERVER_URL" \
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
    echo "========================================"
    
    # Check if path exists
    if [ ! -d "$MONITOR_PATH" ]; then
        echo "Error: Path ${MONITOR_PATH} does not exist"
        exit 1
    fi
    
    # Get folder size
    size_mb=$(get_folder_size_mb "$MONITOR_PATH")
    echo "Folder Size: ${size_mb} MB"
    
    # Send report
    send_report "$size_mb"
}

# Execute main function
main "$@"
