"""
Sentinel ML — Training logic tests
"""

import numpy as np
import pandas as pd


def test_data_loader(tmp_path, monkeypatch):
    import ml.src.training.data_loader as dl

    # Create a dummy raw dataset
    dummy_csv = tmp_path / "creditcard.csv"
    np.random.seed(42)

    n = 100
    df = pd.DataFrame()
    df["Time"] = np.linspace(0, 86400, n)
    df["Amount"] = np.random.exponential(50, n)
    for i in range(1, 29):
        df[f"V{i}"] = np.random.normal(0, 1, n)
    df["Class"] = np.random.choice([0, 1], n, p=[0.9, 0.1])

    df.to_csv(dummy_csv, index=False)

    # Run loader
    X_dict, y_dict, pipeline = dl.load_and_preprocess_data(dummy_csv)

    # Check splits
    assert "train" in X_dict
    assert "val" in X_dict
    assert "test" in X_dict

    assert len(X_dict["train"]) == 70
    assert len(X_dict["val"]) == 15
    assert len(X_dict["test"]) == 15

    # Check target
    assert "Class" not in X_dict["train"].columns
    assert len(y_dict["train"]) == 70

    # Check pipeline
    assert hasattr(pipeline, "transform")
