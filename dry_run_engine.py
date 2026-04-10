"""
Dry-Run Trading Engine for Binance Futures
Simulates trades without real execution. Tracks simulated positions, PnL, and trade history.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from position_reader import PositionReader, PositionState


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"


class PositionSide(Enum):
    BOTH = "BOTH"  # One-way mode
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class SimulatedOrder:
    """Represents a simulated order"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None  # For limit orders
    stop_price: Optional[Decimal] = None  # For stop orders
    status: str = "PENDING"  # PENDING, FILLED, CANCELLED, REJECTED
    filled_qty: Decimal = field(default_factory=lambda: Decimal("0"))
    avg_fill_price: Optional[Decimal] = None
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    filled_at_ms: Optional[int] = None
    commission: Decimal = field(default_factory=lambda: Decimal("0"))
    commission_asset: str = "USDT"
    reject_reason: Optional[str] = None


@dataclass
class SimulatedTrade:
    """Represents a filled trade (position change)"""
    trade_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    realized_pnl: Decimal
    commission: Decimal
    position_after: Decimal  # Position size after trade
    timestamp_ms: int
    order_id: str


@dataclass
class SimulatedPosition:
    """Tracks a simulated position"""
    symbol: str
    side: Optional[PositionSide] = None  # LONG, SHORT, or None (flat)
    size: Decimal = field(default_factory=lambda: Decimal("0"))
    entry_price: Optional[Decimal] = None
    unrealized_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    realized_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    total_commissions: Decimal = field(default_factory=lambda: Decimal("0"))
    trades_count: int = 0
    opened_at_ms: Optional[int] = None
    last_updated_ms: int = field(default_factory=lambda: int(time.time() * 1000))


