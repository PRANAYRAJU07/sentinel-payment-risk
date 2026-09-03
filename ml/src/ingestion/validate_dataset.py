"""
Sentinel ML — Dataset Validator (Phase 3)
==========================================
Validates the downloaded creditcard fraud dataset.

This module:
- Checks file existence
- Reads the actual CSV (no fabrication)
- Validates schema, target column, data types
- Reports data quality issues
- Can be used standalone or imported by tests

Usage:
    python ml/src/ingestion/validate_dataset.py
"""

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Project paths ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_DIR = PROJECT_ROOT / "ml" / "data" / "raw"
METADATA_PATH = PROJECT_ROOT / "ml" / "data" / "dataset_metadata.json"
PRIMARY_FILE = RAW_DIR / "creditcard.csv"

# ── Expected schema (verified against actual Kaggle dataset) ──────────────────
EXPECTED_TARGET_COLUMN = "Class"
EXPECTED_TIME_COLUMN = "Time"
EXPECTED_AMOUNT_COLUMN = "Amount"
EXPECTED_PCA_COLUMNS = [f"V{i}" for i in range(1, 29)]  # V1 to V28
EXPECTED_COLUMNS = (
    [EXPECTED_TIME_COLUMN]
    + EXPECTED_PCA_COLUMNS
    + [EXPECTED_AMOUNT_COLUMN, EXPECTED_TARGET_COLUMN]
)
EXPECTED_COLUMN_COUNT = 31  # Time + V1-V28 + Amount + Class
FRAUD_LABEL = 1
LEGITIMATE_LABEL = 0

# ── Reasonable sanity bounds (not fabricated, conservative) ──────────────────
MIN_EXPECTED_ROWS = 250_000  # dataset has ~284k rows
MIN_EXPECTED_FRAUD_COUNT = 400  # dataset has ~492 fraud cases
MAX_EXPECTED_FRAUD_PERCENTAGE = 5.0  # fraud is <1% in reality


class DatasetValidationError(Exception):
    """Raised when the dataset fails validation."""


