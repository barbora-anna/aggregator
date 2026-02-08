"""Offers read-only endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Offer as OfferModel, Product as ProductModel
from app.schemas import Offer

log = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["offers"])


@router.get("/{product_id}/offers", response_model=list[Offer])
async def get_product_offers(product_id: UUID, session: AsyncSession = Depends(get_session)):
    """Get cached offers for a product."""
    log.info("Fetching offers for product: id=%s", product_id)

    product = await session.get(ProductModel, product_id)
    if not product:
        log.warning("Product not found for offers request: id=%s", product_id)
        raise HTTPException(status_code=404, detail="Product not found")

    log.debug("Product found: name=%s, external_id=%s", product.name, product.external_id)

    result = await session.execute(
        select(OfferModel).where(OfferModel.product_id == product_id)
    )
    offers = result.scalars().all()

    in_stock_count = sum(1 for o in offers if o.items_in_stock > 0)
    log.info(
        "Retrieved %d offers for product %s (name=%s): %d in stock, %d out of stock",
        len(offers),
        product_id,
        product.name,
        in_stock_count,
        len(offers) - in_stock_count,
    )

    return offers
