"""Offer synchronization logic."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Offer as OfferModel
from app.schemas import ExternalOffer

log = logging.getLogger(__name__)


class OfferReconciler:
    """Reconciles external offers with database state."""

    def __init__(self, session: AsyncSession, product_id: UUID) -> None:
        self.session = session
        self.product_id = product_id
        self.db_offers: dict[UUID, OfferModel] = {}

    async def load_existing(self) -> None:
        """Load current offers from database."""
        result = await self.session.execute(
            select(OfferModel).where(OfferModel.product_id == self.product_id)
        )
        self.db_offers = {o.id: o for o in result.scalars().all()}

    def upsert(self, external: ExternalOffer) -> None:
        """Insert or update a single offer."""
        if external.id in self.db_offers:
            db_offer = self.db_offers[external.id]
            if db_offer.price != external.price or db_offer.items_in_stock != external.items_in_stock:
                db_offer.price = external.price
                db_offer.items_in_stock = external.items_in_stock
        else:
            self.session.add(OfferModel(
                id=external.id,
                product_id=self.product_id,
                price=external.price,
                items_in_stock=external.items_in_stock,
            ))

    async def remove_stale(self, current_ids: set[UUID]) -> None:
        """Remove offers no longer present externally."""
        for offer_id, db_offer in self.db_offers.items():
            if offer_id not in current_ids:
                await self.session.delete(db_offer)

    async def reconcile(self, external_offers: list[ExternalOffer]) -> None:
        """Full reconciliation: load, upsert, remove stale."""
        await self.load_existing()

        external_ids = set()
        for ext in external_offers:
            external_ids.add(ext.id)
            self.upsert(ext)

        await self.remove_stale(external_ids)
