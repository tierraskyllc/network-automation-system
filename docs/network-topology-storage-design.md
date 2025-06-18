# Network Topology Data Storage Implementation
## Comprehensive Design for Hybrid LangGraph/LangChain/MCP System

### Overview

This document details the implementation of comprehensive network topology and configuration data storage that extends our existing PostgreSQL schema to support intelligent network automation with rich topological context.

---

## 1. Database Schema Design

### **Core Topology Tables**

```sql
-- Enhanced device table (extends existing)
ALTER TABLE devices ADD COLUMN IF NOT EXISTS topology_data JSONB;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_topology_scan TIMESTAMP;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS topology_scan_status VARCHAR(20) DEFAULT 'pending';

-- Network interfaces table
CREATE TABLE network_interfaces (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    
    -- Interface identification
    interface_name VARCHAR(100) NOT NULL,
    interface_type VARCHAR(50), -- physical, vlan, loopback, port-channel, etc.
    interface_index INTEGER,
    
    -- Physical properties
    admin_status VARCHAR(20), -- up, down, testing
    oper_status VARCHAR(20),  -- up, down, testing, unknown, dormant
    speed BIGINT,             -- in bps
    duplex VARCHAR(20),       -- full, half, auto
    mtu INTEGER,
    
    -- Layer 2 configuration
    switchport_mode VARCHAR(20), -- access, trunk, dynamic
    access_vlan INTEGER,
    native_vlan INTEGER,
    allowed_vlans TEXT,       -- comma-separated VLAN IDs
    
    -- Layer 3 configuration
    ip_addresses JSONB,       -- array of {ip, prefix_length, type}
    vrf VARCHAR(100),
    
    -- Physical connectivity
    media_type VARCHAR(50),   -- copper, fiber, wireless
    connector_type VARCHAR(50), -- rj45, sfp, sfp+, qsfp
    
    -- Hierarchy relationships
    parent_interface_id INTEGER REFERENCES network_interfaces(id),
    is_subinterface BOOLEAN DEFAULT FALSE,
    subinterface_number INTEGER,
    
    -- Metadata
    description TEXT,
    last_change TIMESTAMP,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(device_id, interface_name)
);

-- VLAN definitions and assignments
CREATE TABLE vlans (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    
    -- VLAN identification
    vlan_id INTEGER NOT NULL,
    vlan_name VARCHAR(100),
    
    -- VLAN properties
    status VARCHAR(20),       -- active, suspend, act/lshut, sus/lshut
    type VARCHAR(50),         -- ethernet, fddi, tokenring, fdnet, trnet
    mtu INTEGER,
    
    -- STP configuration
    stp_mode VARCHAR(20),     -- ieee, rapid-pvst, mst
    stp_priority INTEGER,
    stp_root_bridge BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    description TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(device_id, vlan_id)
);

-- Interface-to-VLAN mappings
CREATE TABLE interface_vlan_mappings (
    id SERIAL PRIMARY KEY,
    interface_id INTEGER REFERENCES network_interfaces(id) ON DELETE CASCADE,
    vlan_id INTEGER REFERENCES vlans(id) ON DELETE CASCADE,
    
    -- Mapping type
    mapping_type VARCHAR(20), -- access, trunk, native
    
    -- Tagging information
    is_tagged BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(interface_id, vlan_id, mapping_type)
);

-- Port channel configurations
CREATE TABLE port_channels (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    
    -- Port channel identification
    channel_group_number INTEGER NOT NULL,
    interface_name VARCHAR(100), -- Port-channel1, Po1, etc.
    
    -- Configuration
    protocol VARCHAR(20),     -- lacp, pagp, static
    mode VARCHAR(20),         -- active, passive, on, desirable, auto
    
    -- Load balancing
    load_balance_method VARCHAR(50), -- src-dst-ip, src-dst-mac, etc.
    
    -- Status
    admin_status VARCHAR(20),
    oper_status VARCHAR(20),
    
    -- Metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(device_id, channel_group_number)
);

-- Port channel member interfaces
CREATE TABLE port_channel_members (
    id SERIAL PRIMARY KEY,
    port_channel_id INTEGER REFERENCES port_channels(id) ON DELETE CASCADE,
    interface_id INTEGER REFERENCES network_interfaces(id) ON DELETE CASCADE,
    
    -- Member configuration
    member_status VARCHAR(20), -- bundled, suspended, hot-standby, individual
    priority INTEGER,
    
    -- Statistics
    selected BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(port_channel_id, interface_id)
);

-- CDP/LLDP neighbor discovery
CREATE TABLE neighbor_relationships (
    id SERIAL PRIMARY KEY,
    
    -- Local device and interface
    local_device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    local_interface_id INTEGER REFERENCES network_interfaces(id) ON DELETE CASCADE,
    
    -- Remote device information
    remote_device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    remote_hostname VARCHAR(255),
    remote_interface_name VARCHAR(100),
    remote_ip_address INET,
    
    -- Discovery protocol
    discovery_protocol VARCHAR(10), -- cdp, lldp
    
    -- Device information
    remote_platform VARCHAR(100),
    remote_software_version VARCHAR(200),
    remote_capabilities TEXT[], -- router, switch, bridge, etc.
    
    -- Physical information
    remote_port_description TEXT,
    
    -- Metadata
    hold_time INTEGER,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(local_device_id, local_interface_id, remote_hostname, remote_interface_name)
);

-- Network topology paths (computed relationships)
CREATE TABLE topology_paths (
    id SERIAL PRIMARY KEY,
    
    -- Path endpoints
    source_device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    destination_device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    
    -- Path information
    path_hops JSONB,          -- array of {device_id, interface_id, next_hop}
    path_length INTEGER,
    path_type VARCHAR(20),    -- direct, multi-hop, redundant
    
    -- Path metrics
    total_bandwidth BIGINT,   -- minimum bandwidth along path
    path_latency FLOAT,       -- estimated latency
    
    -- Redundancy information
    primary_path BOOLEAN DEFAULT FALSE,
    backup_paths JSONB,       -- array of alternative path IDs
    
    -- Metadata
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE,
    
    UNIQUE(source_device_id, destination_device_id, path_type)
);

-- Uplink interface identification
CREATE TABLE uplink_interfaces (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    interface_id INTEGER REFERENCES network_interfaces(id) ON DELETE CASCADE,
    
    -- Uplink classification
    uplink_type VARCHAR(20),  -- primary, secondary, backup
    uplink_role VARCHAR(20),  -- distribution, core, wan, internet
    
    -- Redundancy configuration
    redundancy_group INTEGER,
    priority INTEGER,
    
    -- Load balancing
    load_share_percentage FLOAT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(device_id, interface_id)
);

-- SVI (Switched Virtual Interface) configurations
CREATE TABLE svi_interfaces (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    vlan_id INTEGER REFERENCES vlans(id) ON DELETE CASCADE,
    interface_id INTEGER REFERENCES network_interfaces(id) ON DELETE CASCADE,
    
    -- SVI configuration
    is_gateway BOOLEAN DEFAULT FALSE,
    hsrp_group INTEGER,
    hsrp_priority INTEGER,
    hsrp_virtual_ip INET,
    
    -- DHCP configuration
    dhcp_helper_addresses INET[],
    
    -- Metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(device_id, vlan_id)
);
```

### **Indexes for Performance**

