"""
Sentinel ML — Phase 6 Evaluation logic
======================================
Threshold analysis, business cost calculation, and visualization (PR curve, SHAP).
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

from ml.src.training.metrics import compute_metrics

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "ml" / "reports" / "model_comparison"


def calculate_expected_cost(
    fn_count: int, fp_count: int, fn_cost: float = 100.0, fp_cost: float = 5.0
) -> float:
    """
    Calculate simple business cost.
    Assumes a False Negative (missed fraud) costs 100 units.
    Assumes a False Positive (customer friction) costs 5 units.
    """
    return (fn_count * fn_cost) + (fp_count * fp_cost)


def analyze_thresholds(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: list[float] = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50],
) -> pd.DataFrame:
    """
    Evaluate multiple decision thresholds for probabilities.
    Returns a dataframe of metrics per threshold.
    """
    results = []

    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        metrics = compute_metrics(y_true, y_pred, y_prob)

        # Calculate expected cost
        cm = metrics["confusion_matrix"]
        fn, fp = cm[1][0], cm[0][1]
        cost = calculate_expected_cost(fn, fp)

        results.append(
            {
                "threshold": t,
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "fpr": metrics["false_positive_rate"],
                "fnr": metrics["false_negative_rate"],
                "expected_cost": cost,
                "fp_count": fp,
                "fn_count": fn,
            }
        )

    return pd.DataFrame(results)


def plot_precision_recall_curves(
    model_probs: dict[str, np.ndarray],
    y_true: np.ndarray,
    output_name: str = "precision_recall_curve.png",
):
    """
    Plot Precision-Recall curve for multiple models.
    model_probs is a dict of model_name -> predicted probabilities.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 7))

    for model_name, y_prob in model_probs.items():
        precision, recall, _ = precision_recall_curve(y_true, y_prob)
        # Compute PR-AUC for legend
        from sklearn.metrics import average_precision_score

        pr_auc = average_precision_score(y_true, y_prob)
        plt.plot(recall, precision, label=f"{model_name} (PR-AUC = {pr_auc:.3f})")

    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve Comparison")
    plt.legend(loc="lower left")
    plt.grid(True, alpha=0.3)

    out_path = REPORTS_DIR / output_name
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved PR curve to {out_path}")


def plot_threshold_charts(df_thresholds: pd.DataFrame, model_name: str):
    """
    Plot Precision vs Recall and FPR vs Recall for a specific model's thresholds.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Precision vs Recall scatter with thresholds
    plt.figure(figsize=(8, 6))
    plt.plot(
        df_thresholds["recall"], df_thresholds["precision"], marker="o", linestyle="-"
    )
    for idx, row in df_thresholds.iterrows():
        plt.annotate(
            f"{row['threshold']:.2f}",
            (row["recall"], row["precision"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"{model_name} - Precision vs Recall by Threshold")
    plt.grid(True, alpha=0.3)
    plt.savefig(REPORTS_DIR / f"{model_name}_prec_vs_rec.png", dpi=300)
    plt.close()

    # 2. FPR vs Recall
    plt.figure(figsize=(8, 6))
    plt.plot(df_thresholds["recall"], df_thresholds["fpr"], marker="o", linestyle="-")
    for idx, row in df_thresholds.iterrows():
        plt.annotate(
            f"{row['threshold']:.2f}",
            (row["recall"], row["fpr"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    plt.xlabel("Recall (True Positive Rate)")
    plt.ylabel("False Positive Rate")
    plt.title(f"{model_name} - FPR vs Recall by Threshold")
    plt.grid(True, alpha=0.3)
    plt.savefig(REPORTS_DIR / f"{model_name}_fpr_vs_rec.png", dpi=300)
    plt.close()


def generate_shap_summary(model, X_val: pd.DataFrame, max_display: int = 15):
    """
    Generate SHAP summary plot on a small sample of the validation set.
    """
    try:
        import shap
    except ImportError:
        logger.warning("SHAP not installed. Skipping SHAP summary.")
        return

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Use a small sample to prevent massive computation times
    sample_size = min(2000, len(X_val))
    # Stratified sampling is better, but random is okay for quick SHAP
    X_sample = X_val.sample(n=sample_size, random_state=42)

    logger.info(f"Generating SHAP values for sample size {sample_size}...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_sample)

    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, max_display=max_display, show=False)
    plt.title("SHAP Summary Plot (Validation Sample)")

    out_path = REPORTS_DIR / "shap_summary.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved SHAP summary to {out_path}")
