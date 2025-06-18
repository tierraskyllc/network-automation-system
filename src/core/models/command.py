"""
Command Models

Database models for commands, executions, and templates.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
import enum
from datetime import datetime
from typing import Dict, List, Optional

from ..database import Base


class CommandStatus(enum.Enum):
    """Command execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class CommandType(enum.Enum):
    """Command types"""
    SHOW = "show"
    CONFIG = "config"
    EXEC = "exec"
    DIAGNOSTIC = "diagnostic"
    MAINTENANCE = "maintenance"


class RiskLevel(enum.Enum):
    """Command risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Command(Base):
    """Command template model"""
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    command_text = Column(Text, nullable=False)
    description = Column(Text)
    
    # Command classification
    command_type = Column(Enum(CommandType), nullable=False)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    vendor = Column(String(100))
    device_os = Column(String(100))
    
    # Command properties
    is_template = Column(Boolean, default=False)
    template_variables = Column(ARRAY(String), default=list)
    expected_output_pattern = Column(Text)
    timeout_seconds = Column(Integer, default=30)
    
    # Authorization requirements
    requires_approval = Column(Boolean, default=False)
    approval_roles = Column(ARRAY(String), default=list)
    requires_dual_auth = Column(Boolean, default=False)
    
    # Validation
    syntax_validation = Column(Text)  # Regex or validation rules
    pre_execution_checks = Column(JSON, default=dict)
    post_execution_checks = Column(JSON, default=dict)
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    category = Column(String(100))
    version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    executions = relationship("CommandExecution", back_populates="command")
    creator = relationship("User")

    def __repr__(self):
        return f"<Command(name='{self.name}', type='{self.command_type}')>"


class CommandExecution(Base):
    """Command execution record"""
    __tablename__ = "command_executions"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("commands.id"))
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"))
    
    # Execution details
    command_text = Column(Text, nullable=False)  # Actual command executed
    status = Column(Enum(CommandStatus), default=CommandStatus.PENDING)
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    timeout_seconds = Column(Integer, default=30)
    
    # Results
    output = Column(Text)
    error_output = Column(Text)
    exit_code = Column(Integer)
    parsed_output = Column(JSON, default=dict)
    
    # Context
    execution_context = Column(JSON, default=dict)  # Environment, variables, etc.
    session_id = Column(String(255))
    correlation_id = Column(String(255), index=True)
    
    # Approval and authorization
    approval_request_id = Column(String(255))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Metadata
    execution_metadata = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    command = relationship("Command", back_populates="executions")
    device = relationship("Device", back_populates="command_executions")
    user = relationship("User", back_populates="command_executions")
    approver = relationship("User", foreign_keys=[approved_by])
    workflow_execution = relationship("WorkflowExecution", back_populates="command_executions")

    def __repr__(self):
        return f"<CommandExecution(id={self.id}, status='{self.status}')>"


class CommandTemplate(Base):
    """Reusable command templates"""
    __tablename__ = "command_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Template content
    template_text = Column(Text, nullable=False)
    variables = Column(JSON, default=dict)  # Variable definitions
    default_values = Column(JSON, default=dict)
    
    # Template properties
    category = Column(String(100))
    vendor = Column(String(100))
    device_os = Column(String(100))
    version = Column(String(20), default="1.0")
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    
    # Validation
    validation_rules = Column(JSON, default=dict)
    example_usage = Column(Text)
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User")

    def __repr__(self):
        return f"<CommandTemplate(name='{self.name}', category='{self.category}')>"
