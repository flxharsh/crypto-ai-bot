def detect_bos(df):
  """
  Detect Break of Structure from swing highs/lows.
  Returns list of BOS points.
  """
  if len(df) < 10:
      return []

  bos_list = []
  for i in range(5, len(df)):
      current_close = df.iloc[i]['close']
      prev_high = max(df['high'].iloc[i-5:i])
      prev_low = min(df['low'].iloc[i-5:i])

      if current_close > prev_high:
          bos_list.append({'type': 'BOS_UP', 'price': current_close, 'index': i})
      elif current_close < prev_low:
          bos_list.append({'type': 'BOS_DOWN', 'price': current_close, 'index': i})

  return bos_list
