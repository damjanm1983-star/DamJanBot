#!/usr/bin/env python3
"""Test Telegram connection"""
import os
os.environ['TELEGRAM_BOT_TOKEN'] = '8619307561:AAEuopebkFEKGeyv2wbjcyWCgY7ANTWJ27Y'
os.environ['TELEGRAM_CHAT_ID'] = '-1003593624857'

from telegram_notifier import TelegramNotifier

notifier = TelegramNotifier(
    bot_token=os.environ['TELEGRAM_BOT_TOKEN'],
    chat_id=os.environ['TELEGRAM_CHAT_ID']
)

print(f"Telegram enabled: {notifier.enabled}")
print("Sending test message...")

success = notifier.test_connection()
if success:
    print("✅ Test message sent successfully!")
else:
    print("❌ Failed to send test message")