```sql
-- Performance indexes for topology queries
CREATE INDEX idx_interfaces_device_type ON network_interfaces(device_id, interface_type);
CREATE INDEX idx_interfaces_status ON network_interfaces(admin_status, oper_status);
CREATE INDEX idx_vlans_device_vlan ON vlans(device_id, vlan_id);
CREATE INDEX idx_neighbors_local_device ON neighbor_relationships(local_device_id, is_active);
CREATE INDEX idx_neighbors_remote_device ON neighbor_relationships(remote_device_id, is_active);
CREATE INDEX idx_topology_paths_endpoints ON topology_paths(source_device_id, destination_device_id);
CREATE INDEX idx_port_channel_members_channel ON port_channel_members(port_channel_id);
CREATE INDEX idx_interface_vlan_mappings_interface ON interface_vlan_mappings(interface_id);
CREATE INDEX idx_interface_vlan_mappings_vlan ON interface_vlan_mappings(vlan_id);

-- GIN indexes for JSONB columns
CREATE INDEX idx_devices_topology_data ON devices USING GIN(topology_data);
CREATE INDEX idx_interfaces_ip_addresses ON network_interfaces USING GIN(ip_addresses);
CREATE INDEX idx_topology_paths_hops ON topology_paths USING GIN(path_hops);
```

### **Database Views for Common Queries**

```sql
-- View: Complete interface information with VLAN mappings
CREATE VIEW interface_complete_view AS
SELECT 
    ni.id,
    ni.device_id,
    d.hostname as device_hostname,
    ni.interface_name,
    ni.interface_type,
    ni.admin_status,
    ni.oper_status,
    ni.speed,
    ni.switchport_mode,
    ni.access_vlan,
    ni.native_vlan,
    ni.allowed_vlans,
    ni.ip_addresses,
    ni.description,
    -- Aggregated VLAN information
    COALESCE(
        json_agg(
            json_build_object(
                'vlan_id', v.vlan_id,
                'vlan_name', v.vlan_name,
                'mapping_type', ivm.mapping_type,
                'is_tagged', ivm.is_tagged
            )
        ) FILTER (WHERE v.id IS NOT NULL), 
        '[]'::json
    ) as vlan_mappings,
    -- Port channel information
    pc.channel_group_number,
    pc.protocol as pc_protocol,
    pc.mode as pc_mode
FROM network_interfaces ni
JOIN devices d ON ni.device_id = d.id
LEFT JOIN interface_vlan_mappings ivm ON ni.id = ivm.interface_id
LEFT JOIN vlans v ON ivm.vlan_id = v.id
LEFT JOIN port_channel_members pcm ON ni.id = pcm.interface_id
LEFT JOIN port_channels pc ON pcm.port_channel_id = pc.id
GROUP BY ni.id, d.hostname, pc.channel_group_number, pc.protocol, pc.mode;

-- View: Device connectivity matrix
CREATE VIEW device_connectivity_view AS
SELECT 
    ld.hostname as local_device,
    rd.hostname as remote_device,
    nr.local_interface_id,
    li.interface_name as local_interface,
    nr.remote_interface_name,
    nr.discovery_protocol,
    nr.remote_platform,
    nr.last_seen,
    nr.is_active
FROM neighbor_relationships nr
JOIN devices ld ON nr.local_device_id = ld.id
LEFT JOIN devices rd ON nr.remote_device_id = rd.id
JOIN network_interfaces li ON nr.local_interface_id = li.id
WHERE nr.is_active = true;

-- View: VLAN spanning information
CREATE VIEW vlan_spanning_view AS
SELECT 
    v.vlan_id,
    v.vlan_name,
    COUNT(DISTINCT v.device_id) as device_count,
    array_agg(DISTINCT d.hostname) as devices,
    COUNT(DISTINCT ivm.interface_id) as interface_count
FROM vlans v
JOIN devices d ON v.device_id = d.id
LEFT JOIN interface_vlan_mappings ivm ON v.id = ivm.vlan_id
WHERE v.status = 'active'
GROUP BY v.vlan_id, v.vlan_name
HAVING COUNT(DISTINCT v.device_id) > 1;
```

---

## 2. Data Collection Integration

### **pyATS/Genie Parser Integration**

#### **Topology Discovery Service**

