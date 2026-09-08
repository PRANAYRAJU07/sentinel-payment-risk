# Sentinel — AI-Powered Payment Risk Control Tower

<div align="center">
  <h3>Real-time intelligence across transactions, behaviour, and fraud networks.</h3>
</div>

Sentinel is a production-quality, open-source payment risk intelligence platform. Rather than just returning a static ML prediction, Sentinel operates as a complete Security Operations Center (SOC) tool. It ingests transactions in real-time, builds behavioral baselines, detects fraud clusters using a NetworkX graph engine, aggregates risk through a multi-model scoring engine, and provides an AI-powered investigation dashboard for human analysts.

## Features

- **Live Risk Stream**: Stream transactions and their computed risk in real time.
- **Fraud Lab Simulator**: Launch pre-configured synthetic fraud attacks (Account Takeovers, Velocity Bursts) with a single click.
- **Behavioral Profiling**: Sentinel doesn't just ask "Is this transaction bad?" it asks "Is this transaction unusual for *this* customer?".
- **Network Graph Engine**: Detects IP sharing and device clustering across otherwise disconnected accounts to identify coordinated fraud rings.
- **AI Investigator**: Explains precisely why a transaction was flagged, providing deterministic or LLM-backed evidence.
- **Razorpay Test Mode Integration**: Securely receives and processes Razorpay webhooks.

## Architecture

![Architecture](docs/images/architecture.png)
*(Note: A full architectural diagram can be built using Mermaid or external tools)*

Sentinel uses a powerful multi-stage pipeline:
1. **Event Processor**: Normalizes incoming API requests and webhooks.
2. **Machine Learning Model**: (Random Forest) evaluates the core transaction profile.
3. **Behavioral Engine**: Calculates robust Z-Scores against historical profiles.
4. **Rules Engine**: Enforces static business logic.
5. **Graph Engine**: Builds a real-time NetworkX subgraph to detect high-risk neighbors.
6. **Aggregator**: Combines all signals into a 0-100 score.

## Installation

Sentinel provides a completely functional "Demo Mode" out of the box using Docker.

```bash
# Clone the repository
git clone https://github.com/PRANAYRAJU07/sentinel-payment-risk.git
cd sentinel-payment-risk

# Copy the environment file
cp .env.example .env

# Start Sentinel
docker compose up --build
```
On startup, Docker will run migrations and seed the database with 5,000 synthetic customers and 100,000 transactions to build behavioral profiles.

You can then access:
- **Frontend Dashboard**: http://localhost:3000
- **API Swagger**: http://localhost:8000/docs

## Dataset Honesty & Synthetic Data

The ML model in Sentinel is trained on the real `mlg-ulb/creditcardfraud` dataset from Kaggle. However, that dataset does not contain IPs, Devices, or Merchant IDs. To demonstrate Sentinel's Behavioral and Graph capabilities, we dynamically generate a **Synthetic Payment Ecosystem** during the `seed_demo.py` phase. This allows the Fraud Lab and Network Visualizer to function exactly as they would in production.

## Running Tests

```bash
cd backend
python -m pytest
```

## Security

We strongly enforce no-commit of `.env` files. Ensure you use `.env.example` to define dummy variables in CI. Razorpay webhook secrets and LLM API keys should be injected at runtime.
