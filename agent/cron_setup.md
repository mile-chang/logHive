# Disk Monitoring Agent - Cron Setup Guide

## Overview

This guide explains how to configure cron jobs to automatically run the disk monitoring agent on remote VMs.

## Installation

```bash
scp disk_agent.sh user@vm-ip:/opt/disk-agent/
```

```bash
mkdir -p /opt/disk-agent
nano /opt/disk-agent/disk_agent.sh
```

## Configuration

Edit `/opt/disk-agent/disk_agent.sh` and modify the following variables:

```bash
CENTRAL_SERVER_URL="http://your-central-server:5100/api/report"
API_TOKEN="your-api-token-here"
SITE="Site_A"
SUB_SITE="SubSite_1"
SERVER_TYPE="log_server"
```

## Testing

```bash
chmod +x /opt/disk-agent/disk_agent.sh
```

```bash
/opt/disk-agent/disk_agent.sh
```

Should output:
```
========================================
Disk Monitoring Agent - Folder Size Tracking
========================================
Site: Site_A / SubSite_1
Server Type: log_server
Monitor Path: /data
========================================
Folder Size: 1234.56 MB
[2024-01-15 10:30:00] Report successful: 1234.56 MB
```

## Cron Configuration

### Hourly Execution (Recommended)

```bash
0 * * * * /opt/disk-agent/disk_agent.sh >> /opt/dashboard/log/disk-agent.log 2>&1
```

### Daily Execution (2 AM)

```bash
0 2 * * * /opt/disk-agent/disk_agent.sh >> /opt/dashboard/log/disk-agent.log 2>&1
```

## Log Monitoring

```bash
tail -f /opt/dashboard/log/disk-agent.log
```

## Troubleshooting

### Test Manually

```bash
sudo /opt/disk-agent/disk_agent.sh
```
