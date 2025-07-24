import json
import os
from price_data import fetch_price_data

PORTFOLIO_FILE = "portfolio.json"

# Load or initialize portfolio
if os.path.exists(PORTFOLIO_FILE):
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
else:
    portfolio = {
        "balance": 10000.0,
        "positions": {}
    }

def get_current_price(symbol):
    """
    Fetch the latest closing price for the given symbol (1h timeframe).
    """
    df = fetch_price_data(symbol, "1h")
    return round(df['close'].iloc[-1], 2)

def check_position(portfolio_data, symbol):
    """
    Check if an open position exists for a given symbol.
    """
    return symbol in portfolio_data["positions"]

def update_position(portfolio_data, symbol, action, price=None, capital_pct=0.05, timeframe="1h"):
    """
    Update portfolio when a trade is executed.
    BUY: Allocates capital and sets SL/TP.
    SELL: Removes position and adds profit/loss to balance.
    """
    action = action.upper()
    price = price or get_current_price(symbol)

    if action == "BUY":
        capital = portfolio_data["balance"] * capital_pct
        amount = capital / price
        stop_loss = round(price * 0.95, 2)  # 5% SL
        take_profit = round(price * 1.10, 2)  # 10% TP

        portfolio_data["positions"][symbol] = {
            "entry_price": round(price, 2),
            "amount": round(amount, 6),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timeframe": timeframe
        }

        portfolio_data["balance"] -= round(price * amount, 2)

    elif action == "SELL" and symbol in portfolio_data["positions"]:
        position = portfolio_data["positions"].pop(symbol)
        proceeds = round(price * position["amount"], 2)
        portfolio_data["balance"] += proceeds

    save_portfolio(portfolio_data)
    return portfolio_data

def auto_exit_check(portfolio_data, symbol):
    """
    Checks if the current price hits SL or TP. Returns "SL", "TP", or None.
    """
    if symbol not in portfolio_data["positions"]:
        return None

    current_price = get_current_price(symbol)
    pos = portfolio_data["positions"][symbol]

    if current_price <= pos["stop_loss"]:
        return "SL"
    elif current_price >= pos["take_profit"]:
        return "TP"
    return None

def get_portfolio():
    """
    Return the current portfolio.
    """
    return portfolio

def save_portfolio(data):
    """
    Save the current portfolio to JSON file.
    """
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=4)