class DryRunEngine:
    """
    Simulates Binance Futures trading without real execution.
    
    Features:
    - Simulates market, limit, and stop orders
    - Tracks simulated positions and PnL
    - Maintains trade history
    - Validates risk limits
    - Logs all activity for review
    """
    
    COMMISSION_RATE = Decimal("0.0005")  # 0.05% taker fee (Binance futures)
    PRICE_SLIPPAGE = Decimal("0.0001")  # 0.01% slippage simulation
    
    def __init__(self, config, position_reader: Optional[PositionReader] = None):
        self.config = config
        self.position_reader = position_reader
        self.logger = logging.getLogger("DryRunEngine")
        
        # Simulated state
        self.positions: Dict[str, SimulatedPosition] = {}
        self.orders: Dict[str, SimulatedOrder] = {}
        self.trades: List[SimulatedTrade] = []
        self.order_counter = 0
        self.trade_counter = 0
        
        # Initial balance simulation
        self.simulated_balance = Decimal("10000.0")  # 10k USDT starting balance
        self.margin_used = Decimal("0")
        
        self.logger.info("DryRunEngine initialized")
        self.logger.info(f"Starting simulated balance: {self.simulated_balance} USDT")
        self.logger.info(f"Commission rate: {self.COMMISSION_RATE * 100}%")
    
    def _generate_order_id(self) -> str:
        self.order_counter += 1
        return f"DRY_{int(time.time() * 1000)}_{self.order_counter}"
    
    def _generate_trade_id(self) -> str:
        self.trade_counter += 1
        return f"TRADE_{int(time.time() * 1000)}_{self.trade_counter}"
    
    def _get_current_price(self, symbol: str) -> Decimal:
        """Get current market price (would integrate with price feed in real use)"""
        # In real implementation, fetch from Binance or cache
        # For now, return a placeholder that should be updated
        if self.position_reader and hasattr(self.position_reader, 'client'):
            try:
                resp = self.position_reader.client.get_ticker_price(symbol)
                if resp.get("success"):
                    return Decimal(str(resp["data"]["price"]))
            except Exception as e:
                self.logger.warning(f"Could not fetch price for {symbol}: {e}")
        return Decimal("0")
    
    def _apply_slippage(self, price: Decimal, side: OrderSide) -> Decimal:
        """Apply simulated slippage to price"""
        slippage = price * self.PRICE_SLIPPAGE
        if side == OrderSide.BUY:
            return price + slippage
        else:
            return price - slippage
    
    def _calculate_commission(self, notional_value: Decimal) -> Decimal:
        """Calculate trading commission"""
        return notional_value * self.COMMISSION_RATE
    
    def _get_or_create_position(self, symbol: str) -> SimulatedPosition:
        """Get existing position or create new flat position"""
        if symbol not in self.positions:
            self.positions[symbol] = SimulatedPosition(symbol=symbol)
        return self.positions[symbol]
    
    def _update_position(self, symbol: str, side: OrderSide, qty: Decimal, 
                         price: Decimal, commission: Decimal) -> Dict[str, Any]:
        """
        Update position after a fill. Returns realized PnL and position info.
        """
        position = self._get_or_create_position(symbol)
        
        # Determine trade direction relative to current position
        is_buy = side == OrderSide.BUY
        current_size = position.size
        
        realized_pnl = Decimal("0")
        
        if current_size == 0:
            # Opening new position
            position.side = PositionSide.LONG if is_buy else PositionSide.SHORT
            position.size = qty
            position.entry_price = price
            position.opened_at_ms = int(time.time() * 1000)
            
        elif (position.side == PositionSide.LONG and is_buy) or \
             (position.side == PositionSide.SHORT and not is_buy):
            # Adding to existing position (pyramiding)
            # Calculate new average entry price
            total_value = (position.size * position.entry_price) + (qty * price)
            position.size += qty
            position.entry_price = total_value / position.size
            
        else:
            # Reducing or flipping position
            if qty < current_size:
                # Partial close
                if position.side == PositionSide.LONG:
                    realized_pnl = (price - position.entry_price) * qty
                else:
                    realized_pnl = (position.entry_price - price) * qty
                position.size -= qty
                
            elif qty == current_size:
                # Full close
                if position.side == PositionSide.LONG:
                    realized_pnl = (price - position.entry_price) * qty
                else:
                    realized_pnl = (position.entry_price - price) * qty
                position.size = Decimal("0")
                position.side = None
                position.entry_price = None
                
            else:
                # Flip position (close current + open opposite)
                if position.side == PositionSide.LONG:
                    realized_pnl = (price - position.entry_price) * current_size
                else:
                    realized_pnl = (position.entry_price - price) * current_size
                
                remaining = qty - current_size
                position.side = PositionSide.SHORT if is_buy else PositionSide.LONG
                position.size = remaining
                position.entry_price = price
                position.opened_at_ms = int(time.time() * 1000)
        
        position.realized_pnl += realized_pnl
        position.total_commissions += commission
        position.trades_count += 1
        position.last_updated_ms = int(time.time() * 1000)
        
        # Update unrealized PnL
        current_price = self._get_current_price(symbol)
        if position.size > 0 and position.entry_price:
            if position.side == PositionSide.LONG:
                position.unrealized_pnl = (current_price - position.entry_price) * position.size
            else:
                position.unrealized_pnl = (position.entry_price - current_price) * position.size
        else:
            position.unrealized_pnl = Decimal("0")
        
        return {
            "realized_pnl": realized_pnl,
            "position": position,
            "was_flip": qty > current_size and current_size > 0
        }
    
    def place_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                    quantity: Decimal, price: Optional[Decimal] = None,
                    stop_price: Optional[Decimal] = None,
                    market_price: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Place a simulated order.
        
        For dry-run, market orders fill immediately with slippage.
        Limit orders fill if price is acceptable.
        
        Args:
            market_price: Optional price to use for market orders (from alert)
        """
        order_id = self._generate_order_id()
        
        # Validate inputs
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive"}
        
        if order_type == OrderType.LIMIT and price is None:
            return {"success": False, "error": "Limit order requires price"}
        
        if order_type in (OrderType.STOP_MARKET, OrderType.TAKE_PROFIT_MARKET) and stop_price is None:
            return {"success": False, "error": "Stop orders require stop_price"}
        
        # Create order
        order = SimulatedOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status="PENDING"
        )
        
        self.orders[order_id] = order
        
        # Simulate fill logic
        # Use provided market_price if available, otherwise get current price
        if market_price and market_price > 0:
            current_price = market_price
        else:
            current_price = self._get_current_price(symbol)
        
        if order_type == OrderType.MARKET:
            # Market orders fill immediately with slippage
            fill_price = self._apply_slippage(current_price, side)
            self._fill_order(order, fill_price)
            
        elif order_type == OrderType.LIMIT:
            # For dry-run, fill limit orders immediately if price is "acceptable"
            # In reality, this would wait for market to hit the limit
            if (side == OrderSide.BUY and price >= current_price) or \
               (side == OrderSide.SELL and price <= current_price):
                self._fill_order(order, price)
            else:
                order.status = "OPEN"
                self.logger.info(f"Limit order {order_id} placed (not filled yet)")
                
        elif order_type == OrderType.STOP_MARKET:
            # For dry-run, simulate stop trigger
            if (side == OrderSide.BUY and current_price >= stop_price) or \
               (side == OrderSide.SELL and current_price <= stop_price):
                fill_price = self._apply_slippage(current_price, side)
                self._fill_order(order, fill_price)
            else:
                order.status = "OPEN"
                self.logger.info(f"Stop order {order_id} placed (not triggered yet)")
        
        return {
            "success": True,
            "order_id": order_id,
            "status": order.status,
            "simulated": True
        }
    
    def _fill_order(self, order: SimulatedOrder, fill_price: Decimal):
        """Fill an order and update position"""
        order.status = "FILLED"
        order.filled_qty = order.quantity
        order.avg_fill_price = fill_price
        order.filled_at_ms = int(time.time() * 1000)
        
        # Calculate commission
        notional = fill_price * order.quantity
        commission = self._calculate_commission(notional)
        order.commission = commission
        
        # Update position with the fill price as entry price
        position_update = self._update_position(
            order.symbol, 
            order.side, 
            order.quantity, 
            fill_price,
            commission
        )
        
        # Ensure entry price is set for new positions
        position = self.positions.get(order.symbol)
        if position and position.size > 0 and not position.entry_price:
            position.entry_price = fill_price
        
        # Record trade
        trade = SimulatedTrade(
            trade_id=self._generate_trade_id(),
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            realized_pnl=position_update["realized_pnl"],
            commission=commission,
            position_after=position_update["position"].size,
            timestamp_ms=order.filled_at_ms,
            order_id=order.order_id
        )
        self.trades.append(trade)
        
        self.logger.info(
            f"[DRY-RUN] Order {order.order_id} FILLED: "
            f"{order.side.value} {order.quantity} {order.symbol} @ {fill_price} "
            f"(PnL: {position_update['realized_pnl']:.4f}, Comm: {commission:.4f})"
        )
    
    def get_position(self, symbol: str) -> Optional[SimulatedPosition]:
        """Get simulated position for symbol"""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> List[SimulatedPosition]:
        """Get all simulated positions"""
        return list(self.positions.values())
    
    def get_order(self, order_id: str) -> Optional[SimulatedOrder]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_trade_history(self, symbol: Optional[str] = None) -> List[SimulatedTrade]:
        """Get trade history, optionally filtered by symbol"""
        if symbol:
            return [t for t in self.trades if t.symbol == symbol]
        return self.trades
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        total_realized_pnl = sum(p.realized_pnl for p in self.positions.values())
        total_unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        total_commissions = sum(p.total_commissions for p in self.positions.values())
        total_trades = sum(p.trades_count for p in self.positions.values())
        
        winning_trades = len([t for t in self.trades if t.realized_pnl > 0])
        losing_trades = len([t for t in self.trades if t.realized_pnl < 0])
        
        return {
            "simulated_balance": self.simulated_balance,
            "total_realized_pnl": total_realized_pnl,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_commissions": total_commissions,
            "net_pnl": total_realized_pnl - total_commissions,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
            "open_positions": len([p for p in self.positions.values() if p.size > 0]),
            "timestamp": int(time.time() * 1000)
        }
    
    def export_session_log(self, filepath: Optional[str] = None) -> str:
        """Export full session log to JSON"""
        session_data = {
            "session_start": min((t.timestamp_ms for t in self.trades), default=int(time.time() * 1000)),
            "session_end": int(time.time() * 1000),
            "config": {
                "starting_balance": str(self.simulated_balance),
                "commission_rate": str(self.COMMISSION_RATE),
            },
            "performance": self.get_performance_summary(),
            "positions": [
                {
                    "symbol": p.symbol,
                    "side": p.side.value if p.side else None,
                    "size": str(p.size),
                    "entry_price": str(p.entry_price) if p.entry_price else None,
                    "realized_pnl": str(p.realized_pnl),
                    "unrealized_pnl": str(p.unrealized_pnl),
                    "trades_count": p.trades_count
                }
                for p in self.positions.values()
            ],
            "trades": [
                {
                    "trade_id": t.trade_id,
                    "symbol": t.symbol,
                    "side": t.side.value,
                    "quantity": str(t.quantity),
                    "price": str(t.price),
                    "realized_pnl": str(t.realized_pnl),
                    "commission": str(t.commission),
                    "timestamp_ms": t.timestamp_ms
                }
                for t in self.trades
            ]
        }
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            self.logger.info(f"Session log exported to {filepath}")
        
        return json.dumps(session_data, indent=2)


# Convenience functions for common operations

def create_market_order(engine: DryRunEngine, symbol: str, side: str, 
                        quantity: float) -> Dict[str, Any]:
    """Helper to create a market order"""
    return engine.place_order(
        symbol=symbol,
        side=OrderSide(side.upper()),
        order_type=OrderType.MARKET,
        quantity=Decimal(str(quantity))
    )


def create_limit_order(engine: DryRunEngine, symbol: str, side: str,
                       quantity: float, price: float) -> Dict[str, Any]:
    """Helper to create a limit order"""
    return engine.place_order(
        symbol=symbol,
        side=OrderSide(side.upper()),
        order_type=OrderType.LIMIT,
        quantity=Decimal(str(quantity)),
        price=Decimal(str(price))
    )


def create_stop_order(engine: DryRunEngine, symbol: str, side: str,
                      quantity: float, stop_price: float) -> Dict[str, Any]:
    """Helper to create a stop-market order"""
    return engine.place_order(
        symbol=symbol,
        side=OrderSide(side.upper()),
        order_type=OrderType.STOP_MARKET,
        quantity=Decimal(str(quantity)),
        stop_price=Decimal(str(stop_price))
    )
