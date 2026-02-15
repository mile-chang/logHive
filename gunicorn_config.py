# Gunicorn Configuration for Production

import multiprocessing
import os
import sys

# Add current directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import PORT from config
try:
    from config import PORT
except ImportError:
    PORT = 5100  # Fallback to default port

# Bind to all interfaces on configured port
bind = f"0.0.0.0:{PORT}"

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout for worker processes
timeout = 120

# Logging
accesslog = "/var/log/dashboard/gunicorn/access.log"
errorlog = "/var/log/dashboard/gunicorn/error.log"
loglevel = "info"

# Process naming
proc_name = "logHive"

# Daemon mode (set to True for production)
daemon = False

# Reload on code changes (set to False for production)
reload = False
