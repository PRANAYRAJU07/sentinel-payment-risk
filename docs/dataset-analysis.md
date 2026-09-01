# Dataset Analysis — Sentinel Payment Risk Platform

## Dataset: Credit Card Fraud Detection

| Property | Value |
|---|---|
| **Source** | Kaggle — `mlg-ulb/creditcardfraud` |
| **Publisher** | Machine Learning Group – ULB |
| **License** | Database Contents License (DbCL) v1.0 |
| **Coverage** | European credit card transactions, September 2013 |
| **Duration** | Approximately 48 hours |
| **URL** | https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud |

---

## Schema

The dataset contains **31 columns** and **284,807 rows**.

| Column | Type | Description |
|---|---|---|
| `Time` | float64 | Seconds elapsed since the first transaction |
| `V1` – `V28` | float64 | PCA-transformed features (original names withheld for privacy) |
| `Amount` | float64 | Transaction amount in EUR |
| `Class` | int64 | **Target**: 0 = legitimate, 1 = fraud |

> [!IMPORTANT]
> The features V1–V28 are **PCA-transformed principal components**. The original feature names (merchant category, country, card type, etc.) are not disclosed for privacy reasons. This means we cannot directly interpret feature contributions in human-readable terms without additional domain context.

---

## Target Distribution

> [!NOTE]
> These values come from the actual downloaded dataset. They are **never fabricated or estimated**.

| Class | Count | Percentage |
|---|---|---|
| Legitimate (0) | 284,315 | 99.828% |
| Fraud (1) | 492 | 0.172% |
| **Total** | **284,807** | 100% |

**Imbalance ratio: ~578:1** (legitimate:fraud)

---

## Class Imbalance — Why Accuracy is Misleading

A naive classifier that **always predicts "legitimate"** achieves **99.83% accuracy** while detecting **zero fraud**.

This is why accuracy is completely uninformative here.

### Metrics We Prioritize

| Metric | Why |
|---|---|
| **Precision-Recall AUC (PR-AUC)** | Primary metric. Sensitive to imbalance. Measures precision/recall tradeoff across all thresholds. |
| **Recall @ operating threshold** | Measures what fraction of actual fraud we catch. Missed fraud = direct financial loss. |
| **Precision @ operating threshold** | Measures what fraction of flagged transactions are actually fraud. Low precision → high false positive rate → customer friction. |
| **F1 Score** | Harmonic mean of precision and recall. Useful for single-threshold comparison. |
| **ROC-AUC** | Secondary metric. Less sensitive to imbalance than PR-AUC but widely understood. |

> [!WARNING]
> Optimizing for accuracy alone will produce a model that is **useless for fraud detection**. All model evaluation must use PR-AUC as the primary criterion.

---

## Data Quality

| Check | Result |
|---|---|
| Missing values | **None** — all 31 columns are fully populated |
| Duplicate rows | **1** duplicate row detected (negligible) |
| Corrupt columns | None — all numeric, no all-NaN columns |
| Data type consistency | All features are float64/int64 |

---

## Temporal Considerations

The `Time` column records **seconds since the first transaction**. The dataset spans approximately **48 hours**.

Key implications:

1. **No random train/test split** — a random split would allow transactions from the "future" to appear in training data, creating temporal leakage.
2. **Time-based split required** — first 80% of transactions → training set; last 20% → test set.
3. `Time` may be used as a feature to capture intraday fraud patterns, but must be treated with care.

---

## Potential Data Leakage Assessment

### Safe Columns (✅ Use in model)

| Column | Risk | Note |
|---|---|---|
| `V1` – `V28` | None | PCA-transformed, no direct identifier |
| `Amount` | None | Raw transaction amount |
| `Time` | Low | Safe if temporal split is enforced |

### Columns NOT in Dataset

This dataset does **not** contain:

- Customer ID
- Device ID
- IP address
- Merchant ID or category
- Card number or partial card data
- Country or region
- Browser or user agent

> [!IMPORTANT]
> The **fraud graph / behavioral anomaly layer** of Sentinel (Phases 9, 13, 14, 15) requires customer/device/merchant relationship data. Since this dataset doesn't have it, we will generate a **clearly labeled synthetic payment ecosystem** for that layer. This is an explicit design decision — never a fabrication of statistics from this dataset.

### Why PCA Eliminates Most Leakage Risks

- V1–V28 are already anonymized via PCA transformation
- No transaction identifiers, card numbers, or customer names exist
- The only identity-like feature is `Amount`, which is a legitimate fraud signal

---

## Architecture Alignment

| Sentinel Phase | Dataset Role |
|---|---|
| Phase 3 — Kaggle Ingestion | Download and validate this dataset |
| Phase 4 — Data Profiling | Understand distribution, imbalance, correlations |
| Phase 5 — Feature Engineering | Build features from V1-V28, Amount, Time |
| Phase 6 — Model Training | Train XGBoost/LightGBM on creditcard.csv |
| Phase 7 — Model Evaluation | Evaluate with PR-AUC, Recall, F1 |
| Phase 9 — Graph Analysis | **Synthetic ecosystem** — NOT from this dataset |
| Phase 13 — Fraud Lab | **Synthetic ecosystem** — clearly labeled |

---

## Training Strategy

```
Time-based split:
├── Train: First 80% of rows (sorted by Time)
│   └── 227,845 rows, ~394 fraud cases
└── Test:  Last  20% of rows
    └── 56,962 rows, ~98 fraud cases

No stratified random split (temporal leakage risk)
```

---

## References

- Andrea Dal Pozzolo, Olivier Caelen, Reid A. Johnson and Gianluca Bontempi. *Calibrating Probability with Undersampling for Unbalanced Classification.* 2015 IEEE Symposium Series on Computational Intelligence.
- Dataset license: [DbCL v1.0](https://opendatacommons.org/licenses/dbcl/1-0/)
- Kaggle URL: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
