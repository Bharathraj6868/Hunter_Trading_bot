from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trading_bot.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    ticket = Column(Integer, unique=True)
    symbol = Column(String)
    direction = Column(String)
    volume = Column(Float)
    entry_price = Column(Float)
    sl = Column(Float)
    tp = Column(Float)
    entry_time = Column(DateTime, default=datetime.datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    confidence = Column(Float)
    exit_reason = Column(String, nullable=True)

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id = Column(Integer, primary_key=True)
    ticket = Column(Integer)
    symbol = Column(String)
    direction = Column(String)
    entry_time = Column(DateTime, default=datetime.datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    profit_pips = Column(Float, nullable=True)
    features = Column(PickleType)
    won = Column(Boolean, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()