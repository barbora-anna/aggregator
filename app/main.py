"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db import database
from app.db.database import get_session, manage_db_engine
from app.logging_setup import init_logging
from app.routers import offers, products
from app.services.offers_client import OffersClient
from app.tasks.scheduler import start_scheduler, stop_scheduler

init_logging()
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application lifecycle."""
    async with manage_db_engine() as engine:
        database.engine = engine
        start_scheduler()
        yield
        stop_scheduler()
        await OffersClient.close()


app = FastAPI(title="Product Aggregator", lifespan=lifespan)

app.include_router(products.router)
app.include_router(offers.router)


@app.get("/health")
async def health_check():
    """Health check endpoint - verifies DB connectivity."""
    try:
        async for session in get_session():
            await session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        log.error("Health check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)},
        )