class DatasetValidator:
    """
    Validates the Credit Card Fraud Detection dataset.
    All validation is based on actual file contents.
    """

    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or PRIMARY_FILE
        self._df = None
        self.results: dict = {}

    # ── File checks ───────────────────────────────────────────────────────────

    def check_file_exists(self) -> bool:
        """Check that the dataset file exists."""
        exists = self.csv_path.exists()
        self.results["file_exists"] = exists
        if not exists:
            logger.error(
                f"Dataset file not found: {self.csv_path}\n"
                f"Run: python scripts/download_dataset.py"
            )
        return exists

    def check_file_readable(self) -> bool:
        """Check that the file can be opened and is non-empty."""
        try:
            size = self.csv_path.stat().st_size
            readable = size > 0
            self.results["file_readable"] = readable
            self.results["file_size_bytes"] = size
            return readable
        except Exception as e:
            self.results["file_readable"] = False
            logger.error(f"Cannot read file: {e}")
            return False

    # ── Load ─────────────────────────────────────────────────────────────────

    def load(self) -> bool:
        """Load the CSV into a DataFrame."""
        try:
            import pandas as pd

            self._df = pd.read_csv(self.csv_path)
            self.results["loaded"] = True
            return True
        except Exception as e:
            self.results["loaded"] = False
            logger.error(f"Failed to load CSV: {e}")
            return False

    # ── Schema validation ─────────────────────────────────────────────────────

    def validate_schema(self) -> bool:
        """Verify expected columns are present."""
        if self._df is None:
            return False

        actual_cols = list(self._df.columns)
        missing_cols = [c for c in EXPECTED_COLUMNS if c not in actual_cols]
        extra_cols = [c for c in actual_cols if c not in EXPECTED_COLUMNS]

        schema_valid = len(missing_cols) == 0
        self.results["schema_valid"] = schema_valid
        self.results["actual_columns"] = actual_cols
        self.results["missing_columns"] = missing_cols
        self.results["extra_columns"] = extra_cols
        self.results["column_count"] = len(actual_cols)

        if not schema_valid:
            logger.error(f"Missing columns: {missing_cols}")
        if extra_cols:
            logger.warning(f"Extra columns (unexpected): {extra_cols}")

        return schema_valid

    def validate_target_column(self) -> bool:
        """Verify target column exists and has expected binary values."""
        if self._df is None:
            return False

        if EXPECTED_TARGET_COLUMN not in self._df.columns:
            self.results["target_valid"] = False
            return False

        unique_values = sorted(self._df[EXPECTED_TARGET_COLUMN].unique().tolist())
        expected_values = [LEGITIMATE_LABEL, FRAUD_LABEL]
        target_valid = unique_values == expected_values

        self.results["target_valid"] = target_valid
        self.results["target_unique_values"] = unique_values

        if not target_valid:
            logger.error(
                f"Target column has unexpected values: {unique_values}. "
                f"Expected: {expected_values}"
            )

        return target_valid

    # ── Data quality checks ───────────────────────────────────────────────────

    def check_row_count(self) -> bool:
        """Verify dataset has at least MIN_EXPECTED_ROWS rows."""
        if self._df is None:
            return False

        n_rows = len(self._df)
        sufficient = n_rows >= MIN_EXPECTED_ROWS
        self.results["row_count"] = n_rows
        self.results["row_count_sufficient"] = sufficient

        if not sufficient:
            logger.warning(
                f"Row count {n_rows:,} is below minimum {MIN_EXPECTED_ROWS:,}. "
                f"Dataset may be incomplete."
            )

        return sufficient

    def check_missing_values(self) -> dict:
        """Count missing values per column."""
        if self._df is None:
            return {}

        missing = self._df.isna().sum()
        missing_dict = {col: int(cnt) for col, cnt in missing.items() if cnt > 0}
        total_missing = sum(missing_dict.values())

        self.results["missing_values_by_column"] = missing_dict
        self.results["total_missing_values"] = total_missing

        if total_missing > 0:
            logger.warning(f"Missing values found: {missing_dict}")
        else:
            logger.info("  ✓ No missing values")

        return missing_dict

    def check_duplicates(self) -> int:
        """Count duplicate rows."""
        if self._df is None:
            return 0

        n_dups = int(self._df.duplicated().sum())
        self.results["duplicate_rows"] = n_dups

        if n_dups > 0:
            logger.warning(f"  {n_dups} duplicate rows found")
        else:
            logger.info("  ✓ No duplicate rows")

        return n_dups

    def check_class_distribution(self) -> dict:
        """Calculate fraud/legitimate distribution."""
        if self._df is None:
            return {}

        counts = self._df[EXPECTED_TARGET_COLUMN].value_counts().to_dict()
        fraud_count = int(counts.get(FRAUD_LABEL, 0))
        legit_count = int(counts.get(LEGITIMATE_LABEL, 0))
        total = fraud_count + legit_count
        fraud_pct = (fraud_count / total * 100) if total > 0 else 0
        imbalance = legit_count / fraud_count if fraud_count > 0 else None

        dist = {
            "legitimate": legit_count,
            "fraud": fraud_count,
            "total": total,
            "fraud_percentage": round(fraud_pct, 4),
            "imbalance_ratio": round(imbalance, 1) if imbalance else None,
        }
        self.results["class_distribution"] = dist

        fraud_present = fraud_count >= MIN_EXPECTED_FRAUD_COUNT
        self.results["fraud_count_sufficient"] = fraud_present

        return dist

    def check_data_types(self) -> bool:
        """Verify numerical columns are numeric."""
        if self._df is None:
            return False

        non_numeric = []
        for col in self._df.columns:
            if col == EXPECTED_TARGET_COLUMN:
                continue
            if not self._df[col].dtype.kind in ("f", "i"):
                non_numeric.append(col)

        self.results["non_numeric_columns"] = non_numeric
        all_numeric = len(non_numeric) == 0

        if not all_numeric:
            logger.warning(f"Non-numeric columns: {non_numeric}")

        return all_numeric

    def check_no_corruption(self) -> bool:
        """Basic check that numerical columns don't have all-NaN issues."""
        if self._df is None:
            return False

        all_nan_cols = [
            col
            for col in EXPECTED_PCA_COLUMNS
            if col in self._df.columns and self._df[col].isna().all()
        ]
        self.results["all_nan_columns"] = all_nan_cols
        not_corrupted = len(all_nan_cols) == 0

        if not not_corrupted:
            logger.error(f"Fully NaN columns detected: {all_nan_cols}")

        return not_corrupted

    # ── Full validation ───────────────────────────────────────────────────────

    def validate_all(self) -> bool:
        """Run all validation checks. Returns True if all critical checks pass."""
        logger.info(f"\nValidating dataset: {self.csv_path}")
        logger.info("─" * 50)

        # Critical checks (must pass)
        if not self.check_file_exists():
            return False
        if not self.check_file_readable():
            return False
        if not self.load():
            return False

        schema_ok = self.validate_schema()
        target_ok = self.validate_target_column()
        rows_ok = self.check_row_count()

        # Informational checks (warnings, not failures)
        self.check_missing_values()
        self.check_duplicates()
        dist = self.check_class_distribution()
        self.check_data_types()
        self.check_no_corruption()

        critical_pass = schema_ok and target_ok
        self.results["overall_valid"] = critical_pass

        logger.info("─" * 50)
        if critical_pass:
            logger.info("  ✓ Dataset validation PASSED")
            logger.info(f"  Rows: {self.results.get('row_count', 'N/A'):,}")
            logger.info(
                f"  Fraud: {dist.get('fraud', 'N/A'):,} ({dist.get('fraud_percentage', 'N/A'):.4f}%)"
            )
            logger.info(f"  Imbalance ratio: {dist.get('imbalance_ratio', 'N/A')}:1")
        else:
            logger.error("  ✗ Dataset validation FAILED")

        return critical_pass

    def get_summary(self) -> dict:
        """Return a summary of all validation results."""
        return {k: v for k, v in self.results.items()}


# ── Standalone runner ─────────────────────────────────────────────────────────


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    validator = DatasetValidator()
    passed = validator.validate_all()

    if not passed:
        sys.exit(1)

    summary = validator.get_summary()
    print("\n── Validation Summary ──")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
