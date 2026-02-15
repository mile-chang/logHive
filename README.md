<div align="center">

  <samp>Simple. Powerful. Dashboard.</samp>
  <br><br>
  <a href="https://github.com/mile-chang/logHive">
    <img src="static/logo_full.svg" alt="LogHive Logo" width="417">
  </a>
</div>

> A centralized monitoring system for tracking disk usage across multiple sites with real-time visualization and automated data collection.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

[繁體中文](README.zh-TW.md) | [日本語](README.ja.md)

---

## Overview

logHive is a monitoring system designed to track and visualize disk usage across multiple sites. Built with Flask and featuring a responsive web interface, it provides real-time monitoring, historical tracking, and automated data collection through lightweight agents.


## Feature Demo

![LogHive Demo](docs/screenshots/demo.webp)

*Complete walkthrough: Login → Data Loading (with animation) → Interactive Dashboard*

## Key Features

- **Modern Dark Theme** - Sleek glassmorphism design with backdrop blur effects
- **Real-time Monitoring** - Live disk usage tracking with auto-refresh
- **Interactive Charts** - Historical usage visualization using Chart.js
- **Toast Notifications** - Elegant notifications with smooth animations
- **Loading States** - Visual feedback for all async operations
- **Multi-site Support** - Manage unlimited sites with customizable configurations
- **Historical Analytics** - Monthly growth tracking and usage statistics
- **Dual Environments** - Separate test and production databases
- **Automated Agents** - Lightweight bash scripts for data collection
- **SSH Tunnel Support** - Secure data transmission for restricted networks
- **Production Ready** - Systemd integration, Gunicorn, and comprehensive logging

## System Architecture

```mermaid
graph TB
    subgraph "Remote Sites"
        A1[Site_A/SubSite_1<br/>Disk Agent]
        A2[Site_A/SubSite_2<br/>Disk Agent]
        B1[Site_B/SubSite_3<br/>Disk Agent]
        B2[Site_B/SubSite_4<br/>Disk Agent]
    end
    
    subgraph "Central Server"
        API[Flask API<br/>Port 5100]
        DB[(SQLite DB)]
        WEB[Web Dashboard]
    end
    
    subgraph "User Access"
        BROWSER[Web Browser]
    end
    
    A1 -->|POST /api/report| API
    A2 -->|POST /api/report| API
    B1 -->|POST /api/report| API
    B2 -->|POST /api/report| API
    
    API --> DB
    DB --> WEB
    BROWSER --> WEB
    
    style API fill:#4CAF50
    style DB fill:#2196F3
    style WEB fill:#FF9800
    style BROWSER fill:#9C27B0
```

## Data Flow

```mermaid
sequenceDiagram
    participant Agent as Disk Agent<br/>(Remote Server)
    participant API as Flask API
    participant DB as SQLite Database
    participant UI as Web Dashboard
    participant User as End User

    Agent->>Agent: Execute du -sm /data
    Agent->>API: POST /api/report<br/>{site, size_mb, timestamp}
    API->>API: Validate API token
    API->>DB: Insert disk_usage record
    DB-->>API: Confirm save
    API-->>Agent: 200 OK
    
    User->>UI: Access dashboard
    UI->>API: GET /api/summary
    API->>DB: Query latest data
    DB-->>API: Return aggregated data
    API-->>UI: JSON response
    UI-->>User: Render charts & cards
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/logHive.git
cd logHive

# 2. Set up environment
cp .env.example .env
nano .env  # Edit and add your secure keys

# Generate secure keys
python3 <<EOF
import secrets
print("SECRET_KEY=" + secrets.token_hex(32))
print("API_TOKEN=" + secrets.token_urlsafe(32))
EOF

# 3. Install dependencies
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. Initialize database
python -c "from models import init_db; init_db()"

# 5. Start the server
python app.py

# The dashboard will be available at http://localhost:5100
```

### Site Configuration (`config.py`)

```python
SITES_CONFIG = {
    "Site_A": {
        "sub_sites": {
            "SubSite_1": {
                "log_server": {"name": "Log Server"},
                "backup_server": {"name": "Backup Server"}
            }
        }
    }
}
```

