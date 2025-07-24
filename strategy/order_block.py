def detect_order_blocks(df, lookback=50):
    """
    🔮 Pro-Level Order Block Detection using SMC concepts
    - Looks for explosive moves after supply/demand zones
    - Checks for candle structure + volume confirmation
    """
    if len(df) < lookback + 2:
        return "NEUTRAL"

    bullish_blocks = []
    bearish_blocks = []

    for i in range(2, len(df)):
        c1 = df.iloc[i - 2]  # first
        c2 = df.iloc[i - 1]  # second
        c3 = df.iloc[i]      # third (current)

        # 📈 Bullish OB: red candle before strong green break with volume
        if (
            c1['close'] < c1['open'] and  # red
            c2['close'] > c2['open'] and  # green
            c3['close'] > c2['high'] and  # breakout
            c3['volume'] > df['volume'].rolling(lookback).mean().iloc[i]
        ):
            bullish_blocks.append({
                "index": df.index[i],
                "price": min(c1['low'], c2['low']),
                "type": "BULLISH"
            })

        # 🔻 Bearish OB: green candle before strong red breakdown with volume
        if (
            c1['close'] > c1['open'] and  # green
            c2['close'] < c2['open'] and  # red
            c3['close'] < c2['low'] and   # breakdown
            c3['volume'] > df['volume'].rolling(lookback).mean().iloc[i]
        ):
            bearish_blocks.append({
                "index": df.index[i],
                "price": max(c1['high'], c2['high']),
                "type": "BEARISH"
            })

    # 🧠 Use the latest one
    if bullish_blocks and not bearish_blocks:
        return "BULLISH"
    elif bearish_blocks and not bullish_blocks:
        return "BEARISH"
    elif bullish_blocks and bearish_blocks:
        return (
            "BULLISH" if bullish_blocks[-1]["index"] > bearish_blocks[-1]["index"]
            else "BEARISH"
        )
    else:
        return "NEUTRAL"
