import pandas as pd
import numpy as np

class SMCAnalyzer:
    @staticmethod
    def detect_order_blocks(df, atr_mult=0.3):
        df = df.copy()
        df['ob_bull'] = np.nan
        df['ob_bear'] = np.nan
        for i in range(2, len(df)-1):
            body = abs(df['close'].iloc[i] - df['open'].iloc[i])
            if body > df['atr'].iloc[i] * atr_mult:
                if df['close'].iloc[i] > df['open'].iloc[i] and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                    df.loc[df.index[i-1], 'ob_bull'] = df['high'].iloc[i-1]
                elif df['close'].iloc[i] < df['open'].iloc[i] and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                    df.loc[df.index[i-1], 'ob_bear'] = df['low'].iloc[i-1]
        return df

    @staticmethod
    def detect_fvg(df):
        df['fvg_bull'] = np.nan
        df['fvg_bear'] = np.nan
        for i in range(2, len(df)):
            if df['low'].iloc[i] > df['high'].iloc[i-1]:
                df.loc[df.index[i-1], 'fvg_bull'] = df['low'].iloc[i]
            if df['high'].iloc[i] < df['low'].iloc[i-1]:
                df.loc[df.index[i-1], 'fvg_bear'] = df['high'].iloc[i]
        return df

    @staticmethod
    def detect_liquidity_sweeps(df, lookback=10):
        df['liq_sweep_high'] = False
        df['liq_sweep_low'] = False
        for i in range(lookback+2, len(df)-2):
            recent_high = df['high'].iloc[i-lookback:i].max()
            recent_low = df['low'].iloc[i-lookback:i].min()
            if df['high'].iloc[i] > recent_high and df['close'].iloc[i] < recent_high:
                df.loc[df.index[i], 'liq_sweep_high'] = True
            if df['low'].iloc[i] < recent_low and df['close'].iloc[i] > recent_low:
                df.loc[df.index[i], 'liq_sweep_low'] = True
        return df

    def analyze(self, df):
        df = self.detect_order_blocks(df)
        df = self.detect_fvg(df)
        df = self.detect_liquidity_sweeps(df)
        return df