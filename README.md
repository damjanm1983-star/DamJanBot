# 🦞 OpenClaw VPS Migration

Complete backup and migration package for moving OpenClaw to a new Hetzner VPS.

## 📦 What's Included

| File/Folder | Description |
|-------------|-------------|
| `openclaw_backup_20260416_142026.tar.gz` | Full backup archive (config, workspace, certs, etc.) |
| `restore.sh` | Automated restore script |
| `MIGRATION.md` | Step-by-step migration guide |
| `docker-compose.yml` | Optional Docker setup for quick deployment |

## 🚀 Quick Start

### 1. On New VPS

```bash
# Clone this repo
git clone https://github.com/YOUR_USERNAME/openclaw-migration.git
cd openclaw-migration

# Extract and restore
./restore.sh
```

### 2. Update IP Addresses

```bash
# Edit configs with new VPS IP
nano ~/.openclaw/openclaw.json
nano /etc/nginx/sites-available/webhook
```

### 3. Start Services

```bash
sudo systemctl start openclaw-gateway
sudo systemctl start nginx
```

## 📋 Detailed Guide

See [MIGRATION.md](./MIGRATION.md) for complete step-by-step instructions.

## 🔒 Security Notes

- This repo contains sensitive configs (auth tokens, certs)
- **Make it private** on GitHub
- Rotate auth tokens after migration
- Regenerate TLS certificates for new IP

## 📅 Backup Info

- **Created:** 2026-04-16 14:20 UTC
- **Source VPS:** 5.9.248.66
- **OpenClaw Version:** 2026.4.14
- **User:** dame

---

*Created by: Dame & Jan | 2026*
