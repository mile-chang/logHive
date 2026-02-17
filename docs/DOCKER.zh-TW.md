# Docker 部署指南

LogHive 提供完整的 Docker 支援，讓你可以輕鬆部署和運行應用。

## 📋 前置需求

- Docker Engine 20.10+
- Docker Compose 2.0+

## 🚀 快速開始

### 1. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env`，**務必修改以下設定**：
- `SECRET_KEY` - Flask 密鑰
- `API_TOKEN` - API 認證 token
- `ADMIN_PASSWORD` - 管理員密碼

### 2. 使用 Docker Compose 啟動

```bash
docker compose up -d        # 建置並啟動
docker compose logs -f       # 查看日誌
docker compose down          # 停止
```

應用將在 `http://localhost:5100` 上運行。

### 3. 手動建置（替代方式）

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

## 📦 容器管理

```bash
docker compose ps              # 狀態
docker compose logs --tail=100 # 最近日誌
docker compose restart         # 重啟
docker compose exec loghive bash  # 進入容器
```

## 🌐 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `ENVIRONMENT` | 執行環境 | `production` |
| `PORT` | 服務連接埠 | `5100` |
| `SECRET_KEY` | Flask 密鑰 | *必須修改* |
| `API_TOKEN` | API 認證 token | *必須修改* |
| `ADMIN_USERNAME` | 管理員帳號 | `admin` |
| `ADMIN_PASSWORD` | 管理員密碼 | *必須修改* |
| `TEST_USERNAME` | 測試帳號 | `test` |
| `TEST_PASSWORD` | 測試密碼 | *必須修改* |

### 設定優先順序

```
1. docker-compose.yml environment   ← 最高優先（覆蓋其他）
2. .env 檔案                        ← 中等優先
3. config.py 預設值                  ← 最低優先（備援）
```

**Dockerfile ENV** — 僅 Python/Docker 運行時變數（`PYTHONUNBUFFERED`, `PYTHONDONTWRITEBYTECODE`）
**docker-compose ENV** — 應用程式設定（從 `.env` 讀取）
**config.py** — 預設值和設定邏輯
**.env** — 實際設定值（敏感資訊，已 gitignore）

## 💾 資料持久化

Docker Compose 會自動建立以下 volumes：

- `loghive-data` - 資料庫檔案
- `loghive-logs` - 應用日誌

### 備份與還原

```bash
# 備份
docker run --rm \
  -v loghive-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/loghive-data-backup.tar.gz -C /data .

# 還原
docker run --rm \
  -v loghive-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/loghive-data-backup.tar.gz -C /data
```

## 🔐 安全性

1. **修改預設密碼** — 務必在 `.env` 中修改所有憑證
2. **非 root 使用者** — 容器以 `loghive` (UID 1000) 執行
3. **資源限制** — 已設定 CPU 和記憶體限制
4. **唯讀檔案系統** — 容器檔案系統為唯讀
5. **權限最小化** — 已移除所有不必要的 Linux capabilities

### 更新密碼

```bash
docker compose exec loghive python3 update_passwords.py
```

## 🏗️ 進階設定

### 自訂連接埠
```yaml
ports:
  - "8080:5100"  # 主機端口:容器端口
```

### 資源限制
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1024M
```

### 外部資料庫
```yaml
volumes:
  - ./my-data:/app/data
```

## 🐛 疑難排解

| 問題 | 解決方式 |
|------|---------|
| 容器無法啟動 | `docker compose logs loghive` |
| 連接埠衝突 | `lsof -i :5100` 或修改 `.env` 中的 `PORT` |
| 資料庫問題 | `docker compose exec loghive python3 -c "from models import init_db; init_db()"` |
| 健康檢查失敗 | `docker inspect --format='{{.State.Health.Status}}' loghive` |

## 📚 相關連結

- [Docker 官方文件](https://docs.docker.com/)
- [Docker Compose 文件](https://docs.docker.com/compose/)
- [LogHive GitHub](https://github.com/mile-chang/logHive)
