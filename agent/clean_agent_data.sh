#!/bin/bash
# Clean Agent Data - Remove all generated files from agent containers
# Usage:
#   ./agent/clean_agent_data.sh           # Clean all agents
#   ./agent/clean_agent_data.sh agent-a-sub1-log  # Clean specific agent

set -e

CONTAINERS=(
    "agent-a-sub1-log"
    "agent-a-sub1-backup"
    "agent-a-sub2-log"
    "agent-a-sub2-backup"
    "agent-b-sub3-log"
    "agent-b-sub3-backup"
)

# If a specific container is provided, only clean that one
if [ -n "$1" ]; then
    CONTAINERS=("$1")
fi

echo "========================================"
echo "LogHive - Cleaning Agent Data"
echo "========================================"

for container in "${CONTAINERS[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "[SKIP] ${container} is not running"
        continue
    fi

    # Get current size before cleaning
    size_before=$(docker exec "$container" du -sm /data 2>/dev/null | cut -f1)

    # Remove all files in /data
    docker exec "$container" sh -c 'rm -rf /data/*'

    echo "[OK] ${container}: cleaned ${size_before:-0}MB"
done

echo ""
echo "All agent data cleaned."
