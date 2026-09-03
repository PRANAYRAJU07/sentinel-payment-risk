import os

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content.strip() + "\n")

# backend/app/behavior/__init__.py
write_file("backend/app/behavior/__init__.py", "")

# backend/app/behavior/schemas.py
write_file("backend/app/behavior/schemas.py", """
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class HistoricalTransaction(BaseModel):
    transaction_id: str
    entity_id: str
    amount: float
    timestamp: float  # Unix timestamp
    merchant_id: Optional[str] = None
    device_id: Optional[str] = None
    location: Optional[str] = None
    status: str = "SUCCESS"

class BaselineAmount(BaseModel):
    mean: float = 0.0
    median: float = 0.0
    std: float = 0.0
    min: float = 0.0
    max: float = 0.0

class BaselineTime(BaseModel):
    typical_hours: List[int] = Field(default_factory=list)

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
    baseline: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None

class ProfileRequest(BaseModel):
    entity_id: str
    transactions: List[HistoricalTransaction]

class ProfileResponse(BaseModel):
    entity_id: str
    profile_status: str
    transaction_count: int
    profile_version: str
""")

# backend/app/behavior/profile_builder.py
write_file("backend/app/behavior/profile_builder.py", """
import numpy as np
from datetime import datetime, timezone
from typing import List
from collections import Counter
from app.behavior.schemas import HistoricalTransaction, BehaviorProfileData

MIN_PROFILE_TRANSACTIONS = 20

def build_profile(transactions: List[HistoricalTransaction]) -> BehaviorProfileData:
    if len(transactions) < MIN_PROFILE_TRANSACTIONS:
        return BehaviorProfileData()

    amounts = [t.amount for t in transactions if t.status == "SUCCESS"]
    if not amounts:
        amounts = [0.0]
        
    amount_mean = float(np.mean(amounts))
    amount_std = float(np.std(amounts))
    amount_median = float(np.median(amounts))
    amount_min = float(np.min(amounts))
    amount_max = float(np.max(amounts))

    hours = []
    days = set()
    failures = 0
    
    last_ts = 0.0
    
    for t in transactions:
        dt = datetime.fromtimestamp(t.timestamp, tz=timezone.utc)
        hours.append(dt.hour)
        days.add(dt.date())
        if t.status != "SUCCESS":
            failures += 1
        if t.timestamp > last_ts:
            last_ts = t.timestamp

    # Typical hours: hours containing at least 5% of transactions
    hour_counts = Counter(hours)
    threshold = len(transactions) * 0.05
    typical_hours = [h for h, c in hour_counts.items() if c >= threshold]

    days_span = len(days) if len(days) > 0 else 1
    avg_daily = len(transactions) / days_span
    fail_rate = failures / len(transactions)

    profile = BehaviorProfileData()
    profile.amount.mean = amount_mean
    profile.amount.std = amount_std
    profile.amount.median = amount_median
    profile.amount.min = amount_min
    profile.amount.max = amount_max
    
    profile.time.typical_hours = typical_hours
    profile.velocity.avg_daily_count = avg_daily
    profile.failure.failure_rate = fail_rate
    profile.last_transaction_timestamp = last_ts

    return profile
""")

