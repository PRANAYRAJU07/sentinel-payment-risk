from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.transactions import ModelVersion

router = APIRouter()

@router.get("/")
async def list_models(db: AsyncSession = Depends(get_db)):
    stmt = select(ModelVersion).order_by(ModelVersion.created_at.desc())
    res = await db.execute(stmt)
    models = res.scalars().all()
    
    output = []
    for m in models:
        output.append({
            "version": m.version,
            "model_type": m.model_type,
            "is_active": m.is_active,
            "pr_auc": m.pr_auc,
            "roc_auc": m.roc_auc,
            "precision": m.precision,
            "recall": m.recall,
            "f1_score": m.f1_score,
            "trained_at": m.trained_at
        })
    return {"data": output}
