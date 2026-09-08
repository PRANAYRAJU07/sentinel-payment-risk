from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.transactions import Transaction

router = APIRouter()

@router.get("/")
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=500),
    offset: int = Query(0)
):
    """Fetch paginated list of transactions, optionally with risk score attached."""
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.risk_score))
        .order_by(Transaction.time.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    transactions = res.scalars().all()
    
    output = []
    for t in transactions:
        t_dict = {
            "id": t.id,
            "amount": t.amount,
            "currency": t.currency,
            "status": t.status,
            "time": t.time,
            "customer_id": t.customer_id,
            "merchant_id": t.merchant_id
        }
        if t.risk_score:
            t_dict["risk_score"] = t.risk_score.risk_score
            t_dict["decision"] = t.risk_score.decision
        output.append(t_dict)
        
    return {"data": output}

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch single transaction detail with all related risk/investigation info."""
    stmt = (
        select(Transaction)
        .options(
            selectinload(Transaction.risk_score),
            selectinload(Transaction.investigation),
            selectinload(Transaction.audit_logs)
        )
        .filter_by(id=transaction_id)
    )
    res = await db.execute(stmt)
    t = res.scalar_one_or_none()
    
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    return {
        "id": t.id,
        "amount": t.amount,
        "currency": t.currency,
        "status": t.status,
        "time": t.time,
        "customer_id": t.customer_id,
        "merchant_id": t.merchant_id,
        "device_id": t.device_id,
        "ip_address": t.ip_address,
        "risk_score": {
            "score": t.risk_score.risk_score,
            "decision": t.risk_score.decision,
            "ml_score": t.risk_score.ml_score,
            "behavioral_score": t.risk_score.behavioral_score,
            "graph_score": t.risk_score.graph_score,
            "reasons": t.risk_score.risk_reasons
        } if t.risk_score else None,
        "investigation": {
            "summary": t.investigation.summary,
            "recommended_action": t.investigation.recommended_action
        } if t.investigation else None
    }
