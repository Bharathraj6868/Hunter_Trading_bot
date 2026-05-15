class EquityProtector:
    def __init__(self, config):
        self.max_dd = config['risk']['max_drawdown_pct']

    def should_close_all(self, account):
        return account.equity <= account.balance * (1 - self.max_dd)