"""
Shared dependencies for the application
"""

from typing import AsyncGenerator
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.embedding import EmbeddingService, get_embedding_service
from app.repository import LegalTextRepository
from app.config import get_settings


async def get_query_token(x_token: str = Header(None)):
    """
    Validate the X-Token header
    This is a simple example - in production, use proper authentication
    """
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")
    return x_token


async def get_token_header(x_token: str = Header(...)):
    """
    Require and validate the X-Token header
    """
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")
    return x_token


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    """
    async for session in get_async_session():
        yield session


async def get_legal_text_repository(
    db: AsyncSession = Depends(get_db),
) -> LegalTextRepository:
    """
    Dependency to get legal text repository
    """
    return LegalTextRepository(db)


async def get_embedding_service_dependency() -> EmbeddingService:
    """
    Dependency to get embedding service
    """
    settings = get_settings()
    return get_embedding_service(settings)
