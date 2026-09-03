import os

with open("docs/architecture.md", "a") as f:
    f.write("\n\n### Phase 8: Behavioral Anomaly Engine\n")
    f.write("Introduced the persistent behavioral profile storage (`BehaviorProfile`) tracking metrics like average amounts, standard deviations, typical active hours, daily transaction velocities, and historic failure rates. This layer operates completely decoupled from the ML models to detect behavioral drift without fabricating PII-linked dependencies in the Kaggle dataset.\n")

print("Docs updated")
