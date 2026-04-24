# TradingView Alert Setup Guide

## Problem: Duplicate Emails
You have **2 email alerts** because:
1. ✅ "Send email" is checked
2. ✅ "Send plain text" is ALSO checked

**Fix**: Uncheck "Send plain text" — you only need ONE email.

---

## Recommended Alert Setup

### Step 1: Use the Clean Pine Script
Use `BTCUSDT_Clean_Single_Alert.pine` — it has NO built-in alert() calls.

### Step 2: Create ONE Strategy Alert (Not Multiple Alerts)

Instead of creating separate alerts for buy/sell, create **ONE strategy alert**:

1. Click the "Alerts" button (clock icon) in TradingView
2. Click "Create Alert"
3. Set:
   - **Condition**: Select your strategy "BTCUSDT Clean Single Alert"
   - **Message**: `{"action":"{{strategy.order.action}}","symbol":"{{ticker}}","price":{{close}}}`
   - **Frequency**: "Once Per Bar Close" ⭐ IMPORTANT!
   - ✅ Webhook URL: `http://5.9.248.66/webhook`
   - ✅ Send email (only this, uncheck "Send plain text")

### Why This Is Better

| Old Way | New Way |
|---------|---------|
| 2 separate alerts (buy + sell) | 1 strategy alert |
| Multiple emails | 1 email per signal |
| Risk of duplicate webhooks | Single webhook per trade |
| Harder to manage | One alert to rule them all |

---

## Template Variables

These work in TradingView alerts:
- `{{strategy.order.action}}` → "buy" or "sell"
- `{{ticker}}` → "BTCUSDT"
- `{{close}}` → Current price
- `{{time}}` → Timestamp

---

## Debugging Webhook Issues

If webhooks still don't arrive:

1. **Test manually**:
   ```bash
   curl -X POST http://5.9.248.66/webhook \
     -H "Content-Type: application/json" \
     -d '{"action":"buy","symbol":"BTCUSDT","price":70000}'
   ```

2. **Check bot logs**:
   ```bash
   ssh your-server
   tail -f /tmp/trading_bot.log
   ```

3. **Use manual trigger** if webhook fails:
   ```bash
   ./trigger_alert.sh buy    # or sell
   ```

---

## Quick Checklist

- [ ] Using `BTCUSDT_Clean_Single_Alert.pine`
- [ ] ONE strategy alert (not multiple)
- [ ] Message: `{"action":"{{strategy.order.action}}","symbol":"{{ticker}}","price":{{close}}}`
- [ ] Frequency: "Once Per Bar Close"
- [ ] Webhook URL: `http://5.9.248.66/webhook`
- [ ] Only "Send email" checked (NOT "Send plain text")
- [ ] Tested with manual curl command
