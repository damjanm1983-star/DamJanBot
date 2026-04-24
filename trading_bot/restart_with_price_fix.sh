#!/bin/bash
pkill -f trading_bot_server.py 2>/dev/null
sleep 2
cd /home/dame/.openclaw/workspace/trading_bot
/usr/bin/python3 trading_bot_server.py > /tmp/trading_bot.log 2>&1 &
sleep 3
echo "Server restarted with price fix"
# Test with a buy order
curl -s -X POST http://127.0.0.1:8000/webhook -H "Content-Type: application/json" -d '{"action":"buy","symbol":"BTCUSDT","price":72238}'
echo ""
sleep 1
# Check the position
curl -s http://127.0.0.1:8080/api/status | grep -E '"side"|"entry_price"' | head -4
