import sys
sys.path.append('./strategy')

import pandas as pd
from ta.trend import MACD, EMAIndicator, IchimokuIndicator, ADXIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# 🔍 Volume Spike Detection
def is_volume_spike(df, multiplier=1.5):
    try:
        recent_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].iloc[-20:-1].mean()
        return recent_volume > multiplier * avg_volume
    except:
        return False

# 🔄 EMA 9/20 Cross Detection
def analyze_ema_signal(df):
    ema_9 = EMAIndicator(close=df['close'], window=9).ema_indicator()
    ema_20 = EMAIndicator(close=df['close'], window=20).ema_indicator()

    if ema_9.iloc[-2] < ema_20.iloc[-2] and ema_9.iloc[-1] > ema_20.iloc[-1]:
        return "BUY"
    elif ema_9.iloc[-2] > ema_20.iloc[-2] and ema_9.iloc[-1] < ema_20.iloc[-1]:
        return "SELL"
    else:
        return "NEUTRAL"

# 📉 MACD Signal
def detect_macd_signal(df):
    macd = MACD(close=df['close'])
    macd_diff = macd.macd_diff()

    if macd_diff.iloc[-2] < 0 and macd_diff.iloc[-1] > 0:
        return "BUY"
    elif macd_diff.iloc[-2] > 0 and macd_diff.iloc[-1] < 0:
        return "SELL"
    else:
        return "NEUTRAL"

# 📊 RSI
def get_rsi(df, period=14):
    return RSIIndicator(close=df['close'], window=period).rsi()

# 🔠 ADX (Trend Strength)
def get_adx(df):
    try:
        adx = ADXIndicator(high=df['high'], low=df['low'], close=df['close'])
        return adx.adx().iloc[-1]
    except:
        return None

# 📀 Bollinger Band Signal
def analyze_bollinger_signal(df):
    try:
        bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        lower = bb.bollinger_lband()
        upper = bb.bollinger_hband()
        close = df['close']

        if close.iloc[-1] < lower.iloc[-1]:
            return "BUY"
        elif close.iloc[-1] > upper.iloc[-1]:
            return "SELL"
        else:
            return "NEUTRAL"
    except Exception as e:
        print(f"⚠️ Bollinger error: {e}")
        return "NEUTRAL"

# ☁️ Ichimoku Cloud Signal
def analyze_ichimoku_signal(df):
    try:
        ichimoku = IchimokuIndicator(high=df['high'], low=df['low'])
        span_a = ichimoku.ichimoku_a()
        span_b = ichimoku.ichimoku_b()
        close = df['close']

        if close.iloc[-1] > max(span_a.iloc[-1], span_b.iloc[-1]):
            return "BUY"
        elif close.iloc[-1] < min(span_a.iloc[-1], span_b.iloc[-1]):
            return "SELL"
        else:
            return "NEUTRAL"
    except Exception as e:
        print(f"⚠️ Ichimoku error: {e}")
        return "NEUTRAL"

# 🧠 Final Signal Generator per Timeframe
def generate_trade_signal(symbol, df, timeframe, news_sentiment):
    try:
        print(f"\n📊 Analyzing {symbol} | {timeframe} | Rows: {len(df)}")

        macd_signal = detect_macd_signal(df)
        ema_signal = analyze_ema_signal(df)
        rsi_series = get_rsi(df)
        rsi_latest = rsi_series.iloc[-1]
        boll_signal = analyze_bollinger_signal(df)
        ichi_signal = analyze_ichimoku_signal(df)
        vol_ok = is_volume_spike(df)
        adx_value = get_adx(df)

        print(f"📉 MACD: {macd_signal} | EMA: {ema_signal} | RSI: {rsi_latest:.2f} | BB: {boll_signal} | Ichi: {ichi_signal} | Volume: {vol_ok} | ADX: {adx_value}")

        signal = "WAIT"
        reason = "No strong confirmation yet"
        confirmed = False

        if news_sentiment:
            ns = news_sentiment.lower()
            indicators = [macd_signal, ema_signal, boll_signal, ichi_signal]

            indicator_match = any(ind == "BUY" for ind in indicators) if ns == "bullish" else any(ind == "SELL" for ind in indicators)
            volume_or_adx = vol_ok or (adx_value is not None and adx_value >= 20)

            if ns == "bullish" and indicator_match and volume_or_adx:
                confirmed = True
                signal = "BUY"
                reason = "News BULLISH + 1 indicator + Volume or ADX confirm"
            elif ns == "bearish" and indicator_match and volume_or_adx:
                confirmed = True
                signal = "SELL"
                reason = "News BEARISH + 1 indicator + Volume or ADX confirm"

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "macd_signal": macd_signal,
            "ema_signal": ema_signal,
            "rsi": rsi_latest,
            "bollinger": boll_signal,
            "ichimoku": ichi_signal,
            "adx": adx_value,
            "volume_ok": vol_ok,
            "confirmed": confirmed,
            "signal": signal,
            "reason": reason
        }

    except Exception as e:
        print(f"❌ Error in generate_trade_signal for {symbol} on {timeframe}: {e}")
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "macd_signal": "NEUTRAL",
            "ema_signal": "NEUTRAL",
            "rsi": None,
            "bollinger": "NEUTRAL",
            "ichimoku": "NEUTRAL",
            "adx": None,
            "volume_ok": False,
            "confirmed": False,
            "signal": "WAIT",
            "reason": "Error in analysis"
        }

# 🔁 Multi-Timeframe Signal
def analyze_technical(symbol, df_30m, df_1h, news_sentiment):
    print(f"\n🔎 Multi-Timeframe Analysis: {symbol}")

    result_30m = generate_trade_signal(symbol, df_30m, "30m", news_sentiment)
    result_1h = generate_trade_signal(symbol, df_1h, "1h", news_sentiment)

    tf_results = {
        "30m": result_30m,
        "1h": result_1h
    }

    confirmed = [res for res in tf_results.values() if res.get("confirmed")]

    if confirmed:
        final_signal = confirmed[0]["signal"]
        final_reason = confirmed[0]["reason"]
    else:
        final_signal = "WAIT"
        final_reason = "No strong confirmation yet"

    return {
        "symbol": symbol,
        "signal": final_signal,
        "reason": final_reason,
        "news_sentiment": news_sentiment,
        "details": tf_results
    }
