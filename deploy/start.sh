#!/bin/bash
# LogHive Startup Script
# This script handles virtual environment activation, port checking, and service startup

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
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/dashboard.log"
PID_FILE=".dashboard.pid"

# Load VENV_PATH directly from .env file
if [ -f ".env" ]; then
    VENV_PATH=$(grep -E "^VENV_PATH=" .env | sed 's/VENV_PATH=//' | tr -d '\r')
fi

# Check if VENV_PATH environment variable is set (overrides .env)
if [ -n "$VENV_PATH_ENV" ]; then
    VENV_PATH="$VENV_PATH_ENV"
fi

# Expand ~ to home directory if present
if [[ "$VENV_PATH" == "~"* ]]; then
    VENV_PATH="${HOME}${VENV_PATH:1}"
fi

echo "========================================"
echo "Log Hive Startup"
echo "========================================"
echo "Working Directory: $SCRIPT_DIR"
echo "Port: $PORT"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process using the port
kill_port_process() {
    if check_port; then
        echo "⚠ Warning: Port $PORT is already in use"
        PID=$(lsof -ti:$PORT)
        echo "Found process PID: $PID"
        echo "Stopping old process..."
        kill -9 $PID 2>/dev/null
        sleep 2
        
        # Verify it's stopped
        if check_port; then
            echo "✗ Error: Failed to stop process on port $PORT"
            exit 1
        else
            echo "✓ Old process stopped successfully"
        fi
    fi
}

# Activate virtual environment if specified
if [ -n "$VENV_PATH" ] && [ -d "$VENV_PATH" ]; then
    echo "Virtual Environment: $VENV_PATH"

    # Check if activation script exists
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        echo "✓ Virtual environment activated"
    else
        echo "✗ Error: Virtual environment not found at $VENV_PATH"
        exit 1
    fi
else
    echo "Virtual Environment: Using system environment"
fi

# Display Python information
echo "Python: $(which python3)"
echo "Python Version: $(python3 --version)"
echo "========================================"

# Check command line arguments
if [ "$1" = "dev" ]; then
    # Development mode - use Flask dev server
    echo "Starting in DEVELOPMENT mode..."
    echo "Note: Dev mode runs in foreground (Ctrl+C to stop)"
    
    # Kill any process using the port
    kill_port_process
    
    # Run in foreground
    python3 app.py
    
elif [ "$1" = "init" ]; then
    # Initialize database
    echo "Initializing database..."
    python3 -c "from models import init_db; init_db()"
    echo "✓ Database initialized"
    
elif [ "$1" = "test" ]; then
    # Run tests
    echo "Running tests..."
    python3 test_environment.py
    
else
    # Production mode - use Gunicorn in background
    echo "Starting in PRODUCTION mode (background)..."

    # Check if gunicorn is installed
    if ! command -v gunicorn &> /dev/null; then
        echo "✗ Error: gunicorn not found. Please install it:"
        echo "  pip install gunicorn"
        exit 1
    fi

    # Kill any process using the port
    kill_port_process

    # Start gunicorn in background with nohup
    echo "Starting Gunicorn server..."
    nohup gunicorn -c gunicorn_config.py app:app > "$LOG_FILE" 2>&1 &
    APP_PID=$!

    # Wait a moment for startup
    sleep 3

    # Check if process is still running
    if ps -p $APP_PID > /dev/null 2>&1; then
        echo "✓ Service started successfully!"
        echo "  PID: $APP_PID"
        echo "  URL: http://localhost:$PORT"
        echo "  Log: $LOG_FILE"
        echo ""
        echo "Use './stop.sh' to stop the service"
        
        # Save PID to file for stop script
        echo $APP_PID > "$PID_FILE"
    else
        echo "✗ Failed to start service!"
        echo "Check log file: $LOG_FILE"
        exit 1
    fi
fi