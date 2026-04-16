# 🦞 OpenClaw VPS Migration

Complete backup and migration package for moving OpenClaw to a new Hetzner VPS.

## 📦 What's Included

| File/Folder | Description |
|-------------|-------------|
| `openclaw_backup_20260416_142026.tar.gz` | Full backup archive (config, workspace, certs, etc.) |
| `restore.sh` | Automated restore script |
| `MIGRATION.md` | Complete step-by-step migration guide |
| `PUSH_TO_GITHUB.md` | GitHub setup and push instructions |
| `setup-github.sh` | Interactive GitHub setup helper |

## 🚀 Quick Start

### 1. On New VPS

```bash
# Clone this repo
git clone git@github.com:YOUR_USERNAME/openclaw-migration.git
cd openclaw-migration

# Extract and restore
./restore.sh
```

### 2. Update IP Addresses

```bash
# Edit configs with new VPS IP
nano ~/.openclaw/openclaw.json
sudo nano /etc/nginx/sites-available/webhook
```

### 3. Start Services

```bash
sudo systemctl start openclaw-gateway
sudo systemctl start nginx
sudo systemctl start trading-bot
```

## 📋 Documentation

- **[MIGRATION.md](./MIGRATION.md)** - Complete migration guide with all steps
- **[PUSH_TO_GITHUB.md](./PUSH_TO_GITHUB.md)** - How to push this to your own GitHub

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
- **Git Commits:** 3 (initial backup, GitHub helper, push instructions)

## 🗂️ Repository Structure

```
openclaw-migration/
├── openclaw_backup_20260416_142026.tar.gz  # 316 MB backup
├── restore.sh                              # Automated restore
├── MIGRATION.md                            # Full migration guide
├── PUSH_TO_GITHUB.md                       # GitHub push guide
├── setup-github.sh                         # Interactive helper
├── README.md                               # This file
├── .gitignore                              # Excludes sensitive files
└── .gitattributes                          # Binary file handling
```

## 🔄 Migration Checklist

- [ ] Backup created ✓
- [ ] Git repository initialized ✓
- [ ] Push to GitHub ← You are here
- [ ] Provision new Hetzner VPS
- [ ] Clone repo on new VPS
- [ ] Run restore.sh
- [ ] Update IP addresses
- [ ] Regenerate TLS certificates
- [ ] Start services
- [ ] Update TradingView webhook URL
- [ ] Test everything
- [ ] Destroy old VPS

---

*Created by: Dame & Jan | 2026*
