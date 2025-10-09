"""
Main FastAPI application module
"""

from fastapi import FastAPI

# from contextlib import asynccontextmanager
import logging

from app.routers import legal_texts

# from app.database import async_engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Lifespan context manager for startup and shutdown events
#     """
#     # Startup
#     logger.info("Starting Legal MCP API...")

#     # Create database tables
#     try:
#         async with async_engine.begin() as conn:
#             await conn.run_sync(Base.metadata.create_all)
#         logger.info("Database tables created successfully")
#     except Exception as e:
#         logger.error(f"Error creating database tables: {e}")

#     yield

#     # Shutdown
#     logger.info("Shutting down Legal MCP API...")
#     await async_engine.dispose()


app = FastAPI(
    title="Legal MCP API",
    description="A modern FastAPI application for importing and querying German legal texts using vector search",
    version="0.2.0",
    # lifespan=lifespan,
)

# Include routers
app.include_router(legal_texts.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.2.0"}