# backend/app/behavior/anomaly_detector.py
write_file("backend/app/behavior/anomaly_detector.py", """
from datetime import datetime, timezone
from typing import List
from app.behavior.schemas import BehaviorProfileData, AnomalyResult, HistoricalTransaction
from app.risk.risk_response import TransactionInput

class AnomalyDetector:
    def __init__(self):
        pass

    def detect_amount_anomaly(self, tx: TransactionInput, profile: BehaviorProfileData) -> AnomalyResult:
        amt = profile.amount
        if tx.amount <= amt.max and tx.amount <= amt.mean + (3 * amt.std):
            return AnomalyResult(signal="AMOUNT_ANOMALY", available=True, score=0, severity="LOW", value=tx.amount, baseline={"mean": amt.mean, "std": amt.std})

        # Z-score based
        std = amt.std if amt.std > 0 else 1.0
        z_score = (tx.amount - amt.mean) / std
        
        score = min(max(z_score * 10, 0), 100)
        severity = "HIGH" if score > 75 else ("MEDIUM" if score > 40 else "LOW")
        
        reason = None
        if score > 40:
            reason = "Amount is significantly above the customer's historical transaction range"

        return AnomalyResult(
            signal="AMOUNT_ANOMALY",
            available=True,
            score=score,
            severity=severity,
            value=tx.amount,
            baseline={"mean": amt.mean, "std": amt.std},
            reason=reason
        )

    def detect_time_anomaly(self, tx: TransactionInput, profile: BehaviorProfileData) -> AnomalyResult:
        if not profile.time.typical_hours:
            return AnomalyResult(signal="TIME_ANOMALY", available=False)
            
        dt = datetime.fromtimestamp(tx.time, tz=timezone.utc)
        tx_hour = dt.hour
        
        # Calculate circular distance to nearest typical hour
        min_dist = 12
        for th in profile.time.typical_hours:
            dist = min(abs(tx_hour - th), 24 - abs(tx_hour - th))
            if dist < min_dist:
                min_dist = dist
                
        score = min(min_dist * 15, 100)  # Max score at ~6-7 hours away
        severity = "HIGH" if score > 75 else ("MEDIUM" if score > 40 else "LOW")
        
        reason = None
        if score > 40:
            reason = "Transaction occurs at an unusual time for this customer"

        return AnomalyResult(
            signal="TIME_ANOMALY",
            available=True,
            score=score,
            severity=severity,
            value=tx_hour,
            baseline={"typical_hours": profile.time.typical_hours},
            reason=reason
        )

    def detect_velocity_anomaly(self, tx: TransactionInput, profile: BehaviorProfileData) -> AnomalyResult:
        vel_1h = tx.context.get("velocity_1h", 0)
        avg_daily = profile.velocity.avg_daily_count
        
        # If hourly velocity is more than daily average
        if avg_daily > 0 and vel_1h > (avg_daily / 2) + 2:
            ratio = vel_1h / max(avg_daily, 1.0)
            score = min(ratio * 20, 100)
            severity = "HIGH" if score > 75 else ("MEDIUM" if score > 40 else "LOW")
            reason = "Unusual transaction frequency" if score > 40 else None
            return AnomalyResult(
                signal="VELOCITY_ANOMALY", available=True, score=score, severity=severity,
                value=vel_1h, baseline={"avg_daily": avg_daily}, reason=reason
            )
            
        return AnomalyResult(signal="VELOCITY_ANOMALY", available=True, score=0, value=vel_1h, baseline={"avg_daily": avg_daily})

    def detect_failure_anomaly(self, tx: TransactionInput, profile: BehaviorProfileData) -> AnomalyResult:
        failures_24h = tx.context.get("failures_24h", 0)
        fail_rate = profile.failure.failure_rate
        
        if failures_24h > 2 and fail_rate < 0.1:
            score = min(failures_24h * 15, 100)
            severity = "HIGH" if score > 75 else ("MEDIUM" if score > 40 else "LOW")
            reason = "Elevated failure rate compared to historical baseline" if score > 40 else None
            return AnomalyResult(
                signal="FAILURE_ANOMALY", available=True, score=score, severity=severity,
                value=failures_24h, baseline={"historical_rate": fail_rate}, reason=reason
            )
            
        return AnomalyResult(signal="FAILURE_ANOMALY", available=True, score=0, value=failures_24h, baseline={"historical_rate": fail_rate})

    def detect_recency_anomaly(self, tx: TransactionInput, profile: BehaviorProfileData) -> AnomalyResult:
        last_ts = profile.last_transaction_timestamp
        if last_ts == 0:
            return AnomalyResult(signal="RECENCY_ANOMALY", available=False)
            
        diff_sec = tx.time - last_ts
        if diff_sec > 0 and diff_sec < 60: # Under 1 minute
            score = 60.0
            return AnomalyResult(
                signal="RECENCY_ANOMALY", available=True, score=score, severity="MEDIUM",
                value=diff_sec, baseline={"last_ts": last_ts}, reason="Transactions extremely close in time"
            )
            
        return AnomalyResult(signal="RECENCY_ANOMALY", available=True, score=0, value=diff_sec, baseline={"last_ts": last_ts})

    def evaluate_all(self, tx: TransactionInput, profile: BehaviorProfileData) -> List[AnomalyResult]:
        return [
            self.detect_amount_anomaly(tx, profile),
            self.detect_time_anomaly(tx, profile),
            self.detect_velocity_anomaly(tx, profile),
            self.detect_failure_anomaly(tx, profile),
            self.detect_recency_anomaly(tx, profile)
        ]
""")

