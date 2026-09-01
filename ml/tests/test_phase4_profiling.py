"""
Sentinel ML — Phase 4: Data Profiling Tests
============================================
Tests for the dataset profiler.
Unit tests use synthetic DataFrames (no download required).
"""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.ingestion.dataset_registry import (
    PCA_FEATURE_COLUMNS,
    EXPECTED_TARGET_COLUMN,
    TIME_COLUMN,
    AMOUNT_COLUMN,
)
from ml.src.ingestion.profile_dataset import (
    compute_basic_profile,
    compute_target_profile,
    compute_numerical_stats,
    compute_temporal_profile,
    compute_correlation_with_target,
    compute_outlier_summary,
    compute_leakage_assessment,
)


@pytest.fixture
def synthetic_df():
    """Minimal synthetic DataFrame with correct schema."""
    import pandas as pd
    import numpy as np

    n = 500
    n_fraud = 3
    rng = np.random.default_rng(42)

    data = {
        TIME_COLUMN: list(range(n)),
        AMOUNT_COLUMN: rng.uniform(1, 500, n).tolist(),
    }
    for col in PCA_FEATURE_COLUMNS:
        data[col] = rng.standard_normal(n).tolist()
    data[EXPECTED_TARGET_COLUMN] = [1] * n_fraud + [0] * (n - n_fraud)

    return pd.DataFrame(data)


class TestBasicProfile:
    def test_shape_is_correct(self, synthetic_df):
        profile = compute_basic_profile(synthetic_df)
        assert profile["shape"]["rows"] == len(synthetic_df)
        assert profile["shape"]["columns"] == len(synthetic_df.columns)

    def test_column_names_match(self, synthetic_df):
        profile = compute_basic_profile(synthetic_df)
        assert profile["column_names"] == list(synthetic_df.columns)

    def test_missing_values_total(self, synthetic_df):
        profile = compute_basic_profile(synthetic_df)
        assert profile["missing_values"]["total"] == 0

    def test_duplicate_count(self, synthetic_df):
        profile = compute_basic_profile(synthetic_df)
        assert isinstance(profile["duplicates"]["count"], int)
        assert profile["duplicates"]["count"] >= 0

    def test_dtypes_present(self, synthetic_df):
        profile = compute_basic_profile(synthetic_df)
        assert len(profile["dtypes"]) == len(synthetic_df.columns)


class TestTargetProfile:
    def test_fraud_count_correct(self, synthetic_df):
        profile = compute_target_profile(synthetic_df)
        assert profile["fraud_count"] == 3
        assert profile["legitimate_count"] == 497

    def test_fraud_percentage_range(self, synthetic_df):
        profile = compute_target_profile(synthetic_df)
        assert 0 < profile["fraud_percentage"] < 5.0

    def test_imbalance_ratio_present(self, synthetic_df):
        profile = compute_target_profile(synthetic_df)
        assert profile["imbalance_ratio"] is not None
        assert profile["imbalance_ratio"] > 1

    def test_class_imbalance_note_present(self, synthetic_df):
        profile = compute_target_profile(synthetic_df)
        note = profile["class_imbalance_note"]
        assert "accuracy" in note.lower() or "precision" in note.lower()

    def test_totals_add_up(self, synthetic_df):
        profile = compute_target_profile(synthetic_df)
        assert profile["fraud_count"] + profile["legitimate_count"] == profile["total"]


class TestNumericalStats:
    def test_amount_stats_present(self, synthetic_df):
        stats = compute_numerical_stats(synthetic_df)
        assert AMOUNT_COLUMN in stats
        amount = stats[AMOUNT_COLUMN]
        assert "mean" in amount
        assert "median" in amount
        assert "min" in amount
        assert "max" in amount

    def test_pca_stats_present(self, synthetic_df):
        stats = compute_numerical_stats(synthetic_df)
        for col in PCA_FEATURE_COLUMNS:
            assert col in stats

    def test_amount_by_class_present(self, synthetic_df):
        stats = compute_numerical_stats(synthetic_df)
        assert "amount_by_class" in stats
        assert "fraud" in stats["amount_by_class"]
        assert "legitimate" in stats["amount_by_class"]

    def test_stats_are_floats(self, synthetic_df):
        stats = compute_numerical_stats(synthetic_df)
        assert isinstance(stats[AMOUNT_COLUMN]["mean"], float)
        assert isinstance(stats[AMOUNT_COLUMN]["std"], float)


class TestTemporalProfile:
    def test_temporal_has_time_column(self, synthetic_df):
        profile = compute_temporal_profile(synthetic_df)
        assert profile.get("time_column") == TIME_COLUMN

    def test_time_span_positive(self, synthetic_df):
        profile = compute_temporal_profile(synthetic_df)
        assert profile["total_hours"] > 0

    def test_transactions_per_hour_populated(self, synthetic_df):
        profile = compute_temporal_profile(synthetic_df)
        assert len(profile.get("transactions_per_hour", {})) > 0

    def test_temporal_note_mentions_split(self, synthetic_df):
        profile = compute_temporal_profile(synthetic_df)
        note = profile.get("temporal_note", "")
        assert "split" in note.lower()


class TestCorrelationProfile:
    def test_all_feature_correlations_present(self, synthetic_df):
        profile = compute_correlation_with_target(synthetic_df)
        corr = profile["correlations_with_target"]
        for col in PCA_FEATURE_COLUMNS:
            assert col in corr

    def test_correlation_values_in_range(self, synthetic_df):
        profile = compute_correlation_with_target(synthetic_df)
        for col, val in profile["correlations_with_target"].items():
            assert -1.0 <= val <= 1.0, f"Correlation out of range for {col}: {val}"

    def test_pca_note_present(self, synthetic_df):
        profile = compute_correlation_with_target(synthetic_df)
        assert "PCA" in profile.get("note", "")


