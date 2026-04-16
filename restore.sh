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
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Find the backup folder
BACKUP_FOLDER=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "openclaw_backup_*" | head -1)

if [ -z "$BACKUP_FOLDER" ]; then
    echo -e "${RED}❌ No backup folder found!${NC}"
    echo "Expected: openclaw_backup_YYYYMMDD_HHMMSS"
    exit 1
fi

echo -e "${BLUE}📦 Found backup: $(basename "$BACKUP_FOLDER")${NC}"
echo ""

# 1. Restore workspace
echo -e "${BLUE}🧠 Restoring workspace...${NC}"
mkdir -p "$WORKSPACE_DIR"
if [ -d "${BACKUP_FOLDER}/workspace" ]; then
    cp -r "${BACKUP_FOLDER}/workspace/"* "$WORKSPACE_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✅ Workspace restored${NC}"
else
    echo -e "${YELLOW}⚠️  No workspace folder found in backup${NC}"
fi

# 2. Restore OpenClaw config
echo -e "${BLUE}⚙️  Restoring OpenClaw configuration...${NC}"
mkdir -p ~/.openclaw
if [ -d "${BACKUP_FOLDER}/openclaw_config" ]; then
    cp "${BACKUP_FOLDER}/openclaw_config/"* ~/.openclaw/ 2>/dev/null || true
    echo -e "${GREEN}✅ OpenClaw config restored${NC}"
else
    echo -e "${YELLOW}⚠️  No openclaw_config folder found${NC}"
fi

# 3. Restore TLS certificates
echo -e "${BLUE}🔐 Restoring TLS certificates...${NC}"
mkdir -p ~/.openclaw/certs
if [ -d "${BACKUP_FOLDER}/certs" ]; then
    cp "${BACKUP_FOLDER}/certs/"* ~/.openclaw/certs/ 2>/dev/null || true
    chmod 600 ~/.openclaw/certs/*.key 2>/dev/null || true
    chmod 644 ~/.openclaw/certs/*.crt 2>/dev/null || true
    echo -e "${GREEN}✅ Certificates restored${NC}"
else
    echo -e "${YELLOW}⚠️  No certs folder found (will need to regenerate)${NC}"
fi

# 4. Restore agents
echo -e "${BLUE}🤖 Restoring agents...${NC}"
if [ -d "${BACKUP_FOLDER}/agents" ]; then
    cp -r "${BACKUP_FOLDER}/agents/"* ~/.openclaw/ 2>/dev/null || true
    echo -e "${GREEN}✅ Agents restored${NC}"
fi

# 5. Restore memory/flows/tasks/devices
echo -e "${BLUE}💾 Restoring additional data...${NC}"
for folder in memory flows tasks devices; do
    if [ -d "${BACKUP_FOLDER}/$folder" ]; then
        cp -r "${BACKUP_FOLDER}/$folder" ~/.openclaw/ 2>/dev/null || true
        echo -e "${GREEN}✅ $folder restored${NC}"
    fi
done

# 6. Restore SSH keys
echo -e "${BLUE}🔑 Restoring SSH keys...${NC}"
mkdir -p ~/.ssh
chmod 700 ~/.ssh
if [ -d "${BACKUP_FOLDER}/ssh" ]; then
    cp "${BACKUP_FOLDER}/ssh/"* ~/.ssh/ 2>/dev/null || true
    chmod 600 ~/.ssh/* 2>/dev/null || true
    chmod 644 ~/.ssh/*.pub 2>/dev/null || true
    chmod 644 ~/.ssh/config 2>/dev/null || true
    chmod 644 ~/.ssh/known_hosts 2>/dev/null || true
    echo -e "${GREEN}✅ SSH keys restored${NC}"
else
    echo -e "${YELLOW}⚠️  No SSH keys in backup${NC}"
fi

# 7. Restore systemd services
echo -e "${BLUE}🖥️  Restoring systemd services...${NC}"
if [ -d "${BACKUP_FOLDER}/systemd" ]; then
    for service in "${BACKUP_FOLDER}/systemd/"*.service; do
        if [ -f "$service" ]; then
            sudo cp "$service" /etc/systemd/system/
            echo -e "${GREEN}✅ $(basename "$service") restored${NC}"
        fi
    done
    sudo systemctl daemon-reload
else
    echo -e "${YELLOW}⚠️  No systemd services in backup${NC}"
fi

# 8. Restore nginx config
echo -e "${BLUE}🌐 Restoring nginx configuration...${NC}"
if [ -d "${BACKUP_FOLDER}/nginx" ]; then
    for conf in "${BACKUP_FOLDER}/nginx/"*; do
        if [ -f "$conf" ]; then
            sudo cp "$conf" /etc/nginx/sites-available/
            sudo ln -sf "/etc/nginx/sites-available/$(basename "$conf")" /etc/nginx/sites-enabled/ 2>/dev/null || true
            echo -e "${GREEN}✅ $(basename "$conf") restored${NC}"
        fi
    done
    
    # Test nginx config
    if sudo nginx -t; then
        echo -e "${GREEN}✅ Nginx config valid${NC}"
    else
        echo -e "${RED}❌ Nginx config has errors - please fix${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No nginx configs in backup${NC}"
fi

# 9. Restore crontab
echo -e "${BLUE}⏰ Restoring crontab...${NC}"
if [ -f "${BACKUP_FOLDER}/crontab.txt" ]; then
    crontab "${BACKUP_FOLDER}/crontab.txt"
    echo -e "${GREEN}✅ Crontab restored${NC}"
else
    echo -e "${YELLOW}⚠️  No crontab in backup${NC}"
fi

# 10. Setup Python virtual environment for trading bot
echo -e "${BLUE}🐍 Setting up Python virtual environment...${NC}"
if [ -d "$WORKSPACE_DIR/trading_bot" ]; then
    cd "$WORKSPACE_DIR/trading_bot"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    fi
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install flask requests python-binance 2>/dev/null || true
    
    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🎉 RESTORE COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT NEXT STEPS:${NC}"
echo ""
echo "1. ${BLUE}Update IP addresses in configs:${NC}"
echo "   nano ~/.openclaw/openclaw.json"
echo "   sudo nano /etc/nginx/sites-available/webhook"
echo ""
echo "2. ${BLUE}Regenerate TLS certificates:${NC}"
echo "   cd ~/.openclaw/certs"
echo "   rm openclaw.crt openclaw.key"
echo "   openssl req -x509 -newkey rsa:2048 -keyout openclaw.key -out openclaw.crt -days 365 -nodes \\"
echo "     -subj \"/CN=YOUR_NEW_IP\" -addext \"subjectAltName=IP:YOUR_NEW_IP,IP:127.0.0.1\""
echo ""
echo "3. ${BLUE}Start services:${NC}"
echo "   sudo systemctl start openclaw-gateway"
echo "   sudo systemctl start nginx"
echo "   sudo systemctl start trading-bot"
echo ""
echo "4. ${BLUE}Verify everything works:${NC}"
echo "   openclaw status"
echo "   curl http://YOUR_NEW_IP:18789/"
echo ""
echo "5. ${BLUE}Update TradingView webhook URL to new IP${NC}"
echo ""
echo -e "${BLUE}See MIGRATION.md for full details${NC}"
echo ""
