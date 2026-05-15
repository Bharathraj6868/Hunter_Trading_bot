import pandas as pd
import talib

def add_indicators(df):
    df['ema20'] = talib.EMA(df['close'], timeperiod=20)
    df['ema50'] = talib.EMA(df['close'], timeperiod=50)
    df['ema200'] = talib.EMA(df['close'], timeperiod=200)
    df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    df['rsi'] = talib.RSI(df['close'], timeperiod=14)
    macd, signal, hist = talib.MACD(df['close'])
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_hist'] = hist
    upper, middle, lower = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower
    # VWAP
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (typical_price * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
    return df