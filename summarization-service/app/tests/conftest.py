import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


TEST_DATABASE_URL = "sqlite+aiosqlite:///file:summarizer_memdb?mode=memory&cache=shared"
test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


import app.database
app.database.async_session_maker = TestingSessionLocal

from app.database import Base


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def prepare_test_database():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def _create_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _drop_tables():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    loop.run_until_complete(_create_tables())
    yield
    loop.run_until_complete(_drop_tables())


@pytest.fixture(autouse=True)
def mock_gigachat_network_lock():
    mock_response = MagicMock()
    mock_response.text = "Mocked AI report text from GigaChat stub."
    
    mock_achat = AsyncMock(return_value=mock_response)
    
    mock_giga_instance = MagicMock()
    mock_giga_instance.achat = mock_achat
    
    with patch("app.services.GigaChat") as mock_class:
        mock_class.return_value.__aenter__ = AsyncMock(return_value=mock_giga_instance)
        mock_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        yield mock_achat
