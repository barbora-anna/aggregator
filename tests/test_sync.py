"""Tests for OfferReconciler sync logic."""

from uuid import uuid4

from app.db.models import Offer, Product
from app.schemas import ExternalOffer
from app.services.sync_service import OfferReconciler


async def _make_product(session) -> Product:
    product = Product(name="Test Product", external_id=uuid4())
    session.add(product)
    await session.flush()
    return product


async def test_inserts_new_offers(session):
    product = await _make_product(session)
    external = [
        ExternalOffer(id=uuid4(), price=1000, items_in_stock=5),
        ExternalOffer(id=uuid4(), price=2000, items_in_stock=3),
    ]

    reconciler = OfferReconciler(session, product.id)
    await reconciler.reconcile(external)
    await session.flush()

    offers = (await session.execute(
        Offer.__table__.select().where(Offer.product_id == product.id)
    )).fetchall()
    assert len(offers) == 2


async def test_updates_existing_offer(session):
    product = await _make_product(session)
    offer_id = uuid4()

    session.add(Offer(id=offer_id, product_id=product.id, price=1000, items_in_stock=5))
    await session.flush()

    external = [ExternalOffer(id=offer_id, price=1500, items_in_stock=2)]
    reconciler = OfferReconciler(session, product.id)
    await reconciler.reconcile(external)
    await session.flush()

    db_offer = await session.get(Offer, offer_id)
    assert db_offer.price == 1500
    assert db_offer.items_in_stock == 2


async def test_removes_stale_offers(session):
    product = await _make_product(session)
    stale_id = uuid4()
    surviving_id = uuid4()

    session.add(Offer(id=stale_id, product_id=product.id, price=1000, items_in_stock=5))
    session.add(Offer(id=surviving_id, product_id=product.id, price=2000, items_in_stock=3))
    await session.flush()

    # Only surviving_id is in the external response
    external = [ExternalOffer(id=surviving_id, price=2000, items_in_stock=3)]
    reconciler = OfferReconciler(session, product.id)
    await reconciler.reconcile(external)
    await session.flush()

    assert await session.get(Offer, stale_id) is None
    assert await session.get(Offer, surviving_id) is not None


async def test_full_reconcile(session):
    """Mix of new, updated, and stale offers in one cycle."""
    product = await _make_product(session)
    existing_id = uuid4()
    stale_id = uuid4()
    new_id = uuid4()

    session.add(Offer(id=existing_id, product_id=product.id, price=1000, items_in_stock=5))
    session.add(Offer(id=stale_id, product_id=product.id, price=3000, items_in_stock=1))
    await session.flush()

    external = [
        ExternalOffer(id=existing_id, price=1200, items_in_stock=4),  # updated
        ExternalOffer(id=new_id, price=5000, items_in_stock=10),       # new
        # stale_id absent — should be removed
    ]

    reconciler = OfferReconciler(session, product.id)
    await reconciler.reconcile(external)
    await session.flush()

    updated = await session.get(Offer, existing_id)
    assert updated.price == 1200
    assert updated.items_in_stock == 4

    assert await session.get(Offer, new_id) is not None
    assert await session.get(Offer, stale_id) is None
