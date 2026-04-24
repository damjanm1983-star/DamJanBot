Binance API Client - Read-Only MVP
----------------------------------

What it does:
- Provides a minimal, raw-communication interface to Binance USDT-M Futures (BTCUSDT)
- Supports read-only endpoints:
  - get_account_info()
  - get_position_risk(symbol)
  - get_ticker_price(symbol)
  - get_exchange_info()
  - get_position_mode()

Key design notes:
- All requests are signed where required; non-signed for public endpoints.
- 5-second per-request timeout
- Up to 1 retry on recoverable failures (2s backoff)
- Secrets are never logged
- Logs differentiate TESTNET vs LIVE

Usage:
- Instantiate via:
  from BinanceApiClient import BinanceApiClient
  from config import Config

  cfg = Config()
  client = BinanceApiClient(cfg.binance_api_key, cfg.binance_secret_key, cfg.paper_mode)

- Call read-only endpoints as needed.

Testing tips:
- Ensure BINANCE_API_KEY and BINANCE_SECRET_KEY are exported in the environment.
- Set PAPER_MODE to true for testnet before testing account info and positionRisk.
