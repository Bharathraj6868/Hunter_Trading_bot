import pandas as pd
import numpy as np
from core.mt5_connector import MT5Connector

class DataFetcher:
    def __init__(self, connector: MT5Connector):
        self.connector = connector

    def fetch_ohlcv(self, symbol, timeframe, bars=500):
        rates = self.connector.get_rates(symbol, timeframe, bars)
        if rates is None or len(rates) == 0:
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df

    def fetch_multiple_timeframes(self, symbol, timeframes, bars=500):
        data = {}
        for tf in timeframes:
            df = self.fetch_ohlcv(symbol, tf, bars)
            if df is not None:
                data[tf] = df
        return data

    def get_current_spread(self, symbol):
        info = self.connector.get_symbol_info(symbol)
        if info:
            return (info.ask - info.bid) * 10**info.digits
        return None