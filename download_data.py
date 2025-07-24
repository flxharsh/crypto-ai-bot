import requests
import pandas as pd
import os
from datetime import datetime

BASE_URL = "https://api.binance.com/api/v3/klines"

symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
intervals = ["30m", "1h"]
limit = 1000  # max allowed

INTERVAL_MAP = {
    "30m": "30m",
    "1h": "1h"
}

def fetch_klines(symbol, interval):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    ohlc = []
    for entry in data:
        ohlc.append({
            "timestamp": datetime.fromtimestamp(entry[0] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            "open": float(entry[1]),
            "high": float(entry[2]),
            "low": float(entry[3]),
            "close": float(entry[4]),
            "volume": float(entry[5])
        })

    return pd.DataFrame(ohlc)

def save_data(symbol, interval):
    df = fetch_klines(symbol, interval)
    os.makedirs("historical_data", exist_ok=True)
    filename = f"historical_data/{symbol}_{interval}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Saved {symbol} ({interval}) to {filename}")

if __name__ == "__main__":
    for sym in symbols:
        for tf in intervals:
            save_data(sym, INTERVAL_MAP[tf])
