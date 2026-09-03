from collections import Counter
from datetime import datetime, timezone

import numpy as np

from app.behavior.schemas import BehaviorProfileData, HistoricalTransaction

MIN_PROFILE_TRANSACTIONS = 20


def build_profile(transactions: list[HistoricalTransaction]) -> BehaviorProfileData:
    if len(transactions) < MIN_PROFILE_TRANSACTIONS:
        return BehaviorProfileData()

    amounts = [t.amount for t in transactions if t.status == "SUCCESS"]
    if not amounts:
        amounts = [0.0]

    amount_mean = float(np.mean(amounts))
    amount_std = float(np.std(amounts))
    amount_median = float(np.median(amounts))
    amount_min = float(np.min(amounts))
    amount_max = float(np.max(amounts))

    hours = []
    days = set()
    failures = 0

    last_ts = 0.0

    for t in transactions:
        dt = datetime.fromtimestamp(t.timestamp, tz=timezone.utc)
        hours.append(dt.hour)
        days.add(dt.date())
        if t.status != "SUCCESS":
            failures += 1
        last_ts = max(last_ts, t.timestamp)

    # Typical hours: hours containing at least 5% of transactions
    hour_counts = Counter(hours)
    threshold = len(transactions) * 0.05
    typical_hours = [h for h, c in hour_counts.items() if c >= threshold]

    days_span = len(days) if len(days) > 0 else 1
    avg_daily = len(transactions) / days_span
    fail_rate = failures / len(transactions)

    profile = BehaviorProfileData()
    profile.amount.mean = amount_mean
    profile.amount.std = amount_std
    profile.amount.median = amount_median
    profile.amount.min = amount_min
    profile.amount.max = amount_max

    profile.time.typical_hours = typical_hours
    profile.velocity.avg_daily_count = avg_daily
    profile.failure.failure_rate = fail_rate
    profile.last_transaction_timestamp = last_ts

    return profile
