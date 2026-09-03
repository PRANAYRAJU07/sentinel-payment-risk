"""
Sentinel Risk Engine — Schemas
Defines schemas for risk evaluation inputs and outputs.
"""

from typing import Any

from pydantic import BaseModel, Field


class SignalResponse(BaseModel):
    available: bool
    score: float = 0.0  # 0 to 100
    reasons: list[dict[str, Any]] = Field(default_factory=list)


class TransactionInput(BaseModel):
    id: str | None = None
    amount: float
    currency: str = "INR"
    time: float = 0.0  # seconds from start or unix timestamp
    customer_id: str | None = None
    merchant_id: str | None = None
    device_id: str | None = None
    ip_address: str | None = None

    # ML specific features
    v_features: dict[str, float] = Field(default_factory=dict)  # V1 to V28

    # Context (e.g. failed attempts, new device)
    context: dict[str, Any] = Field(default_factory=dict)


class RiskResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    transaction_id: str
    ml_risk_score: float
    behavioral_risk_score: float
    rule_risk_score: float
    graph_risk_score: float
    final_risk_score: int
    risk_level: str
    decision: str
    reasons: list[dict[str, Any]]
    model_version: str
    policy_version: str
    signal_availability: dict[str, bool]
