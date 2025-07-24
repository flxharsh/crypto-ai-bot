import json
import os
from datetime import datetime

TRADE_LOG_FILE = "trade_history.json"

# 🔄 Initialize log file if not present
if not os.path.exists(TRADE_LOG_FILE):
    with open(TRADE_LOG_FILE, "w") as f:
        json.dump([], f)

# ✅ Log new BUY or SELL trades (with validation)
def log_trade(symbol, signal, price, reason, timeframe, news_sentiment="NEUTRAL", result=None):
    if price is None:
        print(f"⚠️ Skipping invalid trade (no price): {symbol} | {signal}")
        return

    try:
        with open(TRADE_LOG_FILE, "r") as f:
            trade_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        trade_data = []

    # 🚫 Clean corrupted trades (BUY with exit_price)
    trade_data = [
        t for t in trade_data
        if not (t.get("signal") == "BUY" and t.get("exit_price") is not None)
    ]

    signal = signal.upper()
    trade_entry = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "signal": signal,
        "entry_price": price if signal == "BUY" else None,
        "exit_price": price if signal == "SELL" else None,
        "price": price,  # Fallback reference
        "reason": reason,
        "timeframe": timeframe,
        "news_sentiment": news_sentiment.upper(),
    }

    if result:
        trade_entry["result"] = result.upper()

    # ❌ Block logging invalid BUY trade with exit_price
    if signal == "BUY" and trade_entry["exit_price"] is not None:
        print(f"❌ Invalid BUY trade with exit_price: {trade_entry}")
        return

    trade_data.append(trade_entry)

    with open(TRADE_LOG_FILE, "w") as f:
        json.dump(trade_data, f, indent=4)

    print(f"✅ Trade logged: {symbol} | {signal} @ {price} | TF: {timeframe} | Result: {result or 'N/A'}")

# 🔁 Update exit price for last open BUY trade
def update_exit_price(symbol, exit_price):
    try:
        with open(TRADE_LOG_FILE, "r") as f:
            trades = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Trade history not found.")
        return

    for trade in reversed(trades):
        if (
            trade.get("symbol") == symbol
            and trade.get("signal") == "BUY"
            and not trade.get("exit_price")
        ):
            trade["exit_price"] = exit_price
            break

    with open(TRADE_LOG_FILE, "w") as f:
        json.dump(trades, f, indent=4)

    print(f"🔁 Updated exit price for {symbol} to {exit_price}")

# 📊 Print portfolio nicely
def print_portfolio_summary(balance, positions):
    print("\n📊 Portfolio Summary")
    print(f"💵 Balance: ${balance:.2f}")
    print("📦 Open Positions:")
    if positions:
        for symbol, pos in positions.items():
            print(f" - {symbol}: {pos}")
    else:
        print(" - None")

# 💾 Confirm saving
def save_trade_summary():
    print("\n📤 Saving Trade History...")
    if os.path.exists(TRADE_LOG_FILE):
        print("✅ Trade history saved to trade_history.json")
    else:
        print("⚠️ No trades to save.")
