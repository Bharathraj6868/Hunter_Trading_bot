import MetaTrader5 as mt5
from core.mt5_connector import MT5Connector

class RiskManager:
    def __init__(self, config, connector: MT5Connector):
        self.config = config['risk']
        self.connector = connector
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.consecutive_losses = 0

    def can_trade(self):
        acc = self.connector.get_account_info()
        if not acc:
            return False
        if self.daily_pnl <= -acc.balance * self.config['max_daily_risk']:
            return False
        if (acc.balance - acc.equity) / acc.balance > self.config['max_drawdown_pct']:
            return False
        if self.trades_today >= self.config['max_trades_per_day']:
            return False
        if self.consecutive_losses >= self.config['max_consecutive_losses']:
            return False
        return True

    def calculate_lot_size(self, symbol, sl_pips):
        risk_pct = self.config['risk_per_trade']
        acc = self.connector.get_account_info()
        risk_amount = acc.balance * risk_pct
        info = self.connector.get_symbol_info(symbol)
        if not info:
            return 0.0
        tick_val = info.trade_tick_value
        tick_size = info.trade_tick_size
        sl_price_move = sl_pips * info.point
        lot = risk_amount / (sl_price_move / tick_size * tick_val)
        step = info.volume_step
        lot = max(info.volume_min, min(info.volume_max, round(lot / step) * step))
        return lot

    def update_metrics(self, profit):
        self.daily_pnl += profit
        self.trades_today += 1
        if profit < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0