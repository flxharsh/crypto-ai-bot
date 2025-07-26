from flask import Flask, render_template
from news_sentiment import fetch_and_analyze_news
from price_data import fetch_price_data
from signal_logic import analyze_technical
from whatsapp_alert import send_whatsapp_message
from binance_trade import place_order, get_price, get_balance
from portfolio_manager import (
    check_position, update_position,
    get_portfolio, save_portfolio,
    auto_exit_check, get_current_price
)
from trade_logger import log_trade, update_exit_price
from accuracy_tracker import evaluate_trade_accuracy
import schedule
import threading
import time

app = Flask(__name__)
dashboard_data = {}

@app.route("/")
def dashboard():
    return render_template("index.html", data=dashboard_data or {})

def run_full_analysis():
    global dashboard_data
    print("\n🚀 Starting Crypto AI Multi-Coin Swing Bot...\n")

    try:
        # 🧠 News Analysis
        news = fetch_and_analyze_news()
        news_sentiment = news.get("sentiment", "NEUTRAL").upper()
        news_confidence = news.get("confidence", 0.0)
        affected_symbols = news.get("affected_symbols", [])
        news_headlines = news.get("headlines", [])

        print(f"🧠 News Sentiment: {news_sentiment} | 🧪 Confidence: {news_confidence:.2f}")
        print(f"📰 Affected Symbols: {affected_symbols}")

        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        timeframes = ["30m", "1h"]
        portfolio = get_portfolio()

        # 🎯 Accuracy Report
        accuracy_report = evaluate_trade_accuracy()
        accuracy_percent = accuracy_report.get("accuracy_percent", 0.0)
        evaluated_trades = accuracy_report.get("evaluated_trades", [])[-5:]

        dashboard_data = {
            "symbols": [],
            "balance": portfolio.get("balance", 0),
            "news_sentiment": news_sentiment,
            "confidence": round(news_confidence * 100, 2) if news_confidence else 0,
            "positions": portfolio.get("positions", {}),
            "accuracy": accuracy_percent,
            "affected_symbols": affected_symbols,
            "news_headlines": news_headlines,
            "total_trades": accuracy_report.get("total_trades", 0),
            "wins": accuracy_report.get("wins", 0),
            "losses": accuracy_report.get("losses", 0),
            "win_rate": accuracy_report.get("win_rate", 0.0),
            "evaluated_trades": evaluated_trades
        }

        for symbol in symbols:
            print(f"\n🔍 Analyzing {symbol}...\n")
            all_timeframes = {}
            for tf in timeframes:
                try:
                    df = fetch_price_data(symbol, tf)
                    result = analyze_technical(symbol, df, df, news_sentiment)
                    tf_result = result["details"][tf]
                    all_timeframes[tf] = tf_result
                    print(f"✅ {symbol} @ {tf} | MACD: {tf_result.get('macd_signal')} | EMA: {tf_result.get('ema_signal')} | OB: {tf_result.get('order_block')} | BOS: {len(tf_result.get('bos', []))}")
                except Exception as e:
                    print(f"❌ Error analyzing {symbol} on {tf}: {e}")

            best_tf = next((tf for tf, res in all_timeframes.items() if res.get("confirmed")), "1h")
            best_result = all_timeframes.get(best_tf, {})

            final = {
                "symbol": symbol,
                "signal": best_result.get("signal", "WAIT"),
                "reason": best_result.get("reason", "No strong confirmation yet"),
                "news_sentiment": news_sentiment,
                "details": all_timeframes,
                "timeframe": best_tf
            }

            print(f"\n📊 Final Signal for {symbol}: {final['signal']}")
            print(f"💡 Reason: {final['reason']}\n{'=' * 60}")
            dashboard_data["symbols"].append(final)

            # ✅ Auto Exit
            if check_position(portfolio, symbol):
                reason = auto_exit_check(portfolio, symbol)
                if reason in ["SL", "TP"]:
                    sell_price = get_current_price(symbol)
                    if sell_price:
                        portfolio = update_position(portfolio, symbol, "SELL", sell_price)
                        log_trade(symbol, "SELL", reason=f"Auto {reason} Hit", news_sentiment=news_sentiment, price=sell_price, timeframe="1h", result=reason)
                        update_exit_price(symbol, sell_price)
                        send_whatsapp_message(f"⚠️ Auto {reason} HIT on {symbol}\nPrice: {sell_price}")
                        print(f"🔻 Auto {reason} executed for {symbol} at {sell_price}")
                    continue

            # ✅ Buy Logic
            if final["signal"] == "BUY" and not check_position(portfolio, symbol):
                tf = final["timeframe"]
                live_price = get_price(symbol.replace("USDT", "/USDT"))
                usdt_balance = get_balance("USDT")

                if live_price and usdt_balance > 0:
                    capital = usdt_balance * 0.05
                    amount = round(capital / live_price, 5)
                    if amount >= 0.001:
                        placed = place_order(symbol.replace("USDT", "/USDT"), "buy", amount)
                        if placed:
                            portfolio = update_position(portfolio, symbol, "BUY", timeframe=tf)
                            pos = portfolio["positions"][symbol]
                            log_trade(symbol, "BUY", reason=final["reason"], news_sentiment=news_sentiment, price=live_price, timeframe=tf)
                            send_whatsapp_message(f"🟢 BUY {symbol} at {live_price}\nTP: {pos['take_profit']}, SL: {pos['stop_loss']}")
                    else:
                        print(f"❌ Skipping {symbol}, amount too small: {amount}")
                else:
                    print(f"⚠️ Skipping trade: price or balance missing for {symbol}")

            # ✅ Sell Logic
            elif final["signal"] == "SELL" and check_position(portfolio, symbol):
                sell_price = get_price(symbol.replace("USDT", "/USDT"))
                if sell_price:
                    placed = place_order(symbol.replace("USDT", "/USDT"), "sell", portfolio["positions"][symbol]["amount"])
                    if placed:
                        tf = final["timeframe"]
                        portfolio = update_position(portfolio, symbol, "SELL", sell_price)
                        log_trade(symbol, "SELL", reason=final["reason"], news_sentiment=news_sentiment, price=sell_price, timeframe=tf)
                        update_exit_price(symbol, sell_price)
                        send_whatsapp_message(f"🔴 SELL {symbol} at {sell_price}\nReason: {final['reason']}")
                else:
                    print(f"⚠️ Skipping SELL for {symbol} due to missing price")

        print("\n📊 Portfolio Summary")
        print(f"💵 Balance: ${portfolio.get('balance', 0):.2f}")
        if portfolio.get("positions"):
            for sym, pos in portfolio["positions"].items():
                print(f" - {sym}: {pos}")
        else:
            print(" - No open positions")

        save_portfolio(portfolio)
        print("✅ Portfolio saved.")
        print("📤 Logging Trades...")
        print("📈 Accuracy: {:.2f}%".format(accuracy_percent))
        print("✅ Done!\n")

    except Exception as e:
        print(f"❌ Unhandled error during analysis: {e}")

def schedule_loop():
    schedule.every(15).minutes.do(run_full_analysis)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_full_analysis()  # Run once on start
    threading.Thread(target=schedule_loop).start()
    app.run(host="0.0.0.0", port=10000)
