# Sentinel Risk Engine Demo & Benchmarks

## Example Evaluations

### Transaction A (Normal)
- **Amount**: 150.0
- **Context**: Normal
- **Result**: 0 -> APPROVE

### Transaction B (Extreme Amount)
- **Amount**: 60000.0
- **Context**: Normal
- **Result**: 40 -> REVIEW

### Transaction C (Velocity + Graph Risk)
- **Amount**: 500.0
- **Context**: 25 tx/hr, connected to fraud graph
- **Result**: 45 -> REVIEW

## Latency Benchmark (1000 synthetic requests)
- **Average Latency**: 45.57 ms
- **P95 Latency**: 70.06 ms
