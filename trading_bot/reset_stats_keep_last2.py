#!/usr/bin/env python3
"""
Reset dashboard statistics while keeping only the last 2 trades.
Recalculates realized PnL from the kept trades only.
"""

import json
import os
from datetime import datetime
from decimal import Decimal

# File paths
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_state.json')
ALERT_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alert_log.jsonl')

def load_alert_log():
    """Load all alerts from log file"""
    alerts = []
    if os.path.exists(ALERT_LOG_FILE):
        with open(ALERT_LOG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        alerts.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return alerts

def get_last_n_trades(alerts, n=2):
    """Get the last N trades that resulted in position flips (realized PnL)"""
    # Filter alerts that have realized_pnl in result
    trades = []
    for alert in alerts:
        result = alert.get('result', {})
        if 'realized_pnl' in result:
            trades.append(alert)
    return trades[-n:] if len(trades) >= n else trades

def calculate_stats_from_trades(trades):
    """Calculate realized PnL and other stats from trade list"""
    total_realized_pnl = Decimal("0")
    for trade in trades:
        pnl_str = str(trade.get('result', {}).get('realized_pnl', '0'))
        total_realized_pnl += Decimal(pnl_str)
    return total_realized_pnl

def main():
    print("=" * 60)
    print("📊 RESET DASHBOARD STATISTICS")
    print("=" * 60)
    
    # Load current state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            current_state = json.load(f)
        print(f"📂 Loaded current state from {STATE_FILE}")
    else:
        current_state = {}
        print("⚠️  No existing state file found")
    
    # Load all alerts
    all_alerts = load_alert_log()
    print(f"📜 Found {len(all_alerts)} total alert entries")
    
    # Get last 2 trades
    last_2_trades = get_last_n_trades(all_alerts, 2)
    print(f"📈 Keeping last {len(last_2_trades)} trades")
    
    # Calculate new realized PnL from kept trades only
    new_realized_pnl = calculate_stats_from_trades(last_2_trades)
    
    # Display the trades we're keeping
    print("\n" + "=" * 60)
    print("📋 LAST 2 TRADES (kept for statistics):")
    print("=" * 60)
    
    for i, trade in enumerate(last_2_trades, 1):
        ts = trade.get('timestamp', 'N/A')
        alert = trade.get('parsed_alert', {})
        result = trade.get('result', {})
        action = alert.get('action', 'N/A').upper()
        price = alert.get('price', 'N/A')
        pnl = Decimal(str(result.get('realized_pnl', '0')))
        pnl_color = "🟢" if pnl >= 0 else "🔴"
        
        print(f"\n  Trade #{i}:")
        print(f"    Time: {ts}")
        print(f"    Action: {action} @ ${price}")
        print(f"    Realized PnL: {pnl_color} ${pnl:.4f} USDT")
    
    print("\n" + "=" * 60)
    print("💰 NEW STATISTICS:")
    print("=" * 60)
    print(f"  Total Realized PnL: ${new_realized_pnl:.4f} USDT")
    print(f"  Trades Count: {len(last_2_trades)}")
    
    # Create new state with reset stats but keeping current position
    new_state = {
        "symbol": current_state.get("symbol", "BTCUSDT"),
        "side": current_state.get("side", "LONG"),
        "size": current_state.get("size", "0.006689620986143788051400371809"),
        "entry_price": current_state.get("entry_price", "74742.65"),
        "realized_pnl": str(new_realized_pnl),
        "trades_count": len(last_2_trades),
        "last_trade_time": last_2_trades[-1].get('timestamp') if last_2_trades else current_state.get('last_trade_time'),
        "last_alert_hash": current_state.get("last_alert_hash"),
        "last_alert_time": current_state.get("last_alert_time")
    }
    
    # Backup old state
    backup_file = STATE_FILE + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w') as f:
        json.dump(current_state, f, indent=2)
    print(f"\n💾 Backup saved to: {backup_file}")
    
    # Save new state
    with open(STATE_FILE, 'w') as f:
        json.dump(new_state, f, indent=2)
    print(f"💾 New state saved to: {STATE_FILE}")
    
    # Also truncate alert log to keep only last 2 trades
    if last_2_trades:
        # Find the line numbers of the last 2 trades in the original file
        with open(ALERT_LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        # Find indices of trades to keep
        keep_indices = []
        for trade in last_2_trades:
            trade_ts = trade.get('timestamp')
            for i, line in enumerate(lines):
                if trade_ts and trade_ts in line:
                    keep_indices.append(i)
                    break
        
        # Backup alert log
        alert_backup = ALERT_LOG_FILE + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with open(alert_backup, 'w') as f:
            f.writelines(lines)
        print(f"💾 Alert log backup saved to: {alert_backup}")
        
        # Keep only the last 2 trade lines
        new_lines = [lines[i] for i in keep_indices]
        with open(ALERT_LOG_FILE, 'w') as f:
            f.writelines(new_lines)
        print(f"💾 Alert log truncated to {len(new_lines)} entries")
    
    print("\n" + "=" * 60)
    print("✅ RESET COMPLETE!")
    print("=" * 60)
    print("\nDashboard will now show:")
    print(f"  • Only {len(last_2_trades)} trades in history")
    print(f"  • Realized PnL: ${new_realized_pnl:.4f} USDT")
    print(f"  • Current position preserved: {new_state['side']} {new_state['size']} BTC")
    print("\n🔄 Restart the dashboard to see the changes.")

if __name__ == "__main__":
    main()
