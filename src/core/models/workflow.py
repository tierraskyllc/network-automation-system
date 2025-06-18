"""
Workflow Models

Database models for workflows, executions, and steps using LangGraph.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
import enum
from datetime import datetime
from typing import Dict, List, Optional

from ..database import Base


class WorkflowStatus(enum.Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class StepStatus(enum.Enum):
    """Workflow step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRY = "retry"


class WorkflowType(enum.Enum):
    """Workflow types"""
    CONFIGURATION = "configuration"
    DIAGNOSTIC = "diagnostic"
    MAINTENANCE = "maintenance"
    DISCOVERY = "discovery"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class Workflow(Base):
    """Workflow definition model"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Workflow definition
    workflow_type = Column(Enum(WorkflowType), nullable=False)
    langgraph_definition = Column(JSON, nullable=False)  # LangGraph workflow definition
    input_schema = Column(JSON, default=dict)  # JSON schema for inputs
    output_schema = Column(JSON, default=dict)  # JSON schema for outputs
    
    # Workflow properties
    version = Column(String(20), default="1.0")
    is_template = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    # Execution settings
    max_execution_time = Column(Integer, default=3600)  # seconds
    max_retry_attempts = Column(Integer, default=3)
    parallel_execution = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    
    # Target constraints
    supported_vendors = Column(ARRAY(String), default=list)
    supported_device_types = Column(ARRAY(String), default=list)
    required_capabilities = Column(ARRAY(String), default=list)
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    category = Column(String(100))
    documentation = Column(Text)
    
    # Usage tracking
    execution_count = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)  # Percentage
    last_executed = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow")
    creator = relationship("User")

    def __repr__(self):
        return f"<Workflow(name='{self.name}', type='{self.workflow_type}')>"


class WorkflowExecution(Base):
    """Workflow execution instance"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Execution details
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    execution_name = Column(String(255))  # User-defined name for this execution
    
    # Input/Output
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    context_data = Column(JSON, default=dict)  # LangGraph state
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Progress tracking
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    current_step = Column(String(255))
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON, default=dict)
    retry_count = Column(Integer, default=0)
    
    # Approval and authorization
    approval_request_id = Column(String(255))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Execution context
    execution_environment = Column(String(50), default="production")
    correlation_id = Column(String(255), index=True)
    session_id = Column(String(255))
    
    # Metadata
    metadata = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    user = relationship("User", back_populates="workflow_executions")
    approver = relationship("User", foreign_keys=[approved_by])
    steps = relationship("WorkflowStep", back_populates="execution", cascade="all, delete-orphan")
    command_executions = relationship("CommandExecution", back_populates="workflow_execution")

    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, status='{self.status}')>"


class WorkflowStep(Base):
    """Individual workflow step execution"""
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False)
    
    # Step identification
    step_name = Column(String(255), nullable=False)
    step_type = Column(String(100), nullable=False)  # command, decision, parallel, etc.
    step_order = Column(Integer, nullable=False)
    
    # Step details
    status = Column(Enum(StepStatus), default=StepStatus.PENDING)
    description = Column(Text)
    
    # Input/Output
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    step_context = Column(JSON, default=dict)
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON, default=dict)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Dependencies
    depends_on = Column(ARRAY(String), default=list)  # Step names this step depends on
    blocks = Column(ARRAY(String), default=list)  # Step names this step blocks
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    execution = relationship("WorkflowExecution", back_populates="steps")

    def __repr__(self):
        return f"<WorkflowStep(name='{self.step_name}', status='{self.status}')>"
