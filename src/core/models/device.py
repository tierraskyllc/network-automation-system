"""
Device Models

Database models for network devices, credentials, and capabilities.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INET, ARRAY
import enum
from datetime import datetime
from typing import Dict, List, Optional

from ..database import Base


class DeviceType(enum.Enum):
    """Supported device types"""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    WIRELESS_CONTROLLER = "wireless_controller"
    ACCESS_POINT = "access_point"
    LOAD_BALANCER = "load_balancer"
    UNKNOWN = "unknown"


class DeviceStatus(enum.Enum):
    """Device operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    UNREACHABLE = "unreachable"
    ERROR = "error"


class ConnectionProtocol(enum.Enum):
    """Supported connection protocols"""
    SSH = "ssh"
    TELNET = "telnet"
    HTTPS = "https"
    HTTP = "http"
    SNMP = "snmp"
    NETCONF = "netconf"
    RESTCONF = "restconf"


class Device(Base):
    """Network device model"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(INET, nullable=False, index=True)
    device_type = Column(Enum(DeviceType), nullable=False, default=DeviceType.UNKNOWN)
    vendor = Column(String(100), nullable=False)
    model = Column(String(100))
    os_version = Column(String(100))
    serial_number = Column(String(100))
    
    # Status and health
    status = Column(Enum(DeviceStatus), nullable=False, default=DeviceStatus.ACTIVE)
    last_seen = Column(DateTime(timezone=True))
    uptime = Column(Integer)  # Uptime in seconds
    
    # Location and organization
    site = Column(String(100))
    rack = Column(String(50))
    position = Column(String(50))
    environment = Column(String(50), default="production")  # production, staging, lab
    
    # Connection details
    management_ip = Column(INET)
    connection_protocols = Column(ARRAY(String), default=list)
    default_protocol = Column(Enum(ConnectionProtocol), default=ConnectionProtocol.SSH)
    port = Column(Integer, default=22)
    
    # Capabilities and features
    capabilities = Column(JSON, default=dict)
    supported_commands = Column(ARRAY(String), default=list)
    
    # Metadata
    description = Column(Text)
    tags = Column(ARRAY(String), default=list)
    device_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    credentials = relationship("DeviceCredential", back_populates="device", cascade="all, delete-orphan")
    capabilities_rel = relationship("DeviceCapability", back_populates="device", cascade="all, delete-orphan")
    command_executions = relationship("CommandExecution", back_populates="device")
    topology_nodes = relationship("TopologyNode", back_populates="device")

    def __repr__(self):
        return f"<Device(hostname='{self.hostname}', ip='{self.ip_address}', type='{self.device_type}')>"


class DeviceCredential(Base):
    """Device authentication credentials"""
    __tablename__ = "device_credentials"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    credential_type = Column(String(50), nullable=False)  # username_password, ssh_key, snmp, api_key
    username = Column(String(100))
    password_hash = Column(Text)  # Encrypted password
    ssh_key_path = Column(String(500))
    enable_password_hash = Column(Text)  # Encrypted enable password
    snmp_community = Column(String(100))
    api_key_hash = Column(Text)  # Encrypted API key
    
    # Credential metadata
    description = Column(String(255))
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    last_used = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="credentials")

    def __repr__(self):
        return f"<DeviceCredential(device_id={self.device_id}, type='{self.credential_type}')>"


class DeviceCapability(Base):
    """Device capabilities and features"""
    __tablename__ = "device_capabilities"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    capability_name = Column(String(100), nullable=False)
    capability_value = Column(String(255))
    is_supported = Column(Boolean, default=True)
    version = Column(String(50))
    
    # Metadata
    description = Column(Text)
    capability_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="capabilities_rel")

    def __repr__(self):
        return f"<DeviceCapability(device_id={self.device_id}, name='{self.capability_name}')>"
