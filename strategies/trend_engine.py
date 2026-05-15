import pandas as pd

class TrendEngine:
    def __init__(self, config):
        self.ema_fast = config['indicators']['ema_fast']
        self.ema_medium = config['indicators']['ema_medium']
        self.ema_slow = config['indicators']['ema_slow']

    def detect_swings(self, df, strength=5):
        highs, lows = df['high'], df['low']
        sh, sl = [], []
        for i in range(strength, len(df)-strength):
            if highs.iloc[i] == highs.iloc[i-strength:i+strength+1].max():
                sh.append((i, highs.iloc[i]))
            if lows.iloc[i] == lows.iloc[i-strength:i+strength+1].min():
                sl.append((i, lows.iloc[i]))
        return sh, sl

    def market_structure(self, df):
        sh, sl = self.detect_swings(df, 5)
        if len(sh) < 2 or len(sl) < 2:
            return 'ranging'
        last_hh = sh[-1][1] > sh[-2][1]
        last_hl = sl[-1][1] > sl[-2][1]
        if last_hh and last_hl:
            return 'bullish'
        last_lh = sh[-1][1] < sh[-2][1]
        last_ll = sl[-1][1] < sl[-2][1]
        if last_lh and last_ll:
            return 'bearish'
        return 'ranging'

    def ema_alignment(self, df):
        if 'ema20' not in df.columns:
            return 'mixed'
        fast = df['ema20'].iloc[-1]
        medium = df['ema50'].iloc[-1]
        slow = df['ema200'].iloc[-1]
        if fast > medium > slow:
            return 'bullish'
        elif fast < medium < slow:
            return 'bearish'
        return 'mixed'

    def multi_tf_trend(self, data_dict):
        score = 0
        for tf, df in data_dict.items():
            if df is None or len(df) < 50:
                continue
            ema = self.ema_alignment(df)
            struct = self.market_structure(df)
            if ema == 'bullish' and struct == 'bullish':
                score += 2
            elif ema == 'bearish' and struct == 'bearish':
                score -= 2
            elif ema == 'bullish':
                score += 1
            elif ema == 'bearish':
                score -= 1
        if score >= 3:
            return 'bullish'
        elif score <= -3:
            return 'bearish'
        return 'neutral'