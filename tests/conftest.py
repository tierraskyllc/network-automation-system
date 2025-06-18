"""
Pytest configuration and fixtures for the Network Automation System tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

# Test configuration
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