class TestOutlierSummary:
    def test_amount_outliers_computed(self, synthetic_df):
        outliers = compute_outlier_summary(synthetic_df)
        assert AMOUNT_COLUMN in outliers
        assert "outlier_count" in outliers[AMOUNT_COLUMN]
        assert "outlier_pct" in outliers[AMOUNT_COLUMN]
        assert "outlier_fraud_rate" in outliers[AMOUNT_COLUMN]

    def test_outlier_count_non_negative(self, synthetic_df):
        outliers = compute_outlier_summary(synthetic_df)
        assert outliers[AMOUNT_COLUMN]["outlier_count"] >= 0


class TestLeakageAssessment:
    def test_target_column_documented(self):
        assessment = compute_leakage_assessment()
        assert assessment["target_column"] == EXPECTED_TARGET_COLUMN

    def test_safe_features_listed(self):
        assessment = compute_leakage_assessment()
        assert len(assessment["safe_feature_columns"]) > 0
        assert AMOUNT_COLUMN in assessment["safe_feature_columns"]

    def test_train_test_strategy_mentions_time(self):
        assessment = compute_leakage_assessment()
        strategy = assessment.get("train_test_strategy", "")
        assert "time" in strategy.lower()

    def test_no_synthetic_features_claimed(self):
        """Leakage assessment must admit no merchant/device/IP data."""
        assessment = compute_leakage_assessment()
        note = str(assessment.get("suspicious_identifiers", {}).get("note", ""))
        assert "merchant" in note.lower() or "device" in note.lower()


class TestFullProfilingPipeline:
    def test_profile_runs_on_synthetic(self, synthetic_df, tmp_path):
        """Profiling pipeline must complete without errors on synthetic data."""
        import ml.src.ingestion.profile_dataset as profiler

        # Temporarily point paths to tmp_path
        original_reports = profiler.REPORTS_DIR
        original_figures = profiler.FIGURES_DIR
        original_primary = profiler.PRIMARY_FILE

        try:
            # Save synthetic df to tmp
            csv_path = tmp_path / "creditcard.csv"
            synthetic_df.to_csv(csv_path, index=False)

            profiler.REPORTS_DIR = tmp_path / "reports"
            profiler.FIGURES_DIR = tmp_path / "reports" / "figures"
            profiler.REPORTS_DIR.mkdir(parents=True)
            profiler.FIGURES_DIR.mkdir(parents=True)

            profile = profiler.run_profiling(csv_path=csv_path, skip_html=True)

            # Verify output structure
            assert "basic" in profile
            assert "target" in profile
            assert "numerical_stats" in profile
            assert "temporal" in profile
            assert "correlations" in profile
            assert "outliers" in profile
            assert "leakage_assessment" in profile
            assert "metric_justification" in profile

            # Verify JSON was written
            json_file = profiler.REPORTS_DIR / "data_profile.json"
            assert json_file.exists()

            # Verify JSON is valid
            with open(json_file) as f:
                loaded = json.load(f)
            assert loaded["target"]["fraud_count"] == 3

        finally:
            profiler.REPORTS_DIR = original_reports
            profiler.FIGURES_DIR = original_figures
            profiler.PRIMARY_FILE = original_primary

    def test_profile_output_has_architecture_note(self, synthetic_df, tmp_path):
        """Profile must include the note about synthetic graph layer."""
        import ml.src.ingestion.profile_dataset as profiler

        original_reports = profiler.REPORTS_DIR
        original_figures = profiler.FIGURES_DIR
        try:
            csv_path = tmp_path / "creditcard.csv"
            synthetic_df.to_csv(csv_path, index=False)
            profiler.REPORTS_DIR = tmp_path / "reports"
            profiler.FIGURES_DIR = tmp_path / "reports" / "figures"
            profiler.REPORTS_DIR.mkdir(parents=True)
            profiler.FIGURES_DIR.mkdir(parents=True)

            profile = profiler.run_profiling(csv_path=csv_path, skip_html=True)
            note = profile.get("architecture_note", "")
            assert "synthetic" in note.lower()
        finally:
            profiler.REPORTS_DIR = original_reports
            profiler.FIGURES_DIR = original_figures


@pytest.mark.requires_dataset
class TestProfilingWithRealDataset:
    """Run profiling on the real dataset. Skipped in CI."""

    @pytest.fixture(scope="class")
    def real_csv(self):
        path = PROJECT_ROOT / "ml" / "data" / "raw" / "creditcard.csv"
        if not path.exists():
            pytest.skip("Real dataset not downloaded yet")
        return path

    def test_profile_runs_on_real_data(self, real_csv, tmp_path):
        import ml.src.ingestion.profile_dataset as profiler
        original_reports = profiler.REPORTS_DIR
        original_figures = profiler.FIGURES_DIR
        try:
            profiler.REPORTS_DIR = tmp_path / "reports"
            profiler.FIGURES_DIR = tmp_path / "reports" / "figures"
            profiler.REPORTS_DIR.mkdir(parents=True)
            profiler.FIGURES_DIR.mkdir(parents=True)
            profile = profiler.run_profiling(csv_path=real_csv, skip_html=True)
            assert profile["target"]["fraud_count"] >= 400
            assert profile["basic"]["shape"]["rows"] >= 250_000
        finally:
            profiler.REPORTS_DIR = original_reports
            profiler.FIGURES_DIR = original_figures
