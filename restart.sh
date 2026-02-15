#!/bin/bash
# LogHive Restart Script
# This script restarts the dashboard service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "Restarting Log Hive"
echo "========================================"

# Stop the service
./stop.sh

# Wait for cleanup
echo "Waiting for cleanup..."
sleep 2

# Start the service
./start.sh "$@"
