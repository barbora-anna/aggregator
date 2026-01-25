"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import database
from app.db.database import manage_db_engine
from app.routers import offers, products
from app.tasks.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    async with manage_db_engine() as engine:
        database.engine = engine
        start_scheduler()
        yield
        stop_scheduler()


app = FastAPI(title="Product Aggregator", lifespan=lifespan)

app.include_router(products.router)
app.include_router(offers.router)
