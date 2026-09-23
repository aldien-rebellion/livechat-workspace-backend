import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config.redis import redis_client
from app.config.settings import settings
from app.db.session import get_db
from app.main import app

test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(
    test_engine, expire_on_commit=False, autoflush=False
)


@pytest.fixture(autouse=True)
def override_db_dependency():
    async def _get_test_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
async def cleanup_redis_pool():
    yield
    try:
        await redis_client.connection_pool.disconnect()
    except Exception:
        pass
