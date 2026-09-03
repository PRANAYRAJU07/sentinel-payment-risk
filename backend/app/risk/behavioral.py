"""
Sentinel Risk Engine — Behavioral Analysis
Calculates deviations from customer baselines.
"""

from app.risk.risk_response import SignalResponse, TransactionInput


class BehavioralAnalyzer:
    def evaluate(self, transaction: TransactionInput) -> SignalResponse:
        ctx = transaction.context

        # If baseline information is missing, signal is unavailable
        if "customer_baseline" not in ctx:
            return SignalResponse(available=False)

        baseline = ctx["customer_baseline"]
        reasons = []
        score = 0.0

        # Amount anomaly (Z-score)
        if "avg_amount" in baseline and "std_amount" in baseline:
            avg = baseline["avg_amount"]
            std = baseline["std_amount"]
            if std > 0:
                z_score = abs(transaction.amount - avg) / std
                if z_score > 3:
                    reasons.append(
                        {
                            "reason_code": "AMOUNT_ANOMALY",
                            "severity": "HIGH",
                            "message": f"Amount {transaction.amount} is > 3 standard deviations from baseline {avg}",
                        }
                    )
                    score += min(z_score * 10, 50.0)

        # Time anomaly
        if "typical_hours" in baseline:
            # We assume transaction.time is unix timestamp, let's extract hour if possible.
            # For prototype, we'll just check if hour is passed in context
            tx_hour = ctx.get("tx_hour", None)
            if tx_hour is not None and tx_hour not in baseline["typical_hours"]:
                reasons.append(
                    {
                        "reason_code": "TIME_ANOMALY",
                        "severity": "MEDIUM",
                        "message": f"Transaction hour {tx_hour} is outside typical hours {baseline['typical_hours']}",
                    }
                )
                score += 20.0

        # Cap score
        score = min(score, 100.0)

        return SignalResponse(available=True, score=score, reasons=reasons)
