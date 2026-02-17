#!/bin/bash
# LogHive Stop Script
# This script stops the dashboard service by finding and killing the process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Read PORT from config.py
PORT=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from config import PORT
    print(PORT)
except:
    print(5100)  # Fallback to default
" 2>/dev/null)

# Configuration
PID_FILE=".dashboard.pid"

echo "========================================"
echo "Log Hive Stop Script"
echo "========================================"
echo "Port: $PORT"

# Method 1: Stop using PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    
    # Check if process is still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "Found process from PID file: $PID"
        echo "Stopping process..."
        
        # Try graceful shutdown first (SIGTERM)
        kill -15 $PID 2>/dev/null
        sleep 2
        
        # If still running, force kill (SIGKILL)
        if ps -p $PID > /dev/null 2>&1; then
            echo "Process still running, forcing shutdown..."
            kill -9 $PID 2>/dev/null
            sleep 1
        fi
        
        # Verify it's stopped
        if ps -p $PID > /dev/null 2>&1; then
            echo "✗ Failed to stop process $PID"
        else
            echo "✓ Process stopped successfully (PID: $PID)"
            rm -f "$PID_FILE"
        fi
    else
        echo "Process from PID file ($PID) is not running"
        rm -f "$PID_FILE"
    fi
fi

# Method 2: Stop by finding process on port
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    PID=$(lsof -ti:$PORT)
    echo "Found process on port $PORT: $PID"
    echo "Stopping process..."
    kill -9 $PID 2>/dev/null
    sleep 1
    
    # Verify port is free
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "✗ Failed to stop process on port $PORT"
        exit 1
    else
        echo "✓ Process on port $PORT stopped successfully"
    fi
else
    echo "✓ No process found on port $PORT"
fi

echo "========================================"
echo "Service stopped"
echo "========================================"
