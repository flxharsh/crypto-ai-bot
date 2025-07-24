import json
import pandas as pd
from signal_logic import generate_trade_signal
from price_data import fetch_price_data
from news_sentiment import fetch_and_analyze_news
from datetime import datetime

# 📊 Strategy Parameters
INITIAL_BALANCE = 10000
TRADE_PERCENT = 0.05  # 5% capital per trade
TP_PERCENT = 0.10     # 10% Take Profit
SL_PERCENT = 0.05     # 5% Stop Loss

def load_symbols():
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def simulate_trades(symbols, timeframe="1h"):
    all_trades = []
    balance = INITIAL_BALANCE
    wins, losses = 0, 0

    # 🧠 Fetch historical news sentiment once for backtest
    news = fetch_and_analyze_news()
    news_sentiment = news.get("sentiment", "NEUTRAL").upper()
    news_confidence = news.get("confidence", 0.0)

    print(f"\n🧠 News Sentiment for Backtest: {news_sentiment} | Confidence: {news_confidence}\n")

    for symbol in symbols:
        print(f"\n📈 Backtesting {symbol} on {timeframe} (90 days)...")
        df = fetch_price_data(symbol, timeframe)

        if df is None or len(df) < 60:
            print(f"⚠️ Not enough data for {symbol}")
            continue

        for i in range(50, len(df) - 1):
            sub_df = df.iloc[:i].copy()
            result = generate_trade_signal(symbol, sub_df, timeframe, news_sentiment)
            signal = result.get("signal")

            if signal not in ["BUY", "SELL"]:
                continue

            entry_price = sub_df["close"].iloc[-1]
            exit_price = df["close"].iloc[i + 1]
            entry_time = str(sub_df.index[-1])
            exit_time = str(df.index[i + 1])

            capital = balance * TRADE_PERCENT
            quantity = capital / entry_price
            tp = entry_price * (1 + TP_PERCENT)
            sl = entry_price * (1 - SL_PERCENT)

            pnl = 0
            result_label = "UNREALIZED"

            if signal == "BUY":
                if exit_price >= tp:
                    pnl = quantity * (tp - entry_price)
                    result_label = "TP"
                    wins += 1
                elif exit_price <= sl:
                    pnl = quantity * (sl - entry_price)
                    result_label = "SL"
                    losses += 1
                else:
                    result_label = "SKIPPED"
                    continue

            elif signal == "SELL":
                if exit_price <= sl:
                    pnl = quantity * (entry_price - sl)
                    result_label = "TP"
                    wins += 1
                elif exit_price >= tp:
                    pnl = quantity * (entry_price - tp)
                    result_label = "SL"
                    losses += 1
                else:
                    result_label = "SKIPPED"
                    continue

            balance += pnl

            trade = {
                "symbol": symbol,
                "signal": signal,
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "pnl": round(pnl, 2),
                "result": result_label,
                "balance": round(balance, 2),
                "entry_time": entry_time,
                "exit_time": exit_time,
                "news_sentiment": news_sentiment,
                "confidence": news_confidence
            }
            all_trades.append(trade)

    # 📂 Save trade log
    with open("backtest_results.json", "w") as f:
        json.dump(all_trades, f, indent=4)

    # 📊 Save summary
    total_trades = wins + losses
    accuracy = round((wins / total_trades) * 100, 2) if total_trades > 0 else 0.0
    summary = {
        "final_balance": round(balance, 2),
        "total_trades": len(all_trades),
        "evaluated_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": accuracy,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    with open("backtest_summary.json", "w") as f:
        json.dump(summary, f, indent=4)

    print(f"\n✅ Backtest Complete")
    print(f"💰 Final Balance: ${balance:.2f}")
    print(f"🎯 Accuracy: {accuracy:.2f}%")
    print(f"✔️ Wins: {wins} | ❌ Losses: {losses}")
    print(f"📦 Total Trades: {len(all_trades)}")

    return all_trades

if __name__ == "__main__":
    simulate_trades(load_symbols())