```python
# src/topology/discovery_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
import logging

from ..network_layer.connectors.genie_connector import GenieConnector
from ..core.models import Device
from .models import NetworkInterface, VLAN, NeighborRelationship, PortChannel
from .parsers import TopologyParserManager

logger = logging.getLogger(__name__)

class TopologyDiscoveryService:
    """Service for discovering and updating network topology"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.parser_manager = TopologyParserManager()
        self.discovery_commands = {
            'cisco_ios': [
                'show interfaces',
                'show interfaces status',
                'show vlan brief',
                'show cdp neighbors detail',
                'show etherchannel summary',
                'show ip interface brief'
            ],
            'cisco_nxos': [
                'show interface',
                'show interface status',
                'show vlan brief',
                'show cdp neighbors detail',
                'show port-channel summary',
                'show ip interface brief'
            ],
            'cisco_iosxe': [
                'show interfaces',
                'show interfaces status',
                'show vlan brief',
                'show cdp neighbors detail',
                'show etherchannel summary',
                'show ip interface brief'
            ],
            'arista_eos': [
                'show interfaces',
                'show interfaces status',
                'show vlan brief',
                'show lldp neighbors detail',
                'show port-channel',
                'show ip interface brief'
            ]
        }

    async def discover_device_topology(self, device_id: int,
                                     full_refresh: bool = False) -> Dict[str, Any]:
        """Discover topology for a single device"""

        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise ValueError(f"Device not found: {device_id}")

        logger.info(f"Starting topology discovery for {device.hostname}")

        # Update device status
        device.topology_scan_status = 'running'
        self.db.commit()

        try:
            # Get appropriate commands for device type
            commands = self.discovery_commands.get(device.device_type,
                                                 self.discovery_commands['cisco_ios'])

            # Execute discovery commands
            connector = GenieConnector(device.to_dict())
            await connector.connect()

            discovery_data = {}
            for command in commands:
                try:
                    result = await connector.execute_command(command)
                    if result.success:
                        discovery_data[command] = {
                            'raw_output': result.output.get('raw', ''),
                            'parsed_output': result.output.get('parsed', {}),
                            'parser_used': result.output.get('parser_used', '')
                        }
                        logger.debug(f"Successfully executed {command} on {device.hostname}")
                    else:
                        logger.warning(f"Failed to execute {command} on {device.hostname}: {result.error}")
                except Exception as e:
                    logger.error(f"Error executing {command} on {device.hostname}: {e}")

            await connector.disconnect()

            # Process discovery data
            topology_result = await self._process_discovery_data(
                device, discovery_data, full_refresh
            )

            # Update device status
            device.topology_scan_status = 'completed'
            device.last_topology_scan = datetime.now()
            device.topology_data = topology_result.get('summary', {})
            self.db.commit()

            logger.info(f"Completed topology discovery for {device.hostname}")
            return topology_result

        except Exception as e:
            device.topology_scan_status = 'failed'
            self.db.commit()
            logger.error(f"Topology discovery failed for {device.hostname}: {e}")
            raise

    async def _process_discovery_data(self, device: Device,
                                    discovery_data: Dict[str, Any],
                                    full_refresh: bool) -> Dict[str, Any]:
        """Process raw discovery data and update database"""

        result = {
            'interfaces_updated': 0,
            'vlans_updated': 0,
            'neighbors_updated': 0,
            'port_channels_updated': 0,
            'summary': {}
        }

        # Process interfaces
        if 'show interfaces' in discovery_data:
            interfaces_result = await self._process_interfaces(
                device, discovery_data['show interfaces'], full_refresh
            )
            result['interfaces_updated'] = interfaces_result['updated_count']

        # Process interface status
        if 'show interfaces status' in discovery_data:
            await self._process_interface_status(
                device, discovery_data['show interfaces status']
            )

        # Process VLANs
        if 'show vlan brief' in discovery_data:
            vlans_result = await self._process_vlans(
                device, discovery_data['show vlan brief'], full_refresh
            )
            result['vlans_updated'] = vlans_result['updated_count']

        # Process CDP/LLDP neighbors
        cdp_command = 'show cdp neighbors detail'
        lldp_command = 'show lldp neighbors detail'

        if cdp_command in discovery_data:
            neighbors_result = await self._process_neighbors(
                device, discovery_data[cdp_command], 'cdp', full_refresh
            )
            result['neighbors_updated'] += neighbors_result['updated_count']

        if lldp_command in discovery_data:
            neighbors_result = await self._process_neighbors(
                device, discovery_data[lldp_command], 'lldp', full_refresh
            )
            result['neighbors_updated'] += neighbors_result['updated_count']

        # Process port channels
        etherchannel_commands = ['show etherchannel summary', 'show port-channel summary', 'show port-channel']
        for cmd in etherchannel_commands:
            if cmd in discovery_data:
                pc_result = await self._process_port_channels(
                    device, discovery_data[cmd], full_refresh
                )
                result['port_channels_updated'] = pc_result['updated_count']
                break

        # Generate summary
        result['summary'] = await self._generate_topology_summary(device)

        return result

    async def _process_interfaces(self, device: Device, command_data: Dict[str, Any],
                                full_refresh: bool) -> Dict[str, Any]:
        """Process interface discovery data"""

        parsed_data = command_data.get('parsed_output', {})
        if not parsed_data:
            return {'updated_count': 0}

        updated_count = 0

        # Handle different parser output formats
        interfaces_data = parsed_data.get('interface', {})
        if not interfaces_data:
            # Try alternative parser formats
            interfaces_data = parsed_data.get('interfaces', {})

        for interface_name, interface_info in interfaces_data.items():
            try:
                # Get or create interface
                interface = self.db.query(NetworkInterface).filter(
                    NetworkInterface.device_id == device.id,
                    NetworkInterface.interface_name == interface_name
                ).first()

                if not interface:
                    interface = NetworkInterface(
                        device_id=device.id,
                        interface_name=interface_name
                    )
                    self.db.add(interface)

                # Update interface properties
                interface.interface_type = self._determine_interface_type(interface_name)
                interface.admin_status = interface_info.get('admin_status', 'unknown')
                interface.oper_status = interface_info.get('oper_status', 'unknown')
                interface.description = interface_info.get('description', '')

                # Handle speed (convert to bps)
                speed_str = interface_info.get('bandwidth', '0')
                interface.speed = self._parse_speed(speed_str)

                # Handle duplex
                interface.duplex = interface_info.get('duplex', 'unknown')

                # Handle MTU
                interface.mtu = interface_info.get('mtu', 1500)

                # Process IP addresses
                ip_addresses = []
                ipv4_data = interface_info.get('ipv4', {})
                for ip, ip_info in ipv4_data.items():
                    if ip != 'unnumbered':
                        ip_addresses.append({
                            'ip': ip,
                            'prefix_length': ip_info.get('prefix_length', 24),
                            'type': 'ipv4'
                        })

                ipv6_data = interface_info.get('ipv6', {})
                for ip, ip_info in ipv6_data.items():
                    ip_addresses.append({
                        'ip': ip,
                        'prefix_length': ip_info.get('prefix_length', 64),
                        'type': 'ipv6'
                    })

                interface.ip_addresses = ip_addresses

                # Handle switchport configuration
                switchport_info = interface_info.get('switchport', {})
                if switchport_info:
                    interface.switchport_mode = switchport_info.get('mode', 'unknown')
                    interface.access_vlan = switchport_info.get('access_vlan')
                    interface.native_vlan = switchport_info.get('native_vlan')

                    # Handle allowed VLANs
                    allowed_vlans = switchport_info.get('trunk_vlans', [])
                    if allowed_vlans:
                        interface.allowed_vlans = ','.join(map(str, allowed_vlans))

                interface.updated_at = datetime.now()
                updated_count += 1

            except Exception as e:
                logger.error(f"Error processing interface {interface_name} on {device.hostname}: {e}")

        self.db.commit()
        return {'updated_count': updated_count}

    async def _process_vlans(self, device: Device, command_data: Dict[str, Any],
                           full_refresh: bool) -> Dict[str, Any]:
        """Process VLAN discovery data"""

        parsed_data = command_data.get('parsed_output', {})
        if not parsed_data:
            return {'updated_count': 0}

        updated_count = 0

        # Handle different VLAN parser formats
        vlans_data = parsed_data.get('vlans', {})

        for vlan_id_str, vlan_info in vlans_data.items():
            try:
                vlan_id = int(vlan_id_str)

                # Get or create VLAN
                vlan = self.db.query(VLAN).filter(
                    VLAN.device_id == device.id,
                    VLAN.vlan_id == vlan_id
                ).first()

                if not vlan:
                    vlan = VLAN(
                        device_id=device.id,
                        vlan_id=vlan_id
                    )
                    self.db.add(vlan)

                # Update VLAN properties
                vlan.vlan_name = vlan_info.get('name', f'VLAN{vlan_id:04d}')
                vlan.status = vlan_info.get('status', 'unknown')
                vlan.type = vlan_info.get('type', 'ethernet')
                vlan.mtu = vlan_info.get('mtu', 1500)

                # Process interfaces assigned to this VLAN
                interfaces = vlan_info.get('interfaces', [])
                await self._update_vlan_interface_mappings(device, vlan, interfaces)

                vlan.updated_at = datetime.now()
                updated_count += 1

            except Exception as e:
                logger.error(f"Error processing VLAN {vlan_id_str} on {device.hostname}: {e}")

        self.db.commit()
        return {'updated_count': updated_count}

    def _determine_interface_type(self, interface_name: str) -> str:
        """Determine interface type from name"""

        name_lower = interface_name.lower()

        if 'loopback' in name_lower:
            return 'loopback'
        elif 'vlan' in name_lower:
            return 'vlan'
        elif 'port-channel' in name_lower or 'po' == name_lower[:2]:
            return 'port-channel'
        elif 'tunnel' in name_lower:
            return 'tunnel'
        elif any(x in name_lower for x in ['ethernet', 'gigabit', 'tengigabit', 'fastethernet']):
            return 'physical'
        elif '.' in interface_name:
            return 'subinterface'
        else:
            return 'unknown'

    def _parse_speed(self, speed_str: str) -> int:
        """Parse speed string to bps"""

        if not speed_str or speed_str == 'unknown':
            return 0

        # Remove non-numeric characters except for unit indicators
        import re
        speed_match = re.search(r'(\d+)\s*([kmgt]?)(bps|bit)?', speed_str.lower())

        if not speed_match:
            return 0

        value = int(speed_match.group(1))
        unit = speed_match.group(2)

        multipliers = {
            '': 1,
            'k': 1000,
            'm': 1000000,
            'g': 1000000000,
            't': 1000000000000
        }

        return value * multipliers.get(unit, 1)
```

