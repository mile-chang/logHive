#!/bin/bash
# Docker entrypoint script for LogHive

set -e

echo "========================================="
echo "LogHive Container Starting"
echo "========================================="
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-5100}"
echo "========================================="

# Create necessary directories
mkdir -p /app/data /app/logs

# Initialize database (safe to run every time - creates tables only if not exist, runs pending migrations)
if [ ! -f "/app/data/dashboard.db" ]; then
    echo "Database not found. Initializing..."
else
    echo "Database found. Checking for pending migrations..."
fi
python3 -c "from models import init_db; init_db()"
echo "✓ Database ready"

# Display startup information
echo "========================================="
echo "Starting application..."
echo "User: $(whoami)"
echo "Python: $(python3 --version)"
echo "Working directory: $(pwd)"
echo "========================================="

# Execute the main command
exec "$@"
