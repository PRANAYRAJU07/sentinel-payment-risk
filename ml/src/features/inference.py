"""
Sentinel ML — Inference API Preparation (Phase 5.16)
====================================================
Interface for transforming raw transactions into feature vectors
for real-time inference.
"""

from typing import Any

import pandas as pd

from ml.src.features.feature_pipeline import load_pipeline, separate_target
from ml.src.preprocessing.data_contract import validate_raw_data


class TransactionTransformer:
    """
    Handles preprocessing of incoming transactions for inference.
    Loads the fitted feature pipeline and applies it.
    """

    def __init__(self, pipeline_path: str = "feature_pipeline.joblib"):
        self.pipeline = load_pipeline(pipeline_path)

    def transform_transaction(self, transaction: dict[str, Any]) -> pd.DataFrame:
        """
        Transforms a single raw transaction dictionary into a feature dataframe.

        Args:
            transaction: Dictionary containing raw transaction data.

        Returns:
            DataFrame containing the engineered features (1 row).
        """
        # Convert to DataFrame
        df_raw = pd.DataFrame([transaction])

        # Validate schema (is_training=False because target is optional at inference)
        df_validated = validate_raw_data(df_raw, is_training=False)

        # Ensure target is isolated if it happens to be present
        X, _ = separate_target(df_validated)

        # Apply transformation
        X_features = self.pipeline.transform(X)

        return X_features

    def transform_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms a batch of raw transactions into a feature dataframe.

        Args:
            df: DataFrame containing raw transaction data.

        Returns:
            DataFrame containing the engineered features.
        """
        # Validate schema (is_training=False because target is optional at inference)
        df_validated = validate_raw_data(df, is_training=False)

        # Ensure target is isolated if it happens to be present
        X, _ = separate_target(df_validated)

        # Apply transformation
        X_features = self.pipeline.transform(X)

        return X_features
