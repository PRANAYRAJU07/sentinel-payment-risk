import asyncio
import uuid
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.transactions import Transaction
from app.api.endpoints.risk import risk_score_endpoint
from app.risk.risk_response import RiskRequest

router = APIRouter()

class SimulationRequest(BaseModel):
    attack_type: str  # ACCOUNT_TAKEOVER, VELOCITY_BURST, MULTIPLE_SIGNALS
    attack_size: int = 5

async def run_attack_simulation(attack_type: str, attack_size: int, db: AsyncSession):
    """
    Background task that generates transactions matching a fraud pattern
    and streams them through the live risk engine.
    """
    # Create fake entities to simulate an attack
    fraud_device = f"dev_sim_{uuid.uuid4().hex[:8]}"
    fraud_ip = f"ip_sim_{uuid.uuid4().hex[:8]}"
    
    for i in range(attack_size):
        # We need to create a transaction request and pass it to the risk engine
        cust_id = f"cust_sim_{uuid.uuid4().hex[:8]}" if attack_type == "ACCOUNT_TAKEOVER" else "cust_sim_target"
        
        tx_req = RiskRequest(
            id=str(uuid.uuid4()),
            amount=5000.0 if attack_type == "MULTIPLE_SIGNALS" else 100.0 + i,
            time=datetime.now(timezone.utc).timestamp(),
            customer_id=cust_id,
            merchant_id="merch_target",
            device_id=fraud_device,
            ip_address=fraud_ip,
            velocity_1h=attack_size if attack_type == "VELOCITY_BURST" else 1,
            failures_24h=5 if attack_type == "ACCOUNT_TAKEOVER" else 0
        )
        
        # Directly call the risk engine endpoint logic
        # (This will save to DB, trigger graph, behavior, etc.)
        try:
            await risk_score_endpoint(tx_req, db)
        except Exception as e:
            print(f"Simulation Error: {e}")
            
        await asyncio.sleep(0.5) # Simulate slight streaming delay

@router.post("/run")
async def launch_simulation(req: SimulationRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Launches a fraud attack simulation in the background."""
    background_tasks.add_task(run_attack_simulation, req.attack_type, req.attack_size, db)
    return {"status": "started", "message": f"Launched {req.attack_type} simulation with {req.attack_size} transactions"}
