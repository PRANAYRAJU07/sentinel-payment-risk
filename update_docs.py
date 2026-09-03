import os

api_doc = """
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
"""

with open("docs/api.md", "a") as f:
    f.write(api_doc)

arch_doc = """
### Phase 7: Real-Time Risk Engine + Decision Engine

The core Risk Engine is built in `backend/app/risk/` and operates via an orchestrator (`RiskEngineOrchestrator`).
It is separated into multiple deterministic components to decouple signals:

1. **ML Risk**: Uses the selected `ml/models/random_forest_model.joblib`. Evaluates purely transactional data.
2. **Rule Risk**: Configurable deterministic bounds (e.g., Extreme Amounts, High Velocity).
3. **Behavioral Risk**: Analyzes anomalies based on a customer baseline (e.g. standard deviation).
4. **Graph Risk**: A pluggable interface for network cluster evaluation (to be implemented later).
5. **Decision Engine**: Normalizes available scores, aggregates via weighted config, applies explicitly defined overrides, and issues a final `APPROVE`, `REVIEW`, or `HOLD`.

Every decision emits a comprehensive, JSON-serializable trace and writes an immutable `AuditLog`.
"""

with open("docs/architecture.md", "a") as f:
    f.write(arch_doc)
