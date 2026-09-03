
### Phase 7: Real-Time Risk Engine + Decision Engine

The core Risk Engine is built in `backend/app/risk/` and operates via an orchestrator (`RiskEngineOrchestrator`).
It is separated into multiple deterministic components to decouple signals:

1. **ML Risk**: Uses the selected `ml/models/random_forest_model.joblib`. Evaluates purely transactional data.
2. **Rule Risk**: Configurable deterministic bounds (e.g., Extreme Amounts, High Velocity).
3. **Behavioral Risk**: Analyzes anomalies based on a customer baseline (e.g. standard deviation).
4. **Graph Risk**: A pluggable interface for network cluster evaluation (to be implemented later).
5. **Decision Engine**: Normalizes available scores, aggregates via weighted config, applies explicitly defined overrides, and issues a final `APPROVE`, `REVIEW`, or `HOLD`.

Every decision emits a comprehensive, JSON-serializable trace and writes an immutable `AuditLog`.


### Phase 8: Behavioral Anomaly Engine
Introduced the persistent behavioral profile storage (`BehaviorProfile`) tracking metrics like average amounts, standard deviations, typical active hours, daily transaction velocities, and historic failure rates. This layer operates completely decoupled from the ML models to detect behavioral drift without fabricating PII-linked dependencies in the Kaggle dataset.
