import MetaTrader5 as mt5
import time
import logging

logger = logging.getLogger("MT5Connector")

class MT5Connector:
    def __init__(self, path=None, login=None, password=None, server=None):
        self.path = path
        self.login = int(login) if login else None
        self.password = password
        self.server = server
        self.connected = False

    def connect(self):
        if not mt5.initialize(path=self.path, login=self.login,
                              password=self.password, server=self.server):
            logger.error(f"MT5 init failed: {mt5.last_error()}")
            return False
        self.connected = True
        logger.info("MT5 connected")
        return True

    def ensure_connected(self):
        if not self.connected or not mt5.terminal_info():
            logger.warning("MT5 disconnected, reconnecting...")
            self.shutdown()
            time.sleep(5)
            return self.connect()
        return True

    def shutdown(self):
        mt5.shutdown()
        self.connected = False

    def get_account_info(self):
        return mt5.account_info()

    def get_positions(self, symbol=None):
        return mt5.positions_get(symbol=symbol)

    def get_symbol_info(self, symbol):
        return mt5.symbol_info(symbol)

    def get_rates(self, symbol, timeframe, count=500):
        tf_map = {
            "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1,
            "MN1": mt5.TIMEFRAME_MN1
        }
        tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        return mt5.copy_rates_from_pos(symbol, tf, 0, count)