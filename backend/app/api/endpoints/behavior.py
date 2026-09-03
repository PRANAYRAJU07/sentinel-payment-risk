from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.behavior.schemas import ProfileRequest, ProfileResponse, AnomalyResult, HistoricalTransaction
from app.behavior.behavioral_service import BehavioralService
from app.behavior.profile_store import BehaviorProfileStore
from app.risk.risk_response import TransactionInput
from datetime import datetime, timezone
import json

router = APIRouter()
service = BehavioralService()
store = BehaviorProfileStore()

@router.post("/profile", response_model=ProfileResponse)
async def build_or_update_profile(req: ProfileRequest, db: AsyncSession = Depends(get_db)):
    """Builds a new profile or overwrites the existing one with the provided historical transactions."""
    status_str, count = await service.build_and_save_profile(db, req.entity_id, req.transactions)
    return ProfileResponse(
        entity_id=req.entity_id,
        profile_status=status_str,
        transaction_count=count,
        profile_version=service.version
    )

@router.get("/profile/{entity_id}")
async def get_profile(entity_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves current behavioral profile."""
    profile_obj = await store.get_profile(db, entity_id)
    if not profile_obj:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    return {
        "entity_id": profile_obj.entity_id,
        "profile_version": profile_obj.profile_version,
        "profile_status": profile_obj.profile_status,
        "transaction_count": profile_obj.transaction_count,
        "profile_data": profile_obj.profile_data,
        "created_at": profile_obj.created_at,
        "updated_at": profile_obj.updated_at
    }

@router.post("/analyze")
async def analyze_transaction(tx: TransactionInput, db: AsyncSession = Depends(get_db)):
    """Evaluates a transaction against the behavioral engine independently."""
    res = await service.get_anomaly_result(tx, db)
    return {
        "behavioral_available": res.available,
        "behavioral_score": res.score,
        "reasons": res.reasons,
        "profile_version": service.version
    }
