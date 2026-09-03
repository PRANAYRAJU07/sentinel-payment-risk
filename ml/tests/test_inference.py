"""
Sentinel ML — Inference API Tests
"""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd

from ml.src.inference.model_predictor import RiskPredictor


def test_risk_predictor_initialization(monkeypatch):
    # Mock load_selected_model
    import ml.src.inference.model_predictor as mp

    mock_model = MagicMock()
    mock_model.predict_proba.return_value = np.array([[0.1, 0.85]])

    mock_metadata = {"decision_threshold": 0.5, "model_name": "test_model"}

    monkeypatch.setattr(mp, "load_selected_model", lambda: (mock_model, mock_metadata))

    # Mock TransactionTransformer to just return a dummy dataframe
    mock_transformer = MagicMock()
    mock_transformer.transform_transaction.return_value = pd.DataFrame({"f1": [1.0]})
    monkeypatch.setattr(mp, "TransactionTransformer", lambda: mock_transformer)

    predictor = RiskPredictor()

    assert predictor.threshold == 0.5
    assert predictor.model_name == "test_model"

    # Test predict_proba
    dummy_tx = {"Amount": 100}
    prob = predictor.predict_proba(dummy_tx)
    assert prob == 0.85

    # Test predict
    pred = predictor.predict(dummy_tx)
    assert pred == 1  # 0.85 >= 0.5

    # Test score_transaction
    score_res = predictor.score_transaction(dummy_tx)
    assert score_res["probability"] == 0.85
    assert score_res["risk_score"] == 85
    assert score_res["decision"] == "HOLD"
    assert score_res["model_used"] == "test_model"
