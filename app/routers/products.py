"""Product CRUD endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Product as ProductModel
from app.schemas import Product, ProductCreate, ProductUpdate
from app.services.offers_client import OffersClient

log = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=Product, status_code=201)
async def create_product(data: ProductCreate, session: AsyncSession = Depends(get_session)):
    """Create a product and register it with the offers service."""
    log.info("Creating product: name=%s", data.name)

    product = ProductModel(name=data.name, description=data.description)
    session.add(product)
    await session.flush()
    log.debug("Product saved to DB with id=%s", product.id)

    log.info("Registering product %s with external offers service", product.id)
    client = OffersClient.get()
    external_id = await client.register_product(product.id, product.name, product.description)
    product.external_id = external_id
    log.info("Product %s registered with external_id=%s", product.id, external_id)

    log.info("Product created successfully: id=%s, name=%s", product.id, product.name)
    return product


@router.get("", response_model=list[Product])
async def list_products(session: AsyncSession = Depends(get_session)):
    """List all products."""
    log.debug("Fetching all products")
    result = await session.execute(select(ProductModel))
    products = result.scalars().all()
    log.info("Retrieved %d products", len(products))
    return products


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: UUID, session: AsyncSession = Depends(get_session)):
    """Get a single product."""
    log.debug("Fetching product: id=%s", product_id)
    product = await session.get(ProductModel, product_id)
    if not product:
        log.warning("Product not found: id=%s", product_id)
        raise HTTPException(status_code=404, detail="Product not found")
    log.info("Retrieved product: id=%s, name=%s", product.id, product.name)
    return product


@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: UUID, data: ProductUpdate, session: AsyncSession = Depends(get_session)):
    """Update a product."""
    log.info("Updating product: id=%s", product_id)
    product = await session.get(ProductModel, product_id)
    if not product:
        log.warning("Product not found for update: id=%s", product_id)
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = data.name
    product.description = data.description

    log.info("Product updated successfully: id=%s", product_id)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: UUID, session: AsyncSession = Depends(get_session)):
    """Delete a product and its offers."""
    log.info("Deleting product: id=%s", product_id)
    product = await session.get(ProductModel, product_id)
    if not product:
        log.warning("Product not found for deletion: id=%s", product_id)
        raise HTTPException(status_code=404, detail="Product not found")

    product_name = product.name
    await session.delete(product)
    log.info("Product deleted successfully: id=%s, name=%s", product_id, product_name)
