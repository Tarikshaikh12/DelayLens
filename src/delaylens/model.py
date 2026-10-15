"""A fitted sklearn pipeline plus a separate chronological probability calibrator."""
import numpy as np
from sklearn.linear_model import LogisticRegression


def log_odds(probabilities):
    p = np.clip(probabilities, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p)).reshape(-1, 1)


class CalibratedRiskModel:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.calibrator = LogisticRegression(C=100.0, max_iter=1000, random_state=42)

    def fit_calibrator(self, X, y):
        self.calibrator.fit(log_odds(self.pipeline.predict_proba(X)[:, 1]), y)
        if self.calibrator.coef_[0, 0] <= 0:
            raise ValueError("Calibration reversed the risk ranking. Investigate before release.")
        return self

    def predict_proba(self, X):
        return self.calibrator.predict_proba(log_odds(self.pipeline.predict_proba(X)[:, 1]))
