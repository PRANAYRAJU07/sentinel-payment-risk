from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.transactions import AuditLog

router = APIRouter()

@router.get("/")
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=500),
    offset: int = Query(0)
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()
    
    output = []
    for log in logs:
        output.append({
            "id": log.id,
            "transaction_id": log.transaction_id,
            "event_id": log.event_id,
            "action": log.action,
            "actor": log.actor,
            "details": log.details,
            "created_at": log.created_at
        })
        
    return {"data": output}
