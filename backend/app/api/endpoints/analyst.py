from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from pydantic import BaseModel

from app.core.database import get_db
from app.models.transactions import Transaction, AnalystReview, AuditLog

router = APIRouter()

class AnalystReviewRequest(BaseModel):
    transaction_id: str
    action: str # CONFIRM_FRAUD / MARK_FALSE_POSITIVE / RELEASE / KEEP_ON_HOLD / APPROVE
    reason: str
    notes: str = ""
    analyst_id: str = "demo_analyst"

class AnalystReviewResponse(BaseModel):
    id: str
    transaction_id: str
    action: str
    status: str = "success"

@router.post("/", response_model=AnalystReviewResponse)
async def submit_review(req: AnalystReviewRequest, db: AsyncSession = Depends(get_db)):
    # 1. Fetch transaction
    res = await db.execute(select(Transaction).filter_by(id=req.transaction_id))
    tx = res.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    # 2. Add Review
    review = AnalystReview(
        transaction_id=tx.id,
        analyst_id=req.analyst_id,
        action=req.action,
        reason=req.reason,
        notes=req.notes
    )
    db.add(review)
    
    # 3. Add Audit Log
    audit = AuditLog(
        transaction_id=tx.id,
        action=f"ANALYST_{req.action}",
        actor=req.analyst_id,
        details={"reason": req.reason, "notes": req.notes}
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(review)
    
    return AnalystReviewResponse(
        id=review.id,
        transaction_id=tx.id,
        action=review.action
    )
