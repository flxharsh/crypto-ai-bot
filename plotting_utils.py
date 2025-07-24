import mplfinance as mpf
import pandas as pd
import os

def plot_trade_chart(df, symbol, timeframe, signal, order_block_level=None, bos_levels=None, save_dir="charts"):
    # Ensure datetime index
    df['open_time'] = pd.to_datetime(df['open_time'])
    df.set_index('open_time', inplace=True)

    # Rename columns for mplfinance
    df = df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })

    # Create save directory if not exists
    os.makedirs(save_dir, exist_ok=True)

    # Plot style
    mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc)

    # Annotations
    add_plots = []
    alines = []

    if order_block_level:
        alines.append([(df.index[0], order_block_level), (df.index[-1], order_block_level)])

    if bos_levels:
        for bos in bos_levels:
            alines.append([(df.index[0], bos), (df.index[-1], bos)])

    title = f"{symbol} {timeframe.upper()} - {signal.upper()}"
    file_path = os.path.join(save_dir, f"{symbol}_{timeframe}.png")

    # Plot with mplfinance
    mpf.plot(df, type='candle', style=s, title=title, ylabel='Price',
             alines=dict(alines=alines, colors=['blue']*len(alines), linewidths=1),
             volume=True, savefig=file_path)

    print(f"📸 Chart saved: {file_path}")
    return file_path
