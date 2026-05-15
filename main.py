import asyncio
import yaml
import os
import threading
import time
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

from core.mt5_connector import MT5Connector
from core.data_fetcher import DataFetcher
from core.database import SessionLocal, TradeLog
from strategies.entry_engine import EntryEngine
from risk.risk_manager import RiskManager
from risk.correlation_filter import CorrelationFilter
from risk.equity_protector import EquityProtector
from execution.order_manager import OrderManager
from execution.exit_manager import ExitManager
from ai.model_trainer import OnlineTrainer
from ai.scorer import AdaptiveScorer
from ai.q_learner import QLearner
from utilities.logger import setup_logger
from utilities.alerts import AlertManager
from utilities.news_filter import NewsFilter

load_dotenv()
logger = setup_logger("MainBot")

def load_config():
    with open("config/config.yaml") as f:
        cfg = yaml.safe_load(f)
    # env var substitution
    for k, v in cfg.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, str) and vv.startswith("${"):
                    cfg[k][kk] = os.getenv(vv[2:-1])
        elif isinstance(v, str) and v.startswith("${"):
            cfg[k] = os.getenv(v[2:-1])
    return cfg

async def process_symbol(symbol, config, fetcher, entry_engine, risk_mgr, order_mgr, news, alerts, correlation):
    data = fetcher.fetch_multiple_timeframes(symbol, config['timeframes'], bars=200)
    if len(data) < len(config['timeframes']):
        return
    if news.is_news_nearby(datetime.now()):
        return
    if not risk_mgr.can_trade():
        return
    # Safe positions fetch
    positions = fetcher.connector.get_positions()
    if positions is None:
        positions = ()
    if correlation.is_correlated(symbol, None, positions):
        return
    spread = fetcher.get_current_spread(symbol)
    signal = entry_engine.evaluate(data, symbol, spread, True, True)
    if signal:
        ticket = order_mgr.place_trade(signal)
        if ticket:
            alerts.send(f"New trade: {symbol} {signal['direction']} Confidence:{signal['confidence']:.1f}%")
            logger.info(f"Trade opened: {symbol} {signal['direction']} Ticket:{ticket}")
            db = SessionLocal()
            db.add(TradeLog(ticket=ticket, symbol=symbol, direction=signal['direction'],
                            entry_time=datetime.utcnow(), features=signal['features']))
            db.commit()
            db.close()

async def close_monitor(connector, exit_mgr, db_session, risk_mgr, scorer, q_learner):
    while True:
        positions = connector.get_positions()
        if positions is None:
            await asyncio.sleep(10)
            continue
        open_tickets = [p.ticket for p in positions if p.magic == 123456]
        db = db_session()
        unclosed = db.query(TradeLog).filter(TradeLog.won == None).all()
        for rec in unclosed:
            if rec.ticket not in open_tickets:
                try:
                    history = mt5.history_deals_get(rec.entry_time, datetime.now())
                    if history is not None:
                        profit = sum(d.profit for d in history if d.position_id == rec.ticket)
                        rec.profit_pips = profit / (mt5.symbol_info(rec.symbol).point * 10) if mt5.symbol_info(rec.symbol) else 0
                        rec.won = profit > 0
                        rec.exit_time = datetime.utcnow()
                        db.commit()
                        risk_mgr.update_metrics(profit)
                        scorer.update_outcome(rec.won)
                except Exception as e:
                    logger.error(f"Error processing closed trade {rec.ticket}: {e}")
        db.close()
        await asyncio.sleep(10)

async def main():
    config = load_config()
    connector = MT5Connector(
        path=config['mt5']['path'],
        login=config['mt5']['login'],
        password=config['mt5']['password'],
        server=config['mt5']['server']
    )
    if not connector.connect():
        return

    fetcher = DataFetcher(connector)
    entry_engine = EntryEngine(config)
    risk_mgr = RiskManager(config, connector)
    order_mgr = OrderManager(connector, risk_mgr)
    correlation = CorrelationFilter(connector)
    equity_prot = EquityProtector(config)
    alerts = AlertManager(config)
    news = NewsFilter(config)
    q_learner = QLearner()
    exit_mgr = ExitManager(connector, config, q_learner)
    scorer = entry_engine.scorer
    trainer = OnlineTrainer()

    def train_loop():
        while True:
            trainer.check_and_retrain()
            time.sleep(300)
    threading.Thread(target=train_loop, daemon=True).start()

    asyncio.create_task(close_monitor(connector, exit_mgr, SessionLocal, risk_mgr, scorer, q_learner))

    symbols = config['symbols']
    logger.info("Bot started - Self-learning AI Trader")

    while True:
        connector.ensure_connected()
        acc = connector.get_account_info()
        if acc and equity_prot.should_close_all(acc):
            alerts.send("🚨 EQUITY PROTECTION: Closing all trades")
            positions = connector.get_positions()
            if positions:
                for pos in positions:
                    if pos.magic == 123456:
                        # Close position – simplified
                        try:
                            close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                            price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask
                            mt5.order_send({
                                "action": mt5.TRADE_ACTION_DEAL,
                                "position": pos.ticket,
                                "symbol": pos.symbol,
                                "volume": pos.volume,
                                "type": close_type,
                                "price": price,
                                "deviation": 20,
                                "magic": 123456,
                                "comment": "equity_protect"
                            })
                        except Exception as e:
                            logger.error(f"Emergency close failed: {e}")
            break

        exit_mgr.manage_positions()

        tasks = [process_symbol(s, config, fetcher, entry_engine, risk_mgr, order_mgr, news, alerts, correlation) for s in symbols]
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)

    connector.shutdown()

if __name__ == "__main__":
    asyncio.run(main())