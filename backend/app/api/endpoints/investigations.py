from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.transactions import Transaction, RiskScore, Investigation
from app.agents.investigator import AIInvestigator
from pydantic import BaseModel

router = APIRouter()
investigator = AIInvestigator()

class InvestigationResponse(BaseModel):
    id: str
    transaction_id: str
    summary: str
    evidence: list
    suspicious_relationships: list
    recommended_action: str
    analyst_questions: list
    confidence: str
    model_used: str

@router.post("/{transaction_id}/run", response_model=InvestigationResponse)
async def run_investigation(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Runs an AI investigation for a given transaction."""
    # 1. Fetch transaction and risk score
    res = await db.execute(select(Transaction).filter_by(id=transaction_id))
    tx = res.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    rs_res = await db.execute(select(RiskScore).filter_by(transaction_id=transaction_id))
    risk = rs_res.scalar_one_or_none()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk score not found for transaction")
        
    # 2. Extract context
    tx_dict = {
        "id": tx.id,
        "amount": tx.amount,
        "customer_id": tx.customer_id
    }
    reasons = risk.risk_reasons or []
    
    # 3. Run investigator
    inv_data = await investigator.investigate_transaction(
        tx=tx_dict,
        risk_score=risk.risk_score,
        reasons=reasons,
        behavior_profile={}, # In a full fetch, we could load from DB
        graph_connections={}
    )
    
    # 4. Check if investigation already exists and update, or create new
    inv_res = await db.execute(select(Investigation).filter_by(transaction_id=transaction_id))
    inv = inv_res.scalar_one_or_none()
    
    if not inv:
        inv = Investigation(transaction_id=transaction_id)
        db.add(inv)
        
    inv.summary = inv_data["summary"]
    inv.evidence = inv_data["evidence"]
    inv.suspicious_relationships = inv_data["suspicious_relationships"]
    inv.recommended_action = inv_data["recommended_action"]
    inv.analyst_questions = inv_data["analyst_questions"]
    inv.confidence = inv_data["confidence"]
    inv.model_used = inv_data["model_used"]
    inv.generated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(inv)
    
    return InvestigationResponse(
        id=inv.id,
        transaction_id=inv.transaction_id,
        summary=inv.summary or "",
        evidence=inv.evidence or [],
        suspicious_relationships=inv.suspicious_relationships or [],
        recommended_action=inv.recommended_action or "",
        analyst_questions=inv.analyst_questions or [],
        confidence=inv.confidence or "",
        model_used=inv.model_used or ""
    )

@router.get("/{transaction_id}", response_model=InvestigationResponse)
async def get_investigation(transaction_id: str, db: AsyncSession = Depends(get_db)):
    inv_res = await db.execute(select(Investigation).filter_by(transaction_id=transaction_id))
    inv = inv_res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    return InvestigationResponse(
        id=inv.id,
        transaction_id=inv.transaction_id,
        summary=inv.summary or "",
        evidence=inv.evidence or [],
        suspicious_relationships=inv.suspicious_relationships or [],
        recommended_action=inv.recommended_action or "",
        analyst_questions=inv.analyst_questions or [],
        confidence=inv.confidence or "",
        model_used=inv.model_used or ""
    )
