"""
Sentinel Risk Engine — Graph Risk Interface
Interface for graph signal. Full engine to be built in later phase.
"""

from app.risk.risk_response import SignalResponse, TransactionInput


class GraphRiskSignal:
    def evaluate(self, transaction: TransactionInput) -> SignalResponse:
        ctx = transaction.context

        if "graph_risk" not in ctx:
            return SignalResponse(available=False)

        graph_data = ctx["graph_risk"]

        reasons = []
        score = float(graph_data.get("score", 0.0))

        if score > 0:
            reasons.append(
                {
                    "reason_code": "SUSPICIOUS_GRAPH_CONNECTION",
                    "severity": "HIGH" if score > 75 else "MEDIUM",
                    "message": "Connected to known risky entities in graph",
                }
            )

        return SignalResponse(available=True, score=score, reasons=reasons)
