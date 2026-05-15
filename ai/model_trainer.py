from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import joblib
import numpy as np
from core.database import SessionLocal, TradeLog
import logging

logger = logging.getLogger("ModelTrainer")

class OnlineTrainer:
    def __init__(self):
        self.retrain_interval = 50
        self.last_count = 0

    def check_and_retrain(self):
        db = SessionLocal()
        total = db.query(TradeLog).filter(TradeLog.won != None).count()
        if total - self.last_count >= self.retrain_interval:
            self.retrain(db)
            self.last_count = total
        db.close()

    def retrain(self, db):
        records = db.query(TradeLog).filter(TradeLog.won != None).all()
        if len(records) < 100:
            return
        X = np.array([r.features for r in records])
        y = np.array([1 if r.won else 0 for r in records])
        # Time decay weighting
        weights = np.array([0.95 ** (len(records) - i) for i in range(len(records))])
        rf = RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42)
        rf.fit(X, y, sample_weight=weights)
        joblib.dump(rf, 'models/rf_model_v2.pkl')
        gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
        gb.fit(X, y, sample_weight=weights)
        joblib.dump(gb, 'models/gb_model_v2.pkl')
        logger.info(f"Model retrained on {len(records)} trades, accuracy: {rf.score(X,y):.2f}")