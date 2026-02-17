# AWS EC2 部署指南 (Ubuntu 24.04 + t3.micro)

本指南涵蓋在 AWS EC2 上使用 Docker 部署 LogHive。

## 環境規格

- **實例**: t3.micro (1 vCPU, 1GB RAM) — 適合 <10 個同時使用者
- **作業系統**: Ubuntu 24.04 LTS
- **儲存空間**: 建議 15GB 以上
- **費用**: 約 $7.50/月（隨需計費）

## 安全群組設定

| 規則 | 連接埠 | 來源 |
|------|--------|------|
| SSH | 22 | 僅你的 IP |
| HTTP | 80 | 0.0.0.0/0 |
| HTTPS | 443 | 0.0.0.0/0 |

> **重要**: 不要將 5100 連接埠直接暴露到網路！

## ⚡ 快速部署（複製貼上）

### 1. 連接並安裝 Docker

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

```bash
sudo apt update && sudo apt upgrade -y && \
sudo apt install -y docker.io docker-compose-v2 git curl nginx certbot python3-certbot-nginx htop && \
sudo systemctl start docker && \
sudo systemctl enable docker && \
sudo usermod -aG docker ubuntu && \
echo "✅ 安裝完成！請登出後重新登入。"
```

```bash
exit
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 2. 部署應用

```bash
cd ~ && \
git clone https://github.com/mile-chang/logHive.git && \
cd logHive

# 自動產生安全憑證
cp .env.example .env && \
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))") && \
API_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))") && \
sed -i "s/your-secret-key-here-change-me/$SECRET_KEY/" .env && \
sed -i "s/your-api-token-here-change-me/$API_TOKEN/" .env && \
ADMIN_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))") && \
sed -i "s/change-me-in-production/$ADMIN_PASS/" .env && \
echo "✅ 憑證已設定"

docker compose up -d && \
sleep 5 && curl -I http://localhost:5100
```

### 3. Nginx 反向代理

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

### 4. 防火牆

```bash
sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && \
sudo ufw --force enable
```

### 5. HTTPS（可選 — 需要網域）

```bash
sudo certbot --nginx -d yourdomain.com
```

### 6. 啟用 Swap（建議）

```bash
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && \
sudo mkswap /swapfile && sudo swapon /swapfile && \
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab && \
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
```

## ✅ 驗證部署

```bash
docker ps                        # 容器執行中
curl http://localhost:5100       # 應用回應正常
sudo systemctl status nginx      # Nginx 執行中
sudo ufw status                  # 防火牆啟用
```

存取: `http://your-ec2-ip`
登入: 帳號 `admin`，密碼見 `~/logHive/.env`

## 🔐 安全強化

### Fail2Ban（暴力破解防護）
```bash
sudo apt install -y fail2ban && \
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local && \
sudo systemctl enable fail2ban && sudo systemctl start fail2ban
```

### 自動安全更新
```bash
sudo apt install -y unattended-upgrades && \
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 💾 自動備份

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
echo "[$(date)] 備份完成: loghive-data-$DATE.tar.gz"
EOF

chmod +x ~/scripts/backup-loghive.sh && \
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/scripts/backup-loghive.sh >> /home/ubuntu/backup.log 2>&1") | crontab -
```

## 📱 常用指令

```bash
cd ~/logHive
docker compose logs -f           # 查看日誌
docker compose restart           # 重啟
docker compose down              # 停止
docker compose up -d             # 啟動
docker compose up -d --build     # 重建並啟動
git pull && docker compose up -d --build  # 更新
~/scripts/backup-loghive.sh      # 手動備份
```

## 🐛 疑難排解

| 問題 | 解決方式 |
|------|---------|
| 容器無法啟動 | `docker compose logs` |
| 記憶體不足 | 啟用 swap（見上方），`free -h` |
| Nginx 502 | `docker ps` 後 `sudo systemctl restart nginx` |
| 磁碟已滿 | `docker system prune -a --volumes` |
| 無法連線 | 檢查安全群組 & `sudo ufw status` |

## 緊急復原

```bash
# 從備份還原
cd ~/logHive && docker compose down
docker run --rm -v loghive_loghive-data:/data -v ~/backups:/backup \
  alpine tar xzf /backup/loghive-data-YYYYMMDD_HHMMSS.tar.gz -C /data
docker compose up -d

# 完全重設（最後手段）
docker compose down -v && docker compose up -d
```
