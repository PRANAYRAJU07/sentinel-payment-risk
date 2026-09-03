"""
Sentinel Risk Engine — Rule Engine Tests
"""

from app.risk.risk_factors import EXTREME_AMOUNT_THRESHOLD, RuleEngine
from app.risk.risk_response import TransactionInput


def test_extreme_amount():
    engine = RuleEngine()

    # Normal amount
    tx = TransactionInput(amount=100.0)
    res = engine.evaluate(tx)
    assert res.score == 0.0
    assert len(res.reasons) == 0

    # Extreme amount
    tx = TransactionInput(amount=EXTREME_AMOUNT_THRESHOLD + 100.0)
    res = engine.evaluate(tx)
    assert res.score == 40.0
    assert res.reasons[0]["reason_code"] == "EXTREME_AMOUNT"


def test_velocity_and_failures():
    engine = RuleEngine()

    tx = TransactionInput(
        amount=100.0, context={"velocity_1h": 15, "recent_failures": 5}
    )
    res = engine.evaluate(tx)

    # 30 for velocity + 25 for failures
    assert res.score == 55.0
    codes = [r["reason_code"] for r in res.reasons]
    assert "HIGH_VELOCITY" in codes
    assert "RECENT_FAILURES" in codes


def test_score_capping():
    engine = RuleEngine()

    tx = TransactionInput(
        amount=EXTREME_AMOUNT_THRESHOLD + 100.0,  # 40
        context={
            "velocity_1h": 15,  # 30
            "recent_failures": 5,  # 25
            "is_new_device": True,  # 15
            "is_new_location": True,  # 15
        },
    )
    res = engine.evaluate(tx)
    # Sum is 125, should be capped at 100
    assert res.score == 100.0
