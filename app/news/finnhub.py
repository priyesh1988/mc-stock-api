import os
import requests
from datetime import date

FINNHUB_BASE = "https://finnhub.io/api/v1"


class FinnhubNewsClient:
    """
    Uses Finnhub Company News endpoint:
    GET /company-news?symbol=...&from=YYYY-MM-DD&to=YYYY-MM-DD&token=...
    """

    def __init__(self, api_key: str | None = None, timeout_s: int = 10):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("FINNHUB_API_KEY is not set")
        self.timeout_s = timeout_s

    def company_news(self, symbol: str, d: date) -> list[dict]:
        dstr = d.strftime("%Y-%m-%d")
        url = f"{FINNHUB_BASE}/company-news"
        params = {
            "symbol": symbol,
            "from": dstr,
            "to": dstr,
            "token": self.api_key,
        }
        r = requests.get(url, params=params, timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else []
