# Push to GitHub - Quick Steps

## Your SSH Key (Already Generated)

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN7WAMOuiyLxLZ8Mkw6VV0L7WPfA0psXjv/CczWVXmyt trading-bot@vps
```

## Step 1: Add SSH Key to GitHub

1. Go to: https://github.com/settings/keys
2. Click **"New SSH key"**
3. Title: `Hetzner VPS`
4. Key type: `Authentication Key`
5. Paste the key above
6. Click **"Add SSH key"**

## Step 2: Create Private Repository

1. Go to: https://github.com/new
2. **Repository name**: `openclaw-migration`
3. **Visibility**: `Private` ⚠️ IMPORTANT!
4. **UNCHECK** "Add a README file"
5. Click **"Create repository"**

## Step 3: Push Your Code

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
cd ~/openclaw-migration

# Add remote (replace YOUR_USERNAME)
git remote add origin git@github.com:YOUR_USERNAME/openclaw-migration.git

# Rename branch to main
git branch -M main

# Push everything
git push -u origin main
```

## Step 4: Verify

```bash
# Test SSH connection
ssh -T git@github.com
# Should say: Hi YOUR_USERNAME! You've successfully authenticated...

# Check remote
git remote -v

# View on GitHub
# https://github.com/YOUR_USERNAME/openclaw-migration
```

## Alternative: Run Helper Script

```bash
cd ~/openclaw-migration
./setup-github.sh
```

This will guide you through interactively.

## ⚠️ IMPORTANT: Keep This Repo PRIVATE

This repository contains:
- ✅ OpenClaw configuration (auth tokens)
- ✅ TLS certificates
- ✅ SSH keys
- ✅ Trading bot code
- ✅ Personal memories and workspace

**DO NOT make this repository public!**

---

## After Migration

Once you've successfully migrated to the new VPS:

1. Update the repo with new IP info
2. Push updates
3. Consider rotating auth tokens for security
