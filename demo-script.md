# Sentinel 5-Minute Demo Script

## Preparation
1. Ensure the system is running using `docker compose up --build`.
2. Wait for the logs to say `Database seeded successfully` and `Uvicorn running on http://0.0.0.0:8000`.
3. Open a browser to `http://localhost:3000`.

## 1. The Dashboard (0:00 - 1:00)
**Action:** Show the main Dashboard page.
**Script:**
> "Welcome to Sentinel, our Payment Risk Control Tower. This dashboard is what our fraud analysts see. At the top, we see the real-time processing metrics. Below is the Live Risk Stream. Sentinel is actively scoring incoming transactions, evaluating their ML risk, behavioral deviation, and graph network signals."

## 2. The Fraud Lab (1:00 - 2:30)
**Action:** Click the "Fraud Lab" tab on the left.
**Script:**
> "Sentinel has a built-in simulator called Fraud Lab. This lets us test how the system reacts to zero-day attacks. I'm going to launch a 'Coordinated Fraud Ring' attack. This simulates 5 synchronized accounts suddenly making high-value purchases using the same underlying device and IP."

**Action:** Click "LAUNCH ATTACK" under Coordinated Fraud Ring. Return to the Dashboard.
**Script:**
> "As you can see on the Dashboard, those new transactions immediately show up. And look at the decisions—they are all flagged as `HOLD`. The system caught them instantly."

## 3. AI Investigation (2:30 - 3:30)
**Action:** Click on one of the new `HOLD` transactions in the stream.
**Script:**
> "Let's dive into one of these flagged transactions to see exactly why it was held. This is the Transaction Detail view. On the right, we have the AI Investigator panel. Sentinel automatically investigates the transaction context. If we scroll down to Evidence & Signals, we see exactly why it was flagged: high ML risk, huge deviation from the customer's behavioral baseline, and importantly, the Graph Engine detected a high-risk cluster."

## 4. Fraud Network (3:30 - 5:00)
**Action:** Copy the `customer_id` from the details page, click "Fraud Network" on the left, paste it in, and click "Load Network".
**Script:**
> "To prove the Graph Engine works, let's visualize this. I've entered the Customer ID. The ReactFlow visualization shows the customer, their transactions, and their linked devices. If you look closely, you can see this device is shared across multiple other customers who were part of the attack. Sentinel built this graph in real-time in memory using NetworkX, without needing an expensive database query."

> "This gives our analysts deterministic proof. They can confidently return to the transaction, hit 'CONFIRM FRAUD', and the system updates the audit log automatically."
