# AWS EC2 Deployment Guide (Ubuntu 24.04 + t3.micro)

This guide covers deploying LogHive on AWS EC2 with Docker.

## Environment Specs

- **Instance**: t3.micro (1 vCPU, 1GB RAM) — suitable for <10 concurrent users
- **OS**: Ubuntu 24.04 LTS
- **Storage**: 15GB+ recommended
- **Cost**: ~$7.50/month (on-demand)

## Security Group Settings

| Rule | Port | Source |
|------|------|--------|
| SSH | 22 | Your IP only |
| HTTP | 80 | 0.0.0.0/0 |
| HTTPS | 443 | 0.0.0.0/0 |

> **Important**: Never expose port 5100 directly to the internet!

## ⚡ Quick Deploy (Copy & Paste)

### 1. Connect and Install Docker

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

```bash
sudo apt update && sudo apt upgrade -y && \
sudo apt install -y docker.io docker-compose-v2 git curl nginx certbot python3-certbot-nginx htop && \
sudo systemctl start docker && \
sudo systemctl enable docker && \
sudo usermod -aG docker ubuntu && \
echo "✅ Installation complete! Log out and back in."
```

```bash
exit
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 2. Deploy Application

```bash
cd ~ && \
git clone https://github.com/mile-chang/logHive.git && \
cd logHive

# Auto-generate secure credentials
cp .env.example .env && \
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))") && \
API_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))") && \
sed -i "s/your-secret-key-here-change-me/$SECRET_KEY/" .env && \
sed -i "s/your-api-token-here-change-me/$API_TOKEN/" .env && \
ADMIN_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))") && \
sed -i "s/change-me-in-production/$ADMIN_PASS/" .env && \
echo "✅ Credentials configured"

docker compose up -d && \
sleep 5 && curl -I http://localhost:5100
```

### 3. Nginx Reverse Proxy

```bash
sudo tee /etc/nginx/sites-available/loghive > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:5100/static/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/loghive /etc/nginx/sites-enabled/ && \
sudo rm -f /etc/nginx/sites-enabled/default && \
sudo nginx -t && sudo systemctl reload nginx && sudo systemctl enable nginx
```

### 4. Firewall

```bash
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && \
sudo ufw --force enable
```

### 5. HTTPS (Optional — requires domain)

```bash
sudo certbot --nginx -d yourdomain.com
```

### 6. Enable Swap (Recommended)

```bash
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && \
sudo mkswap /swapfile && sudo swapon /swapfile && \
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab && \
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
```

## ✅ Verify Deployment

```bash
docker ps                        # Container running
curl http://localhost:5100       # App responding
sudo systemctl status nginx      # Nginx running
sudo ufw status                  # Firewall active
```

Access: `http://your-ec2-ip`
Login: username `admin`, password from `~/logHive/.env`

## 🔐 Security Hardening

### Fail2Ban (Brute-force Protection)
```bash
sudo apt install -y fail2ban && \
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local && \
sudo systemctl enable fail2ban && sudo systemctl start fail2ban
```

### Automatic Security Updates
```bash
sudo apt install -y unattended-upgrades && \
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 💾 Automatic Backups

```bash
mkdir -p ~/scripts && \
cat > ~/scripts/backup-loghive.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker run --rm -v loghive_loghive-data:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/loghive-data-$DATE.tar.gz -C /data .
cp ~/logHive/.env $BACKUP_DIR/.env-$DATE
find $BACKUP_DIR -name "loghive-data-*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name ".env-*" -mtime +7 -delete
echo "[$(date)] Backup completed: loghive-data-$DATE.tar.gz"
EOF

chmod +x ~/scripts/backup-loghive.sh && \
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/scripts/backup-loghive.sh >> /home/ubuntu/backup.log 2>&1") | crontab -
```

## 📱 Common Commands

```bash
cd ~/logHive
docker compose logs -f           # View logs
docker compose restart           # Restart
docker compose down              # Stop
docker compose up -d             # Start
docker compose up -d --build     # Rebuild and start
git pull && docker compose up -d --build  # Update
~/scripts/backup-loghive.sh      # Manual backup
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | `docker compose logs` |
| Out of memory | Enable swap (see above), `free -h` |
| Nginx 502 | `docker ps` then `sudo systemctl restart nginx` |
| Disk full | `docker system prune -a --volumes` |
| Can't connect | Check security group & `sudo ufw status` |

## Emergency Recovery

```bash
# Restore from backup
cd ~/logHive && docker compose down
docker run --rm -v loghive_loghive-data:/data -v ~/backups:/backup \
  alpine tar xzf /backup/loghive-data-YYYYMMDD_HHMMSS.tar.gz -C /data
docker compose up -d

# Full reset (last resort)
docker compose down -v && docker compose up -d
```
