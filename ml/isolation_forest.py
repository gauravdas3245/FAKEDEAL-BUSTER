"""
Isolation Forest Anomaly Detection Module for FakeDeal Buster.

Provides an unsupervised pricing anomaly detector trained exclusively on natural chronological
training data using the agreed 4-feature numerical vector.

CRITICAL GOVERNANCE PRINCIPLES:
1. Unsupervised learning only: Zero reliance on zero-variance 'fake_discount_flag'.
2. Price-spike independence: 'price_spike_flag' is NOT used as ground truth or for oversampling.
3. Anomaly framing: Output is explicitly labeled as 'anomaly_score' and 'is_anomaly'.
   It is NEVER presented as a calibrated fraud probability or proof of illegal seller conduct.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ml.feature_extractor import FEATURE_NAMES


class IsolationForestDetector:
    """
    Wrapper for Scikit-Learn Isolation Forest applied to FakeDeal Buster pricing features.

    Detects multi-dimensional pricing anomalies (unusual combinations of MSRP markup, price depth,
    volatility, and recent surge) without requiring synthetic or unverified binary fraud labels.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.01,
        random_state: int = 42,
        max_samples: Union[str, int, float] = "auto",
        n_jobs: int = -1,
    ):
        """
        Initialize the anomaly detector.

        Args:
            n_estimators: Number of isolation trees (default 100).
            contamination: Expected proportion of outliers in the training population (default 0.01 = 1%).
            random_state: Seed for reproducibility.
            max_samples: Number of samples to draw from X to train each tree.
            n_jobs: Number of CPU threads to use (-1 = all available).
        """
        if not (0.0 < contamination <= 0.5):
            raise ValueError(f"contamination must be in (0.0, 0.5], got: {contamination}")

        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.max_samples = max_samples
        self.n_jobs = n_jobs

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            max_samples=self.max_samples,
            n_jobs=self.n_jobs,
        )
        self.is_fitted = False
        self.feature_names = list(FEATURE_NAMES)

    def fit(self, X: Union[pd.DataFrame, np.ndarray]) -> "IsolationForestDetector":
        """
        Fit the Isolation Forest exclusively on the natural training feature matrix.

        Args:
            X: 2D array or DataFrame of scaled numerical features of shape (N, 4).

        Returns:
            self
        """
        if isinstance(X, pd.DataFrame):
            arr = X[self.feature_names].to_numpy(dtype=np.float64)
        else:
            arr = np.asarray(X, dtype=np.float64)

        if arr.ndim != 2 or arr.shape[1] != len(self.feature_names):
            raise ValueError(
                f"Expected 2D array with {len(self.feature_names)} features, got shape {arr.shape}"
            )
        if not np.all(np.isfinite(arr)):
            raise ValueError("Training matrix contains non-finite values.")

        self.model.fit(arr)
        self.is_fitted = True
        return self

    def score(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Compute continuous anomaly scores.

        In scikit-learn IsolationForest:
        - decision_function returns negative values for anomalies and positive values for normal instances.
        - We invert this to yield an intuitive anomaly intensity: higher positive values = more anomalous.

        Returns:
            1D numpy array of anomaly intensity scores.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before scoring.")
        if isinstance(X, pd.DataFrame):
            arr = X[self.feature_names].to_numpy(dtype=np.float64)
        else:
            arr = np.asarray(X, dtype=np.float64)

        if arr.ndim == 1:
            arr = arr.reshape(1, -1)

        # Invert decision function: higher value = more anomalous
        raw_decision = self.model.decision_function(arr)
        return -raw_decision

    def predict_anomaly(self, X: Union[pd.DataFrame, np.ndarray]) -> Dict[str, Any]:
        """
        Predict whether observations are statistical pricing anomalies.

        Returns:
            Dict containing:
            - 'is_anomaly': bool (True if anomalous, False otherwise)
            - 'anomaly_score': float (continuous anomaly intensity)
            - 'raw_prediction': int (-1 for anomaly, 1 for inlier per sklearn)
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_anomaly().")
        if isinstance(X, pd.DataFrame):
            arr = X[self.feature_names].to_numpy(dtype=np.float64)
        else:
            arr = np.asarray(X, dtype=np.float64)

        if arr.ndim == 1:
            arr = arr.reshape(1, -1)

        raw_preds = self.model.predict(arr)  # -1 for anomaly, 1 for inlier
        scores = self.score(arr)

        if arr.shape[0] == 1:
            return {
                "is_anomaly": bool(raw_preds[0] == -1),
                "anomaly_score": float(scores[0]),
                "raw_prediction": int(raw_preds[0]),
            }

        return {
            "is_anomaly": (raw_preds == -1),
            "anomaly_score": scores,
            "raw_prediction": raw_preds,
        }

    def save(self, file_path: Union[str, Path]) -> None:
        """Save fitted detector using Joblib."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model.")
        joblib.dump(self, file_path)

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "IsolationForestDetector":
        """Load detector from Joblib file."""
        obj = joblib.load(file_path)
        if not isinstance(obj, cls):
            raise TypeError(f"Loaded object is not an instance of {cls.__name__}")
        return obj


def train_isolation_forest(
    X_train: Union[pd.DataFrame, np.ndarray],
    contamination: float = 0.01,
    n_estimators: int = 100,
    random_state: int = 42,
) -> IsolationForestDetector:
    """
    Factory function to train and return an IsolationForestDetector on a training matrix.

    Args:
        X_train: Training feature matrix.
        contamination: Contamination parameter (default 0.01).
        n_estimators: Number of trees.
        random_state: Random seed.

    Returns:
        Fitted IsolationForestDetector instance.
    """
    detector = IsolationForestDetector(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
    )
    detector.fit(X_train)
    return detector
