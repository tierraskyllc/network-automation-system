"""
API Endpoints

This module contains all API endpoint routers for the network automation system.
"""

from .auth import router as auth_router
from .devices import router as devices_router
from .commands import router as commands_router
from .workflows import router as workflows_router
from .topology import router as topology_router
from .users import router as users_router
from .health import router as health_router

__all__ = [
    "auth_router",
    "devices_router",
    "commands_router", 
    "workflows_router",
    "topology_router",
    "users_router",
    "health_router",
]
