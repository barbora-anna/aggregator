from uuid import uuid4

from app.db.models import Offer, Product


async def test_get_offers(client, session):
    product = Product(name="Widget")
    session.add(product)
    await session.flush()

    session.add(Offer(id=uuid4(), product_id=product.id, price=1000, items_in_stock=5))
    session.add(Offer(id=uuid4(), product_id=product.id, price=2000, items_in_stock=0))
    await session.commit()

    response = await client.get(f"/products/{product.id}/offers")
    assert response.status_code == 200
    offers = response.json()
    assert len(offers) == 2
    prices = {o["price"] for o in offers}
    assert prices == {1000, 2000}


async def test_get_offers_empty(client, session):
    product = Product(name="loner")
    session.add(product)
    await session.commit()

    response = await client.get(f"/products/{product.id}/offers")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_offers_product_not_found(client):
    response = await client.get(f"/products/{uuid4()}/offers")
    assert response.status_code == 404
