#!/bin/bash
# Demo File Generator - Instantly create files in all agent containers
# Usage:
#   ./agent/demo_generate.sh        # Create 1 file per agent
#   ./agent/demo_generate.sh 5      # Create 5 files per agent

set -e

COUNT=${1:-1}

# File size range (can be overridden via env or arg)
MIN_FILE_KB=${MIN_FILE_KB:-1}
MAX_FILE_KB=${MAX_FILE_KB:-1024}    # Default: 1MB max
LARGE_FILE_PROB=${LARGE_FILE_PROB:-30}  # % chance of large file

CONTAINERS=(
    "agent-a-sub1-log"
    "agent-a-sub1-backup"
    "agent-a-sub2-log"
    "agent-a-sub2-backup"
    "agent-b-sub3-log"
    "agent-b-sub3-backup"
)

# Weighted random file size
get_random_size_kb() {
    local mid
    mid=$(( (MIN_FILE_KB + MAX_FILE_KB) / 2 ))
    local roll
    roll=$(( RANDOM % 100 ))
    if [ "$roll" -lt "$LARGE_FILE_PROB" ]; then
        local range
        range=$(( MAX_FILE_KB - mid + 1 ))
        echo $(( mid + RANDOM % range ))
    else
        local range
        range=$(( mid - MIN_FILE_KB + 1 ))
        echo $(( MIN_FILE_KB + RANDOM % range ))
    fi
}

echo "========================================"
echo "LogHive Demo - Generating Files"
echo "Files per agent: ${COUNT}"
echo "File size range: ${MIN_FILE_KB}KB - ${MAX_FILE_KB}KB (large prob: ${LARGE_FILE_PROB}%)"
echo "========================================"

for container in "${CONTAINERS[@]}"; do
    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "[SKIP] ${container} is not running"
        continue
    fi

    for _ in $(seq 1 "$COUNT"); do
        size_kb=$(get_random_size_kb)
        filename="demo_$(date +%Y%m%d_%H%M%S)_${RANDOM}.bin"

        docker exec "$container" sh -c \
            "dd if=/dev/urandom of=/data/${filename} bs=1024 count=${size_kb} 2>/dev/null"

        echo "[OK] ${container}: created ${filename} (${size_kb}KB)"
    done
done

echo ""
echo "========================================"
echo "Done! Files created in all agents."
echo ""
echo "Next steps:"
echo "  1. Wait for agents to report (or trigger manually):"
echo "     for c in ${CONTAINERS[*]}; do docker exec \$c /opt/agent/disk_agent.sh; done"
echo "  2. Refresh LogHive dashboard to see changes"
echo "========================================"
