# Behavioral Anomaly Engine

## Architecture
The Behavioral Engine is responsible for creating and maintaining persistent entity profiles and computing real-time anomaly scores when new transactions arrive.

It consists of:
1. **Profile Builder**: Aggregates historical `SUCCESS` transactions to compute `BehaviorProfileData` (mean, median, std, typical hours, daily velocity).
2. **Profile Store**: Handles storage in PostgreSQL, falling back gracefully if unavailable.
3. **Anomaly Detector**: Computes scores (e.g. Robust Z-Score) by comparing incoming properties against the baseline.
4. **Behavioral Service**: Orchestrates the DB fetch, evaluation, and reasons payload creation.

## Leakage Prevention
A critical feature of the system is the separation of baseline construction and anomaly evaluation. The current transaction is **never** used to evaluate its own anomaly baseline, which would improperly pull the average toward the anomaly.

## Handling Incomplete Data
- If standard deviation is 0, it falls back to 1.0 to prevent division by zero while preserving extreme Z-scores for novel amounts.
- If fewer than 20 transactions exist (Cold Start), the engine safely returns `available=False` and the Risk Aggregator renormalizes without penalizing the customer.
