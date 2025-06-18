"""
Network Layer Module

This module provides network device connectivity and management functionality
using pyATS/Genie and other network automation libraries.
"""

from .connectors import (
    BaseConnector,
    GenieConnector,
    NetmikoConnector,
    ConnectionManager,
)
from .parsers import (
    BaseParser,
    GenieParser,
    OutputParser,
)

__all__ = [
    # Connectors
    "BaseConnector",
    "GenieConnector", 
    "NetmikoConnector",
    "ConnectionManager",
    
    # Parsers
    "BaseParser",
    "GenieParser",
    "OutputParser",
]
