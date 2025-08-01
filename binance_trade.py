import ccxt
import os

# 🔐 Load API keys securely from environment variables
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

# ✅ Initialize Binance Futures client (LIVE)
binance = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',        # USDT-M Futures
        'defaultMarket': 'linear',
        'adjustForTimeDifference': True
    }
})

# ⚠️ DO NOT set sandbox or override URLs in LIVE mode

# 🧠 Format symbol correctly: BTCUSDT → BTC/USDT
def format_symbol(symbol):
    if "/" in symbol:
        return symbol
    return f"{symbol[:-4]}/{symbol[-4:]}"  # BTCUSDT → BTC/USDT

# 📉 Fetch current market price
def get_price(symbol):
    try:
        market_symbol = format_symbol(symbol)
        ticker = binance.fetch_ticker(market_symbol)
        price = float(ticker["last"])
        print(f"📉 Live price for {symbol}: {price}")
        return price
    except Exception as e:
        print(f"⚠️ Error fetching price for {symbol}: {e}")
        return None

# 💰 Get current available balance in USDT
def get_balance(asset="USDT"):
    try:
        balance = binance.fetch_balance()
        total = balance['total'].get(asset, 0)
        print(f"💵 Available Balance ({asset}): {total}")
        return float(total)
    except Exception as e:
        print(f"⚠️ Error fetching balance for {asset}: {e}")
        return 0.0

# ❌ Cancel all open orders for a symbol
def cancel_all_open_orders(symbol):
    try:
        market_symbol = format_symbol(symbol)
        orders = binance.fetch_open_orders(market_symbol)
        for order in orders:
            binance.cancel_order(order['id'], market_symbol)
        print(f"❌ Cancelled {len(orders)} open orders for {symbol}")
    except Exception as e:
        print(f"⚠️ Failed to cancel orders for {symbol}: {e}")

# 🛒 Place market or limit order
def place_order(symbol, side, amount, price=None, order_type="market", max_slippage_pct=0.5):
    try:
        side = side.lower()
        order_type = order_type.lower()
        market_symbol = format_symbol(symbol)

        if order_type == "market":
            current_price = get_price(symbol)
            if price and side == "buy":
                slippage = abs(price - current_price) / price * 100
                if slippage > max_slippage_pct:
                    raise Exception(f"❌ Slippage too high ({slippage:.2f}%) for BUY {symbol}")
            print(f"📤 Placing MARKET {side.upper()} order for {amount} {symbol}")
            order = binance.create_market_order(symbol=market_symbol, side=side, amount=amount)

        elif order_type == "limit":
            if price is None:
                raise ValueError("❌ Price required for limit order.")
            print(f"📤 Placing LIMIT {side.upper()} order for {amount} {symbol} @ {price}")
            order = binance.create_limit_order(symbol=market_symbol, side=side, amount=amount, price=price)

        else:
            raise ValueError(f"❌ Unsupported order type: {order_type}")

        print(f"✅ Order Placed! ID: {order['id']} | Status: {order.get('status')} | Qty: {order['amount']}")
        return order

    except Exception as e:
        print(f"❌ Order failed for {symbol}: {e}")
        return None