### **Incremental vs Full Refresh Strategy**

```python
# src/topology/refresh_strategy.py
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

class TopologyRefreshStrategy:
    """Manage incremental vs full topology refresh decisions"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.full_refresh_interval = timedelta(hours=24)
        self.incremental_refresh_interval = timedelta(minutes=15)
        self.change_threshold = 0.1  # 10% change triggers full refresh

    async def should_perform_full_refresh(self, device_id: int) -> bool:
        """Determine if full refresh is needed"""

        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return True

        # Force full refresh if never scanned
        if not device.last_topology_scan:
            return True

        # Force full refresh if last scan was too long ago
        if datetime.now() - device.last_topology_scan > self.full_refresh_interval:
            return True

        # Check for significant changes in recent incremental scans
        recent_changes = await self._analyze_recent_changes(device_id)
        if recent_changes['change_percentage'] > self.change_threshold:
            return True

        return False

    async def _analyze_recent_changes(self, device_id: int) -> Dict[str, Any]:
        """Analyze recent topology changes"""

        # Get recent interface changes
        recent_interface_changes = self.db.query(NetworkInterface).filter(
            NetworkInterface.device_id == device_id,
            NetworkInterface.updated_at > datetime.now() - timedelta(hours=6)
        ).count()

        # Get total interfaces
        total_interfaces = self.db.query(NetworkInterface).filter(
            NetworkInterface.device_id == device_id
        ).count()

        change_percentage = (recent_interface_changes / max(total_interfaces, 1)) if total_interfaces > 0 else 0

        return {
            'recent_changes': recent_interface_changes,
            'total_interfaces': total_interfaces,
            'change_percentage': change_percentage
        }

---

## 3. MCP Context Enhancement

### **Topology-Aware MCP Tools**

```python
# src/mcp_server/topology_tools.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..topology.models import NetworkInterface, VLAN, NeighborRelationship, PortChannel
from ..topology.query_service import TopologyQueryService

router = APIRouter(prefix="/mcp/tools/topology", tags=["MCP Topology Tools"])

class TopologyContextRequest(BaseModel):
    device_id: Optional[str] = None
    hostname: Optional[str] = None
    include_neighbors: bool = True
    include_vlans: bool = True
    include_interfaces: bool = True
    include_port_channels: bool = True

class TopologyContextResponse(BaseModel):
    device_id: str
    hostname: str
    topology_summary: Dict[str, Any]
    interfaces: List[Dict[str, Any]]
    vlans: List[Dict[str, Any]]
    neighbors: List[Dict[str, Any]]
    port_channels: List[Dict[str, Any]]
    uplinks: List[Dict[str, Any]]

@router.post("/get_topology_context", response_model=TopologyContextResponse)
async def get_topology_context(
    request: TopologyContextRequest,
    db: Session = Depends(get_db)
) -> TopologyContextResponse:
    """
    MCP Tool: Get comprehensive topology context for a device
    Used by LangChain to understand network topology before command interpretation
    """

    # Find device
    from ..core.models import Device
    query = db.query(Device)
    if request.device_id:
        device = query.filter(Device.id == int(request.device_id)).first()
    elif request.hostname:
        device = query.filter(Device.hostname == request.hostname).first()
    else:
        raise HTTPException(status_code=400, detail="Must provide device_id or hostname")

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    topology_service = TopologyQueryService(db)

    # Get topology summary
    topology_summary = await topology_service.get_device_topology_summary(device.id)

    # Get interfaces if requested
    interfaces = []
    if request.include_interfaces:
        interfaces_data = await topology_service.get_device_interfaces(device.id)
        interfaces = [
            {
                "interface_name": intf.interface_name,
                "interface_type": intf.interface_type,
                "admin_status": intf.admin_status,
                "oper_status": intf.oper_status,
                "speed": intf.speed,
                "switchport_mode": intf.switchport_mode,
                "access_vlan": intf.access_vlan,
                "native_vlan": intf.native_vlan,
                "allowed_vlans": intf.allowed_vlans,
                "ip_addresses": intf.ip_addresses,
                "description": intf.description
            }
            for intf in interfaces_data
        ]

    # Get VLANs if requested
    vlans = []
    if request.include_vlans:
        vlans_data = await topology_service.get_device_vlans(device.id)
        vlans = [
            {
                "vlan_id": vlan.vlan_id,
                "vlan_name": vlan.vlan_name,
                "status": vlan.status,
                "type": vlan.type,
                "interface_count": len(vlan.interfaces) if hasattr(vlan, 'interfaces') else 0
            }
            for vlan in vlans_data
        ]

    # Get neighbors if requested
    neighbors = []
    if request.include_neighbors:
        neighbors_data = await topology_service.get_device_neighbors(device.id)
        neighbors = [
            {
                "local_interface": neighbor.local_interface.interface_name,
                "remote_hostname": neighbor.remote_hostname,
                "remote_interface": neighbor.remote_interface_name,
                "remote_platform": neighbor.remote_platform,
                "discovery_protocol": neighbor.discovery_protocol,
                "last_seen": neighbor.last_seen.isoformat() if neighbor.last_seen else None
            }
            for neighbor in neighbors_data
        ]

    # Get port channels if requested
    port_channels = []
    if request.include_port_channels:
        pc_data = await topology_service.get_device_port_channels(device.id)
        port_channels = [
            {
                "channel_group": pc.channel_group_number,
                "interface_name": pc.interface_name,
                "protocol": pc.protocol,
                "mode": pc.mode,
                "admin_status": pc.admin_status,
                "oper_status": pc.oper_status,
                "member_count": len(pc.members) if hasattr(pc, 'members') else 0
            }
            for pc in pc_data
        ]

    # Get uplinks
    uplinks_data = await topology_service.get_device_uplinks(device.id)
    uplinks = [
        {
            "interface_name": uplink.interface.interface_name,
            "uplink_type": uplink.uplink_type,
            "uplink_role": uplink.uplink_role,
            "is_active": uplink.is_active,
            "redundancy_group": uplink.redundancy_group
        }
        for uplink in uplinks_data
    ]

    return TopologyContextResponse(
        device_id=str(device.id),
        hostname=device.hostname,
        topology_summary=topology_summary,
        interfaces=interfaces,
        vlans=vlans,
        neighbors=neighbors,
        port_channels=port_channels,
        uplinks=uplinks
    )

