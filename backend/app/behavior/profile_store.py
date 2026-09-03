
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.behavior.schemas import BehaviorProfileData
from app.models.entities import BehaviorProfile


class BehaviorProfileStore:
    def __init__(self):
        # We can wrap a cache interface here in the future
        pass

    async def get_profile(self, db: AsyncSession, entity_id: str) -> dict:
        if not db:
            return None
        res = await db.execute(select(BehaviorProfile).filter_by(entity_id=entity_id))
        return res.scalar_one_or_none()

    async def save_profile(
        self,
        db: AsyncSession,
        entity_id: str,
        profile_data: BehaviorProfileData,
        tx_count: int,
        status: str,
        version: str,
    ):
        if not db:
            return

        stmt = insert(BehaviorProfile).values(
            entity_id=entity_id,
            profile_version=version,
            profile_status=status,
            profile_data=profile_data.model_dump(),
            transaction_count=tx_count,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["entity_id"],
            set_={
                "profile_version": stmt.excluded.profile_version,
                "profile_status": stmt.excluded.profile_status,
                "profile_data": stmt.excluded.profile_data,
                "transaction_count": stmt.excluded.transaction_count,
            },
        )
        await db.execute(stmt)
        await db.commit()
