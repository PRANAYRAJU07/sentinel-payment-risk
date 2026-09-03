"""
Sentinel ML — Train/Test Splitting Utility (Phase 5.8 & 5.9)
============================================================
Handles the splitting of the dataset into Train, Validation, and Test sets.

Phase 5.8 & 5.9:
For fraud detection, temporal ordering is vital to prevent future data
from leaking into training. Therefore, we use a time-based split rather
than a random split.
"""

import pandas as pd


def temporal_split(
    df: pd.DataFrame,
    time_col: str = "Time",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> dict[str, pd.DataFrame]:
    """
    Splits the dataframe into train, validation, and test sets based on time.

    Args:
        df: Input dataframe (must contain time_col)
        time_col: Name of the column representing time (used for sorting)
        train_ratio: Proportion of data to use for training
        val_ratio: Proportion of data to use for validation
                   (The rest will be used for testing)

    Returns:
        Dictionary containing 'train', 'val', and 'test' dataframes.
    """
    if time_col not in df.columns:
        raise ValueError(f"Time column '{time_col}' not found in dataframe.")

    test_ratio = 1.0 - (train_ratio + val_ratio)
    if test_ratio < 0 or test_ratio > 1:
        raise ValueError("train_ratio + val_ratio must be <= 1.0")

    # Sort by time to ensure temporal ordering
    df_sorted = df.sort_values(by=time_col).reset_index(drop=True)

    n_total = len(df_sorted)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_df = df_sorted.iloc[:n_train].copy()
    val_df = df_sorted.iloc[n_train : n_train + n_val].copy()
    test_df = df_sorted.iloc[n_train + n_val :].copy()

    return {"train": train_df, "val": val_df, "test": test_df}
