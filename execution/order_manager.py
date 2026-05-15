import MetaTrader5 as mt5
from core.database import Trade, get_db
from datetime import datetime

class OrderManager:
    def __init__(self, connector, risk_mgr):
        self.connector = connector
        self.risk_mgr = risk_mgr

    def place_trade(self, signal):
        symbol = signal['symbol']
        direction = signal['direction']
        sl_pips = signal['sl_pips']
        tp_pips = signal['tp_pips']
        confidence = signal['confidence']

        lot = self.risk_mgr.calculate_lot_size(symbol, sl_pips)
        if lot <= 0:
            return None

        info = self.connector.get_symbol_info(symbol)
        point = info.point
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if direction == 'BUY' else tick.bid
        sl = price - sl_pips * point if direction == 'BUY' else price + sl_pips * point
        tp = price + tp_pips * point if direction == 'BUY' else price - tp_pips * point

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if direction == 'BUY' else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 123456,
            "comment": f"AI {confidence:.0f}%",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            db = next(get_db())
            trade = Trade(
                ticket=result.order,
                symbol=symbol,
                direction=direction,
                volume=lot,
                entry_price=price,
                sl=sl,
                tp=tp,
                confidence=confidence,
                entry_time=datetime.utcnow()
            )
            db.add(trade)
            db.commit()
            return result.order
        return None