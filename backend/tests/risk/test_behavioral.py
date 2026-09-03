"""
Sentinel Risk Engine — Behavioral Analysis Tests
"""

from app.risk.behavioral import BehavioralAnalyzer
from app.risk.risk_response import TransactionInput


def test_missing_baseline():
    engine = BehavioralAnalyzer()
    tx = TransactionInput(amount=100.0)
    res = engine.evaluate(tx)

    assert res.available is False
    assert res.score == 0.0


def test_amount_anomaly():
    engine = BehavioralAnalyzer()

    # Normal
    tx = TransactionInput(
        amount=1100.0,
        context={"customer_baseline": {"avg_amount": 1000.0, "std_amount": 100.0}},
    )
    res = engine.evaluate(tx)
    assert res.available is True
    assert res.score == 0.0

    # Anomaly (z-score = 4)
    tx = TransactionInput(
        amount=1400.0,
        context={"customer_baseline": {"avg_amount": 1000.0, "std_amount": 100.0}},
    )
    res = engine.evaluate(tx)
    assert res.available is True
    # z=4, score should be min(40, 50) = 40.0
    assert res.score == 40.0
    assert res.reasons[0]["reason_code"] == "AMOUNT_ANOMALY"


def test_time_anomaly():
    engine = BehavioralAnalyzer()
    tx = TransactionInput(
        amount=100.0,
        context={
            "tx_hour": 3,
            "customer_baseline": {"typical_hours": [10, 11, 12, 13]},
        },
    )
    res = engine.evaluate(tx)
    assert res.score == 20.0
    assert res.reasons[0]["reason_code"] == "TIME_ANOMALY"
