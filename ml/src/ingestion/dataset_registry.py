"""
Sentinel ML — Dataset Registry
Defines all Kaggle datasets used in this project.

IMPORTANT:
- All dataset handles are verified against Kaggle before use.
- Never fabricate dataset statistics.
- Never store actual data in this file.
- Download with: python scripts/download_dataset.py
"""
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DatasetConfig:
    """Configuration for a Kaggle dataset."""
    dataset_name: str
    kaggle_handle: str        # Format: "owner/dataset-name"
    version: int
    expected_files: List[str]
    target_column: str
    description: str
    license_note: str


# -----------------------------------------------
# PRIMARY DATASET
#
# IEEE-CIS Fraud Detection
# Handle: mlg-ulb/creditcardfraud
#
# Why chosen:
# 1. Large: 284,807 transactions
# 2. Real-world: European credit card transactions from 2013
# 3. Well-labelled: binary fraud/legitimate
# 4. Temporal: ordered by time (important for time-aware evaluation)
# 5. Class imbalance: 0.17% fraud (realistic)
# 6. Widely studied: good benchmark for comparison
# 7. License: Database Contents License (DbCL) — public
#
# Limitations:
# - PCA-transformed features (V1-V28) — real feature names not disclosed
# - No merchant/device/IP columns — we use what's available
# - Synthetic behavioral/graph features will be clearly labeled
# -----------------------------------------------
PRIMARY_DATASET = DatasetConfig(
    dataset_name="Credit Card Fraud Detection",
    kaggle_handle="mlg-ulb/creditcardfraud",
    version=3,
    expected_files=["creditcard.csv"],
    target_column="Class",
    description=(
        "European credit card transactions from September 2013. "
        "284,807 transactions with 492 fraudulent (0.172%). "
        "Features V1-V28 are PCA-transformed for privacy. "
        "Time and Amount are original. Class is 1=fraud, 0=legitimate."
    ),
    license_note="Database Contents License (DbCL) v1.0 — freely usable for research",
)


# -----------------------------------------------
# ALTERNATIVE DATASETS (for future expansion)
# These are researched and documented but not yet integrated.
# -----------------------------------------------
ALTERNATIVE_DATASETS = [
    DatasetConfig(
        dataset_name="Online Payment Fraud Detection",
        kaggle_handle="rupakroy/online-payments-fraud-detection-dataset",
        version=1,
        expected_files=["onlinefraud.csv"],
        target_column="isFraud",
        description=(
            "Simulated mobile payment transactions. "
            "Includes transaction type, amount, nameOrig, nameDest. "
            "Better for merchant/customer relationship analysis."
        ),
        license_note="CC0 Public Domain",
    ),
    DatasetConfig(
        dataset_name="IEEE-CIS Fraud Detection",
        kaggle_handle="c/ieee-fraud-detection",
        version=1,
        expected_files=["train_transaction.csv", "train_identity.csv"],
        target_column="isFraud",
        description=(
            "Competition dataset with rich device, browser, email, "
            "and address features. Better for device/identity graph. "
            "Requires competition acceptance."
        ),
        license_note="Competition rules apply — requires acceptance",
    ),
]


# Default dataset for this project
ACTIVE_DATASET = PRIMARY_DATASET

# Raw data storage location (relative to project root)
RAW_DATA_DIR = "ml/data/raw"
PROCESSED_DATA_DIR = "ml/data/processed"
METADATA_FILE = "ml/data/dataset_metadata.json"

# Feature column definitions (PRIMARY_DATASET)
TIME_COLUMN = "Time"
AMOUNT_COLUMN = "Amount"
TARGET_COLUMN = "Class"
PCA_FEATURE_COLUMNS = [f"V{i}" for i in range(1, 29)]  # V1 to V28
ALL_FEATURE_COLUMNS = PCA_FEATURE_COLUMNS + [AMOUNT_COLUMN]

# Class labels
FRAUD_LABEL = 1
LEGITIMATE_LABEL = 0
