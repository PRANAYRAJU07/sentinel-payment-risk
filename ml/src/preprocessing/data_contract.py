"""
Sentinel ML — Data Contract (Phase 5.2)
=======================================
Validates that incoming raw transaction dataframes conform to the
exact schema required by the feature engineering pipeline.

INPUT: Raw Kaggle transaction dataframe.
OUTPUT: Validated dataframe (or raises DataContractError).
"""

import pandas as pd


class DataContractError(Exception):
    """Raised when data fails to meet the contract requirements."""


class DataContract:
    def __init__(self):
        self.expected_target = "Class"
        self.expected_time = "Time"
        self.expected_amount = "Amount"
        self.expected_pca = [f"V{i}" for i in range(1, 29)]

        # We explicitly enforce columns that must be present
        self.required_columns = [
            self.expected_time,
            self.expected_amount,
        ] + self.expected_pca

        # If target is present, it must be validated too
        self.target_values = {0, 1}

    def validate(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """
        Validate the dataframe against the contract.

        Args:
            df: Input dataframe.
            is_training: If True, the target column ('Class') is strictly required.
                         If False, the target column is optional (e.g., for inference).

        Returns:
            Validated DataFrame.

        Raises:
            DataContractError if validation fails.
        """
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            raise DataContractError(f"Missing required columns: {missing_cols}")

        # Validate data types for required columns
        for col in self.required_columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise DataContractError(
                    f"Column '{col}' must be numeric, got {df[col].dtype}"
                )

        # Validate target if required or present
        if is_training:
            if self.expected_target not in df.columns:
                raise DataContractError(
                    f"Training data must contain target column '{self.expected_target}'"
                )

        if self.expected_target in df.columns:
            # Check target values (allow NaNs only if it's inference and we're missing labels,
            # but ideally for training it should be strictly 0/1)
            unique_targets = set(df[self.expected_target].dropna().unique())
            if not unique_targets.issubset(self.target_values):
                raise DataContractError(
                    f"Target column '{self.expected_target}' contains invalid values: {unique_targets - self.target_values}"
                )

        # Check for empty dataframe
        if df.empty:
            raise DataContractError("Dataframe is empty.")

        # Return a copy to prevent accidental mutations by caller
        return df.copy()


def validate_raw_data(df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
    """Convenience function to enforce the contract."""
    contract = DataContract()
    return contract.validate(df, is_training=is_training)
