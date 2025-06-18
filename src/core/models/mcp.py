"""
MCP (Model Context Protocol) Models

Database models for MCP context, tools, and resources.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
import enum
from datetime import datetime
from typing import Dict, List, Optional

from ..database import Base


class MCPToolType(enum.Enum):
    """MCP tool types"""
    DEVICE_CONTEXT = "device_context"
    COMMAND_EXECUTION = "command_execution"
    TOPOLOGY_QUERY = "topology_query"
    WORKFLOW_MANAGEMENT = "workflow_management"
    CONFIGURATION_MANAGEMENT = "configuration_management"
    MONITORING = "monitoring"
    CUSTOM = "custom"


class MCPResourceType(enum.Enum):
    """MCP resource types"""
    DEVICE_INFO = "device_info"
    COMMAND_OUTPUT = "command_output"
    TOPOLOGY_DATA = "topology_data"
    CONFIGURATION = "configuration"
    METRICS = "metrics"
    DOCUMENTATION = "documentation"


class MCPContextStatus(enum.Enum):
    """MCP context status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    ERROR = "error"


class MCPContext(Base):
    """MCP context storage for LangChain/LangGraph"""
    __tablename__ = "mcp_contexts"

    id = Column(Integer, primary_key=True, index=True)
    context_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Context details
    context_type = Column(String(100), nullable=False)
    name = Column(String(255))
    description = Column(Text)
    
    # Context data
    context_data = Column(JSON, nullable=False, default=dict)
    context_metadata = Column(JSON, default=dict)
    
    # Scope and filters
    device_scope = Column(ARRAY(Integer), default=list)  # Device IDs
    network_scope = Column(ARRAY(String), default=list)  # Network ranges
    time_scope = Column(JSON, default=dict)  # Time range filters
    
    # Status and lifecycle
    status = Column(Enum(MCPContextStatus), default=MCPContextStatus.ACTIVE)
    ttl_seconds = Column(Integer, default=3600)  # Time to live
    expires_at = Column(DateTime(timezone=True))
    
    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True))
    
    # Versioning
    version = Column(Integer, default=1)
    parent_context_id = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    tools = relationship("MCPTool", back_populates="context")
    resources = relationship("MCPResource", back_populates="context")

    def __repr__(self):
        return f"<MCPContext(context_id='{self.context_id}', type='{self.context_type}')>"


class MCPTool(Base):
    """MCP tools available to LangChain/LangGraph"""
    __tablename__ = "mcp_tools"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(String(255), unique=True, nullable=False, index=True)
    context_id = Column(Integer, ForeignKey("mcp_contexts.id"))
    
    # Tool definition
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    tool_type = Column(Enum(MCPToolType), nullable=False)
    
    # Tool specification
    input_schema = Column(JSON, nullable=False)  # JSON schema for inputs
    output_schema = Column(JSON, nullable=False)  # JSON schema for outputs
    function_definition = Column(JSON, nullable=False)  # OpenAI function format
    
    # Implementation details
    handler_module = Column(String(255))  # Python module path
    handler_function = Column(String(255))  # Function name
    endpoint_url = Column(String(500))  # API endpoint if applicable
    
    # Tool properties
    is_active = Column(Boolean, default=True)
    is_async = Column(Boolean, default=True)
    timeout_seconds = Column(Integer, default=30)
    retry_attempts = Column(Integer, default=3)
    
    # Authorization
    required_permissions = Column(ARRAY(String), default=list)
    required_roles = Column(ARRAY(String), default=list)
    device_access_required = Column(Boolean, default=False)
    
    # Usage tracking
    call_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Performance metrics
    avg_execution_time = Column(Integer)  # milliseconds
    max_execution_time = Column(Integer)
    min_execution_time = Column(Integer)
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    tool_metadata = Column(JSON, default=dict)
    documentation = Column(Text)
    examples = Column(JSON, default=list)
    
    # Versioning
    version = Column(String(20), default="1.0")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    context = relationship("MCPContext", back_populates="tools")
    creator = relationship("User")

    def __repr__(self):
        return f"<MCPTool(tool_id='{self.tool_id}', name='{self.name}')>"


class MCPResource(Base):
    """MCP resources for context and data sharing"""
    __tablename__ = "mcp_resources"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, nullable=False, index=True)
    context_id = Column(Integer, ForeignKey("mcp_contexts.id"))
    
    # Resource identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    resource_type = Column(Enum(MCPResourceType), nullable=False)
    
    # Resource data
    content = Column(JSON, nullable=False)  # Resource content
    content_type = Column(String(100), default="application/json")
    encoding = Column(String(50), default="utf-8")
    
    # Resource properties
    is_cacheable = Column(Boolean, default=True)
    cache_ttl = Column(Integer, default=3600)  # seconds
    is_sensitive = Column(Boolean, default=False)
    
    # Access control
    access_level = Column(String(50), default="private")  # public, private, restricted
    allowed_users = Column(ARRAY(Integer), default=list)  # User IDs
    allowed_roles = Column(ARRAY(String), default=list)
    
    # Source information
    source_device_id = Column(Integer, ForeignKey("devices.id"))
    source_command_id = Column(Integer, ForeignKey("commands.id"))
    source_workflow_id = Column(Integer, ForeignKey("workflows.id"))
    
    # Lifecycle
    expires_at = Column(DateTime(timezone=True))
    last_updated_source = Column(DateTime(timezone=True))
    
    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True))
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    resource_metadata = Column(JSON, default=dict)
    
    # Versioning
    version = Column(Integer, default=1)
    checksum = Column(String(64))  # SHA-256 checksum
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    context = relationship("MCPContext", back_populates="resources")
    source_device = relationship("Device")
    source_command = relationship("Command")
    source_workflow = relationship("Workflow")

    def __repr__(self):
        return f"<MCPResource(resource_id='{self.resource_id}', type='{self.resource_type}')>"