### Agent Deployment

Deploy agents to monitored servers:

```bash
# 1. Copy agent to remote server
scp agent/disk_agent.sh user@remote-server:/opt/disk-agent/

# 2. Configure the agent
nano /opt/disk-agent/disk_agent.sh

# Set these variables:
CENTRAL_SERVER_URL="http://your-server:5100/api/report"
API_TOKEN="your-api-token-from-.env"
SITE="Site_A"
SUB_SITE="SubSite_1"
SERVER_TYPE="log_server"

# 3. Schedule with cron (hourly)
crontab -e
# Add this line:
0 * * * * /opt/disk-agent/disk_agent.sh >> /var/log/disk-agent.log 2>&1
```

## API Endpoints

### Data Collection
```http
POST /api/report
Content-Type: application/json

{
  "token": "your-api-token",
  "site": "Site_A",
  "sub_site": "SubSite_1",
  "server_type": "log_server",
  "path": "/data",
  "size_mb": 1024.5
}
```

### Dashboard Queries
- `GET /api/summary` - All sites summary
- `GET /api/sites` - List all sites
- `GET /api/history/<site>/<sub_site>/<server_type>` - Historical data
- `GET /api/monthly/<site>/<sub_site>/<server_type>` - Monthly statistics

## Project Structure

```
logHive/
├── app.py                 # Main Flask application
├── config.py              # Configuration and site definitions
├── models.py              # Database models and queries
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── gunicorn_config.py     # Production server config
├── agent/                # Remote data collection agents
│   ├── disk_agent.sh     # Standard agent script
│   ├── disk_agent_v2.sh  # SSH tunnel version
│   └── cron_setup.md     # Cron configuration guide
├── static/               # Frontend assets
│   ├── css/              # Stylesheets
│   │   ├── style.css     # Main styles
│   │   ├── sidebar.css   # Sidebar components
│   │   └── toppanel.css  # Top navigation
│   └── js/               # JavaScript files
│       └── dashboard.js  # Dashboard logic
├── templates/            # Jinja2 templates
│   ├── dashboard.html    # Main dashboard
│   └── login.html        # Authentication page
├── data/                 # SQLite databases (gitignored)
└── logs/                 # Application logs (gitignored)
```

## Security Features

- Environment-based secrets (no hardcoded passwords)
- API token authentication for agents
- Password hashing with werkzeug security
- Session-based authentication
- Separate test/production databases
- SSH tunnel support for restricted networks
- Comprehensive `.gitignore` for sensitive data

## Production Deployment

### Using Systemd (Linux)
```bash
# 1. Create service file: /etc/systemd/system/dashboard.service
[Unit]
Description=Log Hive
After=network.target

[Service]
Type=notify
User=appuser
WorkingDirectory=/opt/dashboard
ExecStart=/opt/dashboard/start.sh
Environment="ENVIRONMENT=production"
Restart=always

[Install]
WantedBy=multi-user.target

# 2. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable dashboard
sudo systemctl start dashboard
sudo systemctl status dashboard
```

### Using Gunicorn Directly
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn -c gunicorn_config.py app:app
```

## Tech Stack

**Backend:**
- Flask 2.0+ - Web framework
- SQLite - Database
- Gunicorn - WSGI server
- APScheduler - Background tasks

**Frontend:**
- Vanilla JavaScript - No heavy frameworks
- D3.js - Data visualization
- Responsive CSS - Mobile-friendly

**DevOps:**
- Systemd - Service management
- Bash - Agent scripts
- Git - Version control

## Development

```bash
# Run in development mode
export ENVIRONMENT=test
python app.py

# Load test data
# Login with username: test, password: test123

# Run with debug mode
export FLASK_DEBUG=1
python app.py
```
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## About

This project was developed as a full-stack monitoring solution demonstrating:
- System architecture design
- RESTful API development
- Automated infrastructure monitoring
- Production deployment practices
- Security best practices
- Documentation and maintainability
