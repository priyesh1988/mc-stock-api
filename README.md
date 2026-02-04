# Monte Carlo News-Weighted Stock Prediction API

This FastAPI app predicts a *probability distribution* for the **next-day close** of a stock using:

- Historical daily returns (bootstrap Monte Carlo)
- **Present-day news sentiment** (today’s Finnhub articles)
- **Weighted sampling** based on today’s sentiment

## What you get
`GET /predict?symbol=AAPL`

Returns:
- `p_up`: probability tomorrow close > last close
- `p10/p50/p90`: percentiles of simulated next-day close
- `range_90`: [p5, p95] interval
- `news_sentiment`: today’s sentiment in [-1, +1]
- `news_article_count`: number of articles used
- Optional histogram summary for charting in a UI

---

## Prerequisites
- Python 3.11+
- Alphavantage API key
- A Finnhub API key (free tier is fine)
  - Set env var: `FINNHUB_API_KEY`

Alphavantage endpoint used: Time Series Stock Data APIs
Docs: https://www.alphavantage.co/documentation/

Finnhub endpoint used: Company News (daily)  
Docs: https://finnhub.io/docs/api/company-news

---

## Setup (local)

```bash
git clone <your_repo>
cd mc-stock-api

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
export FINNHUB_API_KEY="YOUR_KEY"
