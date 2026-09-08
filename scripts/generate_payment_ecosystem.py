import os
import json
import uuid
import random
from datetime import datetime, timedelta, timezone

def generate_ecosystem(num_customers=5000, num_merchants=200, num_devices=3000, num_ips=4000, num_transactions=100000):
    print("Generating Sentinel Synthetic Ecosystem...")
    
    customers = []
    merchants = []
    devices = []
    ips = []
    transactions = []
    
    # Generate Merchants
    for _ in range(num_merchants):
        merchants.append({
            "id": f"MERCH_{uuid.uuid4().hex[:8]}",
            "name": f"Merchant_{uuid.uuid4().hex[:4]}",
            "category": random.choice(["RETAIL", "DIGITAL", "TRAVEL", "GAMING", "FOOD"]),
            "risk_level": "LOW"
        })
        
    # Generate Devices
    for _ in range(num_devices):
        devices.append({
            "id": f"DEV_{uuid.uuid4().hex[:8]}",
            "type": random.choice(["mobile", "desktop", "tablet"]),
            "os": random.choice(["iOS", "Android", "Windows", "macOS"])
        })
        
    # Generate IPs
    for _ in range(num_ips):
        ips.append({
            "id": f"IP_{uuid.uuid4().hex[:8]}",
            "country": random.choice(["US", "IN", "UK", "SG", "AU"]),
            "is_vpn": random.random() < 0.05
        })
        
    # Generate Customers
    for _ in range(num_customers):
        customers.append({
            "id": f"CUST_{uuid.uuid4().hex[:8]}",
            "email": f"user_{uuid.uuid4().hex[:6]}@example.com",
            "account_age_days": random.randint(1, 1000)
        })
        
    # Generate Transactions
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=90)
    
    time_increment = (now - start_time).total_seconds() / num_transactions
    current_time = start_time
    
    for i in range(num_transactions):
        c = random.choice(customers)
        m = random.choice(merchants)
        d = random.choice(devices)
        ip = random.choice(ips)
        
        current_time += timedelta(seconds=time_increment * random.uniform(0.5, 1.5))
        
        transactions.append({
            "id": f"TX_{uuid.uuid4().hex[:12]}",
            "customer_id": c["id"],
            "merchant_id": m["id"],
            "device_id": d["id"],
            "ip_address": ip["id"],
            "amount": round(random.lognormvariate(4.0, 1.0), 2),
            "time": current_time.timestamp(),
            "status": "SUCCESS" if random.random() > 0.05 else "FAILED"
        })
        
        if i % 10000 == 0:
            print(f"Generated {i} transactions...")
            
    # Inject Fraud Scenarios
    # Scenario: Coordinated Fraud Ring (Shared Device/IP across many customers)
    print("Injecting Fraud Rings...")
    fraud_device = devices[0]["id"]
    fraud_ip = ips[0]["id"]
    fraud_merchant = merchants[0]["id"]
    
    for i in range(50):
        c = customers[i]
        transactions.append({
            "id": f"TX_FRAUD_{uuid.uuid4().hex[:8]}",
            "customer_id": c["id"],
            "merchant_id": fraud_merchant,
            "device_id": fraud_device,
            "ip_address": fraud_ip,
            "amount": 4999.99,
            "time": (now - timedelta(hours=i)).timestamp(),
            "status": "SUCCESS"
        })
        
    dataset = {
        "customers": customers,
        "merchants": merchants,
        "devices": devices,
        "ips": ips,
        "transactions": transactions
    }
    
    os.makedirs("data/synthetic", exist_ok=True)
    with open("data/synthetic/ecosystem.json", "w") as f:
        json.dump(dataset, f)
        
    print(f"Ecosystem generated and saved to data/synthetic/ecosystem.json")

if __name__ == "__main__":
    generate_ecosystem()
