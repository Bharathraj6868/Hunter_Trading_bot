import numpy as np

class FeatureEngineer:
    @staticmethod
    def extract_all(df, trend_bias, regime):
        feats = []
        # Price momentum
        feats.append((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2])
        # Distance to EMAs
        for ema in ['ema20','ema50','ema200']:
            feats.append((df['close'].iloc[-1] - df[ema].iloc[-1]) / df[ema].iloc[-1])
        # RSI
        feats.append(df['rsi'].iloc[-1] / 100)
        # ATR ratio
        feats.append(df['atr'].iloc[-1] / df['close'].iloc[-1])
        # Volume surge
        avg_vol = df['tick_volume'].rolling(20).mean().iloc[-1]
        feats.append(df['tick_volume'].iloc[-1] / (avg_vol + 1e-9))
        # MACD hist
        feats.append(df['macd_hist'].iloc[-1])
        # Bollinger position
        bb_range = df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1]
        feats.append((df['close'].iloc[-1] - df['bb_lower'].iloc[-1]) / (bb_range + 1e-9))
        # SMC presence
        smc_cols = ['ob_bull','ob_bear','fvg_bull','fvg_bear','liq_sweep_high','liq_sweep_low']
        for col in smc_cols:
            feats.append(1 if df[col].iloc[-5:].any() else 0)
        # Trend
        feats.append(1 if trend_bias == 'bullish' else -1)
        # Regime
        feats.append(regime)
        # Candle signals
        cand_cols = ['bullish_engulfing','bearish_engulfing','pin_bar_bull','pin_bar_bear','hammer','shooting_star','doji']
        for col in cand_cols:
            feats.append(1 if df[col].iloc[-1] else 0)
        return np.array(feats)