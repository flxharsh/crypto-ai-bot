import pandas as pd

def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    Calculates MACD and signal line.
    """
    df['ema_fast'] = df['close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    df['signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
    return df

def detect_macd_signal(df):
    """
    Detects MACD crossover signals.
    Returns: "BUY", "SELL", or None
    """
    df = calculate_macd(df)

    if len(df) < 2:
        return None

    macd_prev = df['macd'].iloc[-2]
    macd_curr = df['macd'].iloc[-1]
    signal_prev = df['signal'].iloc[-2]
    signal_curr = df['signal'].iloc[-1]

    if macd_prev < signal_prev and macd_curr > signal_curr:
        return "BUY"
    elif macd_prev > signal_prev and macd_curr < signal_curr:
        return "SELL"
    else:
        return None
