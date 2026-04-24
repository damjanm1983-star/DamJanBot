#!/usr/bin/env python3
"""
Email Alert Monitor - Fallback for TradingView webhooks
Watches Gmail for TradingView alert emails and triggers webhook locally
"""

import json
import re
import time
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configuration
ALERT_LOG_FILE = '/root/.openclaw/workspace/trading_bot/alert_log.jsonl'
WEBHOOK_URL = 'http://localhost:8000/webhook'
CHECK_INTERVAL = 30  # seconds


def parse_email_alert(subject: str) -> Optional[Dict[str, Any]]:
    """Parse TradingView alert email subject to extract action and data"""
    # Pattern: Alert: {"action":"sell","symbol":"...","price":...}
    match = re.search(r'Alert:\s*(\{.*?\})', subject)
    if not match:
        return None
    
    try:
        data = json.loads(match.group(1))
        return {
            'action': data.get('action', '').lower(),
            'symbol': data.get('symbol', 'BTCUSDT'),
            'price': float(data.get('price', 0)) if data.get('price') else 0
        }
    except (json.JSONDecodeError, ValueError):
        return None


def send_webhook(alert_data: Dict[str, Any]) -> bool:
    """Send alert to local webhook"""
    import urllib.request
    
    try:
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=json.dumps(alert_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"✅ Webhook response: {result.get('status', 'unknown')}")
            return result.get('success', False)
    except Exception as e:
        print(f"❌ Webhook failed: {e}")
        return False


def check_recent_emails():
    """Check for recent TradingView alert emails using aerc or other mail client"""
    # For now, this is a placeholder - we'll use a different approach
    # The user can manually forward emails or we can set up IMAP
    pass


def log_manual_alert(action: str, symbol: str = "BTCUSDT", price: float = 0):
    """Log a manually triggered alert"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "source": "manual_email_fallback",
        "action": action,
        "symbol": symbol,
        "price": price
    }
    with open(ALERT_LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")


if __name__ == "__main__":
    print("📧 Email Alert Monitor")
    print("This script can be used to manually trigger alerts from email")
    print("Usage: python3 email_alert_monitor.py <buy|sell> [price]")
    
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        price = float(sys.argv[2]) if len(sys.argv) > 2 else 0
        
        alert_data = {
            'action': action,
            'symbol': 'BTCUSDT',
            'price': price if price > 0 else 70000  # Default price
        }
        
        print(f"🚨 Triggering {action.upper()} alert at price {alert_data['price']}")
        log_manual_alert(action, price=alert_data['price'])
        
        if send_webhook(alert_data):
            print("✅ Alert processed successfully")
        else:
            print("❌ Alert failed")
