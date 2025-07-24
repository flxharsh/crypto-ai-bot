import pandas as pd

# ============================ 🔹 MACD 🔹 ============================

def macd(df):
    try:
        df = df.copy()

        if 'close' not in df.columns or len(df) < 35:
            return "neutral"  # Not enough data to calculate MACD

        df['EMA12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # Detect crossover
        if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['Signal'].iloc[-2]:
            return "buy"
        elif df['MACD'].iloc[-1] < df['Signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['Signal'].iloc[-2]:
            return "sell"
        else:
            return "neutral"
    except Exception as e:
        print(f"❌ MACD error: {e}")
        return "neutral"


# ======================= 📦 ORDER BLOCK DETECTION =======================

def detect_order_blocks(df):
    try:
        if not {'open', 'close', 'high', 'low'}.issubset(df.columns):
            return "neutral"

        bullish_blocks = []
        bearish_blocks = []

        for i in range(3, len(df)):
            prev_candle = df.iloc[i - 1]
            curr_candle = df.iloc[i]

            # Detect bearish OB: green candle followed by red candle
            if prev_candle['close'] > prev_candle['open'] and curr_candle['close'] < curr_candle['open']:
                bearish_blocks.append(curr_candle['high'])

            # Detect bullish OB: red candle followed by green candle
            elif prev_candle['close'] < prev_candle['open'] and curr_candle['close'] > curr_candle['open']:
                bullish_blocks.append(curr_candle['low'])

        if bullish_blocks and not bearish_blocks:
            return "bullish"
        elif bearish_blocks and not bullish_blocks:
            return "bearish"
        elif len(bullish_blocks) > len(bearish_blocks):
            return "bullish"
        elif len(bearish_blocks) > len(bullish_blocks):
            return "bearish"
        else:
            return "neutral"
    except Exception as e:
        print(f"❌ Order Block error: {e}")
        return "neutral"


# ====================== 🔨 BREAK OF STRUCTURE (BOS) ======================

def detect_bos(df):
    try:
        if not {'high', 'low'}.issubset(df.columns):
            return []

        highs = df['high'].rolling(window=3).max()
        lows = df['low'].rolling(window=3).min()

        bos_points = []

        for i in range(2, len(df)):
            # BOS Up: current high > previous rolling high
            if df['high'].iloc[i] > highs.iloc[i - 1]:
                bos_points.append({
                    "type": "BOS_UP",
                    "price": float(df['high'].iloc[i]),
                    "index": i
                })

            # BOS Down: current low < previous rolling low
            elif df['low'].iloc[i] < lows.iloc[i - 1]:
                bos_points.append({
                    "type": "BOS_DOWN",
                    "price": float(df['low'].iloc[i]),
                    "index": i
                })

        return bos_points[-20:] if bos_points else []
    except Exception as e:
        print(f"❌ BOS error: {e}")
        return []
