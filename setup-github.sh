#!/bin/bash
# Setup GitHub repository for OpenClaw migration

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  GitHub Repository Setup for OpenClaw Migration${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check SSH key
echo -e "${BLUE}🔑 Checking SSH key...${NC}"
if [ -f ~/.ssh/github_tradingbot.pub ]; then
    echo -e "${GREEN}✅ SSH key found: ~/.ssh/github_tradingbot.pub${NC}"
    echo ""
    echo "Public key:"
    cat ~/.ssh/github_tradingbot.pub
    echo ""
else
    echo -e "${YELLOW}⚠️  No github_tradingbot key found${NC}"
    echo "Checking for other keys..."
    ls -la ~/.ssh/*.pub 2>/dev/null || echo "No SSH keys found"
fi

echo ""
echo -e "${YELLOW}📋 STEPS TO PUSH TO GITHUB:${NC}"
echo ""
echo "1. ${BLUE}Create a new PRIVATE repository on GitHub:${NC}"
echo "   https://github.com/new"
echo "   - Name: openclaw-migration (or your choice)"
echo "   - Visibility: PRIVATE (important - contains sensitive data)"
echo "   - Do NOT initialize with README (we have one)"
echo ""
echo "2. ${BLUE}Add your SSH key to GitHub:${NC}"
echo "   https://github.com/settings/keys"
echo "   - Click 'New SSH key'"
echo "   - Paste your public key (shown above)"
echo "   - Title: 'Hetzner VPS' or similar"
echo ""
echo "3. ${BLUE}Add remote and push:${NC}"
echo "   cd ~/openclaw-migration"
echo "   git remote add origin git@github.com:YOUR_USERNAME/openclaw-migration.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4. ${BLUE}Verify the push:${NC}"
echo "   Check your GitHub repo in browser"
echo ""

# Offer to set remote
read -p "Do you want to set the remote now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your GitHub username: " USERNAME
    read -p "Enter repository name [openclaw-migration]: " REPO_NAME
    REPO_NAME=${REPO_NAME:-openclaw-migration}
    
    cd ~/openclaw-migration
    git remote add origin "git@github.com:$USERNAME/$REPO_NAME.git" 2>/dev/null || \
        git remote set-url origin "git@github.com:$USERNAME/$REPO_NAME.git"
    
    git branch -M main
    
    echo -e "${BLUE}🚀 Pushing to GitHub...${NC}"
    if git push -u origin main; then
        echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}"
        echo ""
        echo -e "${BLUE}Repository URL:${NC}"
        echo "https://github.com/$USERNAME/$REPO_NAME"
    else
        echo -e "${RED}❌ Push failed. Common issues:${NC}"
        echo "   - SSH key not added to GitHub"
        echo "   - Repository doesn't exist yet"
        echo "   - Wrong username/repo name"
        echo ""
        echo "Try: ssh -T git@github.com"
    fi
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
