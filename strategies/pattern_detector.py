import talib
import pandas as pd

class PatternDetector:
    @staticmethod
    def candle_patterns(df):
        df = df.copy()
        df['bullish_engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close']) > 0
        df['bearish_engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close']) < 0
        body = abs(df['close'] - df['open'])
        upper_wick = df['high'] - df[['close','open']].max(axis=1)
        lower_wick = df[['close','open']].min(axis=1) - df['low']
        df['pin_bar_bull'] = (lower_wick > body * 2) & (upper_wick < body * 0.5)
        df['pin_bar_bear'] = (upper_wick > body * 2) & (lower_wick < body * 0.5)
        df['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close']) > 0
        df['shooting_star'] = talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close']) > 0
        df['doji'] = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close']) > 0
        df['morning_star'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close']) > 0
        df['evening_star'] = talib.CDLEVENINGSTAR(df['open'], df['high'], df['low'], df['close']) > 0
        return df