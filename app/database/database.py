from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import sys
from ..core.config import settings
from ..core.logging_config import setup_logging
from typing import AsyncGenerator, Dict
import asyncio

setup_logging("fastapi_app", settings.LOG_FILE_PATH) 

DATABASE_URL = settings.DATABASE_URL_CON

DATABASE_GENERAL_URL = settings.DATABASE_GENERAL_URL

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

engineGeneral = create_async_engine(DATABASE_GENERAL_URL, echo=False)
GeneralSessionLocal = sessionmaker(
    engineGeneral,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
