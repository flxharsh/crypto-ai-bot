import json
import os
from price_data import fetch_price_data

PORTFOLIO_FILE = "portfolio.json"

# 📦 Load or initialize portfolio
if os.path.exists(PORTFOLIO_FILE):
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
else:
    portfolio = {
        "balance": 10000.0,
        "positions": {}
    }

# 📈 Get the latest closing price (1h timeframe)
def get_current_price(symbol):
    try:
        df = fetch_price_data(symbol, "1h", days=1)
        return round(df['close'].iloc[-1], 2)
    except Exception as e:
        print(f"⚠️ Error fetching current price for {symbol}: {e}")
        return None

# 🔍 Check if a position exists
def check_position(portfolio_data, symbol):
    return symbol in portfolio_data["positions"]

# 🔄 Update portfolio after BUY or SELL
def update_position(portfolio_data, symbol, action, price=None, capital_pct=0.05, timeframe="1h"):
    action = action.upper()
    price = price or get_current_price(symbol)

    if price is None:
        print(f"❌ Price unavailable for {symbol}, skipping {action}")
        return portfolio_data

    if action == "BUY":
        capital = portfolio_data["balance"] * capital_pct
        amount = capital / price
        stop_loss = round(price * 0.95, 2)
        take_profit = round(price * 1.10, 2)

        portfolio_data["positions"][symbol] = {
            "entry_price": round(price, 2),
            "amount": round(amount, 6),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timeframe": timeframe
        }

        portfolio_data["balance"] -= round(price * amount, 2)
        print(f"✅ BUY {symbol} | Price: {price} | Amount: {amount} | SL: {stop_loss} | TP: {take_profit}")

    elif action == "SELL" and symbol in portfolio_data["positions"]:
        position = portfolio_data["positions"].pop(symbol)
        proceeds = round(price * position["amount"], 2)
        portfolio_data["balance"] += proceeds
        print(f"✅ SELL {symbol} | Exit Price: {price} | Proceeds: {proceeds}")

    save_portfolio(portfolio_data)
    return portfolio_data

# 🔁 Auto-check for Stop Loss or Take Profit
def auto_exit_check(portfolio_data, symbol):
    if symbol not in portfolio_data["positions"]:
        return None

    current_price = get_current_price(symbol)
    if current_price is None:
        return None

    pos = portfolio_data["positions"][symbol]

    if current_price <= pos["stop_loss"]:
        return "SL"
    elif current_price >= pos["take_profit"]:
        return "TP"
    return None

# 📊 Get current portfolio
def get_portfolio():
    return portfolio

# 💾 Save portfolio to JSON file
def save_portfolio(data):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=4)
