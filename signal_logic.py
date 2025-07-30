import sys
sys.path.append('./strategy')

import pandas as pd
from ta.trend import MACD, EMAIndicator, ADXIndicator
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

# 🕯 Pattern Detector (Basic)
def detect_pattern(df):
    try:
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Doji
        if abs(last['open'] - last['close']) / (last['high'] - last['low'] + 1e-9) < 0.1:
            return "Doji"
        # Hammer
        elif last['close'] > last['open'] and (last['low'] < min(prev['low'], last['open'] - (last['high'] - last['close']) * 2)):
            return "Hammer"
        # Shooting Star
        elif last['open'] > last['close'] and (last['high'] > max(prev['high'], last['close'] + (last['open'] - last['low']) * 2)):
            return "Shooting Star"
        else:
            return "None"
    except Exception as e:
        print(f"⚠️ Pattern error: {e}")
        return "None"

# 🧠 Final Signal Generator per Timeframe
def generate_trade_signal(symbol, df, timeframe, news_sentiment):
    try:
        print(f"\n📊 Analyzing {symbol} | {timeframe} | Rows: {len(df)}")

        macd_signal = detect_macd_signal(df)
        ema_signal = analyze_ema_signal(df)
        rsi_series = get_rsi(df)
        rsi_latest = rsi_series.iloc[-1]
        boll_signal = analyze_bollinger_signal(df)
        pattern = detect_pattern(df)
        vol_ok = is_volume_spike(df)
        adx_value = get_adx(df)

        print(f"📉 MACD: {macd_signal} | EMA: {ema_signal} | RSI: {rsi_latest:.2f} | BB: {boll_signal} | Pattern: {pattern} | Volume: {vol_ok} | ADX: {adx_value}")

        signal = "WAIT"
        reason = "No strong confirmation yet"
        confirmed = False

        if news_sentiment:
            ns = news_sentiment.lower()
            indicators = [macd_signal, ema_signal, boll_signal]

            indicator_match = any(ind == "BUY" for ind in indicators) if ns == "bullish" else any(ind == "SELL" for ind in indicators)
            volume_or_adx = vol_ok or (adx_value is not None and adx_value >= 20)

            if ns == "bullish" and indicator_match and volume_or_adx:
                confirmed = True
                signal = "BUY"
                reason = f"News BULLISH + indicator + Volume/ADX + Pattern: {pattern}"
            elif ns == "bearish" and indicator_match and volume_or_adx:
                confirmed = True
                signal = "SELL"
                reason = f"News BEARISH + indicator + Volume/ADX + Pattern: {pattern}"

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "macd_signal": macd_signal,
            "ema_signal": ema_signal,
            "rsi": rsi_latest,
            "bollinger": boll_signal,
            "pattern": pattern,
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
            "pattern": "None",
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
