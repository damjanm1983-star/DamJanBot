import sys
import os
import time
from decimal import Decimal

# Ensure project root is on sys.path so imports work from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from position_reader import PositionReader, PositionState


class MockBinanceApiClient:
    """Lightweight mock that returns canned responses for testing."""

    def __init__(self, response=None):
        self._response = response

    def get_position_risk(self, symbol):
        if self._response is not None:
            return self._response
        return {
            "success": True,
            "data": [
                {
                    "symbol": symbol,
                    "positionAmt": "0.0100000",
                    "entryPrice": "65000.00000",
                    "leverage": "3",
                    "marginType": "isolated",
                    "positionSide": "BOTH",
                }
            ],
            "timestamp": int(time.time() * 1000),
        }


class MockConfig:
    symbol = "BTCUSDT"
    paper_mode = True


def test_long_position():
    client = MockBinanceApiClient()
    reader = PositionReader(client, MockConfig())
    state = reader.read_position("BTCUSDT")
    assert state.is_reliable is True, f"Expected reliable, got error: {state.error}"
    assert state.state == "LONG", f"Expected LONG, got {state.state}"
    assert state.size == Decimal("0.01"), f"Expected 0.01, got {state.size}"
    assert state.entry_price == Decimal("65000"), f"Expected 65000, got {state.entry_price}"
    print("PASS: test_long_position")


def test_short_position():
    resp = {
        "success": True,
        "data": [
            {
                "symbol": "BTCUSDT",
                "positionAmt": "-0.0050000",
                "entryPrice": "70000.00000",
                "leverage": "5",
                "marginType": "isolated",
                "positionSide": "BOTH",
            }
        ],
        "timestamp": int(time.time() * 1000),
    }
    client = MockBinanceApiClient(response=resp)
    reader = PositionReader(client, MockConfig())
    state = reader.read_position("BTCUSDT")
    assert state.is_reliable is True, f"Expected reliable, got error: {state.error}"
    assert state.state == "SHORT", f"Expected SHORT, got {state.state}"
    assert state.size == Decimal("0.005"), f"Expected 0.005, got {state.size}"
    assert state.entry_price == Decimal("70000"), f"Expected 70000, got {state.entry_price}"
    print("PASS: test_short_position")


def test_flat_position():
    resp = {
        "success": True,
        "data": [
            {
                "symbol": "BTCUSDT",
                "positionAmt": "0.0000000",
                "entryPrice": "0.00000",
                "leverage": "3",
                "marginType": "isolated",
                "positionSide": "BOTH",
            }
        ],
        "timestamp": int(time.time() * 1000),
    }
    client = MockBinanceApiClient(response=resp)
    reader = PositionReader(client, MockConfig())
    state = reader.read_position("BTCUSDT")
    assert state.is_reliable is True, f"Expected reliable, got error: {state.error}"
    assert state.state == "FLAT", f"Expected FLAT, got {state.state}"
    assert state.size == Decimal("0"), f"Expected 0, got {state.size}"
    assert state.entry_price is None, f"Expected None, got {state.entry_price}"
    print("PASS: test_flat_position")


def test_api_failure():
    resp = {"success": False, "data": None, "timestamp": int(time.time() * 1000)}
    client = MockBinanceApiClient(response=resp)
    reader = PositionReader(client, MockConfig())
    state = reader.read_position("BTCUSDT")
    assert state.is_reliable is False, "Expected unreliable state on API failure"
    assert state.state == "FLAT", f"Expected FLAT on failure, got {state.state}"
    assert state.size == Decimal("0"), f"Expected 0, got {state.size}"
    assert state.entry_price is None, f"Expected None, got {state.entry_price}"
    print("PASS: test_api_failure")


def test_missing_fields():
    resp = {
        "success": True,
        "data": [{"symbol": "BTCUSDT"}],
        "timestamp": int(time.time() * 1000),
    }
    client = MockBinanceApiClient(response=resp)
    reader = PositionReader(client, MockConfig())
    state = reader.read_position("BTCUSDT")
    assert state.is_reliable is False, "Expected unreliable when fields missing"
    print("PASS: test_missing_fields")


if __name__ == "__main__":
    test_long_position()
    test_short_position()
    test_flat_position()
    test_api_failure()
    test_missing_fields()
    print("\nAll Position Reader tests passed.")
