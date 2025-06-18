"""
Pytest configuration and fixtures for the Network Automation System tests.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient
import redis.asyncio as redis

from src.core.database import Base, get_db
from src.core.config import get_settings
from src.core.models.user import User
from src.core.security.auth import PasswordManager
from src.api.main import app

# Test configuration
pytest_plugins = ["pytest_asyncio"]

# Test settings
settings = get_settings()
TEST_DATABASE_URL = settings.TEST_DATABASE_URL
TEST_REDIS_URL = settings.TEST_REDIS_URL

# Test database engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def redis_client():
    """Create a test Redis client."""
    client = redis.from_url(TEST_REDIS_URL)
    yield client
    await client.flushdb()
    await client.close()


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the get_db dependency for testing."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db) -> TestClient:
    """Create a test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    password_manager = PasswordManager()

    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password_hash=password_manager.hash_password("testpassword"),
        status="active",
        is_verified=True
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def mock_database():
    """Mock database session for testing."""
    return MagicMock()


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    return AsyncMock()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    return AsyncMock()


@pytest.fixture
def mock_device():
    """Mock network device for testing."""
    return {
        "id": 1,
        "hostname": "test-device-01",
        "device_type": "cisco_ios",
        "ip_address": "192.168.1.100",
        "username": "admin",
        "password": "admin",
        "enable_password": "enable"
    }


@pytest.fixture
def sample_command_output():
    """Sample command output for testing."""
    return {
        "raw": "Interface Status\nGigabitEthernet0/1 up up\nGigabitEthernet0/2 down down",
        "parsed": {
            "interfaces": {
                "GigabitEthernet0/1": {
                    "admin_status": "up",
                    "oper_status": "up"
                },
                "GigabitEthernet0/2": {
                    "admin_status": "down", 
                    "oper_status": "down"
                }
            }
        },
        "parser_used": "ShowInterfaceStatus"
    }
