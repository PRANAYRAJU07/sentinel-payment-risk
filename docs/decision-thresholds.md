# Sentinel ML — Decision Thresholds & Business Cost

Fraud detection is fundamentally a business decision problem, not just a mathematical classification task.

## Why Accuracy is Insufficient
In a highly imbalanced dataset (like our credit card fraud dataset where legitimate transactions outnumber fraud 578:1), a naive model that predicts every transaction as "legitimate" will achieve **99.83% accuracy**. 
However, this model detects zero fraud and allows millions of dollars to be stolen. Accuracy is fundamentally misleading here.

## The Trade-off: Precision vs. Recall
When detecting fraud, we face a critical trade-off:
- **Recall (Sensitivity):** Catching as much actual fraud as possible. If we miss fraud (False Negative), we face direct financial loss via chargebacks and stolen goods.
- **Precision:** Ensuring that when we flag a transaction as fraud, it is actually fraud. If we wrongly decline a legitimate transaction (False Positive), we anger customers, cause "insult friction", and lose lifetime value.

## Business Cost Prototype
To select the optimal decision threshold for our ML model probabilities, we use a configurable business cost prototype function.

**Assumptions:**
- **False Negative Cost (`FN_COST` = 100):** A missed fraudulent transaction results in the loss of the item, shipping costs, and chargeback fees.
- **False Positive Cost (`FP_COST` = 5):** A declined legitimate transaction requires customer support intervention or causes mild churn risk.

**Expected Cost Formula:**
`Expected Cost = (FN_count × 100) + (FP_count × 5)`

## Threshold Selection
Instead of blindly using a threshold of `0.5`, Sentinel evaluates probabilities against thresholds like `0.01, 0.05, 0.10, ..., 0.50`.
By mapping the resulting confusion matrices to our Business Cost Prototype, we identify the exact threshold that minimizes total financial loss to the platform.
