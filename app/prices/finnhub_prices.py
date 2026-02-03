# app/prices/finnhub_prices.py
import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

FINNHUB_BASE = "https://finnhub.io/api/v1"

class FinnhubPriceClient:
    def __init__(self, api_key: str | None = None, timeout_s: int = 10):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY is not set")
        self.timeout_s = timeout_s

    def daily_closes(self, symbol: str, lookback_days: int = 730) -> pd.Series:
        """
        Returns a pandas Series of daily close prices indexed by date.
        Uses Finnhub /stock/candle with resolution=D.
        """
        now = datetime.now(timezone.utc)
        frm = now - timedelta(days=lookback_days)

        params = {
            "symbol": symbol,
            "resolution": "D",
            "from": int(frm.timestamp()),
            "to": int(now.timestamp()),
            "token": self.api_key,
        }
        url = f"{FINNHUB_BASE}/stock/candle"
        r = requests.get(url, params=params, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()

        # Finnhub returns {"s":"ok","t":[...],"c":[...],...}
        if data.get("s") != "ok":
            # could be "no_data"
            return pd.Series(dtype=float)

        t = data.get("t", [])
        c = data.get("c", [])
        if not t or not c or len(t) != len(c):
            return pd.Series(dtype=float)

        idx = pd.to_datetime(t, unit="s", utc=True).tz_convert(None)
        closes = pd.Series(c, index=idx, name="Close").astype(float)

        # Remove any duplicates and sort
        closes = closes[~closes.index.duplicated(keep="last")].sort_index()
        return closes
