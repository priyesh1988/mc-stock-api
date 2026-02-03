import os
import requests
import pandas as pd

ALPHA_BASE = "https://www.alphavantage.co/query"

class AlphaVantagePriceClient:
    def __init__(self, api_key: str | None = None, timeout_s: int = 15):
        self.api_key = api_key or os.getenv("ALPHAVANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("ALPHAVANTAGE_API_KEY is not set")
        self.timeout_s = timeout_s

    def daily_closes(self, symbol: str, full: bool = False) -> pd.Series:
        """
        FREE endpoint: TIME_SERIES_DAILY
        Returns daily close prices as a pandas Series indexed by date.
        """
        params = {
            "function": "TIME_SERIES_DAILY",   # <-- free
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "full" if full else "compact",
        }
        r = requests.get(ALPHA_BASE, params=params, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()

        for k in ("Error Message", "Note", "Information"):
            if k in data:
                raise RuntimeError(f"Alpha Vantage response '{k}': {data[k]}")

        ts = data.get("Time Series (Daily)")
        if not ts:
            raise RuntimeError(f"Alpha Vantage unexpected payload keys: {list(data.keys())}")

        rows = []
        for d, fields in ts.items():
            close_str = fields.get("4. close")  # present in TIME_SERIES_DAILY
            if close_str is None:
                continue
            rows.append((d, float(close_str)))

        if not rows:
            raise RuntimeError("Alpha Vantage returned Time Series but no close values.")

        idx = pd.to_datetime([d for d, _ in rows])
        closes = pd.Series([c for _, c in rows], index=idx, name="Close").sort_index()
        return closes
