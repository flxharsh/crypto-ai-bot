import sys
sys.path.append('./strategy')

import pandas as pd
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator

from strategy.order_block import detect_order_blocks
from strategy.bos import detect_bos

# 🔄 EMA 9/20 Cross Detection using `ta`
def analyze_ema_signal(df):
    ema_9 = EMAIndicator(close=df['close'], window=9).ema_indicator()
    ema_20 = EMAIndicator(close=df['close'], window=20).ema_indicator()

    if ema_9.iloc[-2] < ema_20.iloc[-2] and ema_9.iloc[-1] > ema_20.iloc[-1]:
        return "BUY"
    elif ema_9.iloc[-2] > ema_20.iloc[-2] and ema_9.iloc[-1] < ema_20.iloc[-1]:
        return "SELL"
    else:
        return "NEUTRAL"

# 💹 MACD Signal using `ta`
def detect_macd_signal(df):
    macd = MACD(close=df['close'])
    macd_diff = macd.macd_diff()

    if macd_diff.iloc[-2] < 0 and macd_diff.iloc[-1] > 0:
        return "BUY"
    elif macd_diff.iloc[-2] > 0 and macd_diff.iloc[-1] < 0:
        return "SELL"
    else:
        return "NEUTRAL"

# 📊 RSI Calculation using `ta`
def get_rsi(df, period=14):
    return RSIIndicator(close=df['close'], window=period).rsi()

# 🧠 Final Signal Generator per Timeframe
def generate_trade_signal(symbol, df, timeframe, news_sentiment):
    try:
        print(f"\n📊 Analyzing {symbol} | {timeframe} | Rows: {len(df)}")

        # 1️⃣ MACD
        macd_signal = detect_macd_signal(df)
        print(f"💹 MACD: {macd_signal}")

        # 2️⃣ Order Block
        order_block = detect_order_blocks(df)
        print(f"📦 Order Block: {order_block}")

        # 3️⃣ BOS
        bos_list = detect_bos(df)
        last_bos_type = bos_list[-1]["type"] if bos_list and isinstance(bos_list[-1], dict) else None
        print(f"🧱 Last BOS: {last_bos_type}")

        # 4️⃣ EMA
        ema_signal = analyze_ema_signal(df)
        print(f"📈 EMA 9/20: {ema_signal}")

        # 5️⃣ RSI
        rsi_series = get_rsi(df)
        rsi_latest = rsi_series.iloc[-1]
        print(f"📊 RSI: {rsi_latest:.2f}")

        rsi_ok = False
        if rsi_latest < 30 and ema_signal == "BUY" and order_block == "BULLISH":
            rsi_ok = True
        elif rsi_latest > 70 and ema_signal == "SELL" and order_block == "BEARISH":
            rsi_ok = True

        # ✅ Confirm Signal
        confirmed = False
        signal = "WAIT"
        reason = "No strong confirmation yet"

        if macd_signal == "BUY" and order_block == "BULLISH" and ema_signal == "BUY" and last_bos_type == "BOS_UP" and rsi_ok:
            confirmed = True
            signal = "BUY"
            reason = "MACD + OB + EMA + BOS_UP + RSI aligned"

        elif macd_signal == "SELL" and order_block == "BEARISH" and ema_signal == "SELL" and last_bos_type == "BOS_DOWN" and rsi_ok:
            confirmed = True
            signal = "SELL"
            reason = "MACD + OB + EMA + BOS_DOWN + RSI aligned"

        # 🔁 Fallbacks
        elif ema_signal == "BUY" and last_bos_type == "BOS_UP":
            confirmed = True
            signal = "BUY"
            reason = "EMA + BOS_UP (fallback)"
        elif ema_signal == "SELL" and last_bos_type == "BOS_DOWN":
            confirmed = True
            signal = "SELL"
            reason = "EMA + BOS_DOWN (fallback)"
        elif macd_signal == "BUY" and last_bos_type == "BOS_UP":
            confirmed = True
            signal = "BUY"
            reason = "MACD BUY + BOS_UP (fallback)"
        elif macd_signal == "SELL" and last_bos_type == "BOS_DOWN":
            confirmed = True
            signal = "SELL"
            reason = "MACD SELL + BOS_DOWN (fallback)"
        elif news_sentiment:
            ns = news_sentiment.lower()
            if ns == "bullish" and last_bos_type == "BOS_UP":
                confirmed = True
                signal = "BUY"
                reason = "News BULLISH + BOS_UP"
            elif ns == "bearish" and last_bos_type == "BOS_DOWN":
                confirmed = True
                signal = "SELL"
                reason = "News BEARISH + BOS_DOWN"

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "macd_signal": macd_signal,
            "order_block": order_block,
            "bos": bos_list,
            "ema_signal": ema_signal,
            "rsi": rsi_latest,
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
            "order_block": "NEUTRAL",
            "bos": [],
            "ema_signal": "NEUTRAL",
            "rsi": None,
            "confirmed": False,
            "signal": "WAIT",
            "reason": "Error in analysis"
        }

# 🔎 Multi-Timeframe Signal
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
