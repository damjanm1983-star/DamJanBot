#!/usr/bin/env python3
"""
Trading Bot Server with Dry-Run Engine and Dashboard
- Receives TradingView webhooks
- Simulates trades with dry-run engine
- Serves monitoring dashboard on port 6000
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from decimal import Decimal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from dry_run_engine import DryRunEngine, OrderSide, OrderType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger("TradingBot")

# Global state
bot_state = {
    "alerts_received": 0,
    "trades_executed": 0,
    "last_alert": None,
    "last_trade": None,
    "start_time": datetime.now().isoformat(),
    "status": "running"
}

class TradingBot:
    def __init__(self):
        # Setup environment for config
        os.environ['BINANCE_API_KEY'] = 'dry_run_key'
        os.environ['BINANCE_SECRET_KEY'] = 'dry_run_secret'
        os.environ['PAPER_MODE'] = 'true'
        
        self.config = Config()
        self.engine = DryRunEngine(self.config)
        logger.info("Trading Bot initialized in DRY-RUN mode")
        logger.info(f"Starting balance: $1000.00")
        logger.info(f"Position sizing: 50% of balance, 30% margin")
    
    def process_alert(self, alert_data):
        """Process incoming TradingView alert"""
        global bot_state
        
        action = alert_data.get('action', '').lower()
        symbol = alert_data.get('symbol', 'BTCUSDT')
        price = Decimal(str(alert_data.get('price', 0)))
        
        bot_state["alerts_received"] += 1
        bot_state["last_alert"] = {
            "time": datetime.now().isoformat(),
            "action": action,
            "symbol": symbol,
            "price": str(price)
        }
        
        logger.info("=" * 60)
        logger.info(f"🚨 ALERT RECEIVED: {action.upper()} {symbol}")
        logger.info(f"💰 Price: ${price:,.2f}")
        
        # Calculate position size
        balance = Decimal("1000.0")
        allocation = Decimal("0.50")  # 50%
        margin = Decimal("0.30")      # 30%
        
        position_value = balance * allocation
        quantity = position_value / price if price > 0 else Decimal("0.01")
        
        logger.info(f"📊 Position Size: {quantity:.6f} BTC (${position_value:,.2f})")
        logger.info(f"💵 Margin Required: ${position_value * margin:,.2f}")
        
        # Check current position before executing
        current_position = self.engine.get_position(symbol)
        current_side = current_position.side.value if current_position and current_position.side else "FLAT"
        
        # Skip if already in the requested position
        if action == 'buy' and current_side == "LONG":
            logger.info(f"⏭️  Already LONG {symbol}, skipping BUY signal")
            return {"success": True, "status": "skipped", "reason": "already_long"}
        
        if action == 'sell' and current_side == "SHORT":
            logger.info(f"⏭️  Already SHORT {symbol}, skipping SELL signal")
            return {"success": True, "status": "skipped", "reason": "already_short"}
        
        # Execute trade with price from alert
        if action == 'buy':
            result = self.engine.place_order(
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=quantity,
                market_price=price
            )
        elif action == 'sell':
            result = self.engine.place_order(
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=quantity,
                market_price=price
            )
        else:
            logger.warning(f"Unknown action: {action}")
            return {"success": False, "error": "Unknown action"}
        
        # Update state
        if result.get('success'):
            bot_state["trades_executed"] += 1
            bot_state["last_trade"] = {
                "time": datetime.now().isoformat(),
                "action": action,
                "symbol": symbol,
                "quantity": str(quantity),
                "result": result
            }
            logger.info(f"✅ Trade executed: {result['order_id']}")
        else:
            logger.error(f"❌ Trade failed: {result.get('error')}")
        
        logger.info("=" * 60)
        return result
    
    def get_status(self):
        """Get current bot status"""
        position = self.engine.get_position("BTCUSDT")
        performance = self.engine.get_performance_summary()
        
        return {
            "bot": bot_state,
            "position": {
                "symbol": position.symbol if position else None,
                "side": position.side.value if position and position.side else "FLAT",
                "size": str(position.size) if position else "0",
                "entry_price": str(position.entry_price) if position and position.entry_price else None,
                "unrealized_pnl": str(position.unrealized_pnl) if position else "0",
                "realized_pnl": str(position.realized_pnl) if position else "0"
            },
            "performance": {
                "total_trades": performance['total_trades'],
                "win_rate": f"{performance['win_rate']*100:.1f}%",
                "realized_pnl": f"${float(performance['total_realized_pnl']):,.2f}",
                "unrealized_pnl": f"${float(performance['total_unrealized_pnl']):,.2f}",
                "commissions": f"${float(performance['total_commissions']):,.2f}",
                "net_pnl": f"${float(performance['net_pnl']):,.2f}"
            }
        }

# Global bot instance
bot = TradingBot()

class WebhookHandler(BaseHTTPRequestHandler):
    """Handle webhook alerts from TradingView"""
    
    def log_message(self, format, *args):
        logger.info(format % args)
    
    def do_POST(self):
        if self.path == '/webhook':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                alert_data = json.loads(post_data.decode('utf-8'))
                result = bot.process_alert(alert_data)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                logger.error(f"Error processing alert: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Trading Bot Webhook - Send POST to /webhook\n')
        else:
            self.send_response(404)
            self.end_headers()

class DashboardHandler(BaseHTTPRequestHandler):
    """Serve monitoring dashboard"""
    
    def log_message(self, format, *args):
        pass  # Reduce noise
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path == '/api/status':
            self.serve_api_status()
        elif parsed_path.path == '/api/trades':
            self.serve_api_trades()
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_dashboard(self):
        status = bot.get_status()
        
        # Format numbers nicely
        pos_size = float(status['position']['size']) if status['position']['size'] else 0
        entry_price = float(status['position']['entry_price']) if status['position']['entry_price'] else 0
        position_value = pos_size * entry_price if pos_size and entry_price else 0
        unrealized_pnl = float(status['position']['unrealized_pnl']) if status['position']['unrealized_pnl'] else 0
        
        # Format side display
        side = status['position']['side']
        side_class = 'position-long' if side == 'LONG' else 'position-short' if side == 'SHORT' else 'position-flat'
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dame and Jan Trading Bot Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #fff;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #00d4aa;
            border-bottom: 2px solid #00d4aa;
            padding-bottom: 10px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .card {{
            background: #151b3d;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #2a3362;
        }}
        .card h2 {{
            margin-top: 0;
            color: #8892b0;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric {{
            font-size: 32px;
            font-weight: bold;
            color: #00d4aa;
        }}
        .metric.red {{
            color: #ff6b6b;
        }}
        .metric.yellow {{
            color: #ffd93d;
        }}
        .metric.large {{
            font-size: 28px;
        }}
        .detail {{
            margin-top: 10px;
            font-size: 14px;
            color: #8892b0;
            line-height: 1.6;
        }}
        .detail strong {{
            color: #fff;
        }}
        .position-long {{
            color: #00d4aa;
            font-weight: bold;
        }}
        .position-short {{
            color: #ff6b6b;
            font-weight: bold;
        }}
        .position-flat {{
            color: #8892b0;
        }}
        .pnl-positive {{
            color: #00d4aa;
        }}
        .pnl-negative {{
            color: #ff6b6b;
        }}
        .status-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #00d4aa;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-dryrun {{
            background: #ffd93d;
            color: #0a0e27;
        }}
        .price-large {{
            font-size: 24px;
            font-weight: bold;
            color: #fff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            <span class="status-indicator"></span>
            Dame and Jan Trading Bot Dashboard
            <span class="badge badge-dryrun">DRY-RUN MODE</span>
        </h1>
        
        <div class="grid">
            <div class="card">
                <h2>Current Position</h2>
                <div class="metric {side_class}">
                    {side}
                </div>
                <div class="detail">
                    <strong>Size:</strong> {pos_size:.6f} BTC<br>
                    <strong>Entry Price:</strong> <span class="price-large">${entry_price:,.2f}</span><br>
                    <strong>Position Value:</strong> ${position_value:,.2f}<br>
                    <strong>Unrealized PnL:</strong> <span class="{'pnl-positive' if unrealized_pnl >= 0 else 'pnl-negative'}">${unrealized_pnl:,.2f}</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Total Trades</h2>
                <div class="metric">{status['performance']['total_trades']}</div>
                <div class="detail">
                    Win Rate: {status['performance']['win_rate']}<br>
                    Alerts Received: {status['bot']['alerts_received']}
                </div>
            </div>
            
            <div class="card">
                <h2>Realized PnL</h2>
                <div class="metric {'red' if float(status['performance']['realized_pnl'].replace('$', '').replace(',', '')) < 0 else ''}">
                    {status['performance']['realized_pnl']}
                </div>
                <div class="detail">
                    Commissions: {status['performance']['commissions']}
                </div>
            </div>
            
            <div class="card">
                <h2>Net PnL</h2>
                <div class="metric {'red' if float(status['performance']['net_pnl'].replace('$', '').replace(',', '')) < 0 else 'yellow'}">
                    {status['performance']['net_pnl']}
                </div>
                <div class="detail">
                    Unrealized: {status['performance']['unrealized_pnl']}
                </div>
            </div>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h2>Last Alert</h2>
            <div class="detail">
                {json.dumps(status['bot']['last_alert'], indent=2) if status['bot']['last_alert'] else 'No alerts yet'}
            </div>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h2>Configuration</h2>
            <div class="detail">
                <strong>Balance:</strong> $1,000.00<br>
                <strong>Position Size:</strong> 50% ($500)<br>
                <strong>Margin:</strong> 30%<br>
                <strong>Effective Leverage:</strong> ~3.3x<br>
                <strong>Symbol:</strong> BTCUSDT<br>
                <strong>Started:</strong> {status['bot']['start_time']}
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_api_status(self):
        status = bot.get_status()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status, indent=2).encode())
    
    def serve_api_trades(self):
        trades = bot.engine.get_trade_history()
        trade_list = [{
            "id": t.trade_id,
            "symbol": t.symbol,
            "side": t.side.value,
            "quantity": str(t.quantity),
            "price": str(t.price),
            "pnl": str(t.realized_pnl),
            "time": datetime.fromtimestamp(t.timestamp_ms/1000).isoformat()
        } for t in trades]
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(trade_list, indent=2).encode())

def run_webhook_server(port=8000):
    """Run webhook server in separate thread"""
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    logger.info(f"🚀 Webhook server on port {port}")
    server.serve_forever()

def run_dashboard_server(port=8080):
    """Run dashboard server in separate thread"""
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    logger.info(f"📊 Dashboard on http://5.9.248.66:{port}")
    server.serve_forever()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🤖 TRADING BOT SERVER STARTING")
    logger.info("=" * 60)
    logger.info("Mode: DRY-RUN (no real trades)")
    logger.info("Webhook: http://5.9.248.66/webhook")
    logger.info("Dashboard: http://5.9.248.66:6000")
    logger.info("=" * 60)
    
    # Start webhook server in thread
    webhook_thread = threading.Thread(target=run_webhook_server, args=(8000,), daemon=True)
    webhook_thread.start()
    
    # Start dashboard server in main thread
    try:
        run_dashboard_server(6000)
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped")
