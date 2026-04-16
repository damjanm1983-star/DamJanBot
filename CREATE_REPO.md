# Create GitHub Repository

## Step 1: Create the Repository

1. Go to: https://github.com/new
2. **Repository name**: `openclaw-migration`
3. **Description**: `OpenClaw VPS migration backup and restore scripts`
4. **Visibility**: `Private` ⚠️ (IMPORTANT - contains sensitive data)
5. **UNCHECK** "Add a README file" (we already have one)
6. **UNCHECK** "Add .gitignore" (we already have one)
7. **UNCHECK** "Choose a license"
8. Click **"Create repository"**

## Step 2: Add SSH Key to GitHub

Your SSH key:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN7WAMOuiyLxLZ8Mkw6VV0L7WPfA0psXjv/CczWVXmyt trading-bot@vps
```

1. Go to: https://github.com/settings/keys
2. Click **"New SSH key"**
3. Title: `Hetzner VPS`
4. Key type: `Authentication Key`
5. Paste the key above
6. Click **"Add SSH key"**

## Step 3: Test SSH Connection

```bash
ssh -T git@github.com
```

Should say:
```
Hi damjanm1983-star! You've successfully authenticated...
```

## Step 4: Push the Code

```bash
cd ~/openclaw-migration
git push -u origin main
```

## Done!

Your repo will be at:
https://github.com/damjanm1983-star/openclaw-migration
