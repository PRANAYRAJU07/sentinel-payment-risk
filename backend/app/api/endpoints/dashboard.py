from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db
from app.models.transactions import Transaction, RiskScore, FraudCluster

router = APIRouter()

@router.get("/metrics")
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """Returns top-level dashboard metrics based on real database state."""
    
    # Total Transactions
    res_tx = await db.execute(select(func.count(Transaction.id)))
    total_tx = res_tx.scalar_one()
    
    # Decisions
    res_decisions = await db.execute(
        select(RiskScore.decision, func.count(RiskScore.id))
        .group_by(RiskScore.decision)
    )
    decisions = {row[0]: row[1] for row in res_decisions.all()}
    
    # Average Risk
    res_risk = await db.execute(select(func.avg(RiskScore.risk_score)))
    avg_risk = res_risk.scalar_one() or 0.0
    
    # Active Fraud Clusters
    res_clusters = await db.execute(select(func.count(FraudCluster.id)))
    total_clusters = res_clusters.scalar_one()
    
    return {
        "transactions_total": total_tx,
        "approved": decisions.get("APPROVE", 0),
        "review": decisions.get("REVIEW", 0),
        "held": decisions.get("HOLD", 0),
        "average_risk": round(avg_risk, 1),
        "active_clusters": total_clusters
    }
