import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import re

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
analyzer = SentimentIntensityAnalyzer()

def smart_sentiment(text):
    """Returns sentiment label and confidence"""
    vs = analyzer.polarity_scores(text)
    compound = vs["compound"]
    confidence = abs(compound)

    label = "neutral"
    if compound >= 0.5:
        label = "bullish"
    elif compound <= -0.5:
        label = "bearish"

    # Custom keyword-based sentiment override
    text = text.lower()
    bearish_keywords = ["hacked", "lawsuit", "ban", "restrict", "fine", "crash", "fraud", "decline", "sell-off"]
    bullish_keywords = ["partnership", "approval", "etf", "adoption", "institutional", "record high", "surge"]

    for word in bearish_keywords:
        if word in text:
            label = "bearish"
            confidence += 0.2
            break
    for word in bullish_keywords:
        if word in text:
            label = "bullish"
            confidence += 0.2
            break

    confidence = min(confidence, 1.0)
    return label, round(confidence, 2)

def fetch_and_analyze_news():
    try:
        if not NEWS_API_KEY:
            print("❌ NEWS_API_KEY not found in environment.")
            return {
                "sentiment": "NEUTRAL",
                "confidence": 0.0,
                "headlines": [],
                "affected_symbols": []
            }

        url = (
            f"https://newsapi.org/v2/everything?"
            f"q=cryptocurrency OR bitcoin OR ethereum OR solana OR xrp OR bnb&"
            f"language=en&sortBy=publishedAt&pageSize=10&"
            f"apiKey={NEWS_API_KEY}"
        )

        response = requests.get(url)
        data = response.json()

        if data.get("status") != "ok" or "articles" not in data:
            print("⚠️ NewsAPI response error or invalid data")
            return {
                "sentiment": "NEUTRAL",
                "confidence": 0.0,
                "headlines": [],
                "affected_symbols": []
            }

        articles = data.get("articles", [])
        if not articles:
            print("⚠️ No news articles found")
            return {
                "sentiment": "NEUTRAL",
                "confidence": 0.0,
                "headlines": [],
                "affected_symbols": []
            }

        symbol_map = {
            "bitcoin": "BTCUSDT", "btc": "BTCUSDT",
            "ethereum": "ETHUSDT", "eth": "ETHUSDT",
            "solana": "SOLUSDT", "sol": "SOLUSDT",
            "ripple": "XRPUSDT", "xrp": "XRPUSDT",
            "bnb": "BNBUSDT"
        }

        scores = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}
        count = {"bullish": 0, "bearish": 0, "neutral": 0}
        top_headlines = []
        affected = set()

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            url = article.get("url", "")
            if not title and not description:
                continue

            content = f"{title} {description}".strip()
            label, conf = smart_sentiment(content)

            scores[label] += conf
            count[label] += 1

            lowered = content.lower()
            for keyword, symbol in symbol_map.items():
                if re.search(rf"\b{keyword}\b", lowered):
                    affected.add(symbol)

            if len(top_headlines) < 5 and title not in [h['title'] for h in top_headlines]:
                top_headlines.append({"title": title, "url": url})

        # Final decision
        final_sentiment = max(scores, key=scores.get)
        total_votes = sum(count.values())
        confidence = scores[final_sentiment] / total_votes if total_votes > 0 else 0.0

        return {
            "sentiment": final_sentiment.upper(),
            "confidence": round(confidence, 2),
            "headlines": top_headlines,
            "affected_symbols": sorted(list(affected))
        }

    except Exception as e:
        print(f"❌ Error fetching news sentiment: {e}")
        return {
            "sentiment": "NEUTRAL",
            "confidence": 0.0,
            "headlines": [],
            "affected_symbols": []
        }
