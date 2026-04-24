#!/usr/bin/env python3
"""
Telegram notifier for trading bot alerts.
Sends trade notifications to a Telegram channel.
"""

import logging
import requests
from datetime import datetime
from typing import Optional

logger = logging.getLogger("TelegramNotifier")


class TelegramNotifier:
    """Sends trade notifications to Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)
        
        if self.enabled:
            logger.info("Telegram notifier initialized")
        else:
            logger.warning("Telegram notifier disabled - missing token or chat_id")
    
    def send_message(self, message: str) -> bool:
        """Send a message to Telegram"""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def notify_trade(self, action: str, symbol: str, price: float, 
                     size: float, realized_pnl: float, from_side: str, 
                     to_side: str) -> bool:
        """Send a trade execution notification"""
        
        # Format PnL with color indicator
        pnl_emoji = "🟢" if realized_pnl >= 0 else "🔴"
        pnl_sign = "+" if realized_pnl > 0 else ""
        
        # Format position change
        if from_side == "FLAT":
            position_change = f"OPEN {to_side}"
        elif to_side == "FLAT":
            position_change = f"CLOSE {from_side}"
        else:
            position_change = f"{from_side} → {to_side}"
        
        message = f"""<b>🤖 TRADE EXECUTED</b>

<b>Action:</b> {action.upper()}
<b>Position:</b> {position_change}
<b>Symbol:</b> {symbol}
<b>Price:</b> ${price:,.2f}
<b>Size:</b> {size:.6f} BTC
<b>Realized PnL:</b> {pnl_emoji} ${pnl_sign}{realized_pnl:.2f}

<i>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</i>
"""
        return self.send_message(message)
    
    def notify_position_open(self, side: str, symbol: str, price: float, 
                            size: float) -> bool:
        """Notify when a new position is opened"""
        side_emoji = "🟢" if side == "LONG" else "🔴"
        
        message = f"""<b>{side_emoji} POSITION OPENED</b>

<b>Side:</b> {side}
<b>Symbol:</b> {symbol}
<b>Entry Price:</b> ${price:,.2f}
<b>Size:</b> {size:.6f} BTC

<i>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</i>
"""
        return self.send_message(message)
    
    def notify_error(self, error_message: str) -> bool:
        """Send an error notification"""
        message = f"""<b>⚠️ BOT ERROR</b>

<code>{error_message}</code>

<i>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</i>
"""
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """Test Telegram connection by sending a test message"""
        message = "<b>🤖 Trading Bot Connected</b>\n\nTelegram notifications are now active!"
        return self.send_message(message)
