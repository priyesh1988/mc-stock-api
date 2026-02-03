from pydantic import BaseModel, Field
from typing import List, Optional


class PredictionResponse(BaseModel):
    symbol: str
    asof: str
    last_close: float

    n_days_history: int
    n_sims: int
    method: str = "monte_carlo_weighted_bootstrap_returns"

    # "present-day signal" inputs used
    news_sentiment: float = Field(..., ge=-1.0, le=1.0)
    news_article_count: int = Field(..., ge=0)
    sentiment_alpha: float = Field(..., ge=0.0, le=10.0)

    # forecast summary
    p_up: float = Field(..., ge=0.0, le=1.0)
    expected_close: float
    expected_return: float

    # percentiles
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float

    # intervals
    range_68: List[float]   # [p16, p84]
    range_90: List[float]   # [p5, p95]

    # optional histogram summary
    histogram_bins: Optional[List[float]] = None
    histogram_counts: Optional[List[int]] = None
