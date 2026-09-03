"""
Sentinel ML — Phase 3: Dataset Ingestion Tests
================================================
Tests that can run WITHOUT the dataset (unit tests).
Tests that require the dataset are marked: @pytest.mark.requires_dataset

Run all: pytest ml/tests/
Run without dataset: pytest ml/tests/ -m "not requires_dataset"
"""

import json
import sys
from pathlib import Path

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.ingestion.dataset_registry import (
    ACTIVE_DATASET,
    AMOUNT_COLUMN,
    EXPECTED_COLUMN_COUNT,
    EXPECTED_TARGET_COLUMN,
    FRAUD_LABEL,
    LEGITIMATE_LABEL,
    PCA_FEATURE_COLUMNS,
    PRIMARY_DATASET,
    TIME_COLUMN,
)
from ml.src.ingestion.validate_dataset import EXPECTED_COLUMNS, DatasetValidator

# ─────────────────────────────────────────────────────────────────────────────
# Dataset Registry Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestDatasetRegistry:
    """Tests for dataset_registry.py — no download required."""

    def test_primary_dataset_has_handle(self):
        assert PRIMARY_DATASET.kaggle_handle == "mlg-ulb/creditcardfraud"

    def test_primary_dataset_target_column(self):
        assert PRIMARY_DATASET.target_column == "Class"

    def test_primary_dataset_expected_files(self):
        assert "creditcard.csv" in PRIMARY_DATASET.expected_files

    def test_active_dataset_is_primary(self):
        assert ACTIVE_DATASET == PRIMARY_DATASET

    def test_pca_columns_count(self):
        """V1 through V28 = 28 PCA features."""
        assert len(PCA_FEATURE_COLUMNS) == 28
        assert PCA_FEATURE_COLUMNS[0] == "V1"
        assert PCA_FEATURE_COLUMNS[-1] == "V28"

    def test_expected_column_count(self):
        """31 = Time + V1-V28 + Amount + Class."""
        assert EXPECTED_COLUMN_COUNT == 31

    def test_expected_columns_list(self):
        """Verify full expected schema matches registry."""
        assert TIME_COLUMN in EXPECTED_COLUMNS
        assert AMOUNT_COLUMN in EXPECTED_COLUMNS
        assert EXPECTED_TARGET_COLUMN in EXPECTED_COLUMNS
        for col in PCA_FEATURE_COLUMNS:
            assert col in EXPECTED_COLUMNS

    def test_class_labels(self):
        assert FRAUD_LABEL == 1
        assert LEGITIMATE_LABEL == 0

    def test_dataset_has_license(self):
        assert PRIMARY_DATASET.license_note != ""

    def test_dataset_has_description(self):
        assert len(PRIMARY_DATASET.description) > 10

    def test_kaggle_handle_format(self):
        """Kaggle handles must be in 'owner/dataset' format."""
        parts = PRIMARY_DATASET.kaggle_handle.split("/")
        assert len(parts) == 2
        assert parts[0] != ""
        assert parts[1] != ""


# ─────────────────────────────────────────────────────────────────────────────
# Validator Unit Tests (with synthetic DataFrame)
# ─────────────────────────────────────────────────────────────────────────────


