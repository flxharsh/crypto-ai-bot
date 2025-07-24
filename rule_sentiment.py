# rule_sentiment.py
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def rule_based_sentiment(headline):
    vs = analyzer.polarity_scores(headline)
    compound = vs["compound"]

    if compound >= 0.5:
        return "bullish"
    elif compound <= -0.5:
        return "bearish"

    headline_lower = headline.lower()

    if any(word in headline_lower for word in ["hacked", "lawsuit", "ban", "restrict", "fine", "crash"]):
        return "bearish"
    elif any(word in headline_lower for word in ["partnership", "approval", "etf", "adoption", "institutional"]):
        return "bullish"

    return "neutral"
