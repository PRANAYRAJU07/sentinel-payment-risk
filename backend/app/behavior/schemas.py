from typing import Any

from pydantic import BaseModel, Field


class HistoricalTransaction(BaseModel):
    transaction_id: str
    entity_id: str
    amount: float
    timestamp: float  # Unix timestamp
    merchant_id: str | None = None
    device_id: str | None = None
    location: str | None = None
    status: str = "SUCCESS"


class BaselineAmount(BaseModel):
    mean: float = 0.0
    median: float = 0.0
    std: float = 0.0
    min: float = 0.0
    max: float = 0.0


class BaselineTime(BaseModel):
    typical_hours: list[int] = Field(default_factory=list)


class BaselineVelocity(BaseModel):
    avg_daily_count: float = 0.0


class BaselineFailure(BaseModel):
    failure_rate: float = 0.0


class BehaviorProfileData(BaseModel):
    amount: BaselineAmount = Field(default_factory=BaselineAmount)
    time: BaselineTime = Field(default_factory=BaselineTime)
    velocity: BaselineVelocity = Field(default_factory=BaselineVelocity)
    failure: BaselineFailure = Field(default_factory=BaselineFailure)
    last_transaction_timestamp: float = 0.0


class AnomalyResult(BaseModel):
    signal: str
    available: bool
    score: float = 0.0
    severity: str = "LOW"
    value: float = 0.0
    baseline: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None


class ProfileRequest(BaseModel):
    entity_id: str
    transactions: list[HistoricalTransaction]


class ProfileResponse(BaseModel):
    entity_id: str
    profile_status: str
    transaction_count: int
    profile_version: str
