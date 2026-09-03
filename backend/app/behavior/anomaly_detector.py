from datetime import datetime, timezone

from app.behavior.schemas import (
    AnomalyResult,
    BehaviorProfileData,
)
from app.risk.risk_response import TransactionInput


class AnomalyDetector:
    def __init__(self):
        pass

    def detect_amount_anomaly(
        self, tx: TransactionInput, profile: BehaviorProfileData
    ) -> AnomalyResult:
        amt = profile.amount
        if tx.amount <= amt.max and tx.amount <= amt.mean + (3 * amt.std):
            return AnomalyResult(
                signal="AMOUNT_ANOMALY",
                available=True,
                score=0,
                severity="LOW",
                value=tx.amount,
                baseline={"mean": amt.mean, "std": amt.std},
            )

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
            reason=reason,
        )

    def detect_time_anomaly(
        self, tx: TransactionInput, profile: BehaviorProfileData
    ) -> AnomalyResult:
        if not profile.time.typical_hours:
            return AnomalyResult(signal="TIME_ANOMALY", available=False)

        dt = datetime.fromtimestamp(tx.time, tz=timezone.utc)
        tx_hour = dt.hour

        # Calculate circular distance to nearest typical hour
        min_dist = 12
        for th in profile.time.typical_hours:
            dist = min(abs(tx_hour - th), 24 - abs(tx_hour - th))
            min_dist = min(min_dist, dist)

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
            reason=reason,
        )

    def detect_velocity_anomaly(
        self, tx: TransactionInput, profile: BehaviorProfileData
    ) -> AnomalyResult:
        vel_1h = tx.context.get("velocity_1h", 0)
        avg_daily = profile.velocity.avg_daily_count

        # If hourly velocity is more than daily average
        if avg_daily > 0 and vel_1h > (avg_daily / 2) + 2:
            ratio = vel_1h / max(avg_daily, 1.0)
            score = min(ratio * 20, 100)
            severity = "HIGH" if score > 75 else ("MEDIUM" if score > 40 else "LOW")
            reason = "Unusual transaction frequency" if score > 40 else None
            return AnomalyResult(
                signal="VELOCITY_ANOMALY",
                available=True,
                score=score,
                severity=severity,
                value=vel_1h,
                baseline={"avg_daily": avg_daily},
                reason=reason,
            )

        return AnomalyResult(
            signal="VELOCITY_ANOMALY",
            available=True,
            score=0,
            value=vel_1h,
            baseline={"avg_daily": avg_daily},
        )

    def detect_failure_anomaly(
        self, tx: TransactionInput, profile: BehaviorProfileData
    ) -> AnomalyResult:
        failures_24h = tx.context.get("failures_24h", 0)
        fail_rate = profile.failure.failure_rate

        if failures_24h > 2 and fail_rate < 0.1:
            score = min(failures_24h * 15, 100)
            severity = "HIGH" if score > 75 else ("MEDIUM" if score > 40 else "LOW")
            reason = (
                "Elevated failure rate compared to historical baseline"
                if score > 40
                else None
            )
            return AnomalyResult(
                signal="FAILURE_ANOMALY",
                available=True,
                score=score,
                severity=severity,
                value=failures_24h,
                baseline={"historical_rate": fail_rate},
                reason=reason,
            )

        return AnomalyResult(
            signal="FAILURE_ANOMALY",
            available=True,
            score=0,
            value=failures_24h,
            baseline={"historical_rate": fail_rate},
        )

    def detect_recency_anomaly(
        self, tx: TransactionInput, profile: BehaviorProfileData
    ) -> AnomalyResult:
        last_ts = profile.last_transaction_timestamp
        if last_ts == 0:
            return AnomalyResult(signal="RECENCY_ANOMALY", available=False)

        diff_sec = tx.time - last_ts
        if diff_sec > 0 and diff_sec < 60:  # Under 1 minute
            score = 60.0
            return AnomalyResult(
                signal="RECENCY_ANOMALY",
                available=True,
                score=score,
                severity="MEDIUM",
                value=diff_sec,
                baseline={"last_ts": last_ts},
                reason="Transactions extremely close in time",
            )

        return AnomalyResult(
            signal="RECENCY_ANOMALY",
            available=True,
            score=0,
            value=diff_sec,
            baseline={"last_ts": last_ts},
        )

    def evaluate_all(
        self, tx: TransactionInput, profile: BehaviorProfileData
    ) -> list[AnomalyResult]:
        return [
            self.detect_amount_anomaly(tx, profile),
            self.detect_time_anomaly(tx, profile),
            self.detect_velocity_anomaly(tx, profile),
            self.detect_failure_anomaly(tx, profile),
            self.detect_recency_anomaly(tx, profile),
        ]
