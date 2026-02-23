from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# --- Product schemas ---


class ProductCreate(BaseModel):
    name: str
    description: str | None = None


class ProductUpdate(BaseModel):
    name: str
    description: str | None = None


class Product(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Offer schemas ---


class Offer(BaseModel):
    id: UUID
    product_id: UUID
    price: int
    items_in_stock: int

    model_config = {"from_attributes": True}


# --- External service schemas ---


class ExternalAuthResponse(BaseModel):
    access_token: str


class ExternalRegistrationResponse(BaseModel):
    id: UUID


class ExternalOffer(BaseModel):
    id: UUID
    price: int
    items_in_stock: int
