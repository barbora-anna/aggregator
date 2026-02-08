"""Background task scheduler."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.config import settings
from app.db.database import db_session
from app.db.models import Product as ProductModel
from app.services.offers_client import OffersClient
from app.services.sync_service import OfferReconciler

log = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def sync_all_offers() -> None:
    """Sync offers for all registered products."""
    log.info("Starting background offer sync")

    # Fetch all registered products
    try:
        async with db_session() as session:
            result = await session.execute(
                select(ProductModel).where(ProductModel.external_id.isnot(None))
            )
            products = result.scalars().all()
    except Exception:
        log.exception("Database connection failed, skipping sync cycle")
        return

    if not products:
        log.info("No registered products to sync")
        return

    log.info("Syncing offers for %d products", len(products))
    client = OffersClient.get()

    for product in products:
        try:
            async with db_session() as session:
                external_offers = await client.get_offers(product.external_id)
                reconciler = OfferReconciler(session, product.id)
                await reconciler.reconcile(external_offers)
            log.info("Synced offers for product %s", product.id)
        except Exception:
            log.exception("Failed to sync offers for product %s", product.id)

    log.info("Background offer sync complete")


def _parse_cron_expression(expr: str) -> CronTrigger:
    """Parse 6-field cron expression (sec min hour day month dow)."""
    parts = expr.split()
    if len(parts) != 6:
        raise ValueError(f"Expected 6-field cron expression, got {len(parts)} fields")
    return CronTrigger(
        second=parts[0],
        minute=parts[1],
        hour=parts[2],
        day=parts[3],
        month=parts[4],
        day_of_week=parts[5],
    )


def start_scheduler() -> None:
    """Start the background scheduler."""
    trigger = _parse_cron_expression(settings.sync_schedule)
    scheduler.add_job(
        sync_all_offers,
        trigger,
        id="sync_offers",
        replace_existing=True,
    )
    scheduler.start()
    log.info("Scheduler started (schedule: %s)", settings.sync_schedule)


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped")
