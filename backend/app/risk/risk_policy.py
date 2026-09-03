"""
Sentinel Risk Engine — Decision Engine Policy
Maps aggregated score to final decision (APPROVE/REVIEW/HOLD) and handles overrides.
"""


from app.core.config import get_settings
from app.risk.risk_response import TransactionInput


class DecisionEngine:
    def __init__(self):
        self.settings = get_settings()

    def evaluate(
        self, final_score: float, transaction: TransactionInput
    ) -> tuple[str, str, dict | None]:
        """
        Returns (risk_level, decision, override_reason)
        """
        ctx = transaction.context

        # Explicit Overrides
        if ctx.get("known_blocked_entity") is True:
            return (
                "HIGH",
                "HOLD",
                {
                    "reason_code": "BLOCKED_ENTITY_OVERRIDE",
                    "severity": "CRITICAL",
                    "message": "Transaction blocked due to known blocked entity override.",
                },
            )

        if ctx.get("verified_manual_release") is True:
            return (
                "LOW",
                "APPROVE",
                {
                    "reason_code": "MANUAL_RELEASE_OVERRIDE",
                    "severity": "INFO",
                    "message": "Transaction approved due to explicit manual release.",
                },
            )

        # Standard Policy Evaluation
        if final_score >= self.settings.risk_high_threshold:
            return "HIGH", "HOLD", None
        elif final_score >= self.settings.risk_low_threshold:
            return "MEDIUM", "REVIEW", None
        else:
            return "LOW", "APPROVE", None
