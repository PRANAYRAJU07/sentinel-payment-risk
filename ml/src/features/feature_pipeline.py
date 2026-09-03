"""
Sentinel ML — Feature Pipeline (Phase 5)
========================================
Creates a reproducible, scikit-learn compatible feature engineering pipeline.

Phase 5.3: Target is strictly excluded.
Phase 5.4: Cyclic time features (hour_sin, hour_cos).
Phase 5.5: Amount log1p + scaling.
Phase 5.6: V1-V28 passed through.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "ml" / "models"


class TimeFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Phase 5.4: Temporal feature extraction.
    Assumes 'Time' is elapsed seconds. Extracts hour of day and applies
    cyclic encoding (sin/cos) to capture daily seasonality safely.
    """

    def __init__(self, time_col: str = "Time"):
        self.time_col = time_col
        self.feature_names_out_ = [f"{time_col}_hour_sin", f"{time_col}_hour_cos"]

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_out = pd.DataFrame(index=X.index)

        # Calculate hour of day (0-23.999...)
        # Time is in seconds.
        hours = (X[self.time_col] / 3600.0) % 24.0

        # Cyclic encoding
        X_out[self.feature_names_out_[0]] = np.sin(2 * np.pi * hours / 24.0)
        X_out[self.feature_names_out_[1]] = np.cos(2 * np.pi * hours / 24.0)

        return X_out

    def get_feature_names_out(self, input_features=None):
        return np.array(self.feature_names_out_)


def create_feature_pipeline() -> Pipeline:
    """
    Builds the complete feature engineering pipeline.

    The pipeline consists of:
    1. Time feature extraction (cyclic)
    2. Amount transformation (log1p -> StandardScaler)
    3. PCA feature passthrough (V1-V28)

    Returns:
        A scikit-learn Pipeline object.
    """
    pca_cols = [f"V{i}" for i in range(1, 29)]

    # Amount pipeline: log1p followed by standard scaling
    amount_pipeline = Pipeline(
        [
            ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
            ("scaler", StandardScaler()),
        ]
    )

    # Column transformer routes columns to appropriate transformers
    preprocessor = ColumnTransformer(
        transformers=[
            ("time", TimeFeatureExtractor(time_col="Time"), ["Time"]),
            ("amount", amount_pipeline, ["Amount"]),
            ("pca", "passthrough", pca_cols),  # Pass through V1-V28 unmodified
        ],
        remainder="drop",  # Explicitly drop anything else (like Class!)
        verbose_feature_names_out=False,
    )

    # We wrap it in a main pipeline so we can append other steps in future if needed
    pipeline = Pipeline([("preprocessor", preprocessor)])

    # Enable outputting pandas DataFrames directly (scikit-learn >= 1.2 feature)
    pipeline.set_output(transform="pandas")

    return pipeline


def separate_target(
    df: pd.DataFrame, target_col: str = "Class"
) -> tuple[pd.DataFrame, pd.Series | None]:
    """
    Phase 5.3: Ensure strictly isolated target column.

    Args:
        df: Input dataframe
        target_col: Name of the target column

    Returns:
        Tuple of (X, y) where X is the features dataframe and y is the target series (or None).
    """
    if target_col in df.columns:
        X = df.drop(columns=[target_col])
        y = df[target_col]
        return X, y
    return df.copy(), None


def save_pipeline(
    pipeline: Pipeline, filename: str = "feature_pipeline.joblib"
) -> Path:
    """Serialize the fitted pipeline to disk."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = MODELS_DIR / filename
    joblib.dump(pipeline, filepath)
    return filepath


def load_pipeline(filename: str = "feature_pipeline.joblib") -> Pipeline:
    """Load a serialized pipeline from disk."""
    filepath = MODELS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Pipeline file not found: {filepath}")
    return joblib.load(filepath)
