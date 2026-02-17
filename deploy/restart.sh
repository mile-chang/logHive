#!/bin/bash
# LogHive Restart Script
# This script restarts the dashboard service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Restarting Log Hive"
echo "========================================"

# Stop the service
"$SCRIPT_DIR/stop.sh"

# Wait for cleanup
echo "Waiting for cleanup..."
sleep 2

# Start the service
"$SCRIPT_DIR/start.sh" "$@"
