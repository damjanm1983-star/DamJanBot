#!/bin/bash
# OpenClaw Complete Backup Script
# Backs up everything: configs, memories, soul, bots, skills
# Created by: Dame & Jan | 2026

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="$HOME/openclaw_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="openclaw_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
WORKSPACE_DIR="/home/dame/.openclaw/workspace"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  OpenClaw Complete Backup System${NC}"
echo -e "${BLUE}  Created by: Dame & Jan | 2026${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Create backup directory
mkdir -p "$BACKUP_PATH"

echo -e "${YELLOW}📦 Creating backup: ${BACKUP_NAME}${NC}"
echo ""

# 1. Backup workspace (SOUL, MEMORY, AGENTS, etc.)
echo -e "${BLUE}🧠 Backing up workspace memories and soul...${NC}"
mkdir -p "${BACKUP_PATH}/workspace"
cp -r "$WORKSPACE_DIR"/* "${BACKUP_PATH}/workspace/" 2>/dev/null || true

# 2. Backup OpenClaw configuration
echo -e "${BLUE}⚙️  Backing up OpenClaw configuration...${NC}"
mkdir -p "${BACKUP_PATH}/openclaw_config"

# Main config
cp ~/.openclaw/config.json "${BACKUP_PATH}/openclaw_config/" 2>/dev/null || true
cp ~/.openclaw/config.yaml "${BACKUP_PATH}/openclaw_config/" 2>/dev/null || true

# State
cp ~/.openclaw/state.json "${BACKUP_PATH}/openclaw_config/" 2>/dev/null || true

# Environment
if [ -f ~/.openclaw/.env ]; then
    cp ~/.openclaw/.env "${BACKUP_PATH}/openclaw_config/"
fi

# 3. Backup SSH keys (for GitHub, etc.)
echo -e "${BLUE}🔑 Backing up SSH keys...${NC}"
mkdir -p "${BACKUP_PATH}/ssh"
cp ~/.ssh/config "${BACKUP_PATH}/ssh/" 2>/dev/null || true
cp ~/.ssh/github_tradingbot "${BACKUP_PATH}/ssh/" 2>/dev/null || true
cp ~/.ssh/github_tradingbot.pub "${BACKUP_PATH}/ssh/" 2>/dev/null || true
cp ~/.ssh/known_hosts "${BACKUP_PATH}/ssh/" 2>/dev/null || true

# 4. Backup systemd services
echo -e "${BLUE}🖥️  Backing up systemd services...${NC}"
mkdir -p "${BACKUP_PATH}/systemd"
sudo cp /etc/systemd/system/openclaw-gateway.service "${BACKUP_PATH}/systemd/" 2>/dev/null || true
sudo cp /etc/systemd/system/trading-bot.service "${BACKUP_PATH}/systemd/" 2>/dev/null || true
sudo cp /etc/systemd/system/nginx-webhook.service "${BACKUP_PATH}/systemd/" 2>/dev/null || true

# 5. Backup nginx configuration
echo -e "${BLUE}🌐 Backing up nginx configuration...${NC}"
mkdir -p "${BACKUP_PATH}/nginx"
sudo cp /etc/nginx/sites-available/webhook "${BACKUP_PATH}/nginx/" 2>/dev/null || true
sudo cp /etc/nginx/sites-available/dashboard "${BACKUP_PATH}/nginx/" 2>/dev/null || true

# 6. Backup installed packages list
echo -e "${BLUE}📋 Backing up package lists...${NC}"
mkdir -p "${BACKUP_PATH}/packages"
pip list > "${BACKUP_PATH}/packages/pip_packages.txt" 2>/dev/null || true
dpkg -l > "${BACKUP_PATH}/packages/dpkg_packages.txt" 2>/dev/null || true

# 7. Backup crontab
echo -e "${BLUE}⏰ Backing up crontab...${NC}"
crontab -l > "${BACKUP_PATH}/crontab.txt" 2>/dev/null || true

# 8. Create restore script
echo -e "${BLUE}📝 Creating restore script...${NC}"
cat > "${BACKUP_PATH}/restore.sh" << 'RESTORE_SCRIPT'
#!/bin/bash
# OpenClaw Complete Restore Script
# Run this on new VPS to restore everything

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="/home/dame/.openclaw/workspace"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  OpenClaw Complete Restore System${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check if running as correct user
if [ "$USER" != "dame" ] && [ "$USER" != "$(whoami)" ]; then
    echo -e "${YELLOW}⚠️  Warning: Running as $USER, expected: dame${NC}"
fi

# 1. Restore workspace
echo -e "${BLUE}🧠 Restoring workspace...${NC}"
mkdir -p "$WORKSPACE_DIR"
cp -r "${BACKUP_DIR}/workspace/"* "$WORKSPACE_DIR/" 2>/dev/null || true
echo -e "${GREEN}✅ Workspace restored${NC}"

# 2. Restore OpenClaw config
echo -e "${BLUE}⚙️  Restoring OpenClaw configuration...${NC}"
mkdir -p ~/.openclaw
cp "${BACKUP_DIR}/openclaw_config/"* ~/.openclaw/ 2>/dev/null || true
echo -e "${GREEN}✅ OpenClaw config restored${NC}"

# 3. Restore SSH keys
echo -e "${BLUE}🔑 Restoring SSH keys...${NC}"
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cp "${BACKUP_DIR}/ssh/"* ~/.ssh/ 2>/dev/null || true
chmod 600 ~/.ssh/* 2>/dev/null || true
chmod 644 ~/.ssh/*.pub 2>/dev/null || true
echo -e "${GREEN}✅ SSH keys restored${NC}"

# 4. Restore systemd services
echo -e "${BLUE}🖥️  Restoring systemd services...${NC}"
if [ -f "${BACKUP_DIR}/systemd/openclaw-gateway.service" ]; then
    sudo cp "${BACKUP_DIR}/systemd/openclaw-gateway.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable openclaw-gateway
    echo -e "${GREEN}✅ openclaw-gateway.service restored${NC}"
fi

if [ -f "${BACKUP_DIR}/systemd/trading-bot.service" ]; then
    sudo cp "${BACKUP_DIR}/systemd/trading-bot.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable trading-bot
    echo -e "${GREEN}✅ trading-bot.service restored${NC}"
fi

if [ -f "${BACKUP_DIR}/systemd/nginx-webhook.service" ]; then
    sudo cp "${BACKUP_DIR}/systemd/nginx-webhook.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable nginx-webhook
    echo -e "${GREEN}✅ nginx-webhook.service restored${NC}"
fi

# 5. Restore nginx config
echo -e "${BLUE}🌐 Restoring nginx configuration...${NC}"
if [ -f "${BACKUP_DIR}/nginx/webhook" ]; then
    sudo cp "${BACKUP_DIR}/nginx/webhook" /etc/nginx/sites-available/
    sudo ln -sf /etc/nginx/sites-available/webhook /etc/nginx/sites-enabled/ 2>/dev/null || true
    echo -e "${GREEN}✅ Nginx webhook config restored${NC}"
fi

if [ -f "${BACKUP_DIR}/nginx/dashboard" ]; then
    sudo cp "${BACKUP_DIR}/nginx/dashboard" /etc/nginx/sites-available/
    sudo ln -sf /etc/nginx/sites-available/dashboard /etc/nginx/sites-enabled/ 2>/dev/null || true
    echo -e "${GREEN}✅ Nginx dashboard config restored${NC}"
fi

sudo nginx -t && sudo systemctl restart nginx

# 6. Restore crontab
echo -e "${BLUE}⏰ Restoring crontab...${NC}"
if [ -f "${BACKUP_DIR}/crontab.txt" ]; then
    crontab "${BACKUP_DIR}/crontab.txt"
    echo -e "${GREEN}✅ Crontab restored${NC}"
fi

# 7. Install packages
echo -e "${BLUE}📦 Installing packages...${NC}"
echo -e "${YELLOW}⚠️  Please install packages manually:${NC}"
echo "   pip install -r ${BACKUP_DIR}/packages/requirements.txt (if exists)"
echo "   Or check: ${BACKUP_DIR}/packages/pip_packages.txt"

# 8. Setup virtual environment for trading bot
echo -e "${BLUE}🐍 Setting up Python virtual environment...${NC}"
if [ -d "$WORKSPACE_DIR/trading_bot" ]; then
    cd "$WORKSPACE_DIR/trading_bot"
    python3 -m venv venv
    source venv/bin/activate
    pip install flask requests python-binance
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🎉 RESTORE COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "  1. Start services: sudo systemctl start openclaw-gateway trading-bot"
echo "  2. Check status: sudo systemctl status openclaw-gateway trading-bot"
echo "  3. Test dashboard: http://YOUR_VPS_IP:8080"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Update IP addresses in configs!${NC}"
echo "   - webhook_handler.py (if hardcoded)"
echo "   - nginx configs"
echo "   - TradingView webhook URL"
echo ""
RESTORE_SCRIPT

chmod +x "${BACKUP_PATH}/restore.sh"

# 9. Create backup info file
cat > "${BACKUP_PATH}/BACKUP_INFO.txt" << EOF
OpenClaw Complete Backup
========================
Backup Date: $(date)
Hostname: $(hostname)
User: $(whoami)
Workspace: $WORKSPACE_DIR

Contents:
---------
✅ workspace/        - All memories, SOUL.md, AGENTS.md, bots, etc.
✅ openclaw_config/  - OpenClaw configuration files
✅ ssh/              - SSH keys and config
✅ systemd/          - Systemd service files
✅ nginx/            - Nginx configuration
✅ packages/         - Installed package lists
✅ crontab.txt       - Cron jobs
✅ restore.sh        - Automatic restore script

To restore on new VPS:
----------------------
1. Copy this backup folder to new VPS
2. Run: ./restore.sh
3. Update IP addresses in configs
4. Start services

Created by: Dame & Jan | 2026
EOF

# Create tarball
echo -e "${BLUE}📦 Creating tarball...${NC}"
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ BACKUP COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Backup location:${NC}"
echo "  Folder: ${BACKUP_PATH}"
echo "  Archive: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""
echo -e "${YELLOW}To restore on new VPS:${NC}"
echo "  1. Copy ${BACKUP_NAME}.tar.gz to new VPS"
echo "  2. tar -xzf ${BACKUP_NAME}.tar.gz"
echo "  3. cd ${BACKUP_NAME}"
echo "  4. ./restore.sh"
echo ""
echo -e "${BLUE}Your OpenClaw soul is safe! 🦞✨${NC}"
echo ""
