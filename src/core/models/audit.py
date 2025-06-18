"""
Audit and Security Models

Database models for audit logging, security events, and compliance tracking.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INET, ARRAY
import enum
from datetime import datetime
from typing import Dict, List, Optional

from ..database import Base


class AuditAction(enum.Enum):
    """Audit action types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"


class AuditResource(enum.Enum):
    """Auditable resource types"""
    USER = "user"
    DEVICE = "device"
    COMMAND = "command"
    WORKFLOW = "workflow"
    TOPOLOGY = "topology"
    CREDENTIAL = "credential"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


class SecurityEventType(enum.Enum):
    """Security event types"""
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    POLICY_VIOLATION = "policy_violation"
    CREDENTIAL_COMPROMISE = "credential_compromise"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH = "data_breach"
    SYSTEM_COMPROMISE = "system_compromise"


class SecuritySeverity(enum.Enum):
    """Security event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    """Comprehensive audit logging"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Event identification
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    correlation_id = Column(String(255), index=True)
    session_id = Column(String(255), index=True)
    
    # Actor information
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String(100))  # Denormalized for performance
    user_ip = Column(INET)
    user_agent = Column(Text)
    
    # Action details
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(Enum(AuditResource), nullable=False, index=True)
    resource_id = Column(String(255), index=True)
    resource_name = Column(String(255))
    
    # Target information (for network operations)
    target_device_id = Column(Integer, ForeignKey("devices.id"))
    target_device_name = Column(String(255))
    target_ip = Column(INET)
    
    # Event details
    description = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    
    # Request/Response data
    request_data = Column(JSON, default=dict)
    response_data = Column(JSON, default=dict)
    
    # Outcome
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    error_code = Column(String(50))
    
    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    duration_ms = Column(Integer)
    
    # Context
    environment = Column(String(50), default="production")
    application_version = Column(String(50))
    api_version = Column(String(20))
    
    # Compliance and retention
    retention_period_days = Column(Integer, default=2555)  # 7 years default
    is_sensitive = Column(Boolean, default=False)
    compliance_tags = Column(ARRAY(String), default=list)
    
    # Metadata
    audit_metadata = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    target_device = relationship("Device")

    def __repr__(self):
        return f"<AuditLog(event_id='{self.event_id}', action='{self.action}')>"


class SecurityEvent(Base):
    """Security events and incidents"""
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    
    # Event identification
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    correlation_id = Column(String(255), index=True)
    
    # Event classification
    event_type = Column(Enum(SecurityEventType), nullable=False, index=True)
    severity = Column(Enum(SecuritySeverity), nullable=False, index=True)
    category = Column(String(100))
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    
    # Source information
    source_ip = Column(INET, index=True)
    source_user_id = Column(Integer, ForeignKey("users.id"))
    source_device_id = Column(Integer, ForeignKey("devices.id"))
    source_system = Column(String(100))
    
    # Target information
    target_ip = Column(INET)
    target_user_id = Column(Integer, ForeignKey("users.id"))
    target_device_id = Column(Integer, ForeignKey("devices.id"))
    target_resource = Column(String(255))
    
    # Detection information
    detected_by = Column(String(100))  # System/rule that detected the event
    detection_method = Column(String(100))
    confidence_score = Column(Integer)  # 0-100
    
    # Response and status
    status = Column(String(50), default="open")  # open, investigating, resolved, false_positive
    assigned_to = Column(Integer, ForeignKey("users.id"))
    resolution = Column(Text)
    resolution_time = Column(DateTime(timezone=True))
    
    # Impact assessment
    impact_level = Column(String(50))
    affected_systems = Column(ARRAY(String), default=list)
    business_impact = Column(Text)
    
    # Compliance and reporting
    requires_notification = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    compliance_violation = Column(Boolean, default=False)
    regulatory_requirements = Column(ARRAY(String), default=list)
    
    # Timing
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    
    # Metadata
    event_metadata = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    source_user = relationship("User", foreign_keys=[source_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    source_device = relationship("Device", foreign_keys=[source_device_id])
    target_device = relationship("Device", foreign_keys=[target_device_id])

    def __repr__(self):
        return f"<SecurityEvent(event_id='{self.event_id}', type='{self.event_type}', severity='{self.severity}')>"


class ComplianceRule(Base):
    """Compliance rules and policies"""
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Rule definition
    rule_type = Column(String(100), nullable=False)  # access_control, data_retention, etc.
    rule_expression = Column(Text, nullable=False)  # Rule logic/expression
    
    # Compliance framework
    framework = Column(String(100))  # SOX, PCI-DSS, HIPAA, etc.
    control_id = Column(String(100))
    requirement = Column(Text)
    
    # Rule properties
    severity = Column(Enum(SecuritySeverity), default=SecuritySeverity.MEDIUM)
    is_active = Column(Boolean, default=True)
    is_mandatory = Column(Boolean, default=True)
    
    # Evaluation
    evaluation_frequency = Column(String(50), default="daily")  # real-time, hourly, daily, weekly
    last_evaluation = Column(DateTime(timezone=True))
    next_evaluation = Column(DateTime(timezone=True))
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    rule_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User")

    def __repr__(self):
        return f"<ComplianceRule(name='{self.name}', framework='{self.framework}')>"
