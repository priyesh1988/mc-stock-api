from fastapi import FastAPI, Query, HTTPException
from datetime import date

from app.prices.alphavantage_prices import AlphaVantagePriceClient

from app.schemas import PredictionResponse
from app.montecarlo import weighted_bootstrap_mc_next_close, histogram
from app.news.finnhub import FinnhubNewsClient
from app.news.sentiment import score_articles
from app.storage.sqlite_cache import init_db, get_signal, put_signal

app = FastAPI(title="Monte Carlo News-Weighted Stock Prediction API", version="1.0.0")


@app.on_event("startup")
def _startup():
    init_db()

@app.get("/")
def root():
    return {"message": "API is running. Try /docs or /predict?symbol=AAPL"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/predict", response_model=PredictionResponse)
def predict(
    symbol: str = Query(..., description="Ticker symbol, e.g. AAPL, MSFT, NVDA"),
    period: str = Query("2y", description="History period for yfinance: 1y,2y,5y,max"),
    n_sims: int = Query(10000, ge=1000, le=200000),
    seed: int | None = Query(42, description="Random seed (optional)"),
    alpha: float = Query(2.0, ge=0.0, le=10.0, description="Sentiment tilt strength"),
    refresh_news: bool = Query(False, description="Force refresh news sentiment for today"),
    include_histogram: bool = Query(True),
    histogram_bins: int = Query(25, ge=5, le=200),
):
    symbol = symbol.strip().upper()
    today = date.today()

    # ----- 1) Pull daily price history (Alpha Vantage — FREE tier safe) -----
    # On free tier, Alpha Vantage only allows "compact" (~100 trading days).
    # We always fetch compact and optionally trim to a shorter lookback.

    lookback_days: int = 90  # you can tune this (30–100 is reasonable)

    try:
        price_client = AlphaVantagePriceClient()
        # Always use compact on free tier
        closes = price_client.daily_closes(symbol, full=False)

        # Keep only the most recent N trading days
        closes = closes.iloc[-lookback_days:]

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Price provider error (Alpha Vantage): {e}"
        )

    if closes is None or closes.empty or len(closes) < 30:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient price data returned for '{symbol}' (need ≥30 days)"
        )

    # ----- 2) Get today's news sentiment (cached daily) -----
    cached = None if refresh_news else get_signal(symbol, today)
    if cached:
        news_sentiment = cached["sentiment"]
        news_count = cached["article_count"]
    else:
        # Fetch from Finnhub and score
        try:
            client = FinnhubNewsClient()
            articles = client.company_news(symbol, today)
            news_sentiment, news_count = score_articles(articles)
        except Exception:
            # Safe fallback: no news impact if provider fails
            news_sentiment, news_count = 0.0, 0

        # Cache result (even if 0,0 so we don't re-fetch repeatedly)
        put_signal(symbol, today, float(news_sentiment), int(news_count))

    # ----- 3) News-weighted Monte Carlo -----
    try:
        simulated, stats = weighted_bootstrap_mc_next_close(
            closes=closes,
            n_sims=n_sims,
            seed=seed,
            sentiment=float(news_sentiment),
            alpha=float(alpha),
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {e}")

    # as-of date = last market date in series
    asof_date = closes.index.sort_values()[-1]
    asof_str = asof_date.strftime("%Y-%m-%d")

    resp = {
        "symbol": symbol,
        "asof": asof_str,
        "last_close": stats["last_close"],
        "n_days_history": stats["n_days_history"],
        "n_sims": int(n_sims),

        "news_sentiment": float(news_sentiment),
        "news_article_count": int(news_count),
        "sentiment_alpha": float(alpha),

        "p_up": stats["p_up"],
        "expected_close": stats["expected_close"],
        "expected_return": stats["expected_return"],

        "p10": stats["p10"],
        "p25": stats["p25"],
        "p50": stats["p50"],
        "p75": stats["p75"],
        "p90": stats["p90"],

        "range_68": stats["range_68"],
        "range_90": stats["range_90"],
    }

    if include_histogram:
        h = histogram(simulated, bins=histogram_bins)
        resp["histogram_bins"] = h["bins"]
        resp["histogram_counts"] = h["counts"]

    return PredictionResponse(**resp)
