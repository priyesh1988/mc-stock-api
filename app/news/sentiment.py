from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def score_text(text: str) -> float:
    """
    Returns compound sentiment in [-1, +1].
    """
    if not text:
        return 0.0
    return float(_analyzer.polarity_scores(text)["compound"])


def score_articles(articles: list[dict]) -> tuple[float, int]:
    """
    Produces a single sentiment score for the day from a list of articles.
    Headline weighted more than summary.
    """
    if not articles:
        return 0.0, 0

    scores: list[float] = []
    for a in articles:
        headline = (a.get("headline") or "").strip()
        summary = (a.get("summary") or "").strip()

        h = score_text(headline)
        s = score_text(summary)

        combined = 0.7 * h + 0.3 * s
        scores.append(combined)

    return float(sum(scores) / len(scores)), len(scores)
