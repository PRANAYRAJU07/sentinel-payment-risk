"""
Sentinel ML — Model Registry Tests
"""


import pytest
from sklearn.linear_model import LogisticRegression

from ml.src.training.model_registry import load_selected_model, save_model_artifact


def test_save_and_load_model_artifact(tmp_path, monkeypatch):
    import ml.src.training.model_registry as mr

    # Override MODELS_DIR for isolated testing
    monkeypatch.setattr(mr, "MODELS_DIR", tmp_path)

    model = LogisticRegression()
    metadata = {
        "model_name": "test_lr",
        "model_version": "v1",
        "training_timestamp": "2023-01-01T00:00:00Z",
        "is_selected": True,
        "features": ["f1", "f2"],
        "training_rows": 100,
        "validation_rows": 20,
        "test_rows": 20,
        "random_seed": 42,
        "decision_threshold": 0.5,
        "metrics": {"f1": 0.9},
    }

    # Save
    saved_path = save_model_artifact(model, "test_lr", metadata)
    assert saved_path.exists()
    assert (tmp_path / "model_metadata.json").exists()

    # Load
    loaded_model, loaded_meta = load_selected_model()

    assert isinstance(loaded_model, LogisticRegression)
    assert loaded_meta["model_name"] == "test_lr"
    assert loaded_meta["features"] == ["f1", "f2"]


def test_load_selected_model_not_found(tmp_path, monkeypatch):
    import ml.src.training.model_registry as mr

    monkeypatch.setattr(mr, "MODELS_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        load_selected_model()
