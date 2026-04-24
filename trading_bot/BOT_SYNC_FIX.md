# Trading Bot Sync Fix

## Problem
TradingView sends email alerts but webhooks don't always reach the bot, causing position desync.

## Immediate Workaround
When you get an email alert but the bot doesn't update, run:

```bash
# SSH to your server and run:
cd /home/dame/.openclaw/workspace/trading_bot
./trigger_alert.sh sell   # For sell signal
./trigger_alert.sh buy    # For buy signal
```

## Current Status
- Bot is running and functional
- Webhook endpoint: http://5.9.248.66/webhook
- Dashboard: http://5.9.248.66:8080

## What Was Fixed
1. ✅ Added detailed webhook logging (every request is now logged)
2. ✅ Added alert log file (`alert_log.jsonl`)
3. ✅ Created manual trigger script (`trigger_alert.sh`)
4. ✅ Added JSON error handling for malformed requests

## Testing the Webhook
```bash
# Test from your local machine:
curl -X POST http://5.9.248.66/webhook \
  -H "Content-Type: application/json" \
  -d '{"action":"sell","symbol":"BTCUSDT","price":70000}'
```

## Next Steps to Investigate
1. Check if TradingView webhook IP is being blocked
2. Add IP whitelist logging
3. Consider email-based fallback (IMAP polling)

## Root Cause Analysis
The webhook URL is correct, the bot is working, but TradingView's HTTP requests aren't arriving.
Possible causes:
- TradingView free tier webhook limits exceeded
- IP-based rate limiting
- Network/firewall blocking TradingView IPs
- TradingView webhook queue backlog
