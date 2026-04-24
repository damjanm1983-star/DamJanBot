#!/bin/bash
# Quick script to manually trigger an alert when TradingView webhook fails
# Usage: ./trigger_alert.sh buy [price]  or  ./trigger_alert.sh sell [price]

ACTION=${1:-"buy"}
PRICE=${2:-"0"}

# Get current BTC price if not provided
if [ "$PRICE" = "0" ]; then
    # Try to get price from Binance API
    PRICE=$(curl -s "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT" | grep -o '"price":"[^"]*"' | cut -d'"' -f4 | cut -d'.' -f1)
    if [ -z "$PRICE" ]; then
        PRICE="70000"
    fi
fi

echo "🚨 Triggering $ACTION alert at price $PRICE"

curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"$ACTION\",\"symbol\":\"BTCUSDT\",\"price\":$PRICE}"

echo ""