class TestDatasetValidatorUnit:
    """
    Tests DatasetValidator logic using synthetic DataFrames.
    No dataset download required.
    """

    @pytest.fixture
    def synthetic_df(self):
        """Create a minimal synthetic DataFrame matching creditcard schema."""
        import numpy as np
        import pandas as pd

        n = 1000
        n_fraud = 5

        data = {TIME_COLUMN: range(n), AMOUNT_COLUMN: [10.0] * n}
        for col in PCA_FEATURE_COLUMNS:
            data[col] = np.random.randn(n)
        data[EXPECTED_TARGET_COLUMN] = [1] * n_fraud + [0] * (n - n_fraud)

        return pd.DataFrame(data)

    @pytest.fixture
    def synthetic_csv(self, synthetic_df, tmp_path):
        """Write synthetic DataFrame to a temporary CSV file."""
        csv_path = tmp_path / "creditcard.csv"
        synthetic_df.to_csv(csv_path, index=False)
        return csv_path

    def test_validator_loads_synthetic_csv(self, synthetic_csv):
        validator = DatasetValidator(csv_path=synthetic_csv)
        assert validator.check_file_exists()
        assert validator.check_file_readable()
        assert validator.load()

    def test_validator_schema_passes_for_correct_schema(self, synthetic_csv):
        validator = DatasetValidator(csv_path=synthetic_csv)
        validator.load()
        assert validator.validate_schema()

    def test_validator_target_column_present(self, synthetic_csv):
        validator = DatasetValidator(csv_path=synthetic_csv)
        validator.load()
        assert validator.validate_target_column()

    def test_validator_class_distribution(self, synthetic_csv):
        validator = DatasetValidator(csv_path=synthetic_csv)
        validator.load()
        dist = validator.check_class_distribution()
        assert dist["fraud"] == 5
        assert dist["legitimate"] == 995
        assert 0 < dist["fraud_percentage"] < 1.0

    def test_validator_detects_missing_values(self, tmp_path):
        """Validator should detect and report missing values."""
        import pandas as pd

        data = {col: [None, 1.0, 2.0] for col in EXPECTED_COLUMNS}
        df = pd.DataFrame(data)
        csv = tmp_path / "missing.csv"
        df.to_csv(csv, index=False)

        validator = DatasetValidator(csv_path=csv)
        validator.load()
        missing = validator.check_missing_values()
        assert sum(missing.values()) > 0

    def test_validator_detects_duplicates(self, tmp_path):
        """Validator must detect duplicate rows."""
        import pandas as pd

        n = 100
        data = {TIME_COLUMN: list(range(n)), AMOUNT_COLUMN: [10.0] * n}
        for col in PCA_FEATURE_COLUMNS:
            data[col] = [0.5] * n
        data[EXPECTED_TARGET_COLUMN] = [0] * n
        df = pd.DataFrame(data)
        df = pd.concat([df, df.iloc[:5]])  # add 5 duplicates
        csv = tmp_path / "dups.csv"
        df.to_csv(csv, index=False)

        validator = DatasetValidator(csv_path=csv)
        validator.load()
        n_dups = validator.check_duplicates()
        assert n_dups == 5

    def test_validator_fails_for_nonexistent_file(self, tmp_path):
        validator = DatasetValidator(csv_path=tmp_path / "nonexistent.csv")
        assert not validator.check_file_exists()

    def test_validator_fails_for_missing_target_column(self, tmp_path):
        """Validator must fail if target column is missing."""
        import pandas as pd

        data = {
            col: [1.0, 2.0] for col in EXPECTED_COLUMNS if col != EXPECTED_TARGET_COLUMN
        }
        df = pd.DataFrame(data)
        csv = tmp_path / "no_target.csv"
        df.to_csv(csv, index=False)

        validator = DatasetValidator(csv_path=csv)
        validator.load()
        assert not validator.validate_schema()

    def test_validator_full_run_passes_synthetic(self, synthetic_csv):
        """Full validation must pass on a correct synthetic dataset."""
        validator = DatasetValidator(csv_path=synthetic_csv)
        result = validator.validate_all()
        assert result is True


