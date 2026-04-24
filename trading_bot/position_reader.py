from __future__ import annotations

import logging
import time
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any

from binance_api_client import BinanceApiClient


class PositionState:
    def __init__(
        self,
        symbol: str,
        state: str,
        size: Decimal,
        entry_price: Optional[Decimal],
        fetched_at_utc_ms: int,
        is_reliable: bool = True,
        error: Optional[str] = None,
        margin_type: Optional[str] = None,
        leverage: Optional[int] = None,
        raw_position_amt: Optional[str] = None,
    ):
        self.symbol = symbol
        self.state = state
        self.size = size
        self.entry_price = entry_price
        self.fetched_at_utc_ms = fetched_at_utc_ms
        self.is_reliable = is_reliable
        self.error = error
        self.margin_type = margin_type
        self.leverage = leverage
        self.raw_position_amt = raw_position_amt

    def __repr__(self) -> str:
        if not self.is_reliable:
            return f"PositionState(symbol='{self.symbol}', reliable=False, error='{self.error}')"
        return (
            f"PositionState(symbol='{self.symbol}', state='{self.state}', "
            f"size={self.size}, entry_price={self.entry_price}, "
            f"fetched_at={self.fetched_at_utc_ms})"
        )


class PositionReader:
    """
    Reads BinanceApiClient position_risk data and converts it into a
    standardised PositionState.  Strictly read-only — no orders, no
    webhooks, no execution logic.
    """

    def __init__(self, binance_client: BinanceApiClient, config):
        self.client = binance_client
        self.config = config
        self.logger = logging.getLogger("PositionReader")
        if not self.logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            )

    def read_position(self, symbol: str) -> PositionState:
        try:
            resp = self.client.get_position_risk(symbol=symbol)

            if not resp.get("success"):
                return PositionState(
                    symbol, "FLAT", Decimal(0), None,
                    int(time.time() * 1000), False, "API failed",
                )

            data = resp.get("data")
            if not isinstance(data, list):
                return PositionState(
                    symbol, "FLAT", Decimal(0), None,
                    int(time.time() * 1000), False, "Bad response",
                )

            symbol_position = None
            for pos in data:
                if pos.get("symbol") == symbol:
                    symbol_position = pos
                    break

            if symbol_position is None:
                return PositionState(
                    symbol, "FLAT", Decimal(0), None,
                    resp.get("timestamp", int(time.time() * 1000)), True,
                )

            position_amt_str = symbol_position.get("positionAmt")
            entry_price_str = symbol_position.get("entryPrice")
            raw_position_amt = position_amt_str

            if position_amt_str is None or entry_price_str is None:
                return PositionState(
                    symbol, "FLAT", Decimal(0), None,
                    resp.get("timestamp", int(time.time() * 1000)),
                    False, "Missing positionAmt or entryPrice",
                    raw_position_amt=raw_position_amt,
                )

            try:
                position_amt_decimal = Decimal(position_amt_str)
            except InvalidOperation:
                return PositionState(
                    symbol, "FLAT", Decimal(0), None,
                    resp.get("timestamp", int(time.time() * 1000)),
                    False, f"Invalid positionAmt format: {position_amt_str}",
                    raw_position_amt=raw_position_amt,
                )

            current_state = "FLAT"
            position_size = Decimal(0)
            entry_price = None

            if abs(position_amt_decimal) > Decimal("1e-12"):
                current_state = "LONG" if position_amt_decimal > 0 else "SHORT"
                position_size = abs(position_amt_decimal)
                try:
                    entry_price = Decimal(entry_price_str)
                except InvalidOperation:
                    return PositionState(
                        symbol, "FLAT", Decimal(0), None,
                        resp.get("timestamp", int(time.time() * 1000)),
                        False, f"Invalid entryPrice format: {entry_price_str}",
                        raw_position_amt=raw_position_amt,
                    )

            position_side = symbol_position.get("positionSide")
            if position_side != "BOTH":
                self.logger.warning(
                    "Unexpected positionSide '%s' for %s. Expected 'BOTH' (One-Way mode).",
                    position_side, symbol,
                )

            return PositionState(
                symbol=symbol,
                state=current_state,
                size=position_size,
                entry_price=entry_price,
                fetched_at_utc_ms=resp.get("timestamp", int(time.time() * 1000)),
                is_reliable=True,
                raw_position_amt=raw_position_amt,
                margin_type=symbol_position.get("marginType"),
                leverage=(
                    int(symbol_position.get("leverage"))
                    if symbol_position.get("leverage")
                    else None
                ),
            )

        except Exception as e:
            self.logger.error("Error reading position for %s: %s", symbol, e)
            return PositionState(
                symbol, "FLAT", Decimal(0), None,
                int(time.time() * 1000), False, error=str(e),
            )
