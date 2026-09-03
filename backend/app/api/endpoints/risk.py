"""
Sentinel Risk Engine — API Endpoints
Real-time risk scoring and trace retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.risk.risk_response import TransactionInput, RiskResponse
from app.risk.risk_engine import RiskEngineOrchestrator
from app.models.transactions import RiskScore

router = APIRouter()
risk_engine = RiskEngineOrchestrator()

@router.post("/score", response_model=RiskResponse)
async def evaluate_risk(transaction: TransactionInput, db: AsyncSession = Depends(get_db)):
    """
    Evaluates risk for a given transaction.
    """
    try:
        response = await risk_engine.evaluate(transaction, db)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{transaction_id}", response_model=RiskResponse)
async def get_risk_evaluation(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the latest risk evaluation for a transaction.
    """
    res = await db.execute(select(RiskScore).filter(RiskScore.transaction_id == transaction_id))
    score = res.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Risk score not found for this transaction.")
        
    return RiskResponse(
        transaction_id=score.transaction_id,
        ml_risk_score=score.ml_score or 0.0,
        behavioral_risk_score=score.behavioral_score or 0.0,
        rule_risk_score=0.0, # Not explicitly separated in DB schema yet except through reasons
        graph_risk_score=score.graph_score or 0.0,
        final_risk_score=score.risk_score,
        risk_level="UNKNOWN", # Derived or stored in details
        decision=score.decision,
        reasons=score.risk_reasons or [],
        model_version=score.model_version or "unknown",
        policy_version="unknown",
        signal_availability={}
    )

@router.get("/{transaction_id}/trace")
async def get_risk_trace(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the full risk trace.
    For now, it reconstructs it from the risk score and features snapshot.
    """
    res = await db.execute(select(RiskScore).filter(RiskScore.transaction_id == transaction_id))
    score = res.scalar_one_or_none()
    if not score:
        raise HTTPException(status_code=404, detail="Risk score not found.")
        
    return {
        "transaction_id": score.transaction_id,
        "input_features": score.features_snapshot,
        "ml_score": score.ml_score,
        "behavioral_score": score.behavioral_score,
        "graph_score": score.graph_score,
        "final_score": score.risk_score,
        "decision": score.decision,
        "reasons": score.risk_reasons,
        "evaluated_at": score.scored_at
    }
