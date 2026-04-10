#!/bin/bash
pkill -f trading_bot_server.py 2>/dev/null
sleep 2
cd /home/dame/.openclaw/workspace/trading_bot
/usr/bin/python3 trading_bot_server.py > /tmp/trading_bot.log 2>&1 &
sleep 2
echo "Server restarted"
tail -3 /tmp/trading_bot.log
