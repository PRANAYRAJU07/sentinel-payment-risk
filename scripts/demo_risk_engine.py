import sys
import time
import uuid
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.risk.risk_engine import RiskEngineOrchestrator
from app.risk.risk_response import TransactionInput


async def main():
    engine = RiskEngineOrchestrator()
    print("Sentinel Risk Engine Demo & Benchmark")
    print("=====================================\n")

    # --- Demo ---
    print("--- Transaction A: Normal ---")
    tx_a = TransactionInput(id=str(uuid.uuid4()), amount=150.0, context={})
    res_a = await engine.evaluate(tx_a)
    print(f"Score: {res_a.final_risk_score}, Decision: {res_a.decision}")

    print("\n--- Transaction B: High Amount + ML Risk ---")
    tx_b = TransactionInput(
        id=str(uuid.uuid4()),
        amount=60000.0,  # Triggers extreme amount rule
        v_features={"V1": -3.0, "V2": 2.0},  # Might bump ML slightly
        context={},
    )
    res_b = await engine.evaluate(tx_b)
    print(f"Score: {res_b.final_risk_score}, Decision: {res_b.decision}")

    print("\n--- Transaction C: Suspicious Graph + Velocity ---")
    tx_c = TransactionInput(
        id=str(uuid.uuid4()),
        amount=500.0,
        context={"velocity_1h": 25, "graph_risk": {"score": 90.0}},
    )
    res_c = await engine.evaluate(tx_c)
    print(f"Score: {res_c.final_risk_score}, Decision: {res_c.decision}")

    # --- Benchmark ---
    print("\n--- Benchmarking Latency (1000 requests) ---")
    latencies = []

    tx_bench = TransactionInput(
        id=str(uuid.uuid4()),
        amount=250.0,
        v_features={f"V{i}": 0.1 for i in range(1, 29)},
        context={"velocity_1h": 2},
    )

    for _ in range(1000):
        t0 = time.perf_counter()
        await engine.evaluate(tx_bench)
        latencies.append((time.perf_counter() - t0) * 1000)  # ms

    latencies.sort()
    avg_latency = sum(latencies) / len(latencies)
    p95_latency = latencies[int(len(latencies) * 0.95)]

    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"P95 Latency: {p95_latency:.2f} ms")

    # Write to docs/risk-engine-demo.md
    out_path = PROJECT_ROOT / "docs" / "risk-engine-demo.md"
    with open(out_path, "w") as f:
        f.write(f"""# Sentinel Risk Engine Demo & Benchmarks

## Example Evaluations

### Transaction A (Normal)
- **Amount**: 150.0
- **Context**: Normal
- **Result**: {res_a.final_risk_score} -> {res_a.decision}

### Transaction B (Extreme Amount)
- **Amount**: 60000.0
- **Context**: Normal
- **Result**: {res_b.final_risk_score} -> {res_b.decision}

### Transaction C (Velocity + Graph Risk)
- **Amount**: 500.0
- **Context**: 25 tx/hr, connected to fraud graph
- **Result**: {res_c.final_risk_score} -> {res_c.decision}

## Latency Benchmark (1000 synthetic requests)
- **Average Latency**: {avg_latency:.2f} ms
- **P95 Latency**: {p95_latency:.2f} ms
""")
    print(f"\nWrote results to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
