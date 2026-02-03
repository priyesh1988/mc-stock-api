import pandas as pd
import numpy as np

def _fake_price_df(n=252, start="2024-01-01"):
    idx = pd.date_range(start=start, periods=n, freq="B")
    # returns with slight negative drift so weighting effect is visible
    rng = np.random.default_rng(2)
    rets = rng.normal(-0.0005, 0.01, size=n)
    close = 100 * np.cumprod(1 + rets)
    return pd.DataFrame({"Close": close}, index=idx)

def test_predict_positive_news_shifts_distribution(client, monkeypatch):
    import yfinance as yf
    monkeypatch.setattr(yf, "download", lambda *args, **kwargs: _fake_price_df())

    # Mock Finnhub news with strongly positive headlines
    from app.news import finnhub
    class _FakeClient:
        def __init__(self, *a, **k): pass
        def company_news(self, symbol, d):
            return [
                {"headline": "Company beats earnings expectations massively", "summary": "Strong growth and guidance raised"},
                {"headline": "Analysts upgrade stock after great results", "summary": "Multiple upgrades and bullish sentiment"},
            ]
    monkeypatch.setattr(finnhub, "FinnhubNewsClient", _FakeClient)

    # Run with alpha=0 (no tilt) vs alpha high (tilt)
    r0 = client.get("/predict?symbol=TEST&n_sims=20000&alpha=0&seed=7&refresh_news=true")
    assert r0.status_code == 200
    j0 = r0.json()

    r1 = client.get("/predict?symbol=TEST&n_sims=20000&alpha=6&seed=7&refresh_news=true")
    assert r1.status_code == 200
    j1 = r1.json()

    # With positive sentiment + higher alpha, p_up should generally increase vs no-tilt baseline
    # (Not guaranteed in every random dataset, but with our constructed drift it should.)
    assert j1["news_sentiment"] > 0
    assert j1["p_up"] >= j0["p_up"]
