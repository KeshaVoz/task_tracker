from unittest.mock import MagicMock
import pytest
import fakeredis
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import app.database


TEST_DATABASE_URL = "sqlite+aiosqlite:///file:memdb1?mode=memory&cache=shared"
test_engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=False,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


app.database.async_session_maker = TestingSessionLocal
TEST_SYNC_DATABASE_URL = "sqlite:///file:memdb1?mode=memory&cache=shared"
test_sync_engine = create_engine(
    TEST_SYNC_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSyncSessionLocal = sessionmaker(bind=test_sync_engine, expire_on_commit=False)


app.database.sync_session_maker = TestingSyncSessionLocal
from app.main import app
from app.database import Base
from app.celery_client import celery_client


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def mock_redis_client(monkeypatch):
    fake_storage = fakeredis.FakeAsyncRedis(decode_responses=True)
    monkeypatch.setattr("app.redis_client.redis_client", fake_storage)
    yield


@pytest.fixture(autouse=True)
async def prepare_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def mock_celery_delivery():
    celery_client.conf.task_always_eager = True
    yield
    celery_client.conf.task_always_eager = False


@pytest.fixture
async def async_http_test_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def mock_smtp_server(monkeypatch):
    mock_server = MagicMock()
    monkeypatch.setattr(
        "app.services.email.get_smtp_server", 
        lambda: mock_server
    )
    yield mock_server

@pytest.fixture(autouse=True)
def mock_kafka_producer():
    from unittest.mock import MagicMock
    import app.tasks.email

    if app.tasks.email.kafka_producer is None:
        mock_producer = MagicMock()
        app.tasks.email.kafka_producer = mock_producer
    else:
        mock_producer = app.tasks.email.kafka_producer

    mock_producer.send = MagicMock()
    mock_producer.flush = MagicMock()

    yield mock_producer

    mock_producer.send.reset_mock()
    mock_producer.flush.reset_mock()

