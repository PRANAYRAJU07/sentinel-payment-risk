import json
import os
import random
import uuid
from datetime import datetime, timedelta, timezone


def generate_synthetic_behavioral_data(num_entities=1000):
    personas = [
        "NORMAL_CUSTOMER",
        "HIGH_VALUE_CUSTOMER",
        "NIGHT_CUSTOMER",
        "HIGH_FREQUENCY_CUSTOMER",
        "IRREGULAR_CUSTOMER",
        "COMPROMISED_CUSTOMER",
    ]

    dataset = []

    now = datetime.now(timezone.utc)

    for _ in range(num_entities):
        persona = random.choice(personas)
        entity_id = f"user_{uuid.uuid4().hex[:8]}"

        # Base config based on persona
        num_tx = random.randint(25, 100)
        amount_mean = 100.0
        amount_std = 20.0
        active_hours = list(range(9, 18))
        failure_prob = 0.02
        freq_minutes = 60 * 24  # 1 per day

        if persona == "HIGH_VALUE_CUSTOMER":
            amount_mean = 5000.0
            amount_std = 1500.0
        elif persona == "NIGHT_CUSTOMER":
            active_hours = [0, 1, 2, 3, 4, 22, 23]
        elif persona == "HIGH_FREQUENCY_CUSTOMER":
            num_tx = random.randint(150, 300)
            freq_minutes = 60 * 2  # 12 per day
        elif persona == "IRREGULAR_CUSTOMER":
            amount_std = 200.0
            active_hours = list(range(24))
        elif persona == "COMPROMISED_CUSTOMER":
            failure_prob = 0.20
            freq_minutes = 15
            amount_std = 1000.0

        transactions = []
        current_time = now - timedelta(days=90)

        for _ in range(num_tx):
            # Advance time by frequency + some noise
            jump = random.gauss(freq_minutes, freq_minutes * 0.2)
            current_time += timedelta(minutes=max(1, jump))

            # Snap to active hours
            if current_time.hour not in active_hours:
                # shift time to next active hour
                while current_time.hour not in active_hours:
                    current_time += timedelta(hours=1)

            amt = max(1.0, random.gauss(amount_mean, amount_std))
            status = "FAILED" if random.random() < failure_prob else "SUCCESS"

            transactions.append(
                {
                    "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
                    "entity_id": entity_id,
                    "amount": round(amt, 2),
                    "timestamp": current_time.timestamp(),
                    "status": status,
                    "persona": persona,  # Keeping persona for label/debugging
                }
            )

        dataset.append(
            {"entity_id": entity_id, "persona": persona, "transactions": transactions}
        )

    os.makedirs("data/synthetic", exist_ok=True)
    with open("data/synthetic/behavioral_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2)

    print(
        f"Generated {num_entities} synthetic entities in data/synthetic/behavioral_dataset.json"
    )


if __name__ == "__main__":
    generate_synthetic_behavioral_data(1000)
