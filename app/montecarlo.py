from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple


def weighted_bootstrap_mc_next_close(
    closes: pd.Series,
    n_sims: int = 10000,
    seed: int | None = None,
    sentiment: float = 0.0,   # [-1, +1]
    alpha: float = 2.0,       # tilt strength
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Monte Carlo: sample ONE historical daily return (bootstrap) to simulate next-day close.

    Weighted sampling to inject present-day sentiment:
      weights_i = exp(alpha * sentiment * (r_i / sigma))

    - If sentiment≈0 or alpha=0 -> uniform bootstrap
    """
    if closes is None or len(closes) < 30:
        raise ValueError("Need at least 30 closing prices to simulate reliably.")

    closes = closes.dropna().sort_index()
    rets = closes.pct_change().dropna()
    if len(rets) < 20:
        raise ValueError("Not enough return observations after pct_change().")

    last_close = float(closes.iloc[-1])
    r = rets.to_numpy(dtype=float)

    sigma = float(np.std(r))
    if sigma < 1e-12:
        sigma = 1.0

    s = max(-1.0, min(1.0, float(sentiment)))
    a = float(alpha)

    probs = None
    if abs(s) >= 1e-6 and a > 1e-9:
        tilt = a * s * (r / sigma)
        tilt = np.clip(tilt, -20, 20)  # stability
        w = np.exp(tilt)
        probs = w / np.sum(w)

    rng = np.random.default_rng(seed)
    idx = rng.choice(len(r), size=n_sims, replace=True, p=probs)
    sampled_rets = r[idx]

    simulated = last_close * (1.0 + sampled_rets)

    expected_close = float(np.mean(simulated))
    expected_return = float((expected_close / last_close) - 1.0)
    p_up = float(np.mean(simulated > last_close))

    def pct(x: float) -> float:
        return float(np.percentile(simulated, x))

    stats = {
        "last_close": last_close,
        "expected_close": expected_close,
        "expected_return": expected_return,
        "p_up": p_up,
        "p10": pct(10),
        "p25": pct(25),
        "p50": pct(50),
        "p75": pct(75),
        "p90": pct(90),
        "range_68": [pct(16), pct(84)],
        "range_90": [pct(5), pct(95)],
        "n_days_history": int(len(closes)),
        "sentiment": s,
        "alpha": a,
    }
    return simulated, stats


def histogram(simulated: np.ndarray, bins: int = 25) -> Dict[str, Any]:
    counts, edges = np.histogram(simulated, bins=bins)
    mids = (edges[:-1] + edges[1:]) / 2.0
    return {
        "bins": [float(x) for x in mids],
        "counts": [int(x) for x in counts],
    }
