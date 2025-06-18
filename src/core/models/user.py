"""
User and Authentication Models

Database models for users, roles, permissions, and authentication.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
import enum
from datetime import datetime
from typing import List, Optional

from ..database import Base


class UserStatus(enum.Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"


class AuthProvider(enum.Enum):
    """Authentication providers"""
    LOCAL = "local"
    LDAP = "ldap"
    SAML = "saml"
    OAUTH2 = "oauth2"


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('assigned_by', Integer, ForeignKey('users.id')),
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), server_default=func.now()),
)


class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    
    # Authentication
    password_hash = Column(Text)  # For local authentication
    auth_provider = Column(String(50), default=AuthProvider.LOCAL.value)
    external_id = Column(String(255))  # ID from external auth provider
    
    # Account status
    status = Column(String(20), default=UserStatus.ACTIVE.value)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    # Security settings
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(Text)  # Encrypted MFA secret
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    # Profile information
    department = Column(String(100))
    job_title = Column(String(100))
    phone = Column(String(20))
    timezone = Column(String(50), default="UTC")
    
    # Activity tracking
    last_login = Column(DateTime(timezone=True))
    last_activity = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    
    # Preferences
    preferences = Column(Text)  # JSON string for user preferences
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")
    command_executions = relationship("CommandExecution", back_populates="user")
    workflow_executions = relationship("WorkflowExecution", back_populates="user")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Role(Base):
    """Role model for RBAC"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    
    # Role properties
    is_system_role = Column(Boolean, default=False)  # System roles cannot be deleted
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

    def __repr__(self):
        return f"<Role(name='{self.name}')>"


class Permission(Base):
    """Permission model for fine-grained access control"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(100), nullable=False)  # e.g., 'device', 'command', 'workflow'
    action = Column(String(50), nullable=False)  # e.g., 'read', 'write', 'execute', 'delete'
    description = Column(Text)
    
    # Permission properties
    is_system_permission = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission(name='{self.name}', resource='{self.resource}', action='{self.action}')>"


class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, index=True)
    
    # Session details
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    device_info = Column(Text)
    
    # Session status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, active={self.is_active})>"
