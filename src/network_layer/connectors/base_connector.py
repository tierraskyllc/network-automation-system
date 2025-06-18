"""
Base Network Connector

Abstract base class for all network device connectors.
"""

import asyncio
import structlog
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = structlog.get_logger(__name__)


class ConnectionStatus(Enum):
    """Connection status enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    TIMEOUT = "timeout"


class CommandStatus(Enum):
    """Command execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"


@dataclass
class ConnectionResult:
    """Result of a connection attempt"""
    success: bool
    status: ConnectionStatus
    message: str
    connection_time: Optional[float] = None
    error_details: Optional[Dict[str, Any]] = None


@dataclass
class CommandResult:
    """Result of a command execution"""
    success: bool
    status: CommandStatus
    command: str
    output: str
    error: Optional[str] = None
    execution_time: Optional[float] = None
    parsed_output: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class BaseConnector(ABC):
    """Abstract base class for network device connectors"""
    
    def __init__(self, device_config: Dict[str, Any]):
        """
        Initialize connector with device configuration
        
        Args:
            device_config: Device configuration dictionary
        """
        self.device_config = device_config
        self.hostname = device_config.get("hostname", "unknown")
        self.ip_address = device_config.get("ip_address")
        self.device_type = device_config.get("device_type", "unknown")
        self.vendor = device_config.get("vendor", "unknown")
        
        # Connection settings
        self.username = device_config.get("username")
        self.password = device_config.get("password")
        self.enable_password = device_config.get("enable_password")
        self.port = device_config.get("port", 22)
        self.timeout = device_config.get("timeout", 30)
        
        # Connection state
        self.status = ConnectionStatus.DISCONNECTED
        self.connection = None
        self.last_error = None
        self.connected_at = None
        
        self.logger = logger.bind(
            hostname=self.hostname,
            ip_address=self.ip_address,
            device_type=self.device_type
        )
    
    @abstractmethod
    async def connect(self) -> ConnectionResult:
        """
        Establish connection to the device
        
        Returns:
            ConnectionResult: Result of connection attempt
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the device
        
        Returns:
            bool: True if disconnected successfully
        """
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """
        Execute a command on the device
        
        Args:
            command: Command to execute
            **kwargs: Additional command options
            
        Returns:
            CommandResult: Result of command execution
        """
        pass
    
    @abstractmethod
    async def execute_commands(self, commands: List[str], **kwargs) -> List[CommandResult]:
        """
        Execute multiple commands on the device
        
        Args:
            commands: List of commands to execute
            **kwargs: Additional command options
            
        Returns:
            List[CommandResult]: Results of command executions
        """
        pass
    
    @abstractmethod
    async def get_device_info(self) -> Dict[str, Any]:
        """
        Get basic device information
        
        Returns:
            Dict[str, Any]: Device information
        """
        pass
    
    async def is_connected(self) -> bool:
        """
        Check if device is connected
        
        Returns:
            bool: True if connected
        """
        return self.status == ConnectionStatus.CONNECTED and self.connection is not None
    
    async def ping(self) -> bool:
        """
        Ping the device to check connectivity
        
        Returns:
            bool: True if device is reachable
        """
        try:
            import subprocess
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", self.ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.warning("Ping failed", error=str(e))
            return False
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """
        Test various connectivity methods
        
        Returns:
            Dict[str, Any]: Connectivity test results
        """
        results = {
            "ping": False,
            "tcp_connect": False,
            "ssh_connect": False,
            "device_connect": False
        }
        
        # Test ping
        results["ping"] = await self.ping()
        
        # Test TCP connection
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip_address, self.port),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()
            results["tcp_connect"] = True
        except Exception:
            results["tcp_connect"] = False
        
        # Test SSH connection (basic)
        try:
            import asyncssh
            async with asyncssh.connect(
                self.ip_address,
                port=self.port,
                username=self.username,
                password=self.password,
                known_hosts=None,
                connect_timeout=10
            ) as conn:
                results["ssh_connect"] = True
        except Exception:
            results["ssh_connect"] = False
        
        # Test device-specific connection
        try:
            connect_result = await self.connect()
            results["device_connect"] = connect_result.success
            if connect_result.success:
                await self.disconnect()
        except Exception:
            results["device_connect"] = False
        
        return results
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get current connection information
        
        Returns:
            Dict[str, Any]: Connection information
        """
        return {
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "port": self.port,
            "status": self.status.value,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_error": self.last_error
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
    
    def __repr__(self):
        return f"{self.__class__.__name__}(hostname='{self.hostname}', status='{self.status.value}')"
