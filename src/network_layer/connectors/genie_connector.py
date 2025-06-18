"""
Genie/pyATS Network Connector

Network device connector using Cisco's pyATS/Genie framework.
"""

import asyncio
import time
import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_connector import (
    BaseConnector,
    ConnectionResult,
    CommandResult,
    ConnectionStatus,
    CommandStatus,
)

logger = structlog.get_logger(__name__)


class GenieConnector(BaseConnector):
    """Network connector using pyATS/Genie framework"""
    
    def __init__(self, device_config: Dict[str, Any]):
        """
        Initialize Genie connector
        
        Args:
            device_config: Device configuration dictionary
        """
        super().__init__(device_config)
        
        # Genie-specific configuration
        self.os = device_config.get("os", "ios")
        self.platform = device_config.get("platform", "cat9k")
        self.connection_type = device_config.get("connection_type", "ssh")
        
        # pyATS device object
        self.device = None
        self.testbed = None
        
        self.logger = logger.bind(
            hostname=self.hostname,
            os=self.os,
            platform=self.platform
        )
    
    async def connect(self) -> ConnectionResult:
        """
        Establish connection using pyATS/Genie
        
        Returns:
            ConnectionResult: Result of connection attempt
        """
        start_time = time.time()
        self.status = ConnectionStatus.CONNECTING
        
        try:
            # Import pyATS modules
            from pyats.topology import Device
            from pyats.topology import Testbed
            from unicon.core.errors import ConnectionError, TimeoutError
            
            # Create testbed configuration
            testbed_config = {
                'devices': {
                    self.hostname: {
                        'type': self.device_type,
                        'os': self.os,
                        'platform': self.platform,
                        'connections': {
                            'default': {
                                'protocol': self.connection_type,
                                'ip': self.ip_address,
                                'port': self.port,
                                'username': self.username,
                                'password': self.password,
                            }
                        },
                        'credentials': {
                            'default': {
                                'username': self.username,
                                'password': self.password,
                            },
                            'enable': {
                                'password': self.enable_password,
                            }
                        }
                    }
                }
            }
            
            # Create testbed and device
            self.testbed = Testbed.from_dict(testbed_config)
            self.device = self.testbed.devices[self.hostname]
            
            # Connect to device
            await asyncio.get_event_loop().run_in_executor(
                None, self.device.connect, None, 30  # 30 second timeout
            )
            
            connection_time = time.time() - start_time
            self.status = ConnectionStatus.CONNECTED
            self.connected_at = datetime.utcnow()
            
            self.logger.info(
                "Connected to device",
                connection_time=connection_time,
                os=self.device.os,
                platform=self.device.platform
            )
            
            return ConnectionResult(
                success=True,
                status=ConnectionStatus.CONNECTED,
                message="Successfully connected to device",
                connection_time=connection_time
            )
            
        except (ConnectionError, TimeoutError) as e:
            connection_time = time.time() - start_time
            self.status = ConnectionStatus.FAILED
            self.last_error = str(e)
            
            self.logger.error(
                "Connection failed",
                error=str(e),
                connection_time=connection_time
            )
            
            return ConnectionResult(
                success=False,
                status=ConnectionStatus.FAILED,
                message=f"Connection failed: {str(e)}",
                connection_time=connection_time,
                error_details={"error_type": type(e).__name__, "error_message": str(e)}
            )
            
        except Exception as e:
            connection_time = time.time() - start_time
            self.status = ConnectionStatus.FAILED
            self.last_error = str(e)
            
            self.logger.error(
                "Unexpected connection error",
                error=str(e),
                connection_time=connection_time
            )
            
            return ConnectionResult(
                success=False,
                status=ConnectionStatus.FAILED,
                message=f"Unexpected error: {str(e)}",
                connection_time=connection_time,
                error_details={"error_type": type(e).__name__, "error_message": str(e)}
            )
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the device
        
        Returns:
            bool: True if disconnected successfully
        """
        try:
            if self.device and self.device.is_connected():
                await asyncio.get_event_loop().run_in_executor(
                    None, self.device.disconnect
                )
            
            self.status = ConnectionStatus.DISCONNECTED
            self.device = None
            self.testbed = None
            self.connected_at = None
            
            self.logger.info("Disconnected from device")
            return True
            
        except Exception as e:
            self.logger.error("Disconnect failed", error=str(e))
            return False
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """
        Execute a command using Genie
        
        Args:
            command: Command to execute
            **kwargs: Additional options (timeout, etc.)
            
        Returns:
            CommandResult: Result of command execution
        """
        if not await self.is_connected():
            return CommandResult(
                success=False,
                status=CommandStatus.FAILED,
                command=command,
                output="",
                error="Device not connected"
            )
        
        start_time = time.time()
        timestamp = datetime.utcnow()
        
        try:
            timeout = kwargs.get("timeout", 60)
            
            # Execute command
            output = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.device.execute(command, timeout=timeout)
            )
            
            execution_time = time.time() - start_time
            
            # Try to parse output using Genie parsers
            parsed_output = await self._try_parse_output(command, output)
            
            self.logger.info(
                "Command executed successfully",
                command=command,
                execution_time=execution_time,
                output_length=len(output)
            )
            
            return CommandResult(
                success=True,
                status=CommandStatus.SUCCESS,
                command=command,
                output=output,
                execution_time=execution_time,
                parsed_output=parsed_output,
                timestamp=timestamp
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(
                "Command execution failed",
                command=command,
                error=error_msg,
                execution_time=execution_time
            )
            
            return CommandResult(
                success=False,
                status=CommandStatus.FAILED,
                command=command,
                output="",
                error=error_msg,
                execution_time=execution_time,
                timestamp=timestamp
            )
    
    async def execute_commands(self, commands: List[str], **kwargs) -> List[CommandResult]:
        """
        Execute multiple commands
        
        Args:
            commands: List of commands to execute
            **kwargs: Additional options
            
        Returns:
            List[CommandResult]: Results of command executions
        """
        results = []
        
        for command in commands:
            result = await self.execute_command(command, **kwargs)
            results.append(result)
            
            # Stop on first failure if specified
            if not result.success and kwargs.get("stop_on_failure", False):
                break
        
        return results
    
    async def get_device_info(self) -> Dict[str, Any]:
        """
        Get device information using Genie parsers
        
        Returns:
            Dict[str, Any]: Device information
        """
        if not await self.is_connected():
            return {}
        
        try:
            # Get version information
            version_result = await self.execute_command("show version")
            
            device_info = {
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "device_type": self.device_type,
                "os": self.os,
                "platform": self.platform,
                "connection_status": self.status.value,
                "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            }
            
            # Add parsed version info if available
            if version_result.success and version_result.parsed_output:
                device_info.update(version_result.parsed_output)
            
            return device_info
            
        except Exception as e:
            self.logger.error("Failed to get device info", error=str(e))
            return {
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "error": str(e)
            }
    
    async def _try_parse_output(self, command: str, output: str) -> Optional[Dict[str, Any]]:
        """
        Try to parse command output using Genie parsers
        
        Args:
            command: Command that was executed
            output: Raw command output
            
        Returns:
            Optional[Dict[str, Any]]: Parsed output or None
        """
        try:
            from genie.libs.parser.utils import get_parser
            
            # Try to find appropriate parser
            parser = get_parser(command, self.device)
            if parser:
                parsed = await asyncio.get_event_loop().run_in_executor(
                    None, parser.parse
                )
                return parsed
            
        except Exception as e:
            self.logger.debug("Failed to parse output", command=command, error=str(e))
        
        return None
    
    async def learn_feature(self, feature: str) -> Optional[Dict[str, Any]]:
        """
        Learn a network feature using Genie
        
        Args:
            feature: Feature to learn (e.g., 'interface', 'bgp', 'ospf')
            
        Returns:
            Optional[Dict[str, Any]]: Learned feature data
        """
        if not await self.is_connected():
            return None
        
        try:
            from genie.libs.ops.utils import get_ops
            
            # Get the ops class for the feature
            ops_class = get_ops(feature, self.device)
            if not ops_class:
                self.logger.warning("No ops class found for feature", feature=feature)
                return None
            
            # Learn the feature
            ops_obj = ops_class(device=self.device)
            learned_data = await asyncio.get_event_loop().run_in_executor(
                None, ops_obj.learn
            )
            
            self.logger.info("Feature learned successfully", feature=feature)
            return ops_obj.info
            
        except Exception as e:
            self.logger.error("Failed to learn feature", feature=feature, error=str(e))
            return None
