"""
Sentinel Risk Engine — Rule Factors
Evaluates explicit deterministic rules.
"""

from app.risk.risk_response import SignalResponse, TransactionInput

# Prototypical thresholds
EXTREME_AMOUNT_THRESHOLD = 50000.0


class RuleEngine:
    def evaluate(self, transaction: TransactionInput) -> SignalResponse:
        reasons = []
        total_score = 0.0
        available = True

        # Rule 1: Extreme Amount
        if transaction.amount > EXTREME_AMOUNT_THRESHOLD:
            reasons.append(
                {
                    "reason_code": "EXTREME_AMOUNT",
                    "severity": "HIGH",
                    "message": f"Transaction amount {transaction.amount} exceeds configured threshold of {EXTREME_AMOUNT_THRESHOLD}",
                }
            )
            total_score += 40.0

        # Context-based rules
        ctx = transaction.context

        # Rule 2: High transaction velocity
        if "velocity_1h" in ctx and ctx["velocity_1h"] > 10:
            reasons.append(
                {
                    "reason_code": "HIGH_VELOCITY",
                    "severity": "HIGH",
                    "message": f"Transaction frequency ({ctx['velocity_1h']} in 1h) exceeds configured threshold",
                }
            )
            total_score += 30.0

        # Rule 3: Multiple recent failures
        if "recent_failures" in ctx and ctx["recent_failures"] > 3:
            reasons.append(
                {
                    "reason_code": "RECENT_FAILURES",
                    "severity": "MEDIUM",
                    "message": "Multiple recent payment failures detected",
                }
            )
            total_score += 25.0

        # Rule 4 & 5: New device / location
        if ctx.get("is_new_device") is True:
            reasons.append(
                {
                    "reason_code": "NEW_DEVICE",
                    "severity": "LOW",
                    "message": "First time seeing this device for customer",
                }
            )
            total_score += 15.0

        if ctx.get("is_new_location") is True:
            reasons.append(
                {
                    "reason_code": "NEW_LOCATION",
                    "severity": "LOW",
                    "message": "First time seeing this location for customer",
                }
            )
            total_score += 15.0

        # Cap score at 100
        total_score = min(total_score, 100.0)

        return SignalResponse(available=available, score=total_score, reasons=reasons)
