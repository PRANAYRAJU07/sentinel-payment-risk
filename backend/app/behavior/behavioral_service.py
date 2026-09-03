import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.behavior.anomaly_detector import AnomalyDetector
from app.behavior.profile_builder import MIN_PROFILE_TRANSACTIONS, build_profile
from app.behavior.profile_store import BehaviorProfileStore
from app.behavior.schemas import (
    BehaviorProfileData,
    HistoricalTransaction,
)
from app.risk.risk_response import SignalResponse, TransactionInput

logger = logging.getLogger(__name__)


class BehavioralService:
    def __init__(self):
        self.store = BehaviorProfileStore()
        self.detector = AnomalyDetector()
        self.version = "profile-v1"

    async def build_and_save_profile(
        self,
        db: AsyncSession,
        entity_id: str,
        transactions: list[HistoricalTransaction],
    ) -> tuple[str, int]:
        tx_count = len(transactions)
        status = (
            "ESTABLISHED"
            if tx_count >= MIN_PROFILE_TRANSACTIONS
            else "INSUFFICIENT_HISTORY"
        )

        profile_data = build_profile(transactions)

        await self.store.save_profile(
            db, entity_id, profile_data, tx_count, status, self.version
        )
        return status, tx_count

    async def get_anomaly_result(
        self, tx: TransactionInput, db: AsyncSession = None
    ) -> SignalResponse:
        entity_id = tx.customer_id
        if not entity_id:
            return SignalResponse(available=False)

        profile_obj = await self.store.get_profile(db, entity_id)
        if not profile_obj or profile_obj.profile_status == "INSUFFICIENT_HISTORY":
            return SignalResponse(
                available=False,
                reasons=[
                    {
                        "reason_code": "BEHAVIOR_INSUFFICIENT_HISTORY",
                        "severity": "INFO",
                        "message": "Insufficient history for baseline",
                    }
                ],
            )

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
            "RECENCY_ANOMALY": 0.05,
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
                    reasons.append(
                        {
                            "reason_code": f"BEHAVIOR_{an.signal}",
                            "severity": an.severity,
                            "message": an.reason,
                        }
                    )

        if total_weight == 0:
            return SignalResponse(available=False)

        final_score = min(weighted_score / total_weight, 100.0)

        return SignalResponse(available=True, score=final_score, reasons=reasons)
