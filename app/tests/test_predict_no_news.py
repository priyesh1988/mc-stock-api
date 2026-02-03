import pandas as pd
import numpy as np

def _fake_price_df(n=120, start="2024-01-01"):
    idx = pd.date_range(start=start, periods=n, freq="B")
    # simple random-ish walk
    close = 100 + np.cumsum(np.random.default_rng(1).normal(0, 1, size=n))
    return pd.DataFrame({"Close": close}, index=idx)

def test_predict_no_news_fallback(client, monkeypatch):
    # Mock yfinance download
    import yfinance as yf
    monkeypatch.setattr(yf, "download", lambda *args, **kwargs: _fake_price_df())

    # Mock Finnhub client to raise (simulate provider down)
    from app.news import finnhub
    class _Boom:
        def __init__(self, *a, **k): pass
        def company_news(self, *a, **k): raise RuntimeError("down")
    monkeypatch.setattr(finnhub, "FinnhubNewsClient", _Boom)

    r = client.get("/predict?symbol=AAPL&n_sims=5000&alpha=2.0")
    assert r.status_code == 200
    j = r.json()

    assert j["symbol"] == "AAPL"
    assert j["news_sentiment"] == 0.0
    assert j["news_article_count"] == 0
    assert 0.0 <= j["p_up"] <= 1.0
    assert len(j["range_90"]) == 2
