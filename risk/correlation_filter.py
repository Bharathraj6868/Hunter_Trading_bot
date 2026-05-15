class CorrelationFilter:
    def __init__(self, connector):
        self.connector = connector
        self.correlated_pairs = {
            'EURUSD': ['GBPUSD', 'USDCHF', 'EURJPY'],
            'GBPUSD': ['EURUSD', 'GBPJPY'],
            'XAUUSD': ['XAGUSD']
        }

    def is_correlated(self, symbol, direction, open_positions):
        for pos in open_positions:
            if pos.symbol in self.correlated_pairs.get(symbol, []):
                if (pos.type == 0 and direction == 'BUY') or (pos.type == 1 and direction == 'SELL'):
                    return True
        return False