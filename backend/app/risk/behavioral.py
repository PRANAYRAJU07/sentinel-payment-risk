"""
Sentinel Risk Engine — Behavioral Analysis
Calculates deviations from customer baselines.
Now delegates to the persistent BehavioralService (Phase 8).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.risk.risk_response import SignalResponse, TransactionInput
from app.behavior.behavioral_service import BehavioralService

class BehavioralAnalyzer:
    def __init__(self):
        self.service = BehavioralService()

    async def evaluate(self, transaction: TransactionInput, db: AsyncSession = None) -> SignalResponse:
        """
        Evaluate behavioral anomalies by fetching the customer's profile from the DB.
        If no DB is provided or no profile exists, falls back gracefully.
        """
        # If the transaction explicitly provides a baseline (legacy fallback for tests)
        if "customer_baseline" in transaction.context and not db:
            return self._legacy_evaluate(transaction)
            
        return await self.service.get_anomaly_result(transaction, db)
        
    def _legacy_evaluate(self, transaction: TransactionInput) -> SignalResponse:
        ctx = transaction.context
        if "customer_baseline" not in ctx:
            return SignalResponse(available=False)

        baseline = ctx["customer_baseline"]
        reasons = []
        score = 0.0

        if "avg_amount" in baseline and "std_amount" in baseline:
            avg = baseline["avg_amount"]
            std = baseline["std_amount"]
            if std > 0:
                z_score = abs(transaction.amount - avg) / std
                if z_score > 3:
                    reasons.append({
                        "reason_code": "AMOUNT_ANOMALY",
                        "severity": "HIGH",
                        "message": f"Amount {transaction.amount} is > 3 standard deviations from baseline {avg}"
                    })
                    score += min(z_score * 10, 50.0)

        tx_hour = ctx.get("tx_hour", None)
        if tx_hour is not None and "typical_hours" in baseline and tx_hour not in baseline["typical_hours"]:
            reasons.append({
                "reason_code": "TIME_ANOMALY",
                "severity": "MEDIUM",
                "message": f"Transaction hour {tx_hour} is outside typical hours {baseline['typical_hours']}"
            })
            score += 20.0

        return SignalResponse(available=True, score=min(score, 100.0), reasons=reasons)
