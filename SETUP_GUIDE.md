# Trading Bot Setup Guide

## Overview

This trading bot connects TradingView alerts to Binance Futures with:
- **Position sizing:** 50% of balance per trade
- **Margin:** 30% (effective ~3.3x leverage)
- **Symbol:** BTCUSDT
- **Timeframe:** 5min (from Pine Script)

## Architecture

```
TradingView (Pine Script) → Webhook → Bot Handler → Dry-Run Engine or Live Trading
                                    ↓
                              Position Sizing (50% balance, 30% margin)
                                    ↓
                              Binance API (read-only for now)
```

## Files

| File | Purpose |
|------|---------|
| `binance_api_client.py` | Low-level Binance API communication |
| `config.py` | Environment-based configuration |
| `position_reader.py` | Reads current position state |
| `webhook_handler.py` | Receives and processes TradingView alerts |
| `dry_run_engine.py` | Simulates trades without real execution |
| `pine_script_v7_2_alerts.pine` | Updated Pine Script with webhook alerts |
| `test_webhook_integration.py` | Integration tests |

## Setup Steps

### 1. Environment Variables

Create a `.env` file or export these:

```bash
# Required - Get from Binance API Management
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_SECRET_KEY="your_secret_key_here"

# Trading settings
export PAPER_MODE="true"  # Set to "false" for live trading (NOT IMPLEMENTED YET)
export SYMBOL="BTCUSDT"
export POSITION_ALLOCATION_PERCENT="0.50"  # 50% of balance
export TARGET_LEVERAGE="3"
export MAX_NOTIONAL_CAP_USDT="50000"

# Webhook settings
export WEBHOOK_SECRET="your_webhook_secret_here"  # For signature verification
export WEBHOOK_PORT="8000"

# Safety
export STARTUP_SAFE_MODE="true"
```

### 2. TradingView Setup

1. Open the Pine Script editor in TradingView
2. Copy contents from `pine_script_v7_2_alerts.pine`
3. Add to chart
4. Create alerts:
   - **Alert 1:** Condition = "🟢 BUY Signal", Message = `{{strategy.order.alert_message}}`
   - **Alert 2:** Condition = "🔴 SELL Signal", Message = `{{strategy.order.alert_message}}`
   - **Webhook URL:** `http://YOUR_SERVER_IP:8000/webhook`

### 3. Start the Bot

```bash
# Test mode (dry-run)
cd /path/to/trading_bot
python3 test_webhook_integration.py

# Start webhook server (when ready)
python3 -c "
from config import Config
from webhook_handler import create_webhook_server
from dry_run_engine import DryRunEngine

config = Config()
engine = DryRunEngine(config)
server = create_webhook_server(config, dry_run_engine=engine)
print('Server starting on port', config.webhook_port)
server.serve_forever()
"
```

## Position Sizing Logic

For a $1000 balance:

```
Position Value = Balance × 50% = $500
Margin Required = Position Value × 30% = $150
Quantity = Position Value / BTC Price

Example at $50,000 BTC:
  Quantity = $500 / $50,000 = 0.01 BTC
  Effective Leverage = $500 / $150 = 3.33x
```

## Alert Format

Your Pine Script sends this JSON:

```json
{
  "action": "buy",
  "symbol": "BTCUSDT",
  "side": "long",
  "price": 50123.45,
  "strategy": "ema_cross_v7_2",
  "timeframe": "5m",
  "timestamp": 1712678400000,
  "indicators": {
    "rsi": 58.5,
    "adx": 22.3,
    "atr_pct": 0.85
  }
}
```

## Current Status

✅ **Working:**
- Alert parsing from TradingView
- Position sizing (50% balance, 30% margin)
- Dry-run simulation
- Webhook server framework
- Binance API read-only client

❌ **Not Yet Implemented:**
- Live order execution (orders to Binance)
- WebSocket price feeds
- Risk management (daily limits, drawdown)
- Position monitoring/tracking
- Database persistence

## Testing

```bash
# Run integration tests
python3 test_webhook_integration.py

# Test webhook manually
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"action":"buy","symbol":"BTCUSDT","price":50000}'
```

## Next Steps

1. **Test dry-run mode** - Run for a few days to verify signals
2. **Add live trading** - Implement actual order submission
3. **Add monitoring** - Track PnL, positions, errors
4. **Add risk controls** - Daily loss limits, max positions

## Security Notes

- Keep `PAPER_MODE=true` until fully tested
- Use webhook signature verification in production
- Store API keys securely (not in code)
- Start with small position sizes
