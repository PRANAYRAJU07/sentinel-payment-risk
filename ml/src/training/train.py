"""
Sentinel ML — Phase 6 Training Orchestrator
===========================================
Trains Logistic Regression, Random Forest, and XGBoost.
Evaluates them, selects the best model, and generates evaluation artifacts.
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier

# ML Libraries
from sklearn.linear_model import LogisticRegression

try:
    import xgboost as xgb
except ImportError:
    xgb = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.training.data_loader import load_and_preprocess_data
from ml.src.training.evaluation import (
    analyze_thresholds,
    generate_shap_summary,
    plot_precision_recall_curves,
    plot_threshold_charts,
)
from ml.src.training.metrics import compute_metrics
from ml.src.training.model_registry import save_model_artifact

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

REPORTS_DIR = PROJECT_ROOT / "ml" / "reports" / "model_comparison"


def train_logistic_regression(X_train, y_train):
    logger.info("Training Logistic Regression (Baseline)...")
    t0 = time.time()
    model = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    model.fit(X_train, y_train)
    logger.info(f"Logistic Regression trained in {time.time() - t0:.2f}s")
    return model


def train_random_forest(X_train, y_train):
    logger.info("Training Random Forest...")
    t0 = time.time()
    # Using a smaller number of estimators to keep training time manageable for Phase 6
    model = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
        max_depth=15,
    )
    model.fit(X_train, y_train)
    logger.info(f"Random Forest trained in {time.time() - t0:.2f}s")
    return model


def train_xgboost(X_train, y_train, X_val, y_val):
    if xgb is None:
        logger.error("XGBoost not installed. Please pip install xgboost")
        return None

    logger.info("Training XGBoost...")
    t0 = time.time()

    # Calculate scale_pos_weight from TRAINING DATA ONLY
    # scale_pos_weight = count(negative examples) / count(positive examples)
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    logger.info(f"Calculated scale_pos_weight from train data: {scale_pos_weight:.2f}")

    model = xgb.XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=6,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric="aucpr",
        early_stopping_rounds=20,
        n_jobs=-1,
    )

    # Fit with early stopping on validation set
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    logger.info(
        f"XGBoost trained in {time.time() - t0:.2f}s. Best iteration: {model.best_iteration}"
    )
    return model


def evaluate_model(model, X_val, y_val, model_name: str) -> dict:
    """Evaluates a model and returns threshold analysis results."""
    # Handle predict_proba differences
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_val)[:, 1]
    else:
        # Fallback (though all our models have predict_proba)
        y_prob = model.predict(X_val)

    # Analyze thresholds
    df_thresholds = analyze_thresholds(y_val, y_prob)

    # Plot threshold curves
    plot_threshold_charts(df_thresholds, model_name)

    # Find best threshold based on minimal cost, tie-break with F1
    best_row = df_thresholds.sort_values(
        by=["expected_cost", "f1"], ascending=[True, False]
    ).iloc[0]

    return {
        "model_name": model_name,
        "y_prob": y_prob,
        "threshold_analysis": df_thresholds,
        "best_threshold": float(best_row["threshold"]),
        "best_metrics": {
            "precision": float(best_row["precision"]),
            "recall": float(best_row["recall"]),
            "f1": float(best_row["f1"]),
            "fpr": float(best_row["fpr"]),
            "fnr": float(best_row["fnr"]),
            "expected_cost": float(best_row["expected_cost"]),
        },
    }


def main():
    logger.info("═" * 55)
    logger.info("  Sentinel — Model Training & Evaluation")
    logger.info("═" * 55)

    # 1. Load Data
    X_dict, y_dict, feature_pipeline = load_and_preprocess_data()

    X_train, y_train = X_dict["train"], y_dict["train"]
    X_val, y_val = X_dict["val"], y_dict["val"]
    X_test, y_test = X_dict["test"], y_dict["test"]

    logger.info(
        f"Dataset split — Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}"
    )

    models = {}

    # 2. Train Models
    lr_model = train_logistic_regression(X_train, y_train)
    models["logistic_regression"] = lr_model

    rf_model = train_random_forest(X_train, y_train)
    models["random_forest"] = rf_model

    xgb_model = train_xgboost(X_train, y_train, X_val, y_val)
    if xgb_model:
        models["xgboost"] = xgb_model

    # 3. Evaluate on Validation Set (Model Selection)
    logger.info("Evaluating models on Validation set...")
    evaluations = {}
    model_probs = {}

    for name, model in models.items():
        eval_result = evaluate_model(model, X_val, y_val, name)
        evaluations[name] = eval_result
        model_probs[name] = eval_result["y_prob"]

    # 4. Precision-Recall Curve Comparison
    plot_precision_recall_curves(model_probs, y_val)

    # 5. Model Selection
    # We select based on lowest expected business cost on validation set
    best_model_name = min(
        evaluations.keys(),
        key=lambda k: evaluations[k]["best_metrics"]["expected_cost"],
    )
    best_eval = evaluations[best_model_name]
    best_model = models[best_model_name]

    logger.info(
        f"Selected Model: {best_model_name} (Cost: {best_eval['best_metrics']['expected_cost']:.1f}, Threshold: {best_eval['best_threshold']})"
    )

    # 6. Final Evaluation on TEST DATA LOCK
    logger.info("Performing ONE FINAL evaluation on TEST set...")
    # Get probabilities for test set
    if hasattr(best_model, "predict_proba"):
        y_test_prob = best_model.predict_proba(X_test)[:, 1]
    else:
        y_test_prob = best_model.predict(X_test)

    # Apply selected threshold
    y_test_pred = (y_test_prob >= best_eval["best_threshold"]).astype(int)

    final_test_metrics = compute_metrics(y_test, y_test_pred, y_test_prob)

    logger.info(f"Final Test PR-AUC: {final_test_metrics['pr_auc']:.4f}")
    logger.info(f"Final Test Recall: {final_test_metrics['recall']:.4f}")
    logger.info(f"Final Test Precision: {final_test_metrics['precision']:.4f}")

    # 7. SHAP Analysis (if tree-based)
    if best_model_name in ["xgboost", "random_forest"]:
        generate_shap_summary(best_model, X_val)

    # 8. Save Artifacts
    logger.info("Saving models and metadata...")
    for name, model in models.items():
        # Only the best model gets the full unified metadata flagged as 'is_selected'
        is_selected = name == best_model_name

        metadata = {
            "model_name": name,
            "model_version": "v1",
            "training_timestamp": datetime.now(timezone.utc).isoformat(),
            "is_selected": is_selected,
            "features": list(X_train.columns),
            "training_rows": len(X_train),
            "validation_rows": len(X_val),
            "test_rows": len(X_test),
            "random_seed": 42,
            "decision_threshold": best_eval["best_threshold"] if is_selected else None,
            "metrics": final_test_metrics if is_selected else best_eval["best_metrics"],
        }

        save_model_artifact(model, name, metadata)

    # Generate unified comparison JSON
    comparison_summary = {
        name: eval_dict["best_metrics"] for name, eval_dict in evaluations.items()
    }
    with open(REPORTS_DIR / "model_comparison.json", "w") as f:
        json.dump(comparison_summary, f, indent=2)

    # Save Final Evaluation Report
    final_report = {
        "dataset": "mlg-ulb/creditcardfraud",
        "split_strategy": "Temporal (70/15/15)",
        "model": best_model_name,
        "model_version": "v1",
        "feature_count": len(X_train.columns),
        "threshold": best_eval["best_threshold"],
        **final_test_metrics,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with open(PROJECT_ROOT / "ml" / "reports" / "final_model_report.json", "w") as f:
        json.dump(final_report, f, indent=2)

    logger.info("Phase 6 training complete!")


if __name__ == "__main__":
    main()
