"""
Test script for webhook handler and position sizing logic.
Run this to verify the bot handles TradingView alerts correctly.
"""

import json
import logging
from decimal import Decimal
from config import Config
from webhook_handler import WebhookHandler, TradingViewAlert
from dry_run_engine import DryRunEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("TestWebhook")


def test_alert_parsing():
    """Test parsing of TradingView alerts"""
    print("\n=== Testing Alert Parsing ===\n")
    
    # Example alert from your Pine script
    test_alerts = [
        {
            "action": "buy",
            "symbol": "BTCUSDT",
            "side": "long",
            "price": 50123.45,
            "strategy": "ema_cross_v7_2",
            "timeframe": "5m",
            "timestamp": 1712678400000,
            "indicators": {"rsi": 58.5, "adx": 22.3, "atr_pct": 0.85}
        },
        {
            "action": "sell",
            "symbol": "BTCUSDT",
            "side": "short",
            "price": 49876.20,
            "strategy": "ema_cross_v7_2",
            "timeframe": "5m",
            "timestamp": 1712678700000,
            "indicators": {"rsi": 42.1, "adx": 24.7, "atr_pct": 0.92}
        }
    ]
    
    for alert_data in test_alerts:
        try:
            alert = TradingViewAlert(alert_data)
            alert.validate()
            print(f"✅ Parsed: {alert}")
            print(f"   Action: {alert.action}, Side: {alert.get_side()}")
            print(f"   Is Entry: {alert.is_entry()}, Is Exit: {alert.is_exit()}")
        except Exception as e:
            print(f"❌ Failed to parse: {e}")


def test_position_sizing():
    """Test position sizing calculation"""
    print("\n=== Testing Position Sizing ===\n")
    
    # Create config with dummy values for testing
    import os
    os.environ['BINANCE_API_KEY'] = 'test_key'
    os.environ['BINANCE_SECRET_KEY'] = 'test_secret'
    os.environ['PAPER_MODE'] = 'true'
    
    config = Config()
    
    # Create dry-run engine
    engine = DryRunEngine(config)
    
    # Create webhook handler
    handler = WebhookHandler(config, dry_run_engine=engine)
    
    # Test alerts
    test_cases = [
        {"action": "buy", "symbol": "BTCUSDT", "price": 50000},
        {"action": "sell", "symbol": "BTCUSDT", "price": 51000},
    ]
    
    for alert_data in test_cases:
        alert = TradingViewAlert(alert_data)
        quantity = handler.calculate_position_size(alert)
        
        # Calculate what this means
        price = Decimal(str(alert_data["price"]))
        position_value = quantity * price
        margin_30pct = position_value * Decimal("0.30")
        
        print(f"\n📊 {alert.action.upper()} Signal at ${price:,.2f}")
        print(f"   Quantity: {quantity:.6f} BTC")
        print(f"   Position Value: ${position_value:,.2f}")
        print(f"   Margin Required (30%): ${margin_30pct:,.2f}")
        print(f"   Effective Leverage: {(position_value / margin_30pct):.1f}x")


def test_dry_run_execution():
    """Test full execution flow"""
    print("\n=== Testing Dry-Run Execution ===\n")
    
    import os
    os.environ['BINANCE_API_KEY'] = 'test_key'
    os.environ['BINANCE_SECRET_KEY'] = 'test_secret'
    os.environ['PAPER_MODE'] = 'true'
    
    config = Config()
    engine = DryRunEngine(config)
    handler = WebhookHandler(config, dry_run_engine=engine)
    
    # Simulate a BUY alert
    buy_alert = TradingViewAlert({
        "action": "buy",
        "symbol": "BTCUSDT",
        "price": 50000
    })
    
    print("1️⃣ Processing BUY alert...")
    result = handler.handle_alert(buy_alert)
    print(f"   Result: {json.dumps(result, indent=2, default=str)}")
    
    # Check position
    position = engine.get_position("BTCUSDT")
    if position:
        print(f"\n   Position: {position.side.value if position.side else 'FLAT'}")
        print(f"   Size: {position.size:.6f} BTC")
        print(f"   Entry: ${position.entry_price:,.2f}" if position.entry_price else "   Entry: N/A")
    
    # Simulate a SELL alert (flip to short)
    sell_alert = TradingViewAlert({
        "action": "sell",
        "symbol": "BTCUSDT",
        "price": 51000
    })
    
    print("\n2️⃣ Processing SELL alert (flip position)...")
    result = handler.handle_alert(sell_alert)
    print(f"   Result: {json.dumps(result, indent=2, default=str)}")
    
    # Check updated position
    position = engine.get_position("BTCUSDT")
    if position:
        print(f"\n   Position: {position.side.value if position.side else 'FLAT'}")
        print(f"   Size: {position.size:.6f} BTC")
        print(f"   Realized PnL: ${position.realized_pnl:,.2f}")
    
    # Show performance summary
    print("\n3️⃣ Performance Summary:")
    summary = engine.get_performance_summary()
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Realized PnL: ${summary['total_realized_pnl']:,.2f}")
    print(f"   Commissions: ${summary['total_commissions']:,.2f}")
    print(f"   Net PnL: ${summary['net_pnl']:,.2f}")


def test_alert_sequence():
    """Test a sequence of alerts as they would come from TradingView"""
    print("\n=== Testing Alert Sequence ===\n")
    
    import os
    os.environ['BINANCE_API_KEY'] = 'test_key'
    os.environ['BINANCE_SECRET_KEY'] = 'test_secret'
    os.environ['PAPER_MODE'] = 'true'
    
    config = Config()
    engine = DryRunEngine(config)
    handler = WebhookHandler(config, dry_run_engine=engine)
    
    # Simulate price movement and alerts
    scenario = [
        {"action": "buy", "price": 50000, "note": "Signal at support"},
        {"action": "buy", "price": 50500, "note": "Already long, should skip"},
        {"action": "sell", "price": 51000, "note": "Flip to short"},
        {"action": "sell", "price": 49500, "note": "Add to short"},
        {"action": "buy", "price": 52000, "note": "Stop loss hit, flip long"},
    ]
    
    for i, step in enumerate(scenario, 1):
        print(f"\n📍 Step {i}: {step['note']}")
        print(f"   Price: ${step['price']:,}")
        
        alert = TradingViewAlert({
            "action": step["action"],
            "symbol": "BTCUSDT",
            "price": step["price"]
        })
        
        result = handler.handle_alert(alert)
        
        position = engine.get_position("BTCUSDT")
        if position and position.size > 0:
            print(f"   → Position: {position.side.value} {position.size:.4f} BTC")
            print(f"   → Unrealized PnL: ${position.unrealized_pnl:,.2f}")
        else:
            print(f"   → Position: FLAT")
        
        if not result.get("success"):
            print(f"   ⚠️  {result.get('error', 'Unknown error')}")
    
    # Final summary
    print("\n📊 Final Results:")
    summary = engine.get_performance_summary()
    print(f"   Total Trades: {summary['total_trades']}")
    print(f"   Win Rate: {summary['win_rate']*100:.1f}%")
    print(f"   Net PnL: ${summary['net_pnl']:,.2f}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Trading Bot Integration Tests")
    print("=" * 60)
    
    try:
        test_alert_parsing()
        test_position_sizing()
        test_dry_run_execution()
        test_alert_sequence()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
