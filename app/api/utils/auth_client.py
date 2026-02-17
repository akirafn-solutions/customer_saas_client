import logging
from typing import Dict

from fastapi import logger, Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database.database import get_async_session
from ...models.client import (Client)
from ...schemas.client import ClientResponse, ClientStatusEnum

logger = logging.getLogger(__name__)

# --- Utils ---
def client_base_query():
    return (
        select(Client)
        .options(
            selectinload(Client.audit_logs),
            selectinload(Client.credentials),
        )
    )

async def find_by_site_key(site_key: str, db: AsyncSession = Depends(get_async_session)) -> Dict:
    try:
        active_val = ClientStatusEnum.ACTIVE.value
        trial_val = ClientStatusEnum.TRIAL.value

        stmt = (
            client_base_query()
            .where(and_(Client.site_key == site_key, Client.status.in_([active_val, trial_val])))
            .limit(1)
        )
        result = await db.execute(stmt)
        clients = result.unique().scalars().first()

        if not clients:
            return None
        
        return ClientResponse.model_validate(clients)
    except Exception as e:
        logger.error(f"Error in find_by_site_key: {e}")
        return []