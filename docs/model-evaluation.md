# Sentinel Model Evaluation & Selection

This document summarizes the Phase 6 evaluation of Machine Learning models for the Sentinel platform.

## Evaluated Models
1. **Logistic Regression (Baseline):** Trained with `class_weight="balanced"`. Provides a fast, highly interpretable baseline.
2. **Random Forest:** Trained with `class_weight="balanced_subsample"`. A powerful bagging tree ensemble that handles nonlinear relationships well.
3. **XGBoost:** Trained using explicitly calculated `scale_pos_weight` from the training distribution. The industry standard for tabular data.

## Class Imbalance Handling
Because fraud represents ~0.17% of the dataset, class weighting was used during model training. This tells the algorithms to penalize errors on the minority class more severely.
- No synthetic oversampling (like SMOTE) was used, as tree-based models with `scale_pos_weight` often perform better and are less susceptible to overlapping distributions in high-dimensional PCA space.

## Model Comparison Strategy
Models were trained on 70% of the data (ordered temporally). They were then evaluated on a 15% Validation set.
The primary metric used to evaluate overall probabilistic separation was **PR-AUC (Precision-Recall Area Under Curve)**, as it is highly sensitive to imbalanced positive classes.

To pick a decision threshold, we used our Business Cost Prototype (`FN cost = 100`, `FP cost = 5`). The model and threshold combination that minimized expected financial cost on the validation set was selected.

## Test Data Lock
Once the final model and its threshold were selected based purely on Validation performance, a **single final evaluation** was performed on the remaining 15% Test set. This guarantees an unbiased estimate of future performance, completely preventing overfitting to the validation threshold.

## Final Selection
The final results, charts (Precision-Recall curves), and SHAP plots are automatically generated and saved to `ml/reports/model_comparison/` and `ml/reports/final_model_report.json` by the training orchestrator.

## Limitations
- The XGBoost prototype currently uses a fixed set of hyperparameters. Automated hyperparameter tuning (e.g., Optuna) can be introduced in later phases.
- The `Risk Score` output by the Inference API is currently a direct scalar mapping of the raw probability (`prob * 100`). It is not yet strictly calibrated (via Isotonic Regression or Platt Scaling) to represent a true calibrated probability of fraud.
