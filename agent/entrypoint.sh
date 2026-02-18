#!/bin/bash
# Agent Container Entrypoint
# Starts file_generator.sh in background + disk_agent.sh in foreground loop

set -e

REPORT_INTERVAL=${REPORT_INTERVAL:-3600}  # Default: hourly
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "LogHive Agent Container Starting"
echo "========================================"
echo "Site: ${SITE:-not_set}"
echo "SubSite: ${SUB_SITE:-not_set}"
echo "ServerType: ${SERVER_TYPE:-not_set}"
echo "Monitor Path: ${MONITOR_PATH:-/data}"
echo "Report Interval: ${REPORT_INTERVAL}s"
echo "File Gen Interval: ${FILE_GEN_INTERVAL:-86400}s"
echo "Max Size: ${MAX_SIZE_MB:-500}MB"
echo "========================================"

# Ensure data directory exists
mkdir -p "${MONITOR_PATH:-/data}"

# Start file generator in background
"${SCRIPT_DIR}/file_generator.sh" &
FILE_GEN_PID=$!

# Trap to clean up background process
trap "kill $FILE_GEN_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Run disk agent in a loop
while true; do
    "${SCRIPT_DIR}/disk_agent.sh"
    sleep "$REPORT_INTERVAL"
done
