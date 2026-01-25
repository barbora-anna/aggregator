"""Product CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.models import Product as ProductModel
from app.schemas import Product, ProductCreate, ProductUpdate
from app.services.offers_client import OffersClient

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=Product, status_code=201)
async def create_product(data: ProductCreate, session: AsyncSession = Depends(get_session)):
    """Create a product and register it with the offers service."""
    product = ProductModel(name=data.name, description=data.description)
    session.add(product)
    await session.flush()

    client = OffersClient()
    external_id = await client.register_product(product.id, product.name, product.description)
    product.external_id = external_id

    await session.commit()
    return product


@router.get("", response_model=list[Product])
async def list_products(session: AsyncSession = Depends(get_session)):
    """List all products."""
    result = await session.execute(select(ProductModel))
    return result.scalars().all()


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: UUID, session: AsyncSession = Depends(get_session)):
    """Get a single product."""
    product = await session.get(ProductModel, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: UUID, data: ProductUpdate, session: AsyncSession = Depends(get_session)):
    """Update a product."""
    product = await session.get(ProductModel, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description

    await session.commit()
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: UUID, session: AsyncSession = Depends(get_session)):
    """Delete a product and its offers."""
    product = await session.get(ProductModel, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await session.delete(product)
    await session.commit()
