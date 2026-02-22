"""add index on product external_id

Revision ID: 3cdb298b2d13
Revises: 001
Create Date: 2026-02-22 19:00:54.858010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3cdb298b2d13'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_product_external_id'), 'product', ['external_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_external_id'), table_name='product')
