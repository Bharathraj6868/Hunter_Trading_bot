import pandas as pd
import numpy as np
from strategies.trend_engine import TrendEngine
from strategies.smc_analyzer import SMCAnalyzer
from strategies.ict_analyzer import ICTAnalyzer
from strategies.pattern_detector import PatternDetector
from ai.feature_engineering import FeatureEngineer
from ai.scorer import AdaptiveScorer
from ai.regime_detector import RegimeDetector

class EntryEngine:
    def __init__(self, config):
        self.config = config
        self.trend = TrendEngine(config)
        self.smc = SMCAnalyzer()
        self.ict = ICTAnalyzer()
        self.pattern = PatternDetector()
        self.scorer = AdaptiveScorer()
        self.regime_detector = RegimeDetector()
        self.min_rr = config['entry']['min_rr_ratio']
        self.conf_tfs = config['entry']['confirmation_timeframes']

    def evaluate(self, multi_tf_data, symbol, spread_pips, news_ok, correlation_ok):
        if not news_ok or not correlation_ok:
            return None
        # Multi-TF trend
        trend_bias = self.trend.multi_tf_trend(multi_tf_data)
        if trend_bias == 'neutral':
            return None
        # Primary TF
        primary_tf = self.config['primary_tf']
        df = multi_tf_data.get(primary_tf)
        if df is None or len(df) < 100:
            return None
        # Ensure indicators
        from indicators.indicators import add_indicators
        df = add_indicators(df)
        df = self.smc.analyze(df)
        df = self.pattern.candle_patterns(df)

        # Candle confirmation
        if trend_bias == 'bullish':
            candle_ok = (df['bullish_engulfing'].iloc[-1] or df['pin_bar_bull'].iloc[-1] or df['morning_star'].iloc[-1])
        else:
            candle_ok = (df['bearish_engulfing'].iloc[-1] or df['pin_bar_bear'].iloc[-1] or df['evening_star'].iloc[-1])
        if not candle_ok:
            return None

        # Volume confirmation
        avg_vol = df['tick_volume'].rolling(20).mean().iloc[-1]
        if df['tick_volume'].iloc[-1] < avg_vol * self.config['entry']['min_volume_ratio']:
            return None

        # SMC check
        if self.config['entry']['use_smc']:
            if trend_bias == 'bullish':
                smc_ok = (not pd.isna(df['ob_bull'].iloc[-5:]).all() or
                          not pd.isna(df['fvg_bull'].iloc[-5:]).all() or
                          df['liq_sweep_low'].iloc[-5:].any())
            else:
                smc_ok = (not pd.isna(df['ob_bear'].iloc[-5:]).all() or
                          not pd.isna(df['fvg_bear'].iloc[-5:]).all() or
                          df['liq_sweep_high'].iloc[-5:].any())
            if not smc_ok:
                return None

        # Spread filter
        if spread_pips and spread_pips > self.config['risk']['max_spread_pips']:
            return None

        # ATR-based SL/TP
        atr = df['atr'].iloc[-1]
        sl_dist = atr * 1.5
        tp_dist = sl_dist * self.min_rr
        point = 0.00001 if 'JPY' not in symbol else 0.001  # simplified
        sl_pips = sl_dist / point
        tp_pips = tp_dist / point

        if trend_bias == 'bullish':
            direction = 'BUY'
            entry_price = df['close'].iloc[-1]
        else:
            direction = 'SELL'
            entry_price = df['close'].iloc[-1]

        # Market regime
        returns = df['close'].pct_change().dropna().values
        regime = self.regime_detector.predict(returns[-200:])
        # Extract features for AI
        features = FeatureEngineer.extract_all(df, trend_bias, regime)
        confidence, threshold = self.scorer.predict(features)
        if confidence < threshold:
            return None

        return {
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'sl_pips': sl_pips,
            'tp_pips': tp_pips,
            'confidence': confidence,
            'atr': atr,
            'features': features,
            'regime': regime
        }