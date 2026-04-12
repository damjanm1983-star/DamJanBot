#!/usr/bin/env python3
"""
Fix the corrupted position state.
Based on logs, the position should be SHORT at ~$72,234 after the SELL signal on April 12.
"""

import json
import os

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_state.json')

# The position should be SHORT after the SELL signal at $72,234
# From the logs: SELL executed at $72,234.80, quantity ~0.006921 BTC
fixed_state = {
    "symbol": "BTCUSDT",
    "side": "SHORT",
    "size": "0.006921",
    "entry_price": "72234.80",
    "realized_pnl": "0.66",
    "trades_count": 3,
    "last_trade_time": "2026-04-12T01:45:04",
    "last_alert_hash": "sell:BTCUSDT:72242",
    "last_alert_time": "2026-04-12T01:45:04"
}

print("🔧 Fixing position state...")
print(f"   Before: LONG 0.00691 BTC @ $72,234 (WRONG)")
print(f"   After:  SHORT 0.006921 BTC @ $72,234.80")

with open(STATE_FILE, 'w') as f:
    json.dump(fixed_state, f, indent=2)

print(f"\n✅ State saved to {STATE_FILE}")
print("\n📝 To apply this fix:")
print("   1. Restart the trading bot server")
print("   2. Check dashboard at http://5.9.248.66:6000")
print("\n🔄 Or manually reset via API:")
print("   curl 'http://5.9.248.66:6000/api/reset?side=SHORT&size=0.006921&entry=72234.80'")
