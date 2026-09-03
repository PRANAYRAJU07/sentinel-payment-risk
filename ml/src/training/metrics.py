"""
Sentinel ML — Phase 6 Metrics
=============================
Implements metrics for evaluating fraud detection models.
Prioritizes PR-AUC, Recall, and Precision over Accuracy.
"""

from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray
) -> dict[str, Any]:
    """
    Computes all required business metrics for a given set of predictions.

    Args:
        y_true: True binary labels
        y_pred: Predicted binary labels (at a specific threshold)
        y_prob: Predicted probabilities for the positive class

    Returns:
        Dictionary of metrics
    """
    cm = confusion_matrix(y_true, y_pred)
    # Handle single-class predictions in edge cases
    if cm.shape == (1, 1):
        if y_true[0] == 0:
            tn, fp, fn, tp = cm[0, 0], 0, 0, 0
        else:
            tn, fp, fn, tp = 0, 0, 0, cm[0, 0]
    else:
        tn, fp, fn, tp = cm.ravel()

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    pr_auc = average_precision_score(y_true, y_prob)

    try:
        roc_auc = roc_auc_score(y_true, y_prob)
    except ValueError:
        roc_auc = 0.5  # Edge case: only one class in y_true

    # False Positive Rate: FP / (FP + TN)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    # False Negative Rate: FN / (FN + TP)
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "pr_auc": float(pr_auc),
        "roc_auc": float(roc_auc),
        "false_positive_rate": float(fpr),
        "false_negative_rate": float(fnr),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }
