import os
from BinanceApiClient import BinanceApiClient
from config import Config


def main():
    cfg = Config()
    client = BinanceApiClient(
        api_key=cfg.binance_api_key,
        api_secret=cfg.binance_secret_key,
        paper_mode=cfg.paper_mode,
        max_retries=1
    )
    symbol = cfg.symbol

    print("Testing get_account_info...")
    print(client.get_account_info())

    print("Testing get_position_risk...")
    print(client.get_position_risk(symbol))

    print("Testing get_ticker_price...")
    print(client.get_ticker_price(symbol))

    print("Testing get_exchange_info...")
    print(client.get_exchange_info())

    print("Testing get_position_mode...")
    print(client.get_position_mode())


if __name__ == "__main__":
    main()
