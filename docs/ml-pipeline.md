# Sentinel ML Pipeline Architecture

This document describes the design decisions behind the Sentinel Machine Learning Pipeline.

## 1. Train / Validation / Test Splitting Strategy

**Strategy:** Temporal Split (Time-based ordering)

**Proportions:**
- Train: 70%
- Validation: 15%
- Test: 15%

**Justification:**
In fraud detection, temporal ordering is critical. Fraudsters continuously adapt their tactics over time. If we perform a random stratified split, we risk leaking future patterns into our training dataset, artificially inflating offline performance metrics. To mimic a real-world production environment where the model predicts the future based on the past, we sort the transactions by the `Time` column and split them chronologically.

## 2. Leakage Protection

Data leakage occurs when information from outside the training dataset is used to create the model. To prevent this, the Sentinel pipeline enforces strict rules:

- **Target Isolation:** The `Class` column is completely excluded from the feature pipeline. It is separated early and never passed into scikit-learn transformers.
- **Pipeline Fitting:** Transformers like `StandardScaler` are fitted **only** on the training dataset. Validation and test sets are only *transformed*.
- **Temporal Strictness:** By utilizing a temporal split, we prevent future distributions of the `Amount` or `PCA` features from influencing the scaling factors or feature engineering logic.

## 3. Class Imbalance Handling

**Observation:** The dataset contains roughly 0.17% fraud and 99.83% legitimate transactions.

**Decision:** We do **not** perform synthetic oversampling (like SMOTE) or undersampling during the initial Phase 5 feature engineering. 

**Justification:** 
Handling class imbalance is an algorithm-specific consideration (e.g., configuring `scale_pos_weight` in XGBoost, or using specialized sampling techniques during model training). Feature engineering should remain objective, stable, and purely focused on mapping raw data distributions into feature space. We will address class imbalance explicitly during Model Training and Evaluation (Phase 6), evaluating its impact on PR-AUC.

## 4. Pipeline Serialization

The canonical feature pipeline (`ml/src/features/feature_pipeline.py`) is defined once.
It exposes `fit`, `transform`, and `fit_transform` methods.
After fitting on the training set, it is serialized using `joblib` into `ml/models/feature_pipeline.joblib`. 
This identical artifact will be loaded for batch offline evaluation, the Fraud Lab simulation, and the real-time inference API.
