#!/bin/bash
pkill -f trading_bot_server.py 2>/dev/null
sleep 2
cd /home/dame/.openclaw/workspace/trading_bot
/usr/bin/python3 trading_bot_server.py > /tmp/trading_bot.log 2>&1 &
sleep 3
echo "Dashboard restarted with improved UI"
curl -s http://127.0.0.1:8080/ | grep -o '<title>.*</title>'
