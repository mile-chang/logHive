# Configuration for LogHive
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment setting: 'test' or 'production'
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')

# Flask configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Server port configuration
PORT = int(os.environ.get('PORT', 5100))

# Database configuration
def get_database_path(environment='production'):
    """Get database path based on environment"""
    if environment == 'test':
        return os.path.join(os.path.dirname(__file__), 'data', 'dashboard_test.db')
    else:
        return os.path.join(os.path.dirname(__file__), 'data', 'dashboard.db')

# Default database path (for backward compatibility)
DATABASE_PATH = get_database_path('production')

# Session configuration
SESSION_LIFETIME = timedelta(hours=24)

# API Token for agents (change in production)
API_TOKEN = os.environ.get('API_TOKEN', 'change-me-set-api-token-in-env')

# Site and Server Configuration
SITES_CONFIG = {
    "Site_A": {
        "sub_sites": {
            "SubSite_1": {
                "log_server": {"name": "Log Server"},
                "backup_server": {"name": "Backup Server"}
            },
            "SubSite_2": {
                "log_server": {"name": "Log Server"},
                "backup_server": {"name": "Backup Server"}
            },
            "SubSite_4": {
                "log_server": {"name": "Log Server"},
                "backup_server": {"name": "Backup Server"}
            },
            "SubSite_6": {
                "log_server": {"name": "Log Server"},
                "backup_server": {"name": "Backup Server"}
            }
        }
    },
    "Site_B": {
        "sub_sites": {
            "SubSite_3": {
                "log_server": {"name": "Log Server"},
                "backup_log_server": {"name": "Backup Log Server"}
            },
            "SubSite_5": {
                "log_server": {"name": "Log Server"},
                "backup_log_server": {"name": "Backup Log Server"}
            },
            "SubSite_6": {
                "log_server": {"name": "Log Server"},
                "backup_log_server": {"name": "Backup Log Server"}
            },
            "SubSite_Lab": {
                "log_server": {"name": "Log Server"},
                "backup_log_server": {"name": "Backup Log Server"}
            },
            "SubSite_4": {
                "log_server": {"name": "Log Server"},
                "backup_log_server": {"name": "Backup Log Server"}
            }
        }
    }
}

# User accounts configuration
USERS_CONFIG = {
    "test": {
        "username": os.environ.get('TEST_USERNAME', 'test'),
        "password": os.environ.get('TEST_PASSWORD', 'change-me-in-production'),  # Change via environment variable
        "environment": "test"
    },
    "admin": {
        "username": os.environ.get('ADMIN_USERNAME', 'admin'),
        "password": os.environ.get('ADMIN_PASSWORD', 'change-me-in-production'),  # Change via environment variable
        "environment": "production"
    }
}

# Path to virtual environment (leave empty for current environment)
VENV_PATH = os.environ.get('VENV_PATH', '')
