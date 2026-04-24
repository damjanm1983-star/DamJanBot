import os
import time
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode
from typing import Any, Dict, Optional

# Logger setup
logger = logging.getLogger("BinanceApiClient")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

# Exceptions
class BinanceAPIError(Exception):
    pass

class BinanceAuthError(BinanceAPIError):
    pass

class BinanceRateLimitError(BinanceAPIError):
    pass

class BinanceServerError(BinanceAPIError):
    pass

class BinanceConnectionError(BinanceAPIError):
    pass

class BinanceValidationError(BinanceAPIError):
    pass

class BinanceApiClient:
    """
    Read-only MVP client for Binance USDT-M Futures (BTCUSDT).
    - Base URLs switch by PAPER_MODE
    - Authenticated endpoints use HMAC-SHA256 signature
    - 5s per-request timeout
    - Single retry for recoverable errors (2s backoff)
    - Returns structured dicts; never raw HTTP
    - Logging hygiene: no secrets logged
    """
    def __init__(self, api_key: str, api_secret: str, paper_mode: bool,
                 request_timeout: int = 5, retry_delay: int = 2, max_retries: int = 1):
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper_mode = paper_mode
        self.request_timeout = request_timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries

        self.base_url = "https://testnet.binancefuture.com" if self.paper_mode else "https://fapi.binance.com"
        self.mode_str = "TESTNET" if self.paper_mode else "LIVE"

        logger.info(f"BinanceApiClient initialized in {self.mode_str} mode. Base URL: {self.base_url}")
        logger.info("BINANCE_API keys loaded successfully.")

        self._exchange_info = None

    def _get_signed_headers_and_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key or not self.api_secret:
            raise BinanceAuthError("API key/secret not configured.")
        params = dict(params)  # copy
        params["timestamp"] = int(time.time() * 1000)
        sorted_params = urlencode(sorted(params.items()))
        signature = hmac.new(self.api_secret.encode("utf-8"), sorted_params.encode("utf-8"), hashlib.sha256).hexdigest()
        params["signature"] = signature
        headers = {"X-MBX-APIKEY": self.api_key}
        return {"headers": headers, "params": params}

    def _make_request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, needs_auth: bool = True) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {}
        request_params = params or {}

        if needs_auth:
            sign_res = self._get_signed_headers_and_params(request_params)
            headers = sign_res["headers"]
            request_params = sign_res["params"]

        logger.info(f"[{self.mode_str}] {method} {path} called (auth={needs_auth})")

        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.request(
                    method,
                    url,
                    headers=headers,
                    params=request_params if method.upper() == "GET" else None,
                    json=request_params if method.upper() != "GET" else None,
                    timeout=self.request_timeout
                )

                status = resp.status_code

                if status == 200:
                    try:
                        data = resp.json()
                        return {"success": True, "data": data, "timestamp": int(time.time() * 1000)}
                    except ValueError:
                        raise BinanceValidationError("Invalid JSON in response")

                if status == 429:
                    logger.warning(f"[{self.mode_str}] 429 Rate limit on {path}, attempt {attempt+1}")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    raise BinanceRateLimitError("429 after retry")

                if status >= 500:
                    logger.error(f"[{self.mode_str}] Binance server error {status} on {path}")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    raise BinanceServerError(f"Server error {status}")

                if status >= 400:
                    try:
                        data = resp.json()
                        code = data.get("code")
                        msg = data.get("msg", resp.text)
                        if status in (401, 403):
                            raise BinanceAuthError(msg, error_code=code, raw_response=resp.text)
                        else:
                            raise BinanceValidationError(msg, error_code=code, raw_response=resp.text)
                    except ValueError:
                        raise BinanceValidationError(f"HTTP {status}: {resp.text}")

            except requests.Timeout:
                logger.error(f"[{self.mode_str}] Timeout on {path}, attempt {attempt+1}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                raise BinanceConnectionError("Request timed out (exhausted retries)")

            except requests.ConnectionError as e:
                logger.error(f"[{self.mode_str}] Connection error on {path}: {e}, attempt {attempt+1}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                raise BinanceConnectionError(f"Connection error: {e}")

            except Exception as e:
                logger.error(f"[{self.mode_str}] Unexpected error on {path}: {e}, attempt {attempt+1}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                raise BinanceAPIError(f"Unexpected error: {e}")

        raise BinanceAPIError(f"Request failed after {self.max_retries+1} attempts for {path}")

    # MVP Read-Only Endpoints
    def get_account_info(self) -> Dict[str, Any]:
        path = "/fapi/v2/account"
        return self._make_request("GET", path, needs_auth=True)

    def get_position_risk(self, symbol: str) -> Dict[str, Any]:
        path = "/fapi/v2/positionRisk"
        return self._make_request("GET", path, params={"symbol": symbol}, needs_auth=True)

    def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        path = "/fapi/v1/ticker/price"
        return self._make_request("GET", path, params={"symbol": symbol}, needs_auth=False)

    def get_exchange_info(self) -> Dict[str, Any]:
        path = "/fapi/v1/exchangeInfo"
        return self._make_request("GET", path, needs_auth=False)

    def get_position_mode(self) -> Dict[str, Any]:
        path = "/fapi/v1/positionSide/dual"
        return self._make_request("GET", path, needs_auth=True)

# End of file

