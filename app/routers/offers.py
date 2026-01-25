"""Offers read-only endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Offer as OfferModel, Product as ProductModel
from app.schemas import Offer
from app.services.offers_client import OffersClient
from app.services.sync_service import OfferReconciler

log = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["offers"])


@router.get("/{product_id}/offers", response_model=list[Offer])
async def get_product_offers(product_id: UUID, session: AsyncSession = Depends(get_session)):
    """Get offers for a product. Best-effort refresh from external service."""
    product = await session.get(ProductModel, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Best-effort on-demand refresh
    if product.external_id:
        try:
            client = OffersClient()
            external_offers = await client.get_offers(product.external_id)
            reconciler = OfferReconciler(session, product_id)
            await reconciler.reconcile(external_offers)
            await session.commit()
        except Exception:
            log.exception("On-demand refresh failed for product %s, using cached data", product_id)
            await session.rollback()

    # Always return from DB (source of truth)
    result = await session.execute(
        select(OfferModel).where(OfferModel.product_id == product_id)
    )
    return result.scalars().all()
