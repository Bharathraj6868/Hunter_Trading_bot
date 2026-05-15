import joblib
import numpy as np

class AdaptiveScorer:
    def __init__(self):
        try:
            self.rf = joblib.load('models/rf_model_v2.pkl')
        except:
            self.rf = None
        try:
            self.gb = joblib.load('models/gb_model_v2.pkl')
        except:
            self.gb = None
        self.recent_wins = []
        self.base_threshold = 65

    def predict(self, features):
        prob = 0.5
        if self.rf:
            prob = self.rf.predict_proba([features])[0][1]
        if self.gb:
            prob = (prob + self.gb.predict_proba([features])[0][1]) / 2
        # Dynamic threshold
        if len(self.recent_wins) >= 20:
            winrate = sum(self.recent_wins[-20:]) / 20
            adj = self.base_threshold + 10 * (0.5 - winrate)
        else:
            adj = self.base_threshold
        return prob * 100, adj

    def update_outcome(self, won):
        self.recent_wins.append(won)
        if len(self.recent_wins) > 50:
            self.recent_wins.pop(0)