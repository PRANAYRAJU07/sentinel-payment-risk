"""
Sentinel ML — Metrics Tests
"""

import numpy as np

from ml.src.training.evaluation import analyze_thresholds, calculate_expected_cost
from ml.src.training.metrics import compute_metrics


def test_compute_metrics_perfect():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.9, 0.8])

    metrics = compute_metrics(y_true, y_pred, y_prob)

    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["false_positive_rate"] == 0.0
    assert metrics["false_negative_rate"] == 0.0
    assert metrics["confusion_matrix"] == [[2, 0], [0, 2]]
    assert 0.8 <= metrics["pr_auc"] <= 1.0


def test_compute_metrics_all_zero():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 0, 0])
    y_prob = np.array([0.1, 0.2, 0.3, 0.4])

    metrics = compute_metrics(y_true, y_pred, y_prob)

    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1"] == 0.0
    assert metrics["false_positive_rate"] == 0.0
    assert metrics["false_negative_rate"] == 1.0
    assert metrics["confusion_matrix"] == [[2, 0], [2, 0]]


def test_calculate_expected_cost():
    fn = 2
    fp = 10
    cost = calculate_expected_cost(fn, fp, fn_cost=100.0, fp_cost=5.0)
    assert cost == (2 * 100.0) + (10 * 5.0)


def test_analyze_thresholds():
    y_true = np.array([0, 0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.8, 0.9])

    df = analyze_thresholds(y_true, y_prob, thresholds=[0.15, 0.5])
    assert len(df) == 2
    assert "threshold" in df.columns
    assert "expected_cost" in df.columns
