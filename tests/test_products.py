"""Tests for product CRUD endpoints."""

from uuid import uuid4


async def test_create_product(client):
    response = await client.post("/products", json={"name": "something", "description": "a fine something"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "something"
    assert data["description"] == "a fine something"
    assert "id" in data


async def test_create_product_without_description(client):
    response = await client.post("/products", json={"name": "Gadget"})
    assert response.status_code == 201
    assert response.json()["description"] is None


async def test_list_products_empty(client):
    response = await client.get("/products")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_products(client):
    await client.post("/products", json={"name": "A"})
    await client.post("/products", json={"name": "B"})
    response = await client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_product(client):
    create = await client.post("/products", json={"name": "something"})
    product_id = create.json()["id"]

    response = await client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "something"


async def test_get_product_not_found(client):
    response = await client.get(f"/products/{uuid4()}")
    assert response.status_code == 404


async def test_update_product(client):
    create = await client.post("/products", json={"name": "old", "description": "something old"})
    product_id = create.json()["id"]

    response = await client.put(f"/products/{product_id}", json={"name": "new", "description": "something new"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "new"
    assert data["description"] == "something new"


async def test_update_product_clears_description(client):
    create = await client.post("/products", json={"name": "old", "description": "something old"})
    product_id = create.json()["id"]

    response = await client.put(f"/products/{product_id}", json={"name": "old"})
    assert response.status_code == 200
    assert response.json()["description"] is None


async def test_update_product_not_found(client):
    response = await client.put(f"/products/{uuid4()}", json={"name": "aaaaaa"})
    assert response.status_code == 404


async def test_delete_product(client):
    create = await client.post("/products", json={"name": "doomed"})
    product_id = create.json()["id"]

    response = await client.delete(f"/products/{product_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/products/{product_id}")
    assert get_response.status_code == 404


async def test_delete_product_not_found(client):
    response = await client.delete(f"/products/{uuid4()}")
    assert response.status_code == 404
