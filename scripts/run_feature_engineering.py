"""
Sentinel ML — Run Feature Engineering (Phase 5)
===============================================
Loads raw data, validates contract, splits it temporally,
fits the feature pipeline, transforms the data, and generates
feature distribution reports.
"""

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.features.feature_pipeline import (
    create_feature_pipeline,
    save_pipeline,
    separate_target,
)
from ml.src.preprocessing.data_contract import validate_raw_data
from ml.src.preprocessing.splitter import temporal_split

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RAW_FILE = PROJECT_ROOT / "ml" / "data" / "raw" / "creditcard.csv"
REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"


def generate_feature_profile(X_trans: pd.DataFrame) -> dict:
    """Generate basic stats for the transformed features."""
    profile = {}
    for col in X_trans.columns:
        series = X_trans[col]
        profile[col] = {
            "dtype": str(series.dtype),
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std()),
            "missing_count": int(series.isna().sum()),
            "infinite_count": int(np.isinf(series).sum()),
        }
    return profile


def analyze_correlations(X_trans: pd.DataFrame, threshold: float = 0.8) -> dict:
    """Find highly correlated features (absolute correlation > threshold)."""
    corr_matrix = X_trans.corr().abs()
    high_corr = []
    cols = corr_matrix.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if corr_matrix.iloc[i, j] > threshold:
                high_corr.append(
                    {
                        "feature_1": cols[i],
                        "feature_2": cols[j],
                        "correlation": float(corr_matrix.iloc[i, j]),
                    }
                )
    return {"high_correlations_above_0.8": high_corr}


def main():
    if not RAW_FILE.exists():
        logger.error(
            f"Raw dataset not found at {RAW_FILE}. Please run download_dataset.py first."
        )
        sys.exit(1)

    logger.info("Loading raw dataset...")
    df_raw = pd.read_csv(RAW_FILE)

    logger.info("Validating data contract...")
    df_valid = validate_raw_data(df_raw, is_training=True)

    logger.info("Splitting dataset temporally (70/15/15)...")
    splits = temporal_split(df_valid, train_ratio=0.70, val_ratio=0.15)

    X_train_raw, y_train = separate_target(splits["train"])
    X_val_raw, y_val = separate_target(splits["val"])
    X_test_raw, y_test = separate_target(splits["test"])

    logger.info("Initializing and fitting feature pipeline on TRAIN set only...")
    pipeline = create_feature_pipeline()

    import time

    t0 = time.time()
    X_train_trans = pipeline.fit_transform(X_train_raw)
    fit_time = time.time() - t0
    logger.info(f"Pipeline fit_transform took {fit_time:.2f} seconds.")

    logger.info("Transforming validation and test sets...")
    X_val_trans = pipeline.transform(X_val_raw)
    X_test_trans = pipeline.transform(X_test_raw)

    logger.info("Serializing pipeline...")
    save_pipeline(pipeline, "feature_pipeline.joblib")

    logger.info("Generating feature profile report...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    profile = generate_feature_profile(X_train_trans)

    correlations = analyze_correlations(X_train_trans)

    report = {
        "pipeline_fit_time_seconds": fit_time,
        "dataset_rows": len(df_raw),
        "train_rows": len(X_train_trans),
        "val_rows": len(X_val_trans),
        "test_rows": len(X_test_trans),
        "feature_count": len(X_train_trans.columns),
        "features": profile,
        "correlations": correlations,
    }

    report_path = REPORTS_DIR / "feature_profile.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Feature profile saved to {report_path}")
    logger.info(f"Feature count: {len(X_train_trans.columns)}")
    logger.info("Feature engineering complete!")


if __name__ == "__main__":
    main()
