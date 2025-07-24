from indicators import detect_order_blocks, detect_bos, macd

def analyze_technical(symbol, df, timeframe, news_sentiment=None):
    try:
        # 🧪 Debug Info
        print(f"\n🔬 Analyzing {symbol} | Timeframe: {timeframe}")
        print(f"📊 Columns: {df.columns.tolist()} | Rows: {len(df)}")
        print(df.tail(3))

        # 1️⃣ MACD Signal
        try:
            if len(df) < 35:
                print(f"⚠️ Not enough candles for MACD ({len(df)}) on {symbol} {timeframe}")
                macd_signal = "neutral"
            else:
                macd_signal = macd(df[-35:])
                if not macd_signal or not isinstance(macd_signal, str):
                    macd_signal = "neutral"
        except Exception as e:
            print(f"❌ MACD error for {symbol}: {e}")
            macd_signal = "neutral"
        macd_signal = macd_signal.lower()
        print(f"💹 MACD Signal: {macd_signal}")

        # 2️⃣ Order Block Signal
        try:
            ob_signal = detect_order_blocks(df)
            if not ob_signal or not isinstance(ob_signal, str):
                ob_signal = "neutral"
        except Exception as e:
            print(f"❌ Order Block error for {symbol}: {e}")
            ob_signal = "neutral"
        ob_signal = ob_signal.lower()
        print(f"📦 Order Block Signal: {ob_signal}")

        # 3️⃣ BOS Signal
        try:
            bos = detect_bos(df)
        except Exception as e:
            print(f"❌ BOS error for {symbol}: {e}")
            bos = []

        last_bos = bos[-1]["type"] if bos and isinstance(bos[-1], dict) else None
        print(f"🧱 Last BOS: {last_bos}")

        # 4️⃣ Default Signal
        confirmed = False
        signal = "WAIT"
        reason = "No strong signal yet"

        # 5️⃣ Strategy Logic
        if ob_signal == "bullish" and last_bos == "BOS_UP":
            if macd_signal in ["buy", "neutral"]:
                confirmed = True
                signal = "BUY"
                reason = "Bullish OB + BOS_UP + MACD supportive"

        elif ob_signal == "bearish" and last_bos == "BOS_DOWN":
            if macd_signal in ["sell", "neutral"]:
                confirmed = True
                signal = "SELL"
                reason = "Bearish OB + BOS_DOWN + MACD supportive"

        elif macd_signal in ["buy", "sell"] and ob_signal == "neutral":
            confirmed = True
            signal = macd_signal.upper()
            reason = f"MACD={macd_signal.upper()} strong without OB"

        # 6️⃣ Fallback via News Sentiment
        if not confirmed and news_sentiment:
            news_sentiment = news_sentiment.lower()
            if news_sentiment == "bullish" and last_bos == "BOS_UP":
                confirmed = True
                signal = "BUY"
                reason = "News BULLISH + BOS_UP (Fallback)"
            elif news_sentiment == "bearish" and last_bos == "BOS_DOWN":
                confirmed = True
                signal = "SELL"
                reason = "News BEARISH + BOS_DOWN (Fallback)"

        # ✅ Return Final Result
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "macd_signal": macd_signal,
            "order_block": ob_signal,
            "bos": bos,
            "confirmed": confirmed,
            "signal": signal,
            "reason": reason
        }

    except Exception as e:
        print(f"❌ Error in analyze_technical for {symbol} on {timeframe}: {e}")
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "macd_signal": "neutral",
            "order_block": "neutral",
            "bos": [],
            "confirmed": False,
            "signal": "WAIT",
            "reason": "Error during analysis"
        }
