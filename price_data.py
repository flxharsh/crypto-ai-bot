import requests
import pandas as pd
import time
from datetime import datetime, timedelta

def fetch_price_data(symbol: str, interval: str = "1h", days: int = 90, save_csv=False):
    base_url = "https://testnet.binancefuture.com/fapi/v1/klines"
    limit = 1000
    end_time = int(time.time() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    all_data = []
    print(f"📡 Fetching {symbol} | Interval: {interval} | Days: {days}")
    while start_time < end_time:
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": start_time,
            "limit": limit
        }
        for attempt in range(3):
            try:
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()
                raw_data = response.json()
                break
            except Exception as e:
                print(f"❌ Attempt {attempt+1} failed: {e}")
                time.sleep(1.5)
        else:
            print(f"❌ Failed 3 times while fetching {symbol} {interval}")
            return pd.DataFrame()
        if not raw_data:
            print("⚠️ No more data returned by Binance.")
            break
        all_data += raw_data
        last_candle = raw_data[-1][0]
        start_time = last_candle + 1
        time.sleep(0.3)
    if not all_data:
        raise ValueError(f"⚠️ No data found for {symbol}")
    df = pd.DataFrame(all_data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    df.set_index("open_time", inplace=True)
    if save_csv:
        filename = f"{symbol}_{interval}_last_{days}_days.csv"
        df.to_csv(filename)
        print(f"✅ Saved to CSV: {filename}")
    print(f"✅ Loaded: {symbol} | {len(df)} candles")
    return df