# backend/app/behavior/profile_store.py
write_file("backend/app/behavior/profile_store.py", """
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
import json
from app.models.entities import BehaviorProfile
from app.behavior.schemas import BehaviorProfileData

class BehaviorProfileStore:
    def __init__(self):
        # We can wrap a cache interface here in the future
        pass

    async def get_profile(self, db: AsyncSession, entity_id: str) -> dict:
        if not db:
            return None
        res = await db.execute(select(BehaviorProfile).filter_by(entity_id=entity_id))
        return res.scalar_one_or_none()

    async def save_profile(self, db: AsyncSession, entity_id: str, profile_data: BehaviorProfileData, tx_count: int, status: str, version: str):
        if not db:
            return
            
        stmt = insert(BehaviorProfile).values(
            entity_id=entity_id,
            profile_version=version,
            profile_status=status,
            profile_data=profile_data.model_dump(),
            transaction_count=tx_count
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['entity_id'],
            set_={
                'profile_version': stmt.excluded.profile_version,
                'profile_status': stmt.excluded.profile_status,
                'profile_data': stmt.excluded.profile_data,
                'transaction_count': stmt.excluded.transaction_count
            }
        )
        await db.execute(stmt)
        await db.commit()
""")

# backend/app/behavior/behavioral_service.py
write_file("backend/app/behavior/behavioral_service.py", """
from typing import Tuple, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.behavior.schemas import HistoricalTransaction, BehaviorProfileData, AnomalyResult
from app.behavior.profile_builder import build_profile, MIN_PROFILE_TRANSACTIONS
from app.behavior.profile_store import BehaviorProfileStore
from app.behavior.anomaly_detector import AnomalyDetector
from app.risk.risk_response import TransactionInput, SignalResponse
import json
import logging

logger = logging.getLogger(__name__)

class BehavioralService:
    def __init__(self):
        self.store = BehaviorProfileStore()
        self.detector = AnomalyDetector()
        self.version = "profile-v1"

    async def build_and_save_profile(self, db: AsyncSession, entity_id: str, transactions: List[HistoricalTransaction]) -> Tuple[str, int]:
        tx_count = len(transactions)
        status = "ESTABLISHED" if tx_count >= MIN_PROFILE_TRANSACTIONS else "INSUFFICIENT_HISTORY"
        
        profile_data = build_profile(transactions)
        
        await self.store.save_profile(db, entity_id, profile_data, tx_count, status, self.version)
        return status, tx_count

    async def get_anomaly_result(self, tx: TransactionInput, db: AsyncSession = None) -> SignalResponse:
        entity_id = tx.customer_id
        if not entity_id:
            return SignalResponse(available=False)

        profile_obj = await self.store.get_profile(db, entity_id)
        if not profile_obj or profile_obj.profile_status == "INSUFFICIENT_HISTORY":
            return SignalResponse(available=False, reasons=[{"reason_code": "BEHAVIOR_INSUFFICIENT_HISTORY", "severity": "INFO", "message": "Insufficient history for baseline"}])

        try:
            profile_data = BehaviorProfileData(**profile_obj.profile_data)
        except Exception as e:
            logger.error(f"Failed to parse profile data for {entity_id}: {e}")
            return SignalResponse(available=False)

        anomalies = self.detector.evaluate_all(tx, profile_data)
        
        # Weighted aggregation
        # amount: 40%, time: 20%, velocity: 25%, failure: 10%, recency: 5%
        weights = {
            "AMOUNT_ANOMALY": 0.40,
            "TIME_ANOMALY": 0.20,
            "VELOCITY_ANOMALY": 0.25,
            "FAILURE_ANOMALY": 0.10,
            "RECENCY_ANOMALY": 0.05
        }
        
        total_weight = 0.0
        weighted_score = 0.0
        reasons = []
        
        for an in anomalies:
            if an.available:
                w = weights.get(an.signal, 0.0)
                total_weight += w
                weighted_score += an.score * w
                if an.reason:
                    reasons.append({
                        "reason_code": f"BEHAVIOR_{an.signal}",
                        "severity": an.severity,
                        "message": an.reason
                    })
                    
        if total_weight == 0:
            return SignalResponse(available=False)
            
        final_score = min(weighted_score / total_weight, 100.0)
        
        return SignalResponse(
            available=True,
            score=final_score,
            reasons=reasons
        )
""")

print("Behavior module created.")