@router.get("/find_vlan_devices/{vlan_id}")
async def find_vlan_devices(
    vlan_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    MCP Tool: Find all devices that have a specific VLAN
    Used by LangChain for VLAN-spanning queries
    """

    topology_service = TopologyQueryService(db)
    vlan_devices = await topology_service.find_devices_with_vlan(vlan_id)

    devices_info = []
    for device, vlan_info in vlan_devices:
        devices_info.append({
            "device_id": device.id,
            "hostname": device.hostname,
            "device_type": device.device_type,
            "vlan_name": vlan_info.vlan_name,
            "vlan_status": vlan_info.status,
            "interface_count": await topology_service.count_vlan_interfaces(device.id, vlan_id)
        })

    return {
        "vlan_id": vlan_id,
        "device_count": len(devices_info),
        "devices": devices_info,
        "spanning_multiple_devices": len(devices_info) > 1
    }

@router.post("/find_network_path")
async def find_network_path(
    source_device_id: str,
    destination_device_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    MCP Tool: Find network path between two devices
    Used by LangGraph for path analysis and troubleshooting
    """

    topology_service = TopologyQueryService(db)

    # Find direct and multi-hop paths
    paths = await topology_service.find_paths_between_devices(
        int(source_device_id),
        int(destination_device_id)
    )

    if not paths:
        return {
            "source_device_id": source_device_id,
            "destination_device_id": destination_device_id,
            "paths_found": 0,
            "paths": [],
            "reachable": False
        }

    formatted_paths = []
    for path in paths:
        path_hops = []
        for hop in path.path_hops:
            hop_device = db.query(Device).filter(Device.id == hop['device_id']).first()
            hop_interface = db.query(NetworkInterface).filter(
                NetworkInterface.id == hop['interface_id']
            ).first()

            path_hops.append({
                "device_hostname": hop_device.hostname if hop_device else "unknown",
                "interface_name": hop_interface.interface_name if hop_interface else "unknown",
                "next_hop": hop.get('next_hop')
            })

        formatted_paths.append({
            "path_id": path.id,
            "path_type": path.path_type,
            "path_length": path.path_length,
            "total_bandwidth": path.total_bandwidth,
            "path_latency": path.path_latency,
            "is_primary": path.primary_path,
            "hops": path_hops
        })

    return {
        "source_device_id": source_device_id,
        "destination_device_id": destination_device_id,
        "paths_found": len(formatted_paths),
        "paths": formatted_paths,
        "reachable": True
    }

@router.get("/analyze_port_channel/{device_id}/{channel_group}")
async def analyze_port_channel(
    device_id: str,
    channel_group: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    MCP Tool: Analyze port channel configuration and status
    Used by LangChain for port channel troubleshooting
    """

    topology_service = TopologyQueryService(db)
    pc_analysis = await topology_service.analyze_port_channel(
        int(device_id), channel_group
    )

    if not pc_analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Port channel {channel_group} not found on device {device_id}"
        )

    return pc_analysis

@router.post("/get_interface_neighbors")
async def get_interface_neighbors(
    device_id: str,
    interface_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    MCP Tool: Get neighbors connected to specific interface
    Used by LangChain for interface-specific troubleshooting
    """

    # Find interface
    interface = db.query(NetworkInterface).join(Device).filter(
        Device.id == int(device_id),
        NetworkInterface.interface_name == interface_name
    ).first()

    if not interface:
        raise HTTPException(
            status_code=404,
            detail=f"Interface {interface_name} not found on device {device_id}"
        )

    # Get neighbors
    neighbors = db.query(NeighborRelationship).filter(
        NeighborRelationship.local_interface_id == interface.id,
        NeighborRelationship.is_active == True
    ).all()

    neighbor_info = []
    for neighbor in neighbors:
        neighbor_info.append({
            "remote_hostname": neighbor.remote_hostname,
            "remote_interface": neighbor.remote_interface_name,
            "remote_ip": str(neighbor.remote_ip_address) if neighbor.remote_ip_address else None,
            "discovery_protocol": neighbor.discovery_protocol,
            "remote_platform": neighbor.remote_platform,
            "remote_capabilities": neighbor.remote_capabilities,
            "last_seen": neighbor.last_seen.isoformat() if neighbor.last_seen else None
        })

    return {
        "device_id": device_id,
        "interface_name": interface_name,
        "interface_status": {
            "admin_status": interface.admin_status,
            "oper_status": interface.oper_status,
            "speed": interface.speed,
            "duplex": interface.duplex
        },
        "neighbor_count": len(neighbor_info),
        "neighbors": neighbor_info
    }
```

### **Enhanced LangChain Integration with Topology Context**

```python
# src/langchain_layer/topology_enhanced_processor.py
from typing import Dict, Any, List, Optional
import json

class TopologyEnhancedLangChainProcessor:
    """LangChain processor enhanced with topology context"""

    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.llm = OpenAI(temperature=0.1)

    async def process_with_topology_context(self, user_input: str,
                                          device_hint: Optional[str] = None) -> Dict[str, Any]:
        """Process user input with comprehensive topology context"""

        # Get topology context if device is specified
        topology_context = {}
        if device_hint:
            try:
                topology_context = await self.mcp_client.call_tool(
                    "get_topology_context",
                    {
                        "hostname": device_hint,
                        "include_neighbors": True,
                        "include_vlans": True,
                        "include_interfaces": True,
                        "include_port_channels": True
                    }
                )
            except Exception as e:
                print(f"Warning: Could not get topology context: {e}")

        # Analyze user intent for topology-related queries
        intent_analysis = await self._analyze_topology_intent(user_input, topology_context)

        # Create topology-aware prompt
        prompt = self._create_topology_aware_prompt(user_input, topology_context, intent_analysis)

        # Process with LLM
        result = await self.llm.arun(prompt)
        parsed_result = json.loads(result)

        # Enhance result with topology validation
        if topology_context:
            validation = await self._validate_with_topology(parsed_result, topology_context)
            parsed_result['topology_validation'] = validation

        return parsed_result

    async def _analyze_topology_intent(self, user_input: str,
                                     topology_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if user input requires topology-aware processing"""

        topology_keywords = {
            'vlan_queries': ['vlan', 'vlan id', 'layer 2', 'switching'],
            'interface_queries': ['interface', 'port', 'link', 'connection'],
            'neighbor_queries': ['neighbor', 'connected', 'cdp', 'lldp', 'adjacent'],
            'path_queries': ['path', 'route', 'connectivity', 'reachable'],
            'port_channel_queries': ['port-channel', 'etherchannel', 'lag', 'bundle'],
            'uplink_queries': ['uplink', 'trunk', 'distribution', 'core']
        }

        detected_intents = []
        user_input_lower = user_input.lower()

        for intent_type, keywords in topology_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                detected_intents.append(intent_type)

        return {
            'requires_topology': len(detected_intents) > 0,
            'detected_intents': detected_intents,
            'complexity': 'high' if len(detected_intents) > 2 else 'medium' if detected_intents else 'low'
        }

    def _create_topology_aware_prompt(self, user_input: str,
                                    topology_context: Dict[str, Any],
                                    intent_analysis: Dict[str, Any]) -> str:
        """Create prompt enhanced with topology context"""

        prompt = f"""
        You are a network automation expert with access to comprehensive topology information.

        User Request: {user_input}

        Topology Context Available: {bool(topology_context)}
        """

        if topology_context:
            prompt += f"""

        Device Information:
        - Hostname: {topology_context.get('hostname')}
        - Interface Count: {len(topology_context.get('interfaces', []))}
        - VLAN Count: {len(topology_context.get('vlans', []))}
        - Neighbor Count: {len(topology_context.get('neighbors', []))}
        - Port Channel Count: {len(topology_context.get('port_channels', []))}
        - Uplink Count: {len(topology_context.get('uplinks', []))}

        Topology Summary: {topology_context.get('topology_summary', {})}
        """

        if intent_analysis['requires_topology']:
            prompt += f"""

        Detected Topology Intents: {intent_analysis['detected_intents']}

        Available Topology Data:
        - Interfaces: {[intf['interface_name'] for intf in topology_context.get('interfaces', [])[:10]]}
        - VLANs: {[f"VLAN {vlan['vlan_id']} ({vlan['vlan_name']})" for vlan in topology_context.get('vlans', [])[:10]]}
        - Neighbors: {[f"{neighbor['remote_hostname']} via {neighbor['local_interface']}" for neighbor in topology_context.get('neighbors', [])[:5]]}
        """

        prompt += """

        Based on the user request and available topology context, determine:
        1. The appropriate command(s) to execute
        2. Target device(s) and interfaces
        3. Required parameters
        4. Whether this requires topology-aware processing
        5. If multiple devices need to be queried for complete answer

        Respond in JSON format with:
        {
            "command_name": "specific_command",
            "device_id": "target_device_id",
            "parameters": {"param1": "value1"},
            "requires_topology": true/false,
            "multi_device_query": true/false,
            "topology_scope": "single_device|vlan_spanning|network_wide",
            "reasoning": "explanation of the interpretation"
        }
        """

        return prompt

    async def _validate_with_topology(self, parsed_result: Dict[str, Any],
                                    topology_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parsed result against topology context"""

        validation = {
            'valid': True,
            'warnings': [],
            'suggestions': []
        }

        # Validate interface references
        if 'parameters' in parsed_result:
            interface_param = parsed_result['parameters'].get('interface')
            if interface_param:
                available_interfaces = [intf['interface_name'] for intf in topology_context.get('interfaces', [])]
                if interface_param not in available_interfaces:
                    validation['warnings'].append(f"Interface {interface_param} not found on device")
                    validation['suggestions'].append(f"Available interfaces: {', '.join(available_interfaces[:5])}")

        # Validate VLAN references
        vlan_param = parsed_result.get('parameters', {}).get('vlan_id')
        if vlan_param:
            available_vlans = [vlan['vlan_id'] for vlan in topology_context.get('vlans', [])]
            if int(vlan_param) not in available_vlans:
                validation['warnings'].append(f"VLAN {vlan_param} not configured on device")
                validation['suggestions'].append(f"Available VLANs: {', '.join(map(str, available_vlans[:10]))}")

        return validation

---

## 4. Data Relationships and Queries

### **Complex Topology Query Service**

```python
# src/topology/query_service.py
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
import networkx as nx
from datetime import datetime, timedelta

from .models import (
    NetworkInterface, VLAN, NeighborRelationship, PortChannel,
    PortChannelMember, TopologyPath, UplinkInterface
)
from ..core.models import Device

class TopologyQueryService:
    """Advanced topology querying and analysis service"""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def find_devices_with_vlan(self, vlan_id: int) -> List[Tuple[Device, VLAN]]:
        """Find all devices that have a specific VLAN configured"""

        results = self.db.query(Device, VLAN).join(
            VLAN, Device.id == VLAN.device_id
        ).filter(
            VLAN.vlan_id == vlan_id,
            VLAN.status == 'active'
        ).all()

        return results

    async def find_vlan_spanning_devices(self, vlan_id: int) -> Dict[str, Any]:
        """Analyze VLAN spanning across multiple devices"""

        devices_with_vlan = await self.find_devices_with_vlan(vlan_id)

        if len(devices_with_vlan) <= 1:
            return {
                'vlan_id': vlan_id,
                'spans_devices': False,
                'device_count': len(devices_with_vlan),
                'devices': []
            }

        spanning_info = []
        for device, vlan in devices_with_vlan:
            # Get interfaces for this VLAN on this device
            interfaces = self.db.query(NetworkInterface).join(
                InterfaceVlanMapping, NetworkInterface.id == InterfaceVlanMapping.interface_id
            ).join(
                VLAN, InterfaceVlanMapping.vlan_id == VLAN.id
            ).filter(
                VLAN.device_id == device.id,
                VLAN.vlan_id == vlan_id
            ).all()

            # Categorize interfaces
            access_interfaces = [intf for intf in interfaces if intf.switchport_mode == 'access']
            trunk_interfaces = [intf for intf in interfaces if intf.switchport_mode == 'trunk']

            spanning_info.append({
                'device_id': device.id,
                'hostname': device.hostname,
                'vlan_name': vlan.vlan_name,
                'vlan_status': vlan.status,
                'total_interfaces': len(interfaces),
                'access_interfaces': len(access_interfaces),
                'trunk_interfaces': len(trunk_interfaces),
                'interface_details': [
                    {
                        'name': intf.interface_name,
                        'type': intf.switchport_mode,
                        'status': intf.oper_status
                    }
                    for intf in interfaces
                ]
            })

        return {
            'vlan_id': vlan_id,
            'spans_devices': True,
            'device_count': len(devices_with_vlan),
            'devices': spanning_info,
            'trunk_connections': await self._find_vlan_trunk_connections(vlan_id)
        }

    async def _find_vlan_trunk_connections(self, vlan_id: int) -> List[Dict[str, Any]]:
        """Find trunk connections carrying a specific VLAN"""

        # Find trunk interfaces carrying this VLAN
        trunk_interfaces = self.db.query(NetworkInterface).filter(
            NetworkInterface.switchport_mode == 'trunk',
            or_(
                NetworkInterface.allowed_vlans.contains(str(vlan_id)),
                NetworkInterface.native_vlan == vlan_id
            )
        ).all()

        trunk_connections = []
        for trunk_intf in trunk_interfaces:
            # Find neighbors on this trunk interface
            neighbors = self.db.query(NeighborRelationship).filter(
                NeighborRelationship.local_interface_id == trunk_intf.id,
                NeighborRelationship.is_active == True
            ).all()

            for neighbor in neighbors:
                trunk_connections.append({
                    'local_device_id': trunk_intf.device_id,
                    'local_interface': trunk_intf.interface_name,
                    'remote_hostname': neighbor.remote_hostname,
                    'remote_interface': neighbor.remote_interface_name,
                    'vlan_type': 'native' if trunk_intf.native_vlan == vlan_id else 'tagged'
                })

        return trunk_connections

    async def find_paths_between_devices(self, source_device_id: int,
                                       destination_device_id: int) -> List[TopologyPath]:
        """Find network paths between two devices using graph analysis"""

        # Check if path already computed and cached
        existing_paths = self.db.query(TopologyPath).filter(
            TopologyPath.source_device_id == source_device_id,
            TopologyPath.destination_device_id == destination_device_id,
            TopologyPath.is_valid == True
        ).all()

        # If paths exist and are recent, return them
        if existing_paths:
            recent_threshold = datetime.now() - timedelta(hours=1)
            if all(path.computed_at > recent_threshold for path in existing_paths):
                return existing_paths

        # Build network graph from neighbor relationships
        network_graph = await self._build_network_graph()

        # Find paths using NetworkX
        try:
            # Convert device IDs to strings for NetworkX
            source_str = str(source_device_id)
            dest_str = str(destination_device_id)

            # Find all simple paths (no cycles)
            all_paths = list(nx.all_simple_paths(
                network_graph,
                source_str,
                dest_str,
                cutoff=5  # Maximum 5 hops
            ))

            # Convert paths back to database objects and store
            topology_paths = []
            for i, path_nodes in enumerate(all_paths):
                path_hops = []
                total_bandwidth = float('inf')

                for j in range(len(path_nodes) - 1):
                    current_device_id = int(path_nodes[j])
                    next_device_id = int(path_nodes[j + 1])

                    # Find the interface connecting these devices
                    connection_info = await self._find_connection_interface(
                        current_device_id, next_device_id
                    )

                    if connection_info:
                        path_hops.append({
                            'device_id': current_device_id,
                            'interface_id': connection_info['interface_id'],
                            'next_hop': next_device_id
                        })

                        # Track minimum bandwidth
                        if connection_info['bandwidth'] < total_bandwidth:
                            total_bandwidth = connection_info['bandwidth']

                # Create or update topology path
                topology_path = TopologyPath(
                    source_device_id=source_device_id,
                    destination_device_id=destination_device_id,
                    path_hops=path_hops,
                    path_length=len(path_nodes) - 1,
                    path_type='direct' if len(path_nodes) == 2 else 'multi-hop',
                    total_bandwidth=total_bandwidth if total_bandwidth != float('inf') else 0,
                    primary_path=(i == 0),  # First path is primary
                    computed_at=datetime.now(),
                    is_valid=True
                )

                self.db.add(topology_path)
                topology_paths.append(topology_path)

            self.db.commit()
            return topology_paths

        except nx.NetworkXNoPath:
            return []

    async def _build_network_graph(self) -> nx.Graph:
        """Build NetworkX graph from neighbor relationships"""

        graph = nx.Graph()

        # Add all devices as nodes
        devices = self.db.query(Device).all()
        for device in devices:
            graph.add_node(str(device.id), hostname=device.hostname)

        # Add edges from neighbor relationships
        neighbors = self.db.query(NeighborRelationship).filter(
            NeighborRelationship.is_active == True,
            NeighborRelationship.remote_device_id.isnot(None)
        ).all()

        for neighbor in neighbors:
            # Get interface bandwidth for edge weight
            interface = self.db.query(NetworkInterface).filter(
                NetworkInterface.id == neighbor.local_interface_id
            ).first()

            bandwidth = interface.speed if interface else 1000000000  # Default 1Gbps

            graph.add_edge(
                str(neighbor.local_device_id),
                str(neighbor.remote_device_id),
                weight=1.0 / bandwidth,  # Lower weight for higher bandwidth
                bandwidth=bandwidth,
                local_interface=neighbor.local_interface_id,
                remote_interface=neighbor.remote_interface_name
            )

        return graph

    async def _find_connection_interface(self, device1_id: int,
                                       device2_id: int) -> Optional[Dict[str, Any]]:
        """Find interface connecting two devices"""

        neighbor = self.db.query(NeighborRelationship).filter(
            NeighborRelationship.local_device_id == device1_id,
            NeighborRelationship.remote_device_id == device2_id,
            NeighborRelationship.is_active == True
        ).first()

        if not neighbor:
            return None

        interface = self.db.query(NetworkInterface).filter(
            NetworkInterface.id == neighbor.local_interface_id
        ).first()

        return {
            'interface_id': interface.id,
            'interface_name': interface.interface_name,
            'bandwidth': interface.speed or 1000000000
        }

    async def analyze_port_channel(self, device_id: int,
                                 channel_group: int) -> Optional[Dict[str, Any]]:
        """Analyze port channel configuration and health"""

        # Get port channel
        port_channel = self.db.query(PortChannel).filter(
            PortChannel.device_id == device_id,
            PortChannel.channel_group_number == channel_group
        ).first()

        if not port_channel:
            return None

        # Get member interfaces
        members = self.db.query(PortChannelMember).join(
            NetworkInterface, PortChannelMember.interface_id == NetworkInterface.id
        ).filter(
            PortChannelMember.port_channel_id == port_channel.id
        ).all()

        # Analyze member status
        active_members = [m for m in members if m.member_status == 'bundled']
        inactive_members = [m for m in members if m.member_status != 'bundled']

        # Calculate aggregated bandwidth
        total_bandwidth = sum(
            member.interface.speed or 0 for member in active_members
        )

        # Check for load balancing issues
        load_balance_analysis = await self._analyze_load_balancing(port_channel, active_members)

        # Check for redundancy
        redundancy_analysis = {
            'total_members': len(members),
            'active_members': len(active_members),
            'inactive_members': len(inactive_members),
            'redundancy_level': 'high' if len(active_members) > 2 else 'medium' if len(active_members) == 2 else 'low'
        }

        return {
            'port_channel': {
                'channel_group': port_channel.channel_group_number,
                'interface_name': port_channel.interface_name,
                'protocol': port_channel.protocol,
                'mode': port_channel.mode,
                'admin_status': port_channel.admin_status,
                'oper_status': port_channel.oper_status
            },
            'members': [
                {
                    'interface_name': member.interface.interface_name,
                    'status': member.member_status,
                    'speed': member.interface.speed,
                    'selected': member.selected
                }
                for member in members
            ],
            'aggregated_bandwidth': total_bandwidth,
            'load_balancing': load_balance_analysis,
            'redundancy': redundancy_analysis,
            'health_score': self._calculate_port_channel_health(
                port_channel, active_members, inactive_members
            )
        }

    async def _analyze_load_balancing(self, port_channel: PortChannel,
                                    active_members: List[PortChannelMember]) -> Dict[str, Any]:
        """Analyze load balancing across port channel members"""

        if not active_members:
            return {'status': 'no_active_members', 'distribution': []}

        # Check if all members have same speed
        speeds = [member.interface.speed for member in active_members]
        uniform_speed = len(set(speeds)) == 1

        # Simulate load distribution (in real implementation, this would use traffic statistics)
        expected_distribution = 100.0 / len(active_members)

        return {
            'status': 'optimal' if uniform_speed else 'suboptimal',
            'uniform_member_speeds': uniform_speed,
            'expected_distribution_per_member': expected_distribution,
            'load_balance_method': port_channel.load_balance_method or 'unknown',
            'recommendations': [
                'Ensure all members have same speed' if not uniform_speed else 'Load balancing optimal'
            ]
        }

    def _calculate_port_channel_health(self, port_channel: PortChannel,
                                     active_members: List[PortChannelMember],
                                     inactive_members: List[PortChannelMember]) -> float:
        """Calculate port channel health score (0-100)"""

        score = 100.0

        # Deduct points for inactive members
        if inactive_members:
            score -= (len(inactive_members) / (len(active_members) + len(inactive_members))) * 30

        # Deduct points for protocol issues
        if port_channel.protocol == 'static':
            score -= 10  # Static LAG is less robust

        # Deduct points for operational status
        if port_channel.oper_status != 'up':
            score -= 50

        # Deduct points for insufficient redundancy
        if len(active_members) < 2:
            score -= 20

        return max(0.0, score)

    async def get_device_uplinks(self, device_id: int) -> List[UplinkInterface]:
        """Get uplink interfaces for a device"""

        uplinks = self.db.query(UplinkInterface).join(
            NetworkInterface, UplinkInterface.interface_id == NetworkInterface.id
        ).filter(
            UplinkInterface.device_id == device_id,
            UplinkInterface.is_active == True
        ).options(
            joinedload(UplinkInterface.interface)
        ).all()

        return uplinks

    async def analyze_network_redundancy(self, device_id: int) -> Dict[str, Any]:
        """Analyze network redundancy for a device"""

        uplinks = await self.get_device_uplinks(device_id)

        # Group uplinks by redundancy group
        redundancy_groups = {}
        for uplink in uplinks:
            group = uplink.redundancy_group or 0
            if group not in redundancy_groups:
                redundancy_groups[group] = []
            redundancy_groups[group].append(uplink)

        # Analyze each redundancy group
        redundancy_analysis = []
        for group_id, group_uplinks in redundancy_groups.items():
            active_uplinks = [u for u in group_uplinks if u.interface.oper_status == 'up']

            redundancy_analysis.append({
                'redundancy_group': group_id,
                'total_uplinks': len(group_uplinks),
                'active_uplinks': len(active_uplinks),
                'redundancy_status': 'redundant' if len(active_uplinks) > 1 else 'single_point_of_failure',
                'uplinks': [
                    {
                        'interface_name': uplink.interface.interface_name,
                        'uplink_type': uplink.uplink_type,
                        'uplink_role': uplink.uplink_role,
                        'status': uplink.interface.oper_status,
                        'priority': uplink.priority
                    }
                    for uplink in group_uplinks
                ]
            })

        # Overall redundancy assessment
        total_redundancy_groups = len(redundancy_groups)
        redundant_groups = len([g for g in redundancy_analysis if g['redundancy_status'] == 'redundant'])

        overall_redundancy = {
            'redundancy_score': (redundant_groups / total_redundancy_groups * 100) if total_redundancy_groups > 0 else 0,
            'total_groups': total_redundancy_groups,
            'redundant_groups': redundant_groups,
            'single_points_of_failure': total_redundancy_groups - redundant_groups
        }

        return {
            'device_id': device_id,
            'overall_redundancy': overall_redundancy,
            'redundancy_groups': redundancy_analysis,
            'recommendations': self._generate_redundancy_recommendations(redundancy_analysis)
        }

    def _generate_redundancy_recommendations(self, redundancy_analysis: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for improving network redundancy"""

        recommendations = []

        for group in redundancy_analysis:
            if group['redundancy_status'] == 'single_point_of_failure':
                recommendations.append(
                    f"Add redundant uplink to group {group['redundancy_group']} to eliminate single point of failure"
                )

            if group['active_uplinks'] == 0:
                recommendations.append(
                    f"All uplinks in group {group['redundancy_group']} are down - investigate connectivity issues"
                )

        if not recommendations:
            recommendations.append("Network redundancy is optimal")

        return recommendations
```

### **Example Queries for Cisco WLC Integration**

```python
# src/topology/cisco_wlc_queries.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session

class CiscoWLCTopologyQueries:
    """Specialized queries for Cisco Wireless Controller topology"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.query_service = TopologyQueryService(db_session)

    async def find_ap_management_vlans(self) -> Dict[str, Any]:
        """Find VLANs used for AP management across WLCs"""

        # Find all WLC devices
        wlc_devices = self.db.query(Device).filter(
            Device.device_type == 'cisco_wlc'
        ).all()

        ap_mgmt_vlans = {}

        for wlc in wlc_devices:
            # Look for management VLANs (typically VLAN 1 or specific mgmt VLANs)
            mgmt_vlans = self.db.query(VLAN).filter(
                VLAN.device_id == wlc.id,
                or_(
                    VLAN.vlan_name.ilike('%mgmt%'),
                    VLAN.vlan_name.ilike('%management%'),
                    VLAN.vlan_id == 1
                )
            ).all()

            ap_mgmt_vlans[wlc.hostname] = [
                {
                    'vlan_id': vlan.vlan_id,
                    'vlan_name': vlan.vlan_name,
                    'status': vlan.status
                }
                for vlan in mgmt_vlans
            ]

        return {
            'wlc_count': len(wlc_devices),
            'management_vlans': ap_mgmt_vlans,
            'vlan_consistency': self._check_vlan_consistency(ap_mgmt_vlans)
        }

    async def analyze_wlc_uplink_redundancy(self) -> Dict[str, Any]:
        """Analyze uplink redundancy for all WLCs"""

        wlc_devices = self.db.query(Device).filter(
            Device.device_type == 'cisco_wlc'
        ).all()

        redundancy_analysis = {}

        for wlc in wlc_devices:
            redundancy = await self.query_service.analyze_network_redundancy(wlc.id)
            redundancy_analysis[wlc.hostname] = redundancy

        # Overall assessment
        total_wlcs = len(wlc_devices)
        redundant_wlcs = len([
            wlc for wlc, analysis in redundancy_analysis.items()
            if analysis['overall_redundancy']['redundancy_score'] > 50
        ])

        return {
            'total_wlcs': total_wlcs,
            'redundant_wlcs': redundant_wlcs,
            'redundancy_percentage': (redundant_wlcs / total_wlcs * 100) if total_wlcs > 0 else 0,
            'wlc_analysis': redundancy_analysis,
            'recommendations': self._generate_wlc_redundancy_recommendations(redundancy_analysis)
        }

    def _check_vlan_consistency(self, ap_mgmt_vlans: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Check consistency of management VLANs across WLCs"""

        all_vlan_ids = set()
        for wlc_vlans in ap_mgmt_vlans.values():
            for vlan in wlc_vlans:
                all_vlan_ids.add(vlan['vlan_id'])

        consistency_issues = []
        for vlan_id in all_vlan_ids:
            wlcs_with_vlan = [
                wlc for wlc, vlans in ap_mgmt_vlans.items()
                if any(v['vlan_id'] == vlan_id for v in vlans)
            ]

            if len(wlcs_with_vlan) != len(ap_mgmt_vlans):
                consistency_issues.append({
                    'vlan_id': vlan_id,
                    'missing_from': [
                        wlc for wlc in ap_mgmt_vlans.keys()
                        if wlc not in wlcs_with_vlan
                    ]
                })

        return {
            'consistent': len(consistency_issues) == 0,
            'issues': consistency_issues
        }

    def _generate_wlc_redundancy_recommendations(self, redundancy_analysis: Dict[str, Any]) -> List[str]:
        """Generate WLC-specific redundancy recommendations"""

        recommendations = []

        for wlc_hostname, analysis in redundancy_analysis.items():
            if analysis['overall_redundancy']['redundancy_score'] < 50:
                recommendations.append(
                    f"WLC {wlc_hostname} has insufficient uplink redundancy - consider adding backup uplinks"
                )

            single_points = analysis['overall_redundancy']['single_points_of_failure']
            if single_points > 0:
                recommendations.append(
                    f"WLC {wlc_hostname} has {single_points} single points of failure in uplink configuration"
                )

        if not recommendations:
            recommendations.append("All WLCs have adequate uplink redundancy")

        return recommendations
```

---

## Implementation Summary

### **Key Benefits of This Topology Storage Design**

1. **Comprehensive Data Model**: Captures all aspects of network topology including physical, logical, and protocol relationships

2. **Intelligent Discovery**: pyATS/Genie parsers automatically populate topology data with vendor-specific handling

3. **Rich MCP Context**: Topology-aware MCP tools provide intelligent context to LangChain/LangGraph

4. **Advanced Querying**: Complex topology queries support path analysis, VLAN spanning, and redundancy assessment

5. **Cisco WLC Integration**: Specialized queries and analysis for wireless controller environments

### **Integration with Existing System**

- **Database Extension**: Builds on existing PostgreSQL schema with new topology tables
- **MCP Enhancement**: New topology tools integrate seamlessly with existing MCP architecture
- **LangChain Integration**: Topology context enhances natural language processing accuracy
- **pyATS/Genie Leverage**: Utilizes existing parser infrastructure for data collection

This comprehensive topology storage design transforms the hybrid system into a topology-aware network automation platform capable of intelligent decision-making based on complete network context.
```
```