# ─────────────────────────────────────────────────────────────────────────────
# Security Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestSecurityConstraints:
    """
    Verify no secrets are accidentally exposed.
    """

    def _project_root(self):
        """Resolve project root relative to this test file."""
        # ml/tests/ → ml/ → project root
        return Path(__file__).resolve().parent.parent.parent

    def test_download_script_has_no_hardcoded_token(self):
        """The download script must never contain a real API token."""
        script_path = self._project_root() / "scripts" / "download_dataset.py"
        if not script_path.exists():
            pytest.skip(f"Script not found: {script_path}")
        script = script_path.read_text(encoding="utf-8")
        # Real tokens are 32-char hex strings assigned to a variable
        import re

        suspicious = re.findall(
            r'(?i)(?:key|token|api)\s*=\s*["\']([a-f0-9]{32})["\']', script
        )
        assert suspicious == [], f"Possible hardcoded token found: {suspicious}"

    def test_download_script_reads_from_env(self):
        """Download script must read credentials from os.environ."""
        script_path = self._project_root() / "scripts" / "download_dataset.py"
        if not script_path.exists():
            pytest.skip(f"Script not found: {script_path}")
        script = script_path.read_text(encoding="utf-8")
        assert "os.environ" in script
        assert "KAGGLE_USERNAME" in script
        assert "KAGGLE_API_TOKEN" in script

    def test_env_file_is_gitignored(self):
        """The .env file must be listed in .gitignore."""
        gitignore = (self._project_root() / ".gitignore").read_text(encoding="utf-8")
        assert ".env\n" in gitignore or ".env\r\n" in gitignore

    def test_raw_data_dir_is_gitignored(self):
        """ml/data/raw/ must be in .gitignore."""
        gitignore = (self._project_root() / ".gitignore").read_text(encoding="utf-8")
        assert "ml/data/raw/" in gitignore

    def test_csv_extension_is_gitignored(self):
        """*.csv files must be in .gitignore."""
        gitignore = (self._project_root() / ".gitignore").read_text(encoding="utf-8")
        assert "*.csv" in gitignore

    def test_dataset_registry_has_no_secrets(self):
        """dataset_registry.py must contain no credentials."""
        registry_path = (
            self._project_root() / "ml" / "src" / "ingestion" / "dataset_registry.py"
        )
        registry = registry_path.read_text(encoding="utf-8")
        import re

        suspicious = re.findall(
            r'(?i)(?:key|token|password)\s*=\s*["\']([a-zA-Z0-9]{10,})["\']', registry
        )
        assert suspicious == [], f"Suspicious credential found: {suspicious}"


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests (require downloaded dataset)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.requires_dataset
class TestWithRealDataset:
    """
    Integration tests that run only when the real dataset is present.
    Skip in CI with: pytest -m "not requires_dataset"
    """

    @pytest.fixture(scope="class")
    def real_csv_path(self):
        path = PROJECT_ROOT / "ml" / "data" / "raw" / "creditcard.csv"
        if not path.exists():
            pytest.skip(
                f"Real dataset not found: {path}\n"
                f"Run: python scripts/download_dataset.py"
            )
        return path

    def test_real_dataset_exists(self, real_csv_path):
        assert real_csv_path.exists()

    def test_real_dataset_is_readable(self, real_csv_path):
        import pandas as pd

        df = pd.read_csv(real_csv_path, nrows=5)
        assert len(df) == 5

    def test_real_dataset_row_count(self, real_csv_path):
        """Must have at least 250,000 rows."""
        import pandas as pd

        df = pd.read_csv(real_csv_path)
        assert len(df) >= 250_000, f"Only {len(df):,} rows — dataset incomplete?"

    def test_real_dataset_schema(self, real_csv_path):
        """All 31 expected columns must be present."""
        import pandas as pd

        df = pd.read_csv(real_csv_path, nrows=1)
        for col in EXPECTED_COLUMNS:
            assert col in df.columns, f"Missing column: {col}"

    def test_real_dataset_target_values(self, real_csv_path):
        """Target must have exactly 2 unique values: 0 and 1."""
        import pandas as pd

        df = pd.read_csv(real_csv_path)
        unique = sorted(df[EXPECTED_TARGET_COLUMN].unique().tolist())
        assert unique == [0, 1]

    def test_real_dataset_no_all_nan_columns(self, real_csv_path):
        """No column should be entirely NaN."""
        import pandas as pd

        df = pd.read_csv(real_csv_path)
        all_nan = [col for col in df.columns if df[col].isna().all()]
        assert all_nan == [], f"All-NaN columns found: {all_nan}"

    def test_metadata_file_exists(self):
        meta = PROJECT_ROOT / "ml" / "data" / "dataset_metadata.json"
        assert meta.exists(), (
            f"Metadata not found: {meta}\n" f"Run: python scripts/download_dataset.py"
        )

    def test_metadata_has_required_keys(self):
        meta = PROJECT_ROOT / "ml" / "data" / "dataset_metadata.json"
        if not meta.exists():
            pytest.skip("Metadata not generated yet")
        with open(meta) as f:
            data = json.load(f)
        for key in [
            "dataset_name",
            "handle",
            "downloaded_at",
            "dimensions",
            "target_distribution",
        ]:
            assert key in data, f"Missing key in metadata: {key}"

    def test_metadata_no_credentials(self):
        """Metadata must not contain the Kaggle API token."""
        meta = PROJECT_ROOT / "ml" / "data" / "dataset_metadata.json"
        if not meta.exists():
            pytest.skip("Metadata not generated yet")
        content = meta.read_text()
        import re

        tokens = re.findall(r"\b[a-f0-9]{32}\b", content)
        # Allow SHA256 checksums (64 chars) but not 32-char API tokens
        assert tokens == [], f"Possible credential in metadata: {tokens[:1]}"

    def test_full_validator_on_real_dataset(self, real_csv_path):
        """DatasetValidator must pass all critical checks on real dataset."""
        validator = DatasetValidator(csv_path=real_csv_path)
        passed = validator.validate_all()
        assert passed, f"Validation failed: {validator.get_summary()}"
