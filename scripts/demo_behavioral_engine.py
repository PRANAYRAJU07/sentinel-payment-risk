import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone

from app.behavior.behavioral_service import BehavioralService
from app.behavior.schemas import HistoricalTransaction
from app.core.database import get_db_engine
from app.risk.risk_response import TransactionInput
from sqlalchemy.ext.asyncio import AsyncSession


async def main():
    engine = get_db_engine()
    service = BehavioralService()

    # Create dummy entity
    entity_id = "demo_user_1"
    now = datetime.now(timezone.utc)

    # Generate 50 normal transactions for baseline
    # Amount ~ 100, Hour ~ 10-18, No failures
    txs = []
    current_time = now - timedelta(days=30)
    for i in range(50):
        current_time += timedelta(hours=14)
        if current_time.hour < 9 or current_time.hour > 18:
            current_time = current_time.replace(hour=12)

        txs.append(
            HistoricalTransaction(
                transaction_id=f"tx_{i}",
                entity_id=entity_id,
                amount=100.0 + (i % 10),
                timestamp=current_time.timestamp(),
                status="SUCCESS",
            )
        )

    async with engine.begin() as conn:
        from app.models.entities import Base

        await conn.run_sync(Base.metadata.create_all)

    from sqlalchemy.orm import sessionmaker

    AsyncSessionLocal = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with AsyncSessionLocal() as db:
        print("--- Building Profile ---")
        status, count = await service.build_and_save_profile(db, entity_id, txs)
        print(f"Profile Status: {status}, Transactions: {count}")

        scenarios = [
            ("Normal", 105.0, now.replace(hour=12).timestamp(), 1, 0),
            ("Amount Anomaly", 5000.0, now.replace(hour=12).timestamp(), 1, 0),
            ("Time Anomaly", 105.0, now.replace(hour=3).timestamp(), 1, 0),
            ("Velocity Anomaly", 105.0, now.replace(hour=12).timestamp(), 20, 0),
            ("Multiple Anomalies", 5000.0, now.replace(hour=3).timestamp(), 20, 5),
        ]

        for name, amt, ts, vel, fails in scenarios:
            tx = TransactionInput(
                id=str(uuid.uuid4()),
                amount=amt,
                time=ts,
                customer_id=entity_id,
                context={"velocity_1h": vel, "failures_24h": fails},
            )
            res = await service.get_anomaly_result(tx, db)
            print(f"\n--- Scenario: {name} ---")
            print(f"Behavioral Score: {res.score}")
            for r in res.reasons:
                print(f"  - {r['reason_code']}: {r['message']}")

        print("\n--- Benchmarking (10,000 transactions) ---")
        latencies = []
        for _ in range(10000):
            tx = TransactionInput(
                id=str(uuid.uuid4()),
                amount=105.0,
                time=now.replace(hour=12).timestamp(),
                customer_id=entity_id,
                context={"velocity_1h": 1, "failures_24h": 0},
            )
            t0 = time.perf_counter()
            await service.get_anomaly_result(tx, db)
            latencies.append((time.perf_counter() - t0) * 1000)

        latencies.sort()
        avg = sum(latencies) / len(latencies)
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]

        print(f"Average Latency: {avg:.2f} ms")
        print(f"P50 Latency: {p50:.2f} ms")
        print(f"P95 Latency: {p95:.2f} ms")
        print(f"P99 Latency: {p99:.2f} ms")


if __name__ == "__main__":
    asyncio.run(main())
