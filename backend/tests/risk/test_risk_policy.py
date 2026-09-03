"""
Sentinel Risk Engine — Decision Engine Policy Tests
"""

from app.risk.risk_policy import DecisionEngine
from app.risk.risk_response import TransactionInput


def test_decision_thresholds():
    engine = DecisionEngine()

    # Defaults: LOW=40, HIGH=75
    # LOW
    tx = TransactionInput(amount=10.0)
    level, decision, override = engine.evaluate(20.0, tx)
    assert level == "LOW"
    assert decision == "APPROVE"
    assert override is None

    # MEDIUM
    level, decision, override = engine.evaluate(50.0, tx)
    assert level == "MEDIUM"
    assert decision == "REVIEW"

    # HIGH
    level, decision, override = engine.evaluate(80.0, tx)
    assert level == "HIGH"
    assert decision == "HOLD"


def test_explicit_overrides():
    engine = DecisionEngine()

    # Blocked entity -> HIGH/HOLD regardless of score
    tx = TransactionInput(amount=10.0, context={"known_blocked_entity": True})
    level, decision, override = engine.evaluate(10.0, tx)
    assert level == "HIGH"
    assert decision == "HOLD"
    assert override["reason_code"] == "BLOCKED_ENTITY_OVERRIDE"

    # Manual release -> LOW/APPROVE regardless of score
    tx = TransactionInput(amount=10.0, context={"verified_manual_release": True})
    level, decision, override = engine.evaluate(99.0, tx)
    assert level == "LOW"
    assert decision == "APPROVE"
    assert override["reason_code"] == "MANUAL_RELEASE_OVERRIDE"
