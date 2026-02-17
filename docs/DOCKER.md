# Docker Deployment Guide

LogHive provides full Docker support for easy deployment and operation.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## 🚀 Quick Start

### 1. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` — **you MUST change these**:
- `SECRET_KEY` - Flask secret key
- `API_TOKEN` - API authentication token
- `ADMIN_PASSWORD` - Admin password

### 2. Start with Docker Compose

```bash
docker compose up -d        # Build and start
docker compose logs -f       # View logs
docker compose down          # Stop
```

The application will be available at `http://localhost:5100`.

### 3. Manual Build (Alternative)

```bash
docker build -t loghive:latest .

docker run -d \
  --name loghive \
  -p 5100:5100 \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_PASSWORD=your-password \
  -v loghive-data:/app/data \
  -v loghive-logs:/app/logs \
  loghive:latest
```

## 📦 Container Management

```bash
docker compose ps              # Status
docker compose logs --tail=100 # Recent logs
docker compose restart         # Restart
docker compose exec loghive bash  # Enter shell
```

## 🌐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Runtime environment | `production` |
| `PORT` | Service port | `5100` |
| `SECRET_KEY` | Flask secret key | *Must change* |
| `API_TOKEN` | API auth token | *Must change* |
| `ADMIN_USERNAME` | Admin username | `admin` |
| `ADMIN_PASSWORD` | Admin password | *Must change* |
| `TEST_USERNAME` | Test username | `test` |
| `TEST_PASSWORD` | Test password | *Must change* |

### Configuration Hierarchy

```
1. docker-compose.yml environment   ← Highest priority (overrides others)
2. .env file                        ← Medium priority
3. config.py defaults               ← Lowest priority (fallback)
```

**Dockerfile ENV** — Only Python/Docker runtime variables (`PYTHONUNBUFFERED`, `PYTHONDONTWRITEBYTECODE`)
**docker-compose ENV** — Application config (reads from `.env`)
**config.py** — Default values and config logic
**.env** — Actual config values (sensitive data, gitignored)

## 💾 Data Persistence

Docker Compose creates these volumes automatically:

- `loghive-data` - Database files
- `loghive-logs` - Application logs

### Backup & Restore

```bash
# Backup
docker run --rm \
  -v loghive-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/loghive-data-backup.tar.gz -C /data .

# Restore
docker run --rm \
  -v loghive-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/loghive-data-backup.tar.gz -C /data
```

## 🔐 Security

1. **Change default passwords** - Always modify credentials in `.env`
2. **Non-root user** - Container runs as `loghive` (UID 1000)
3. **Resource limits** - CPU and memory limits configured
4. **Read-only filesystem** - Container filesystem is read-only
5. **Dropped capabilities** - All Linux capabilities dropped except required ones

### Update Passwords

```bash
docker compose exec loghive python3 update_passwords.py
```

## 🏗️ Advanced Configuration

### Custom Port
```yaml
ports:
  - "8080:5100"  # host_port:container_port
```

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1024M
```

### External Database
```yaml
volumes:
  - ./my-data:/app/data
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | `docker compose logs loghive` |
| Port conflict | `lsof -i :5100` or change `PORT` in `.env` |
| Database issues | `docker compose exec loghive python3 -c "from models import init_db; init_db()"` |
| Health check failing | `docker inspect --format='{{.State.Health.Status}}' loghive` |

## 📚 Related Links

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [LogHive GitHub](https://github.com/mile-chang/logHive)
