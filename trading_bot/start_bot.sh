#!/bin/bash
cd /home/dame/.openclaw/workspace/trading_bot
pkill -f trading_bot_server.py 2>/dev/null
sleep 2
python3 trading_bot_server.py > /tmp/trading_bot.log 2>&1 &
echo "Bot started"
