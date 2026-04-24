#!/bin/bash
# Start trading bot with Telegram notifications enabled

# Telegram Bot Configuration
export TELEGRAM_BOT_TOKEN="8619307561:AAEuopebkFEKGeyv2wbjcyWCgY7ANTWJ27Y"
export TELEGRAM_CHAT_ID="-1003593624857"

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start the trading bot server
echo "Starting Trading Bot with Telegram notifications..."
echo "Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
echo "Chat ID: $TELEGRAM_CHAT_ID"
python3 trading_bot_server.py
