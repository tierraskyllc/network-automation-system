"""
Network Topology Models

Database models for network topology, links, and nodes.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INET, ARRAY
import enum
from datetime import datetime
from typing import Dict, List, Optional

from ..database import Base


class TopologyType(enum.Enum):
    """Network topology types"""
    PHYSICAL = "physical"
    LOGICAL = "logical"
    LAYER2 = "layer2"
    LAYER3 = "layer3"
    OVERLAY = "overlay"


class LinkType(enum.Enum):
    """Network link types"""
    ETHERNET = "ethernet"
    FIBER = "fiber"
    WIRELESS = "wireless"
    TUNNEL = "tunnel"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


class LinkStatus(enum.Enum):
    """Link operational status"""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class NodeType(enum.Enum):
    """Topology node types"""
    DEVICE = "device"
    INTERFACE = "interface"
    SUBNET = "subnet"
    VLAN = "vlan"
    VRF = "vrf"
    VIRTUAL = "virtual"


class NetworkTopology(Base):
    """Network topology container"""
    __tablename__ = "network_topologies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Topology properties
    topology_type = Column(Enum(TopologyType), nullable=False)
    version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)
    
    # Discovery information
    discovery_method = Column(String(100))  # cdp, lldp, snmp, manual
    last_discovery = Column(DateTime(timezone=True))
    discovery_status = Column(String(50))
    
    # Scope and filters
    included_networks = Column(ARRAY(String), default=list)  # CIDR blocks
    excluded_networks = Column(ARRAY(String), default=list)
    device_filters = Column(JSON, default=dict)
    
    # Statistics
    node_count = Column(Integer, default=0)
    link_count = Column(Integer, default=0)
    device_count = Column(Integer, default=0)
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    nodes = relationship("TopologyNode", back_populates="topology", cascade="all, delete-orphan")
    links = relationship("TopologyLink", back_populates="topology", cascade="all, delete-orphan")
    creator = relationship("User")

    def __repr__(self):
        return f"<NetworkTopology(name='{self.name}', type='{self.topology_type}')>"


class TopologyNode(Base):
    """Network topology node"""
    __tablename__ = "topology_nodes"

    id = Column(Integer, primary_key=True, index=True)
    topology_id = Column(Integer, ForeignKey("network_topologies.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"))
    
    # Node identification
    node_id = Column(String(255), nullable=False, index=True)  # Unique within topology
    node_type = Column(Enum(NodeType), nullable=False)
    name = Column(String(255), nullable=False)
    
    # Node properties
    ip_address = Column(INET)
    mac_address = Column(String(17))
    interface_name = Column(String(100))
    vlan_id = Column(Integer)
    subnet = Column(String(50))
    
    # Physical properties
    vendor = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    
    # Location and positioning
    site = Column(String(100))
    building = Column(String(100))
    floor = Column(String(50))
    rack = Column(String(50))
    position_x = Column(Float)  # For topology visualization
    position_y = Column(Float)
    position_z = Column(Float)
    
    # Status and health
    status = Column(String(50), default="unknown")
    health_score = Column(Integer)  # 0-100
    last_seen = Column(DateTime(timezone=True))
    
    # Capabilities
    capabilities = Column(ARRAY(String), default=list)
    protocols = Column(ARRAY(String), default=list)
    
    # Metadata
    properties = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    topology = relationship("NetworkTopology", back_populates="nodes")
    device = relationship("Device", back_populates="topology_nodes")
    source_links = relationship("TopologyLink", foreign_keys="TopologyLink.source_node_id", back_populates="source_node")
    target_links = relationship("TopologyLink", foreign_keys="TopologyLink.target_node_id", back_populates="target_node")

    def __repr__(self):
        return f"<TopologyNode(name='{self.name}', type='{self.node_type}')>"


class TopologyLink(Base):
    """Network topology link/connection"""
    __tablename__ = "topology_links"

    id = Column(Integer, primary_key=True, index=True)
    topology_id = Column(Integer, ForeignKey("network_topologies.id"), nullable=False)
    
    # Link endpoints
    source_node_id = Column(Integer, ForeignKey("topology_nodes.id"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("topology_nodes.id"), nullable=False)
    
    # Link identification
    link_id = Column(String(255), index=True)  # Unique within topology
    name = Column(String(255))
    
    # Link properties
    link_type = Column(Enum(LinkType), default=LinkType.UNKNOWN)
    status = Column(Enum(LinkStatus), default=LinkStatus.UNKNOWN)
    
    # Interface details
    source_interface = Column(String(100))
    target_interface = Column(String(100))
    source_port = Column(String(50))
    target_port = Column(String(50))
    
    # Physical properties
    medium = Column(String(50))  # copper, fiber, wireless
    speed = Column(String(50))  # 1G, 10G, 100G, etc.
    duplex = Column(String(20))  # full, half
    mtu = Column(Integer)
    
    # Performance metrics
    utilization_in = Column(Float)  # Percentage
    utilization_out = Column(Float)
    latency_ms = Column(Float)
    packet_loss = Column(Float)
    error_rate = Column(Float)
    
    # VLAN and Layer 2
    vlan_id = Column(Integer)
    trunk_vlans = Column(ARRAY(Integer), default=list)
    native_vlan = Column(Integer)
    
    # Layer 3 information
    source_ip = Column(INET)
    target_ip = Column(INET)
    subnet = Column(String(50))
    
    # Discovery information
    discovery_protocol = Column(String(50))  # cdp, lldp, snmp
    discovered_at = Column(DateTime(timezone=True))
    last_verified = Column(DateTime(timezone=True))
    
    # Metadata
    properties = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    topology = relationship("NetworkTopology", back_populates="links")
    source_node = relationship("TopologyNode", foreign_keys=[source_node_id], back_populates="source_links")
    target_node = relationship("TopologyNode", foreign_keys=[target_node_id], back_populates="target_links")

    def __repr__(self):
        return f"<TopologyLink(id={self.id}, type='{self.link_type}', status='{self.status}')>"
