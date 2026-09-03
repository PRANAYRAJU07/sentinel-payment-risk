"""
Sentinel Risk Engine — Orchestrator Tests
"""

import uuid
import pytest
import asyncio

from app.risk.risk_engine import RiskEngineOrchestrator
from app.risk.risk_response import SignalResponse, TransactionInput


def test_engine_weight_renormalization(monkeypatch):
    # Test that if some signals are unavailable, weights are correctly normalized.
    engine = RiskEngineOrchestrator()

    # Mock settings
    engine.settings.risk_ml_weight = 0.60
    engine.settings.risk_behavior_weight = 0.20
    engine.settings.risk_rule_weight = 0.15
    engine.settings.risk_graph_weight = 0.05

    # Scenario 1: All available
    ml = SignalResponse(available=True, score=50.0)
    beh = SignalResponse(available=True, score=50.0)
    rule = SignalResponse(available=True, score=50.0)
    graph = SignalResponse(available=True, score=50.0)

    score = engine._aggregate_scores(ml, beh, rule, graph)
    assert score == 50.0

    # Scenario 2: Graph unavailable (0.95 total weight available)
    # ML = 60/95, Beh = 20/95, Rule = 15/95
    graph = SignalResponse(available=False, score=0.0)
    # Give ML 100, others 0 -> (100 * 60/95) = 63.15
    ml = SignalResponse(available=True, score=100.0)
    beh = SignalResponse(available=True, score=0.0)
    rule = SignalResponse(available=True, score=0.0)

    score = engine._aggregate_scores(ml, beh, rule, graph)
    assert round(score, 2) == 63.16

    # Scenario 3: Only ML available (0.60 total weight)
    # ML weight becomes 1.0
    beh = SignalResponse(available=False)
    rule = SignalResponse(available=False)
    ml = SignalResponse(available=True, score=77.0)

    score = engine._aggregate_scores(ml, beh, rule, graph)
    assert score == 77.0


@pytest.mark.asyncio
async def test_engine_evaluation_mocked():
    engine = RiskEngineOrchestrator()

    # Let's see what happens without ML model loaded
    tx = TransactionInput(id=str(uuid.uuid4()), amount=100.0)
    res = await engine.evaluate(tx, db=None)

    # Only rules might trigger (but amount=100 is low, no context)
    assert res.final_risk_score == 0
    assert res.decision == "APPROVE"
    assert res.signal_availability["behavioral"] == False
    assert res.signal_availability["graph"] == False
