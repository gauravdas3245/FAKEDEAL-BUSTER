"""
Feature Preprocessor Module for FakeDeal Buster.

Provides reproducible scaling, feature alignment, and validation for the 4 Isolation Forest
numerical features. Ensures:
- Consistent feature order: ['msrp_to_30d_avg', 'ratio_to_30d_avg', 'price_volatility_30d', 'recent_7d_surge']
- Parameters fitted strictly on training data (no split leakage).
- JSON-serializable parameters (for lightweight backend deployment) and Joblib persistence.
- Rejection of non-finite or missing values during transformation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler, StandardScaler

from ml.feature_extractor import FEATURE_NAMES


class FeaturePreprocessor:
    """
    Reproducible preprocessor for FakeDeal Buster Isolation Forest numerical features.

    Maintains strict canonical feature ordering and fits center/scale statistics exclusively
    on training data to prevent split leakage.
    """

    def __init__(
        self,
        scaler_type: str = "robust",
        feature_names: Sequence[str] = FEATURE_NAMES,
    ):
        """
        Initialize preprocessor.

        Args:
            scaler_type: 'robust' (RobustScaler using median/IQR) or 'standard' (StandardScaler).
            feature_names: Canonical list of feature names.
        """
        if scaler_type not in ("robust", "standard"):
            raise ValueError(f"Unsupported scaler_type '{scaler_type}'. Choose 'robust' or 'standard'.")

        self.scaler_type = scaler_type
        self.feature_names = list(feature_names)
        self.scaler = RobustScaler() if scaler_type == "robust" else StandardScaler()
        self.is_fitted = False
        self.fitted_params_: Dict[str, Dict[str, float]] = {}

    def _extract_array(self, X: Union[pd.DataFrame, np.ndarray, Sequence[Sequence[float]]]) -> np.ndarray:
        """Convert input to a 2D float64 numpy array with canonical column alignment."""
        if isinstance(X, pd.DataFrame):
            missing_cols = [c for c in self.feature_names if c not in X.columns]
            if missing_cols:
                raise ValueError(f"Input DataFrame is missing required features: {missing_cols}")
            arr = X[self.feature_names].to_numpy(dtype=np.float64)
        elif isinstance(X, np.ndarray):
            if X.ndim == 1:
                arr = X.reshape(1, -1).astype(np.float64)
            elif X.ndim == 2:
                arr = X.astype(np.float64)
            else:
                raise ValueError(f"Expected 1D or 2D array, got shape {X.shape}")
            if arr.shape[1] != len(self.feature_names):
                raise ValueError(
                    f"Array column count ({arr.shape[1]}) does not match expected feature count ({len(self.feature_names)})."
                )
        else:
            arr = np.array(X, dtype=np.float64)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            if arr.shape[1] != len(self.feature_names):
                raise ValueError(f"Input dimension mismatch: expected {len(self.feature_names)} features, got {arr.shape[1]}")

        # Check for NaN / infinite values
        if not np.all(np.isfinite(arr)):
            raise ValueError("Input feature matrix contains NaN or non-finite values.")

        return arr

    def fit(self, X: Union[pd.DataFrame, np.ndarray]) -> "FeaturePreprocessor":
        """
        Fit scaling statistics on training data only.

        Args:
            X: Training feature matrix.

        Returns:
            self
        """
        arr = self._extract_array(X)
        self.scaler.fit(arr)
        self.is_fitted = True

        # Extract fitted center and scale per feature
        if self.scaler_type == "robust":
            centers = self.scaler.center_
            scales = self.scaler.scale_
        else:
            centers = self.scaler.mean_
            scales = self.scaler.scale_

        self.fitted_params_ = {
            feat: {
                "center": float(centers[i]),
                "scale": float(scales[i]),
            }
            for i, feat in enumerate(self.feature_names)
        }
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """
        Transform features using parameters fitted on training data.

        Args:
            X: Feature matrix to scale.

        Returns:
            Scaled 2D numpy array.
        """
        if not self.is_fitted:
            raise RuntimeError("FeaturePreprocessor must be fitted before calling transform().")
        arr = self._extract_array(X)
        return self.scaler.transform(arr)

    def fit_transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Fit on training data and return transformed matrix."""
        return self.fit(X).transform(X)

    def transform_single(self, feature_dict: Dict[str, float]) -> np.ndarray:
        """
        Transform a single dictionary of features for real-time inference.

        Args:
            feature_dict: Dictionary mapping feature names to numerical values.

        Returns:
            Scaled 1D numpy array of length 4.
        """
        if not self.is_fitted:
            raise RuntimeError("FeaturePreprocessor must be fitted before calling transform_single().")
        missing = [f for f in self.feature_names if f not in feature_dict]
        if missing:
            raise ValueError(f"Missing required features for inference: {missing}")

        raw_vec = np.array([[feature_dict[f] for f in self.feature_names]], dtype=np.float64)
        if not np.all(np.isfinite(raw_vec)):
            raise ValueError(f"Feature vector contains non-finite values: {feature_dict}")

        scaled_2d = self.scaler.transform(raw_vec)
        return scaled_2d[0]

    def save_json(self, json_path: Union[str, Path]) -> None:
        """Save fitted scaling parameters as human-readable JSON metadata."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted preprocessor.")
        payload = {
            "scaler_type": self.scaler_type,
            "feature_names": self.feature_names,
            "fitted_params": self.fitted_params_,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    @classmethod
    def load_json(cls, json_path: Union[str, Path]) -> "FeaturePreprocessor":
        """Reconstruct preprocessor from saved JSON configuration."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        preprocessor = cls(
            scaler_type=data["scaler_type"],
            feature_names=data["feature_names"],
        )
        # Reconstruct underlying sklearn scaler
        n_feats = len(preprocessor.feature_names)
        centers = np.zeros(n_feats, dtype=np.float64)
        scales = np.zeros(n_feats, dtype=np.float64)

        for i, feat in enumerate(preprocessor.feature_names):
            params = data["fitted_params"][feat]
            centers[i] = params["center"]
            scales[i] = params["scale"]

        if preprocessor.scaler_type == "robust":
            preprocessor.scaler.center_ = centers
            preprocessor.scaler.scale_ = scales
        else:
            preprocessor.scaler.mean_ = centers
            preprocessor.scaler.scale_ = scales

        preprocessor.scaler.n_features_in_ = n_feats
        preprocessor.fitted_params_ = data["fitted_params"]
        preprocessor.is_fitted = True
        return preprocessor

    def save_joblib(self, file_path: Union[str, Path]) -> None:
        """Save preprocessor state using Joblib."""
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted preprocessor.")
        joblib.dump(self, file_path)

    @classmethod
    def load_joblib(cls, file_path: Union[str, Path]) -> "FeaturePreprocessor":
        """Load preprocessor from Joblib file."""
        obj = joblib.load(file_path)
        if not isinstance(obj, cls):
            raise TypeError(f"Loaded object is not an instance of {cls.__name__}")
        return obj
