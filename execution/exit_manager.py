import MetaTrader5 as mt5
from core.database import Trade, TradeLog, get_db
from datetime import datetime
from ai.q_learner import QLearner
import numpy as np

class ExitManager:
    def __init__(self, connector, config, q_learner=None):
        self.connector = connector
        self.config = config
        self.trail_atr_mult = config['risk']['trailing_step_atr_mult']
        self.breakeven_atr_mult = config['risk']['breakeven_after_atr_mult']
        self.partial_ratio = config['risk']['partial_tp_ratio']
        self.partial_atr_mult = config['risk']['partial_tp_atr_mult']
        self.q_learner = q_learner

    def manage_positions(self):
        positions = self.connector.get_positions()
        if positions is None:
            return
        for pos in positions:
            if pos.magic != 123456:
                continue
            self._manage_single(pos)

    def _manage_single(self, pos):
        symbol = pos.symbol
        info = self.connector.get_symbol_info(symbol)
        if info is None:
            return
        point = info.point
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return
        current_price = tick.bid if pos.type == 0 else tick.ask
        atr = self._get_atr(symbol)
        if atr is None:
            return

        # Breakeven move
        if pos.sl != 0:
            profit_pips = abs(current_price - pos.price_open) / point
            if profit_pips >= self.breakeven_atr_mult * atr / point:
                new_sl = pos.price_open
                if (pos.type == 0 and new_sl > pos.sl) or (pos.type == 1 and new_sl < pos.sl):
                    self._modify_sl(pos.ticket, new_sl)

        # Trailing with optional RL override
        trail_mult = self.trail_atr_mult
        if self.q_learner:
            regime = self._get_regime(symbol)  # implement if needed
            state = self.q_learner.get_state(regime, profit_pips, atr/point)
            action_idx = self.q_learner.choose_action(state)
            trail_mult = self.q_learner.actions[action_idx]

        trail_dist = atr * trail_mult
        if pos.type == 0:
            new_sl = current_price - trail_dist
            if new_sl > pos.sl + trail_dist * 0.3:
                self._modify_sl(pos.ticket, new_sl)
        else:
            new_sl = current_price + trail_dist
            if new_sl < pos.sl - trail_dist * 0.3:
                self._modify_sl(pos.ticket, new_sl)

        # Partial TP
        if self.partial_ratio > 0 and pos.tp != 0:
            tp_price = pos.tp
            if (pos.type == 0 and current_price >= tp_price) or (pos.type == 1 and current_price <= tp_price):
                close_vol = pos.volume * self.partial_ratio
                self._close_partial(pos.ticket, close_vol)

    def _get_atr(self, symbol):
        # Replace this with a real ATR fetch (from live data cache)
        # For now, return a safe default to avoid stalling
        return 0.0015  # This is a placeholder – implement proper live ATR retrieval

    def _get_regime(self, symbol):
        # Placeholder – you can return 0 for now
        return 0

    def _modify_sl(self, ticket, sl):
        request = {"action": mt5.TRADE_ACTION_SLTP, "position": ticket, "sl": sl}
        mt5.order_send(request)

    def _close_partial(self, ticket, volume):
        pos = mt5.positions_get(ticket=ticket)
        if pos is None or len(pos) == 0:
            return
        pos = pos[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": pos.symbol,
            "volume": volume,
            "type": close_type,
            "price": price,
            "deviation": 20,
            "magic": 123456,
            "comment": "partial"
        }
        mt5.order_send(request)