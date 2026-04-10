#!/bin/bash
# Push OpenClaw backup to GitHub (separate private repo)
# This keeps your complete soul safe in the cloud

set -e

BACKUP_DIR="$HOME/openclaw_backups"
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/openclaw_backup_*.tar.gz | head -1)
BACKUP_NAME=$(basename "$LATEST_BACKUP" .tar.gz)

echo "📦 Latest backup: $BACKUP_NAME"
echo ""

# Check if backup-github repo exists locally
if [ ! -d "$BACKUP_DIR/backup-repo" ]; then
    echo "🔧 Creating backup repository..."
    mkdir -p "$BACKUP_DIR/backup-repo"
    cd "$BACKUP_DIR/backup-repo"
    git init
    git config user.email "damjan@example.com"
    git config user.name "Damjan"
    
    # Create README
    cat > README.md << 'EOF'
# OpenClaw Complete Backups

This repository contains full backups of the OpenClaw workspace.

## What's included:
- 🧠 Workspace (SOUL.md, MEMORY.md, memories/, bots/)
- ⚙️ OpenClaw configuration
- 🔑 SSH keys
- 🖥️ Systemd services
- 🌐 Nginx configuration
- 📦 Package lists
- ⏰ Crontab

## How to restore:
1. Download the latest `.tar.gz` file
2. Extract: `tar -xzf openclaw_backup_YYYYMMDD_HHMMSS.tar.gz`
3. Run: `./restore.sh`

---
**Created by:** Dame & Jan | 2026
EOF
    
    git add README.md
    git commit -m "Initial backup repo"
    
    # Add remote (you need to create this repo on GitHub first!)
    echo ""
    echo "⚠️  IMPORTANT: Create a PRIVATE repo on GitHub first!"
    echo "   Repo name suggestion: damjanm1983-star/OpenClaw-Backups"
    echo ""
    read -p "Enter GitHub repo URL (git@github.com:USER/REPO.git): " REPO_URL
    git remote add origin "$REPO_URL"
fi

# Copy latest backup to repo
cd "$BACKUP_DIR/backup-repo"
cp "$LATEST_BACKUP" .

# Update README with latest backup info
cat > LATEST_BACKUP.txt << EOF
Latest Backup: $BACKUP_NAME
Date: $(date)
Size: $(ls -lh "$BACKUP_NAME.tar.gz" | awk '{print $5}')
EOF

# Commit and push
git add -A
git commit -m "Backup: $BACKUP_NAME"
git push origin main || git push origin master

echo ""
echo "✅ Backup pushed to GitHub!"
echo "📍 Location: $REPO_URL"
echo ""
