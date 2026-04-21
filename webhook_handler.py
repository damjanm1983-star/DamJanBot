"""
Webhook Handler for TradingView Alerts
Routes alerts to dry-run engine or live trading based on configuration.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from decimal import Decimal
from typing import Any, Dict, Optional
from datetime import datetime

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from config import Config
from binance_api_client import BinanceApiClient
from position_reader import PositionReader
from dry_run_engine import DryRunEngine, OrderSide, OrderType, create_market_order


class WebhookAuthError(Exception):
    pass


class WebhookValidationError(Exception):
    pass


class TradingViewAlert:
    """Parsed TradingView alert"""
    
    VALID_ACTIONS = ["buy", "sell", "long", "short", "close", "flatten"]
    
    def __init__(self, raw_data: Dict[str, Any]):
        self.raw = raw_data
        self.timestamp_ms = int(datetime.now().timestamp() * 1000)
        
        # Required fields
        self.action = raw_data.get("action", "").lower().strip()
        self.symbol = raw_data.get("symbol", "")
        
        # Optional fields with defaults
        self.quantity = raw_data.get("quantity") or raw_data.get("qty")
        self.price = raw_data.get("price")
        self.stop_price = raw_data.get("stop_price") or raw_data.get("stop")
        self.order_type = raw_data.get("order_type", "market").lower()
        self.leverage = raw_data.get("leverage")
        self.message = raw_data.get("message", "")
        self.strategy = raw_data.get("strategy", "unknown")
        
        # Risk management
        self.risk_percent = raw_data.get("risk_percent")
        self.take_profit = raw_data.get("take_profit") or raw_data.get("tp")
        self.stop_loss = raw_data.get("stop_loss") or raw_data.get("sl")
    
    def validate(self) -> bool:
        """Validate the alert has required fields"""
        if not self.action:
            raise WebhookValidationError("Missing 'action' field")
        
        if self.action not in self.VALID_ACTIONS:
            raise WebhookValidationError(f"Invalid action: {self.action}. Must be one of: {self.VALID_ACTIONS}")
        
        if not self.symbol:
            raise WebhookValidationError("Missing 'symbol' field")
        
        # Normalize symbol (TradingView often sends BTCUSDT, we need BTCUSDT for Binance)
        self.symbol = self.symbol.upper().replace(".", "")
        
        return True
    
    def is_entry(self) -> bool:
        """Check if this is an entry signal"""
        return self.action in ["buy", "sell", "long", "short"]
    
    def is_exit(self) -> bool:
        """Check if this is an exit signal"""
        return self.action in ["close", "flatten"]
    
    def get_side(self) -> Optional[OrderSide]:
        """Convert action to OrderSide"""
        if self.action in ["buy", "long"]:
            return OrderSide.BUY
        elif self.action in ["sell", "short"]:
            return OrderSide.SELL
        return None
    
    def __repr__(self) -> str:
        return f"TradingViewAlert(action={self.action}, symbol={self.symbol}, qty={self.quantity})"


class WebhookHandler:
    """
    Handles TradingView webhook alerts and routes them to:
    - Dry-run engine (for testing)
    - Live trading (when explicitly enabled)
    """
    
    def __init__(self, config: Config, dry_run_engine: Optional[DryRunEngine] = None,
                 binance_client: Optional[BinanceApiClient] = None):
        self.config = config
        self.dry_run_engine = dry_run_engine
        self.binance_client = binance_client
        self.position_reader = PositionReader(binance_client, config) if binance_client else None
        
        self.logger = logging.getLogger("WebhookHandler")
        
        # Alert history for audit
        self.alert_history: list = []
        self.max_history = 1000
        
        self.logger.info("WebhookHandler initialized")
        self.logger.info(f"Dry-run mode: {self.dry_run_engine is not None}")
        self.logger.info(f"Live client: {self.binance_client is not None}")
    
    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature (if configured)"""
        if not secret:
            return True  # No secret configured, skip verification
        
        if not signature:
            raise WebhookAuthError("Missing signature header")
        
        expected = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    def parse_alert(self, payload: bytes) -> TradingViewAlert:
        """Parse and validate incoming alert"""
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise WebhookValidationError(f"Invalid JSON: {e}")
        
        alert = TradingViewAlert(data)
        alert.validate()
        
        return alert
    
    def calculate_position_size(self, alert: TradingViewAlert) -> Decimal:
        """
        Calculate position size based on:
        - Account balance (fetched from Binance)
        - Position allocation percent (default 50%)
        - Margin percent (default 30% = 3.33x leverage)
        - Current BTC price
        
        Formula: (Balance * Allocation%) / (Price * Margin%)
        Example: ($1000 * 50%) / ($50000 * 30%) = $500 / $15000 = 0.0333 BTC
        """
        # If alert explicitly specifies quantity, use it
        if alert.quantity:
            return Decimal(str(alert.quantity))
        
        try:
            # Fetch account balance
            account_info = self._get_account_balance()
            if not account_info:
                raise ValueError("Could not fetch account balance")
            
            balance_usdt = Decimal(str(account_info.get('availableBalance', 0)))
            if balance_usdt <= 0:
                raise ValueError(f"Invalid balance: {balance_usdt}")
            
            # Get current BTC price
            current_price = self._get_current_price(alert.symbol)
            if current_price <= 0:
                raise ValueError(f"Invalid price for {alert.symbol}")
            
            # Configuration
            allocation_percent = Decimal("0.50")  # 50% of balance
            margin_percent = Decimal("0.30")      # 30% margin = 3.33x leverage
            
            # Calculate position size
            position_value_usdt = balance_usdt * allocation_percent  # $500
            margin_required = position_value_usdt * margin_percent   # $150
            quantity_btc = position_value_usdt / current_price       # 0.01 BTC at $50k
            
            self.logger.info(
                f"Position sizing: Balance=${balance_usdt:.2f}, "
                f"Price=${current_price:.2f}, "
                f"PositionValue=${position_value_usdt:.2f}, "
                f"Margin=${margin_required:.2f}, "
                f"Quantity={quantity_btc:.6f} BTC"
            )
            
            return quantity_btc
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            # Fallback to minimum quantity
            return Decimal("0.001")  # 0.001 BTC minimum
    
    def _get_account_balance(self) -> Optional[Dict[str, Any]]:
        """Fetch USDT balance from Binance or dry-run engine"""
        if not self.binance_client:
            # Dry-run mode: return updated simulated balance from engine
            if self.dry_run_engine:
                balance = self.dry_run_engine.simulated_balance
                return {'availableBalance': str(balance)}
            return {'availableBalance': '1000.0'}
        
        try:
            resp = self.binance_client.get_account_info()
            if resp.get('success'):
                # Find USDT balance
                for asset in resp['data'].get('assets', []):
                    if asset.get('asset') == 'USDT':
                        return asset
                # Return total wallet balance
                return {'availableBalance': resp['data'].get('availableBalance', '0')}
        except Exception as e:
            self.logger.error(f"Failed to fetch account balance: {e}")
        
        return None
    
    def _get_current_price(self, symbol: str) -> Decimal:
        """Get current market price"""
        if not self.binance_client:
            # Return simulated price for dry-run
            return Decimal("50000.0")
        
        try:
            resp = self.binance_client.get_ticker_price(symbol)
            if resp.get('success'):
                return Decimal(str(resp['data']['price']))
        except Exception as e:
            self.logger.error(f"Failed to fetch price: {e}")
        
        return Decimal("0")
    
    def handle_alert(self, alert: TradingViewAlert) -> Dict[str, Any]:
        """
        Process a validated TradingView alert.
        Routes to dry-run or live based on configuration.
        """
        self.logger.info(f"Processing alert: {alert}")
        
        # Record alert
        self._record_alert(alert)
        
        # Determine execution path
        if self.config.paper_mode or self.dry_run_engine:
            return self._execute_dry_run(alert)
        else:
            return self._execute_live(alert)
    
    def _execute_dry_run(self, alert: TradingViewAlert) -> Dict[str, Any]:
        """Execute alert in dry-run mode"""
        if not self.dry_run_engine:
            return {
                "success": False,
                "error": "Dry-run engine not initialized",
                "mode": "dry_run"
            }
        
        try:
            if alert.is_exit():
                # Close position
                position = self.dry_run_engine.get_position(alert.symbol)
                if position and position.size > 0:
                    # Determine opposite side for closing
                    close_side = OrderSide.SELL if position.side.value == "LONG" else OrderSide.BUY
                    result = self.dry_run_engine.place_order(
                        symbol=alert.symbol,
                        side=close_side,
                        order_type=OrderType.MARKET,
                        quantity=position.size
                    )
                    self.logger.info(f"[DRY-RUN] Closed position: {result}")
                    return {"success": True, "mode": "dry_run", "action": "close", "result": result}
                else:
                    return {"success": True, "mode": "dry_run", "action": "close", "note": "No position to close"}
            
            elif alert.is_entry():
                # Open new position
                quantity = self.calculate_position_size(alert)
                side = alert.get_side()
                
                if not side:
                    return {"success": False, "error": "Could not determine order side", "mode": "dry_run"}
                
                # Map order type
                order_type_map = {
                    "market": OrderType.MARKET,
                    "limit": OrderType.LIMIT,
                    "stop": OrderType.STOP_MARKET,
                    "stop_market": OrderType.STOP_MARKET
                }
                order_type = order_type_map.get(alert.order_type, OrderType.MARKET)
                
                # Build order parameters
                order_params = {
                    "symbol": alert.symbol,
                    "side": side,
                    "order_type": order_type,
                    "quantity": quantity
                }
                
                if alert.price and order_type == OrderType.LIMIT:
                    order_params["price"] = Decimal(str(alert.price))
                
                if alert.stop_price and order_type in (OrderType.STOP_MARKET, OrderType.TAKE_PROFIT_MARKET):
                    order_params["stop_price"] = Decimal(str(alert.stop_price))
                
                result = self.dry_run_engine.place_order(**order_params)
                
                self.logger.info(f"[DRY-RUN] Entry order placed: {result}")
                return {"success": True, "mode": "dry_run", "action": "entry", "result": result}
            
            else:
                return {"success": False, "error": f"Unknown action: {alert.action}", "mode": "dry_run"}
                
        except Exception as e:
            self.logger.error(f"[DRY-RUN] Error executing alert: {e}")
            return {"success": False, "error": str(e), "mode": "dry_run"}
    
    def _execute_live(self, alert: TradingViewAlert) -> Dict[str, Any]:
        """Execute alert in live mode (placeholder - requires careful implementation)"""
        self.logger.warning("LIVE MODE NOT IMPLEMENTED - Use dry-run only")
        return {
            "success": False,
            "error": "Live trading not implemented. Set PAPER_MODE=true for dry-run.",
            "mode": "live"
        }
    
    def _record_alert(self, alert: TradingViewAlert):
        """Record alert to history"""
        self.alert_history.append({
            "timestamp_ms": alert.timestamp_ms,
            "action": alert.action,
            "symbol": alert.symbol,
            "quantity": alert.quantity,
            "raw": alert.raw
        })
        
        # Trim history if needed
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get handler status"""
        return {
            "dry_run_enabled": self.dry_run_engine is not None,
            "live_enabled": self.binance_client is not None and not self.config.paper_mode,
            "alerts_received": len(self.alert_history),
            "paper_mode": self.config.paper_mode,
            "symbol": self.config.symbol
        }


class WebhookHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for webhook server"""
    
    # Class-level webhook handler instance
    webhook_handler: Optional[WebhookHandler] = None
    webhook_secret: str = ""
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logging.getLogger("WebhookServer").info(format % args)
    
    def do_POST(self):
        """Handle POST requests (webhook alerts)"""
        if self.path not in ["/webhook", "/alert", "/"]:
            self._send_error(404, "Not found")
            return
        
        try:
            # Read payload
            content_length = int(self.headers.get('Content-Length', 0))
            payload = self.rfile.read(content_length)
            
            # Verify signature if secret is configured
            if self.webhook_secret:
                signature = self.headers.get('X-Signature') or self.headers.get('Signature')
                if not self.webhook_handler.verify_signature(payload, signature, self.webhook_secret):
                    self._send_error(401, "Invalid signature")
                    return
            
            # Parse and handle alert
            alert = self.webhook_handler.parse_alert(payload)
            result = self.webhook_handler.handle_alert(alert)
            
            # Send response
            self._send_json(200, result)
            
        except WebhookAuthError as e:
            self._send_error(401, str(e))
        except WebhookValidationError as e:
            self._send_error(400, str(e))
        except Exception as e:
            logging.getLogger("WebhookServer").error(f"Error handling webhook: {e}")
            self._send_error(500, f"Internal error: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests (status check)"""
        if self.path == "/status" or self.path == "/":
            status = self.webhook_handler.get_status() if self.webhook_handler else {"status": "not_initialized"}
            self._send_json(200, status)
        else:
            self._send_error(404, "Not found")
    
    def _send_json(self, code: int, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _send_error(self, code: int, message: str):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": message}).encode('utf-8'))


def create_webhook_server(config: Config, port: Optional[int] = None,
                          dry_run_engine: Optional[DryRunEngine] = None,
                          binance_client: Optional[BinanceApiClient] = None) -> HTTPServer:
    """
    Create and configure webhook HTTP server.
    
    Usage:
        server = create_webhook_server(config, dry_run_engine=engine)
        server.serve_forever()
    """
    handler = WebhookHandler(config, dry_run_engine=dry_run_engine, binance_client=binance_client)
    
    WebhookHTTPRequestHandler.webhook_handler = handler
    WebhookHTTPRequestHandler.webhook_secret = config.webhook_secret
    
    server_port = port or config.webhook_port
    server = HTTPServer(('0.0.0.0', server_port), WebhookHTTPRequestHandler)
    
    logging.getLogger("WebhookServer").info(f"Webhook server started on port {server_port}")
    logging.getLogger("WebhookServer").info(f"Endpoints: POST /webhook, GET /status")
    
    return server


# Example TradingView alert message format:
EXAMPLE_ALERT_FORMAT = """
{
    "action": "buy",
    "symbol": "BTCUSDT",
    "quantity": 0.01,
    "order_type": "market",
    "strategy": "ema_cross",
    "message": "EMA 12/26 bullish cross on 1h"
}
"""
