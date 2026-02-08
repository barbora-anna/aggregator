from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.database import make_session_factory
from app.db.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture()
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture()
async def test_session_factory(engine):
    return make_session_factory(engine)


@pytest.fixture()
async def session(test_session_factory) -> AsyncSession:
    async with test_session_factory() as sesh:
        yield sesh


@pytest.fixture()
async def mock_offers_client():
    mock = AsyncMock()
    mock.register_product = AsyncMock(return_value=uuid4())
    mock.get_offers = AsyncMock(return_value=[])
    with patch("app.services.offers_client.OffersClient.get", return_value=mock):
        yield mock


@pytest.fixture()
async def client(engine, test_session_factory, mock_offers_client):
    import app.db.database as db_module

    original_engine = db_module.engine
    original_factory = db_module.session_factory
    db_module.engine = engine
    db_module.session_factory = test_session_factory

    with patch("app.main.start_scheduler"), patch("app.main.stop_scheduler"):
        from app.main import app

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    db_module.engine = original_engine
    db_module.session_factory = original_factory