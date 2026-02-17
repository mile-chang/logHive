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

# Initialize database if it doesn't exist
if [ ! -f "/app/data/dashboard.db" ]; then
    echo "Database not found. Initializing..."
    python3 -c "from models import init_db; init_db()"
    echo "✓ Database initialized"
else
    echo "✓ Database found"
    
    # Run migrations if needed
    if [ -f "migrate_db.py" ]; then
        echo "Running database migrations..."
        python3 migrate_db.py || echo "⚠ Migration skipped or failed"
    fi
fi

# Display startup information
echo "========================================="
echo "Starting application..."
echo "User: $(whoami)"
echo "Python: $(python3 --version)"
echo "Working directory: $(pwd)"
echo "========================================="

# Execute the main command
exec "$@"
