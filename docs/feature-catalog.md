# Sentinel Feature Catalog

This catalog documents all final features output by the Sentinel feature engineering pipeline.

| Feature Name | Source Column | Transformation | Data Type | Purpose | Potential Leakage Risk |
|---|---|---|---|---|---|
| `time__Time_hour_sin` | `Time` | `sin(2π * ((Time/3600) % 24) / 24)` | float64 | Capture daily cyclical fraud seasonality. | **Low**: Time-based splits prevent future leakage. |
| `time__Time_hour_cos` | `Time` | `cos(2π * ((Time/3600) % 24) / 24)` | float64 | Capture daily cyclical fraud seasonality. | **Low**: Time-based splits prevent future leakage. |
| `amount__Amount` | `Amount` | `StandardScaler(log1p(Amount))` | float64 | Reduce extreme skew in transaction amounts and standardize variance. | **None**: Scaler fitted strictly on training data. |
| `pca__V1` ... `pca__V28` | `V1` ... `V28` | None (Passthrough) | float64 | Provide raw anonymized transaction signals. | **None**: No statistical fitting applied. |

### Note on Feature Naming

Because we use scikit-learn's `ColumnTransformer` (with output converted to Pandas), the generated feature columns are prefixed with the step name (e.g., `amount__Amount`, `pca__V1`). This structure ensures traceability back to the original transformations and prevents naming collisions.
