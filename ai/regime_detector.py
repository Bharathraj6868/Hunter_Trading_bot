import numpy as np
from hmmlearn import hmm

class RegimeDetector:
    def __init__(self):
        self.model = hmm.GaussianHMM(n_components=3, covariance_type="full", n_iter=100, random_state=42)
        self._trained = False

    def predict(self, returns):
        if len(returns) < 100:
            return 0
        X = returns.reshape(-1, 1)
        try:
            self.model.fit(X)
            state = self.model.predict(X)[-1]
            # Map to -1,0,1 (simplified)
            return state - 1
        except:
            return 0