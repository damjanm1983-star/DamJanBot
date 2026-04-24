#!/bin/bash
pkill -f trading_bot_server.py 2>/dev/null
sleep 2
cd /home/dame/.openclaw/workspace/trading_bot
sed -i 's/port=6000/port=8080/' trading_bot_server.py
/usr/bin/python3 trading_bot_server.py > /tmp/trading_bot.log 2>&1 &
echo "Dashboard starting on port 8080..."
sleep 3
curl -s http://127.0.0.1:8080/ | grep title
