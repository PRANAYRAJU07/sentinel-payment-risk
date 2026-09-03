"""
Sentinel ML — Feature Engineering Tests (Phase 5)
=================================================
Tests pipeline structure, validation contract, splitting logic, and robustness.
"""

import numpy as np
import pandas as pd
import pytest

from ml.src.features.feature_pipeline import (
    create_feature_pipeline,
    load_pipeline,
    save_pipeline,
    separate_target,
)
from ml.src.features.inference import TransactionTransformer
from ml.src.preprocessing.data_contract import DataContractError, validate_raw_data
from ml.src.preprocessing.splitter import temporal_split

# --- Fixtures ---


@pytest.fixture
def dummy_raw_data():
    """Generates 100 rows of fake but schema-compliant raw data."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame()
    df["Time"] = np.linspace(0, 86400, n)  # 1 day of seconds
    df["Amount"] = np.random.exponential(50, n)
    for i in range(1, 29):
        df[f"V{i}"] = np.random.normal(0, 1, n)
    df["Class"] = np.random.choice([0, 1], n, p=[0.95, 0.05])
    return df


@pytest.fixture
def trained_pipeline(dummy_raw_data):
    X, _ = separate_target(dummy_raw_data)
    pipe = create_feature_pipeline()
    return pipe.fit(X)


# --- Data Contract Tests ---


def test_data_contract_missing_col(dummy_raw_data):
    df = dummy_raw_data.drop(columns=["V5"])
    with pytest.raises(DataContractError, match="Missing required columns"):
        validate_raw_data(df)


def test_data_contract_invalid_type(dummy_raw_data):
    df = dummy_raw_data.copy()
    df["Amount"] = "string_amount"
    with pytest.raises(DataContractError, match="must be numeric"):
        validate_raw_data(df)


def test_data_contract_missing_target_training(dummy_raw_data):
    df = dummy_raw_data.drop(columns=["Class"])
    with pytest.raises(DataContractError, match="must contain target column"):
        validate_raw_data(df, is_training=True)


def test_data_contract_inference_allows_missing_target(dummy_raw_data):
    df = dummy_raw_data.drop(columns=["Class"])
    validated = validate_raw_data(df, is_training=False)
    assert len(validated) == len(df)


# --- Splitting Tests ---


def test_temporal_split(dummy_raw_data):
    splits = temporal_split(dummy_raw_data, train_ratio=0.5, val_ratio=0.25)
    train_df = splits["train"]
    val_df = splits["val"]
    test_df = splits["test"]

    assert len(train_df) == 50
    assert len(val_df) == 25
    assert len(test_df) == 25

    # Check temporal ordering
    assert train_df["Time"].max() <= val_df["Time"].min()
    assert val_df["Time"].max() <= test_df["Time"].min()


# --- Feature Pipeline Tests ---


def test_pipeline_fit_transform(dummy_raw_data):
    X, y = separate_target(dummy_raw_data)
    pipe = create_feature_pipeline()
    X_trans = pipe.fit_transform(X)

    assert isinstance(X_trans, pd.DataFrame)
    assert len(X_trans) == len(X)
    assert "Time_hour_sin" in X_trans.columns
    assert "Time_hour_cos" in X_trans.columns
    assert "Amount" in X_trans.columns
    assert "V1" in X_trans.columns


def test_pipeline_no_nans_or_infs(trained_pipeline, dummy_raw_data):
    X, _ = separate_target(dummy_raw_data)
    X_trans = trained_pipeline.transform(X)

    assert not X_trans.isna().any().any()
    assert not np.isinf(X_trans.values).any()


def test_target_excluded_from_features(trained_pipeline, dummy_raw_data):
    # Pass DataFrame WITH Class column to transform
    # The remainder='drop' should drop it safely.
    X_trans = trained_pipeline.transform(dummy_raw_data)
    for col in X_trans.columns:
        assert "Class" not in col


def test_pipeline_deterministic(trained_pipeline, dummy_raw_data):
    X, _ = separate_target(dummy_raw_data)
    out1 = trained_pipeline.transform(X)
    out2 = trained_pipeline.transform(X)
    pd.testing.assert_frame_equal(out1, out2)


def test_serialization_works(trained_pipeline, dummy_raw_data, tmp_path):
    import ml.src.features.feature_pipeline as fp

    # Temporarily override MODELS_DIR for testing
    old_models_dir = fp.MODELS_DIR
    fp.MODELS_DIR = tmp_path

    try:
        save_pipeline(trained_pipeline, "test_pipe.joblib")
        loaded = load_pipeline("test_pipe.joblib")

        X, _ = separate_target(dummy_raw_data)
        out1 = trained_pipeline.transform(X)
        out2 = loaded.transform(X)

        pd.testing.assert_frame_equal(out1, out2)
    finally:
        fp.MODELS_DIR = old_models_dir


def test_inference_api(trained_pipeline, dummy_raw_data, tmp_path, monkeypatch):
    import ml.src.features.feature_pipeline as fp
    import ml.src.features.inference as fi

    fp.MODELS_DIR = tmp_path
    save_pipeline(trained_pipeline, "test_inf_pipe.joblib")

    # Mock load_pipeline inside inference module to use our tmp dir
    monkeypatch.setattr(fi, "load_pipeline", lambda p: fp.load_pipeline(p))

    transformer = TransactionTransformer("test_inf_pipe.joblib")

    # Take a single raw row
    raw_dict = dummy_raw_data.iloc[0].drop("Class").to_dict()

    result = transformer.transform_transaction(raw_dict)
    assert len(result) == 1
    assert "Amount" in result.columns
    assert "Class" not in result.columns
