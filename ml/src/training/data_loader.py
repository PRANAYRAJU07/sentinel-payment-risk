"""
Sentinel ML — Phase 6 Data Loader
=================================
Reusable data loader for model training and evaluation.
Ensures identical preprocessing logic is applied to train, validation, and test sets.
"""

import logging
from pathlib import Path

import pandas as pd
from sklearn.pipeline import Pipeline

from ml.src.features.feature_pipeline import create_feature_pipeline, separate_target
from ml.src.preprocessing.data_contract import validate_raw_data
from ml.src.preprocessing.splitter import temporal_split

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_FILE = PROJECT_ROOT / "ml" / "data" / "raw" / "creditcard.csv"


def load_and_preprocess_data(
    file_path: Path = RAW_FILE,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.Series], Pipeline]:
    """
    Loads raw data, validates schema, applies temporal split, fits the feature pipeline
    ON TRAINING DATA ONLY, and transforms all sets.

    Returns:
        X_dict: Dictionary containing 'train', 'val', 'test' feature dataframes.
        y_dict: Dictionary containing 'train', 'val', 'test' target series.
        pipeline: The fitted scikit-learn feature pipeline.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at {file_path}")

    logger.info(f"Loading data from {file_path}")
    df_raw = pd.read_csv(file_path)

    logger.info("Validating data contract...")
    df_valid = validate_raw_data(df_raw, is_training=True)

    logger.info("Applying temporal split...")
    splits = temporal_split(df_valid, train_ratio=0.70, val_ratio=0.15)

    X_dict = {}
    y_dict = {}

    X_train_raw, y_train = separate_target(splits["train"])
    X_val_raw, y_val = separate_target(splits["val"])
    X_test_raw, y_test = separate_target(splits["test"])

    logger.info("Fitting feature pipeline on TRAIN set...")
    pipeline = create_feature_pipeline()
    X_train_trans = pipeline.fit_transform(X_train_raw)

    logger.info("Transforming validation and test sets...")
    X_val_trans = pipeline.transform(X_val_raw)
    X_test_trans = pipeline.transform(X_test_raw)

    X_dict = {"train": X_train_trans, "val": X_val_trans, "test": X_test_trans}

    y_dict = {"train": y_train, "val": y_val, "test": y_test}

    return X_dict, y_dict, pipeline
