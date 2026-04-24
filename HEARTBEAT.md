# HEARTBEAT.md - Periodic Checks

## Tasks to check periodically:

1. **Trading Bot Status** - Check if bot is running, check P&L
2. **System Health** - Disk space, memory, load
3. **OpenClaw Gateway** - Ensure gateway is responsive

## Quick Status Commands:

```bash
# Bot status
curl -s http://127.0.0.1:8080/api/status | python3 -m json.tool

# System status
df -h / && free -h

# Services
systemctl status trading-bot openclaw-gateway
```
