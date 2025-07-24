import requests
import pandas as pd
import time
from datetime import datetime, timedelta

def fetch_price_data(symbol: str, interval: str = "1h", days: int = 90, save_csv=False):
    """
    Fetch OHLCV data from Binance for a symbol and interval, over a custom number of days.
    Automatically paginates through historical candles.

    Params:
    - symbol: e.g., "BTCUSDT"
    - interval: e.g., "1h", "30m", "1d"
    - days: how many past days of data to fetch
    - save_csv: True to save CSV

    Returns:
    - pandas DataFrame
    """
    base_url = "https://api.binance.com/api/v3/klines"
    end_time = int(time.time() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    limit = 1000

    all_data = []

    while start_time < end_time:
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": start_time,
            "limit": limit
        }

        for attempt in range(3):
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                raw_data = response.json()
                break
            except Exception as e:
                print(f"❌ Error fetching {symbol} ({interval}): {e}")
                time.sleep(2)
        else:
            raise Exception(f"Failed after 3 retries for {symbol}")

        if not raw_data:
            print("⚠️ No more data returned.")
            break

        all_data += raw_data
        last_time = raw_data[-1][0]
        start_time = last_time + 1  # Avoid duplicate candle

        # Avoid hitting rate limits
        time.sleep(0.3)

    if not all_data:
        raise ValueError(f"⚠️ No data found for {symbol}")

    df = pd.DataFrame(all_data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    # Clean + format
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    df.set_index("open_time", inplace=True)

    if save_csv:
        filename = f"{symbol}_{interval}_last_{days}_days.csv"
        df.to_csv(filename)
        print(f"📁 Saved: {filename}")

    return df
