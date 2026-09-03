from datetime import datetime, timezone

from app.behavior.anomaly_detector import AnomalyDetector
from app.behavior.profile_builder import build_profile
from app.behavior.schemas import BehaviorProfileData, HistoricalTransaction
from app.risk.risk_response import TransactionInput


def test_data_leakage_current_tx_not_in_baseline():
    """
    PHASE 8.30 EXPLICIT REQUIREMENT
    Prove that the transaction being evaluated is NOT included in the baseline
    used to evaluate itself.
    """
    # 1. Build profile from transactions 1-100
    txs = []
    for i in range(100):
        txs.append(
            HistoricalTransaction(
                transaction_id=f"tx_{i}",
                entity_id="leak_test_user",
                amount=50.0,  # Strict $50 historical average
                timestamp=1600000000 + (i * 3600),
                status="SUCCESS",
            )
        )

    profile = build_profile(txs)

    assert profile.amount.mean == 50.0
    assert profile.amount.std == 0.0

    # 2. Evaluate transaction 101
    tx_101 = TransactionInput(
        id="tx_101",
        amount=5000.0,
        time=1600000000 + (101 * 3600),
        customer_id="leak_test_user",
    )

    detector = AnomalyDetector()
    res = detector.detect_amount_anomaly(tx_101, profile)

    # 3. Verify baseline used was based ONLY on 1-100
    # The mean should STILL be 50.0, not skewed by 5000.0
    assert res.baseline["mean"] == 50.0
    assert (
        res.score == 100.0
    )  # Max anomaly because std is 0 (handled as 1.0) and Z-score is huge


def test_zero_std_handling():
    detector = AnomalyDetector()
    profile = BehaviorProfileData()
    profile.amount.mean = 100.0
    profile.amount.std = 0.0
    profile.amount.max = 100.0

    # Normal tx (100)
    tx_normal = TransactionInput(id="t1", amount=100.0)
    res_normal = detector.detect_amount_anomaly(tx_normal, profile)
    assert res_normal.score == 0

    # Anomalous tx (200), should use std=1.0 fallback
    tx_anom = TransactionInput(id="t2", amount=200.0)
    res_anom = detector.detect_amount_anomaly(tx_anom, profile)
    assert res_anom.score == 100.0


def test_time_anomaly():
    detector = AnomalyDetector()
    profile = BehaviorProfileData()
    profile.time.typical_hours = [10, 11, 12, 13, 14]

    # 1. Exact match
    dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    tx = TransactionInput(id="1", amount=10, time=dt.timestamp())
    res = detector.detect_time_anomaly(tx, profile)
    assert res.score == 0

    # 2. Far anomaly (3 AM)
    dt2 = datetime(2023, 1, 1, 3, 0, 0, tzinfo=timezone.utc)
    tx2 = TransactionInput(id="2", amount=10, time=dt2.timestamp())
    res2 = detector.detect_time_anomaly(tx2, profile)
    assert res2.score > 50


def test_velocity_anomaly():
    detector = AnomalyDetector()
    profile = BehaviorProfileData()
    profile.velocity.avg_daily_count = 2.0

    tx1 = TransactionInput(id="1", amount=10, context={"velocity_1h": 1})
    res1 = detector.detect_velocity_anomaly(tx1, profile)
    assert res1.score == 0

    tx2 = TransactionInput(id="2", amount=10, context={"velocity_1h": 15})
    res2 = detector.detect_velocity_anomaly(tx2, profile)
    assert res2.score == 100.0
