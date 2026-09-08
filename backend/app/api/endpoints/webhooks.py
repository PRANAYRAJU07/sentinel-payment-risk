import os
import hmac
import hashlib
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
import json
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.transactions import PaymentEvent
# Future: From here we'll trigger Risk Evaluation asynchronously.

logger = logging.getLogger(__name__)
router = APIRouter()

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "demo_secret")

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Handles incoming Razorpay Test Mode webhooks.
    """
    payload = await request.body()
    
    # 1. Verify Signature
    if not x_razorpay_signature:
        logger.warning("Missing Razorpay signature")
        raise HTTPException(status_code=400, detail="Missing signature")
        
    expected_sig = hmac.new(
        bytes(RAZORPAY_WEBHOOK_SECRET, 'utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_sig, x_razorpay_signature):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    # 2. Parse Payload
    try:
        data = json.loads(payload.decode('utf-8'))
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    event_id = data.get("account_id", "") + "_" + data.get("event", "unknown")
    event_type = data.get("event")
    
    # We will use the Razorpay event id if provided in payload headers, otherwise build one
    # Razorpay usually sends x-razorpay-event-id header
    rzp_event_id = request.headers.get("x-razorpay-event-id", event_id)
    
    # 3. Idempotent Persistence
    stmt = insert(PaymentEvent).values(
        event_id=rzp_event_id,
        event_type=event_type,
        source="RAZORPAY",
        payload=data,
        processed=False
    ).on_conflict_do_nothing(index_elements=['event_id'])
    
    result = await db.execute(stmt)
    await db.commit()
    
    if result.rowcount == 0:
        logger.info(f"Duplicate webhook skipped: {rzp_event_id}")
        return {"status": "ok", "message": "Already processed"}
        
    logger.info(f"Persisted webhook {rzp_event_id} of type {event_type}")
    
    # Note: In a production system, this would drop a message on Kafka to process the risk.
    # For now we'll just ack the webhook to Razorpay.
    
    return {"status": "ok"}
