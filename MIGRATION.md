# 🦞 OpenClaw VPS Migration Guide

Complete guide for migrating OpenClaw from old VPS (5.9.248.66) to new Hetzner VPS.

---

## 📋 Pre-Migration Checklist

- [ ] Current VPS is backed up ✓
- [ ] New Hetzner VPS provisioned
- [ ] SSH access to new VPS working
- [ ] GitHub repo cloned/downloaded to new VPS

---

## 🚀 Step-by-Step Migration

### Step 1: Provision New Hetzner VPS

1. Log into [Hetzner Cloud Console](https://console.hetzner.cloud/)
2. Create new server:
   - **Location:** Your preferred location
   - **Image:** Ubuntu 22.04 LTS (or match old VPS)
   - **Type:** CX21 or higher (2 vCPU, 4 GB RAM minimum)
   - **SSH Key:** Add your SSH key
3. Note the new IP address: `NEW_VPS_IP`

### Step 2: Initial Server Setup

```bash
# SSH into new VPS as root
ssh root@NEW_VPS_IP

# Update system
apt update && apt upgrade -y

# Create user 'dame' (must match old setup)
adduser dame
usermod -aG sudo dame

# Set up SSH for dame
mkdir -p /home/dame/.ssh
cp ~/.ssh/authorized_keys /home/dame/.ssh/
chown -R dame:dame /home/dame/.ssh
chmod 700 /home/dame/.ssh
chmod 600 /home/dame/.ssh/authorized_keys

# Install dependencies
apt install -y curl git nginx python3 python3-pip python3-venv nodejs npm

# Exit and re-login as dame
exit
ssh dame@NEW_VPS_IP
```

### Step 3: Install OpenClaw

```bash
# Install OpenClaw (same version as old VPS)
npm install -g openclaw@2026.4.14

# Verify installation
openclaw --version
# Should show: OpenClaw 2026.4.14
```

### Step 4: Clone Migration Repo

```bash
# On new VPS, as user 'dame'
cd ~

# Clone this repo (make sure you have access)
git clone https://github.com/YOUR_USERNAME/openclaw-migration.git
cd openclaw-migration

# Or if you downloaded the tarball:
# scp openclaw_backup_*.tar.gz dame@NEW_VPS_IP:~/
```

### Step 5: Run Restore Script

```bash
cd ~/openclaw-migration

# Extract backup
tar -xzf openclaw_backup_20260416_142026.tar.gz

# Run restore
./restore.sh
```

The restore script will:
- ✅ Restore workspace (SOUL.md, MEMORY.md, bots, skills)
- ✅ Restore OpenClaw configuration
- ✅ Restore SSH keys
- ✅ Restore systemd services
- ✅ Restore nginx configuration
- ✅ Restore crontab

### Step 6: Update IP Addresses (CRITICAL!)

Your backup contains the **old IP (5.9.248.66)**. You MUST update these:

#### 6.1 Update OpenClaw Config

```bash
nano ~/.openclaw/openclaw.json
```

Find and replace all instances of `5.9.248.66` with `NEW_VPS_IP`:

```json
{
  "gateway": {
    "controlUi": {
      "allowedOrigins": [
        "http://NEW_VPS_IP",
        "https://NEW_VPS_IP", 
        "http://NEW_VPS_IP:18789",
        "https://NEW_VPS_IP:18789",
        "http://127.0.0.1",
        "https://127.0.0.1"
      ]
    }
  }
}
```

#### 6.2 Update Nginx Config

```bash
sudo nano /etc/nginx/sites-available/webhook
```

Change:
```nginx
server_name 5.9.248.66;
# TO:
server_name NEW_VPS_IP;
```

If you have dashboard config:
```bash
sudo nano /etc/nginx/sites-available/dashboard
# Update server_name here too
```

#### 6.3 Regenerate TLS Certificates

```bash
cd ~/.openclaw/certs
rm openclaw.crt openclaw.key

# Generate new certs for new IP
openssl req -x509 -newkey rsa:2048 \
  -keyout openclaw.key \
  -out openclaw.crt \
  -days 365 \
  -nodes \
  -subj "/CN=NEW_VPS_IP" \
  -addext "subjectAltName=IP:NEW_VPS_IP,IP:127.0.0.1"

# Fix permissions
chmod 600 openclaw.key
chmod 644 openclaw.crt
```

#### 6.4 Update Trading Bot Configs (if applicable)

```bash
# Check for hardcoded IPs in trading bot
grep -r "5.9.248.66" ~/.openclaw/workspace/trading_bot/

# Update any found files
nano ~/.openclaw/workspace/trading_bot/webhook_handler.py
# etc.
```

### Step 7: Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start OpenClaw Gateway
sudo systemctl enable openclaw-gateway
sudo systemctl start openclaw-gateway

# Start Nginx
sudo systemctl restart nginx

# Start trading bot (if you have it)
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

### Step 8: Verify Everything Works

```bash
# Check OpenClaw status
openclaw status

# Check services
sudo systemctl status openclaw-gateway
sudo systemctl status nginx
sudo systemctl status trading-bot

# Test dashboard
curl http://NEW_VPS_IP:18789/

# Test webhook endpoint
curl -X POST http://NEW_VPS_IP/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### Step 9: Update TradingView Webhook URL

Go to TradingView → Alerts → Edit your alert:

```
# OLD URL:
http://5.9.248.66/webhook

# NEW URL:
http://NEW_VPS_IP/webhook
```

### Step 10: Update DNS (If Using Domain)

If you have a domain pointing to the old IP:

1. Go to your DNS provider
2. Update A record from `5.9.248.66` to `NEW_VPS_IP`
3. Wait for propagation (5-60 minutes)
4. Test: `nslookup yourdomain.com`

---

## 🔒 Security Hardening (Recommended)

### 1. Change Auth Token

Generate new auth token:

```bash
# Generate new token
NEW_TOKEN=$(openssl rand -hex 24)
echo "New token: $NEW_TOKEN"

# Update openclaw.json
nano ~/.openclaw/openclaw.json
# Change: "token": "..." to "token": "$NEW_TOKEN"

# Restart
sudo systemctl restart openclaw-gateway
```

### 2. Configure Firewall

```bash
# Install UFW
sudo apt install ufw

# Allow necessary ports
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 18789/tcp   # OpenClaw Gateway

# Enable firewall
sudo ufw enable
```

### 3. Set Up Fail2Ban

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 🧪 Testing Checklist

- [ ] OpenClaw dashboard loads: `http://NEW_VPS_IP:18789/`
- [ ] Gateway is running: `openclaw status`
- [ ] Nginx is serving: `curl http://NEW_VPS_IP/`
- [ ] Webhook receives alerts: Test from TradingView
- [ ] Trading bot processes signals: Check logs
- [ ] Memory/personality intact: Chat with Claw
- [ ] SSH keys work: `ssh -T git@github.com`

---

## 🆘 Troubleshooting

### OpenClaw Won't Start

```bash
# Check logs
openclaw logs --follow

# Check config syntax
cat ~/.openclaw/openclaw.json | python3 -m json.tool

# Reset and reconfigure
openclaw config reset
openclaw onboard
```

### Nginx Errors

```bash
# Test config
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Restart
sudo systemctl restart nginx
```

### Webhook Not Receiving

```bash
# Check nginx is listening on webhook path
sudo nginx -T | grep -A 10 webhook

# Test locally
curl -X POST http://localhost:8080/webhook -d '{"test": true}'

# Check firewall
sudo ufw status
```

### Trading Bot Issues

```bash
# Check logs
sudo journalctl -u trading-bot -f

# Check Python environment
cd ~/.openclaw/workspace/trading_bot
source venv/bin/activate
pip list | grep -E "flask|requests|binance"
```

---

## 📞 Post-Migration

### 1. Update This Repo

After successful migration, update the repo with new IP:

```bash
cd ~/openclaw-migration

# Update README with new IP
sed -i 's/5.9.248.66/NEW_VPS_IP/g' README.md

# Commit and push
git add .
git commit -m "Migration complete - updated to NEW_VPS_IP"
git push
```

### 2. Clean Up Old VPS

Only after confirming everything works:

```bash
# On old VPS - create final backup
./backup_openclaw.sh

# Download backup
scp dame@5.9.248.66:~/openclaw_backups/*.tar.gz ./

# Then destroy old VPS in Hetzner Console
```

### 3. Document New Setup

Update `MEMORY.md` with new VPS details:

```bash
nano ~/.openclaw/workspace/MEMORY.md
# Add: Migrated to new VPS on 2026-04-XX
# New IP: NEW_VPS_IP
```

---

## 📁 Backup Contents Reference

Your backup contains:

```
openclaw_backup_20260416_142026/
├── workspace/              # SOUL.md, MEMORY.md, trading_bot/, skills/
├── openclaw_config/        # openclaw.json, state.json
├── ssh/                    # SSH keys and config
├── systemd/                # Service files
├── nginx/                  # Nginx site configs
├── packages/               # pip and dpkg package lists
├── crontab.txt             # Cron jobs
├── restore.sh              # Automated restore script
└── BACKUP_INFO.txt         # Backup metadata
```

---

*Migration guide created: 2026-04-16*
*Source: 5.9.248.66 → Destination: YOUR_NEW_VPS_IP*
