
## Risk Engine

### `POST /api/v1/risk/score`
Evaluates risk for a given transaction across all signals.

**Request:**
```json
{
  "id": "tx_123",
  "amount": 500.0,
  "currency": "INR",
  "v_features": {"V1": 0.1, "V2": -0.2},
  "context": {
    "velocity_1h": 5
  }
}
```

**Response:**
```json
{
  "transaction_id": "tx_123",
  "ml_risk_score": 85.0,
  "behavioral_risk_score": 0.0,
  "rule_risk_score": 15.0,
  "graph_risk_score": 0.0,
  "final_risk_score": 88,
  "risk_level": "HIGH",
  "decision": "HOLD",
  "reasons": [
    {"reason_code": "ML_HIGH_RISK", "severity": "HIGH", "message": "ML model assigned a high transaction risk score"}
  ],
  "model_version": "random-forest-v1",
  "policy_version": "policy-v1",
  "signal_availability": {
    "ml": true,
    "behavioral": false,
    "rule": true,
    "graph": false
  }
}
```

### `GET /api/v1/risk/{transaction_id}`
Retrieves the latest risk evaluation for a transaction.

### `GET /api/v1/risk/{transaction_id}/trace`
Retrieves the full risk trace and feature snapshot for audit logging.
