import asyncio
import json
import os
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.database import get_db_engine, Base
from app.models.entities import Customer, Merchant, Device, IpAddress
from app.models.transactions import Transaction

async def seed_database():
    print("Starting database seed process...")
    engine = get_db_engine()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("Database schema reset.")
        
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    dataset_path = "data/synthetic/ecosystem.json"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}. Please run generate_payment_ecosystem.py first.")
        return
        
    print("Loading dataset...")
    with open(dataset_path, "r") as f:
        data = json.load(f)
        
    async with AsyncSessionLocal() as db:
        print(f"Seeding {len(data['customers'])} customers...")
        for chunk in [data['customers'][i:i+1000] for i in range(0, len(data['customers']), 1000)]:
            db.add_all([Customer(id=c['id'], external_id=c['id'], email=c['email'], is_synthetic=True) for c in chunk])
        await db.commit()
        
        print(f"Seeding {len(data['merchants'])} merchants...")
        for chunk in [data['merchants'][i:i+1000] for i in range(0, len(data['merchants']), 1000)]:
            db.add_all([Merchant(id=m['id'], external_id=m['id'], name=m['name'], is_synthetic=True) for m in chunk])
        await db.commit()
        
        # We must also seed devices and IPs if they are foreign keys!
        print(f"Seeding {len(data.get('devices', []))} devices...")
        for chunk in [data['devices'][i:i+1000] for i in range(0, len(data['devices']), 1000)]:
            db.add_all([Device(id=d['id'], device_fingerprint=d['id'], is_synthetic=True) for d in chunk])
        await db.commit()
        
        print(f"Seeding {len(data.get('ips', []))} IPs...")
        for chunk in [data['ips'][i:i+1000] for i in range(0, len(data['ips']), 1000)]:
            db.add_all([IpAddress(id=ip['id'], ip_address=ip['id'], is_synthetic=True) for ip in chunk])
        await db.commit()
        
        # Note: In a real system we'd seed devices/IPs properly as entities, 
        # but for demo speed we'll rely on the transactions table for graph building
        print(f"Seeding {len(data['transactions'])} transactions...")
        for i in range(0, len(data['transactions']), 10000):
            chunk = data['transactions'][i:i+10000]
            txs = []
            for t in chunk:
                txs.append(Transaction(
                    id=t['id'],
                    customer_id=t['customer_id'],
                    merchant_id=t['merchant_id'],
                    device_id=t['device_id'],
                    ip_id=t['ip_address'],
                    amount=t['amount'],
                    transaction_at=datetime.fromtimestamp(t['time'], tz=timezone.utc),
                    status=t['status'],
                    is_synthetic=True
                ))
            db.add_all(txs)
            await db.commit()
            print(f"  Inserted {i+len(chunk)} transactions")
            
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_database())
