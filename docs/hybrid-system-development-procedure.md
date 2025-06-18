# Hybrid LangGraph/LangChain/MCP Network Automation System
## Development Procedure and Architecture Guide

### Table of Contents
1. [Executive Summary](#executive-summary)
2. [Conversation Analysis](#conversation-analysis)
3. [Current Codebase Assessment](#current-codebase-assessment)
4. [Networking Libraries Comparison](#networking-libraries-comparison)
5. [System Architecture](#system-architecture)
6. [Implementation Plan](#implementation-plan)
7. [Integration Points](#integration-points)
8. [Testing and Validation](#testing-and-validation)

---

## Executive Summary

This document outlines the development procedure for a hybrid system that integrates:
- **LangGraph** for workflow orchestration and state management
- **LangChain** for natural language processing and LLM integration
- **MCP (Model Context Protocol)** for standardized context management
- **PostgreSQL + FastAPI** for device and command management
- **Network automation libraries** for multi-vendor device connectivity

The system will provide a natural language interface for network device management, supporting multiple device types and vendors through a modular, scalable architecture.

---

## Conversation Analysis

### Key Actionable Suggestions Extracted

#### 1. **Hybrid Architecture Approach**
- **User Interaction Layer**: LangChain for natural language processing
- **Command Processing Layer**: MCP model for device and command management
- **Workflow Orchestration**: LangGraph for complex state management
- **Data Persistence**: PostgreSQL with FastAPI for scalable data management

#### 2. **Device Management Strategy**
- Centralized device registry with metadata (capabilities, connection details)
- Modular device handlers for each device type
- Dynamic loading of device modules
- Protocol-specific communication handling

#### 3. **Command Management Strategy**
- Template-based command system with variable substitution
- Dynamic command generation based on user input
- Command validation and parameter handling
- Version control for command definitions

#### 4. **Natural Language Processing**
- User input interpretation and command translation
- Dynamic parameter extraction from natural language
- Context-aware command generation
- User-friendly response formatting

#### 5. **Database-Driven Configuration**
- PostgreSQL for device and command storage
- FastAPI for RESTful API management
- CRUD operations for dynamic updates
- Configuration management without code changes

---

## Current Codebase Assessment

### Existing Components
- **Conversation transcript**: Contains detailed architectural discussions and code examples
- **No existing implementation**: Clean slate for development

### Components to Build
1. **LangChain Integration Layer**
   - Natural language command interpreter
   - Prompt templates for device-specific commands
   - Response formatting and parsing

2. **LangGraph Workflow Engine**
   - State management for complex workflows
   - Multi-step command orchestration
   - Error handling and retry logic

3. **MCP Command Processing Layer**
   - Device registry and management
   - Command routing and execution
   - Protocol abstraction layer

4. **FastAPI Backend Services**
   - Device CRUD operations
   - Command management APIs
   - Configuration endpoints

5. **Database Schema**
   - Device tables with metadata
   - Command templates with parameters
   - Execution logs and audit trails

6. **Network Library Integration**
   - Multi-vendor device connectors
   - Protocol handlers (SSH, Telnet, etc.)
   - Connection pooling and management

---

## Networking Libraries Comparison

### 1. **Cisco pyATS and Genie Libraries**

#### Capabilities
- **Comprehensive Testing Framework**: Built for network test automation and validation
- **Multi-vendor Support**: Extensive device support beyond Cisco
- **Genie Parsers**: Pre-built parsers for common show commands
- **Testbed Management**: YAML-based device inventory and topology
- **Advanced Features**: 
  - State comparison and diff analysis
  - Automated test case generation
  - Integration with CI/CD pipelines
  - Rich reporting and analytics

#### Use Cases
- Large-scale network testing and validation
- Configuration compliance checking
- Network state monitoring and comparison
- Enterprise-grade automation with robust error handling

#### Pros
- Enterprise-ready with extensive documentation
- Built-in parsers for hundreds of commands
- Strong state management and comparison capabilities
- Excellent for complex testing scenarios

#### Cons
- Steeper learning curve
- Heavier framework overhead
- May be overkill for simple automation tasks

### 2. **Unicon: The Connection Library**

#### Capabilities
- **Connection Abstraction**: Unified interface for SSH, Telnet, Serial connections
- **Proxy Support**: Jump host and proxy connections
- **State Management**: Connection state tracking and recovery
- **Plugin Architecture**: Extensible for custom device types
- **Integration**: Designed to work with pyATS ecosystem

#### Use Cases
- Standardized connection management across device types
- Complex network topologies with jump hosts
- Integration with pyATS testing frameworks
- Multi-protocol device access

#### Pros
- Robust connection handling with automatic recovery
- Excellent proxy and jump host support
- Consistent API across connection types
- Strong integration with pyATS

#### Cons
- Primarily designed for pyATS ecosystem
- Less standalone documentation
- Requires understanding of pyATS concepts

### 3. **Netmiko Library (Baseline)**

#### Capabilities
- **Multi-vendor SSH Support**: 200+ device types supported
- **Simple API**: Straightforward connection and command execution
- **Configuration Management**: Send configuration commands
- **File Transfer**: SCP file transfer capabilities
- **Session Management**: Connection pooling and reuse

#### Use Cases
- Simple network automation tasks
- Configuration deployment
- Information gathering from devices
- Quick prototyping and scripting

#### Pros
- Simple and intuitive API
- Extensive device support
- Lightweight and fast
- Excellent documentation and community

#### Cons
- Limited advanced features
- Basic error handling
- No built-in parsing capabilities
- Manual connection management

### **REVISED Recommendation for Hybrid System**

**Primary Choice: pyATS/Genie with Unicon** ⭐

**Rationale for Revision:**
1. **Extensive Parser Library**: 400+ pre-built parsers for major platforms (IOS, IOS-XE, IOS-XR, NX-OS, Juniper JunOS, Arista EOS)
2. **Structured Output**: Parsers convert raw command output to structured Python dictionaries automatically
3. **Multi-Vendor Support**: Comprehensive coverage of enterprise network devices
4. **Robust Connection Management**: Unicon provides enterprise-grade connection handling
5. **Production Ready**: Battle-tested in Cisco's internal automation for 20+ years
6. **API Integration**: Clean APIs that integrate well with LangChain/LangGraph workflows

**Supported Platforms & Parsers:**
- **Cisco IOS/IOS-XE**: 150+ parsers (show version, show interface, show ip route, etc.)
- **Cisco IOS-XR**: 100+ parsers (show route, show interface, show bgp, etc.)
- **Cisco NX-OS**: 120+ parsers (show version, show interface, show vpc, etc.)
- **Juniper JunOS**: 80+ parsers (show version, show interfaces, show route, etc.)
- **Arista EOS**: 60+ parsers (show version, show interfaces, show ip route, etc.)

**Implementation Strategy:**
```python
# Example: Structured output from Genie parser
from genie.libs.parser.ios.show_interface import ShowInterface

parser = ShowInterface(device=device)
parsed_output = parser.parse()
# Returns structured dictionary instead of raw text
```

**Secondary Integration: Netmiko for Simple Cases**
- Use Netmiko for basic command execution where parsing isn't critical
- Implement as lightweight option for simple automation tasks
- Maintain as fallback for unsupported devices

**Benefits for Hybrid System:**
- **LangChain Integration**: Structured data improves LLM processing accuracy
- **LangGraph Workflows**: Reliable data structures enable complex decision logic
- **MCP Context**: Rich device context from parsed data enhances context management
- **Error Handling**: Built-in validation and error detection in parsers

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   CLI Client    │  │   Web Interface │  │   API Client    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 LangChain Integration Layer                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Natural Language Processor                                 │ │
│  │  • Command interpretation                                   │ │
│  │  • Parameter extraction                                     │ │
│  │  • Response formatting                                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                LangGraph Workflow Orchestration                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Workflow Engine                                            │ │
│  │  • State management                                         │ │
│  │  • Multi-step orchestration                                 │ │
│  │  • Error handling and retry logic                           │ │
│  │  • Conditional branching                                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                MCP Command Processing Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Device Registry │  │ Command Manager │  │ Protocol Handler│ │
│  │ • Device metadata│  │ • Command routing│  │ • SSH/Telnet   │ │
│  │ • Capabilities  │  │ • Template mgmt │  │ • Connection    │ │
│  │ • Connection    │  │ • Parameter     │  │   pooling       │ │
│  │   details       │  │   validation    │  │ • Error handling│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Services                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Device API    │  │  Command API    │  │ Configuration   │ │
│  │   • CRUD ops    │  │  • Template mgmt│  │     API         │ │
│  │   • Search      │  │  • Execution    │  │  • Settings     │ │
│  │   • Validation  │  │  • History      │  │  • Preferences  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Devices       │  │    Commands     │  │   Execution     │ │
│  │   • Metadata    │  │   • Templates   │  │     Logs        │ │
│  │   • Credentials │  │   • Parameters  │  │   • Audit trail │ │
│  │   • Capabilities│  │   • Validation  │  │   • Performance │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Network Device Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Cisco IOS     │  │    Juniper      │  │   Arista EOS    │ │
│  │   • SSH/Telnet  │  │   • NETCONF     │  │   • eAPI        │ │
│  │   • Commands    │  │   • SSH         │  │   • SSH         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. **LangChain Integration Layer**
- Natural language command interpretation
- Dynamic prompt generation based on device type
- Response parsing and formatting
- Context management for conversation flow

#### 2. **LangGraph Workflow Orchestration**
- Complex multi-step workflow management
- State persistence across command sequences
- Conditional logic and branching
- Error recovery and retry mechanisms
- Parallel execution coordination

#### 3. **MCP Command Processing Layer**
- Device registry and capability management
- Command template management and validation
- Protocol abstraction and connection handling
- Security and authentication management

#### 4. **FastAPI Backend Services**
- RESTful API for all system operations
- Database abstraction and ORM management
- Authentication and authorization
- Real-time monitoring and logging

#### 5. **PostgreSQL Database**
- Persistent storage for all system data
- ACID compliance for critical operations
- Scalable query performance
- Backup and recovery capabilities

---

## Implementation Plan

### Phase 1: Foundation Setup (Weeks 1-2)

#### 1.1 Environment Setup
```bash
# Create project structure
mkdir hybrid-network-automation
cd hybrid-network-automation

# Initialize Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies
pip install fastapi[all] sqlalchemy psycopg2-binary
pip install langchain langchain-openai langgraph
pip install 'pyats[full]'  # Includes Genie parsers and Unicon
pip install netmiko paramiko  # Keep as secondary option
pip install pydantic python-multipart
pip install pytest pytest-asyncio
```

#### 1.2 Database Setup
```sql
-- Create database
CREATE DATABASE network_automation;

-- Create tables
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    device_type VARCHAR(50) NOT NULL,
    hostname VARCHAR(255) NOT NULL UNIQUE,
    ip_address INET NOT NULL,
    connection_details JSONB NOT NULL,
    capabilities TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commands (
    id SERIAL PRIMARY KEY,
    command_name VARCHAR(100) NOT NULL UNIQUE,
    command_template TEXT NOT NULL,
    device_types TEXT[],
    parameters JSONB,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE execution_logs (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id),
    command_id INTEGER REFERENCES commands(id),
    executed_command TEXT NOT NULL,
    output TEXT,
    status VARCHAR(20) NOT NULL,
    execution_time INTERVAL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 1.3 Project Structure
```
hybrid-network-automation/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── devices.py
│   │   ├── commands.py
│   │   └── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── config.py
│   ├── langchain_layer/
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   └── prompts.py
│   ├── langgraph_layer/
│   │   ├── __init__.py
│   │   ├── workflows.py
│   │   └── state.py
│   ├── mcp_layer/
│   │   ├── __init__.py
│   │   ├── device_registry.py
│   │   ├── command_manager.py
│   │   └── protocol_handler.py
│   └── network_layer/
│       ├── __init__.py
│       ├── connectors/
│       │   ├── __init__.py
│       │   ├── genie_connector.py
│       │   ├── netmiko_connector.py
│       │   └── base_connector.py
│       └── parsers/
│           ├── __init__.py
│           ├── genie_parser.py
│           └── output_parser.py
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

### Phase 2: Core Backend Development (Weeks 3-4)

#### 2.1 Database Models and FastAPI Setup

**Core Models (src/core/models.py)**
```python
from sqlalchemy import Column, Integer, String, Text, ARRAY, JSON, DateTime, Interval
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_type = Column(String(50), nullable=False)
    hostname = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=False)  # Supports IPv6
    connection_details = Column(JSON, nullable=False)
    capabilities = Column(ARRAY(String))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, index=True)
    command_name = Column(String(100), nullable=False, unique=True)
    command_template = Column(Text, nullable=False)
    device_types = Column(ARRAY(String))
    parameters = Column(JSON)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False)
    command_id = Column(Integer, nullable=False)
    executed_command = Column(Text, nullable=False)
    output = Column(Text)
    status = Column(String(20), nullable=False)
    execution_time = Column(Interval)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

# Pydantic models for API
class DeviceCreate(BaseModel):
    device_type: str
    hostname: str
    ip_address: str
    connection_details: Dict
    capabilities: Optional[List[str]] = []

class DeviceResponse(DeviceCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class CommandCreate(BaseModel):
    command_name: str
    command_template: str
    device_types: List[str]
    parameters: Optional[Dict] = {}
    description: Optional[str] = ""

class CommandResponse(CommandCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

**FastAPI Application Setup (src/api/main.py)**
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from src.core.database import get_db, engine
from src.core.models import Base
from src.api.devices import router as devices_router
from src.api.commands import router as commands_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hybrid Network Automation System",
    description="LangGraph/LangChain/MCP Network Automation API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(devices_router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(commands_router, prefix="/api/v1/commands", tags=["commands"])

@app.get("/")
async def root():
    return {"message": "Hybrid Network Automation System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### 2.2 Device Registry Implementation

**Device API (src/api/devices.py)**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.core.models import Device, DeviceCreate, DeviceResponse

router = APIRouter()

@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    # Check if device already exists
    existing_device = db.query(Device).filter(Device.hostname == device.hostname).first()
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device with this hostname already exists"
        )

    db_device = Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    devices = db.query(Device).offset(skip).limit(limit).all()
    return devices

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    return device

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(device_id: int, device_update: DeviceCreate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    for key, value in device_update.dict().items():
        setattr(device, key, value)

    db.commit()
    db.refresh(device)
    return device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    db.delete(device)
    db.commit()
```

#### 2.3 Command Management System

**Command API (src/api/commands.py)**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.core.database import get_db
from src.core.models import Command, CommandCreate, CommandResponse
import re

router = APIRouter()

@router.post("/", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
async def create_command(command: CommandCreate, db: Session = Depends(get_db)):
    # Validate command template
    if not _validate_command_template(command.command_template):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid command template format"
        )

    existing_command = db.query(Command).filter(Command.command_name == command.command_name).first()
    if existing_command:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command with this name already exists"
        )

    db_command = Command(**command.dict())
    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    return db_command

@router.get("/", response_model=List[CommandResponse])
async def list_commands(device_type: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(Command)
    if device_type:
        query = query.filter(Command.device_types.contains([device_type]))

    commands = query.offset(skip).limit(limit).all()
    return commands

@router.get("/{command_id}", response_model=CommandResponse)
async def get_command(command_id: int, db: Session = Depends(get_db)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )
    return command

@router.post("/{command_id}/render")
async def render_command(command_id: int, parameters: Dict[str, Any], db: Session = Depends(get_db)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Command not found"
        )

    try:
        rendered_command = _render_command_template(command.command_template, parameters)
        return {"rendered_command": rendered_command}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error rendering command: {str(e)}"
        )

def _validate_command_template(template: str) -> bool:
    """Validate command template format"""
    # Check for valid parameter placeholders
    pattern = r'\{(\w+)\}'
    matches = re.findall(pattern, template)
    return len(matches) >= 0  # Allow templates without parameters

def _render_command_template(template: str, parameters: Dict[str, Any]) -> str:
    """Render command template with parameters"""
    try:
        return template.format(**parameters)
    except KeyError as e:
        raise ValueError(f"Missing parameter: {e}")
    except Exception as e:
        raise ValueError(f"Template rendering error: {e}")
```

#### 2.4 Network Connectivity with pyATS/Genie

**Base Connector (src/network_layer/connectors/base_connector.py)**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

@dataclass
class ConnectionResult:
    success: bool
    message: str
    output: Optional[str] = None
    error: Optional[str] = None

class BaseConnector(ABC):
    """Abstract base class for network device connectors"""

    def __init__(self, device_config: Dict[str, Any]):
        self.device_config = device_config
        self.status = ConnectionStatus.DISCONNECTED
        self.connection = None

    @abstractmethod
    async def connect(self) -> ConnectionResult:
        """Establish connection to device"""
        pass

    @abstractmethod
    async def disconnect(self) -> ConnectionResult:
        """Disconnect from device"""
        pass

    @abstractmethod
    async def execute_command(self, command: str) -> ConnectionResult:
        """Execute command on device"""
        pass

    @abstractmethod
    async def send_config(self, config_commands: list) -> ConnectionResult:
        """Send configuration commands to device"""
        pass

    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self.status == ConnectionStatus.CONNECTED
```

**Genie Connector (src/network_layer/connectors/genie_connector.py)**
```python
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
from genie.testbed import load
from genie.libs.parser.utils import get_parser
from unicon.core.errors import ConnectionError, CommandTimeoutError
import yaml
import tempfile
import os

from .base_connector import BaseConnector, ConnectionResult, ConnectionStatus

class GenieConnector(BaseConnector):
    """pyATS/Genie connector with advanced parsing capabilities"""

    def __init__(self, device_config: Dict[str, Any]):
        super().__init__(device_config)
        self.device = None
        self.testbed = None
        self.supported_parsers = {}
        self._initialize_testbed()

    def _initialize_testbed(self):
        """Initialize pyATS testbed from device config"""
        testbed_config = {
            'testbed': {
                'name': 'dynamic_testbed'
            },
            'devices': {
                self.device_config['hostname']: {
                    'type': self.device_config.get('device_type', 'router'),
                    'os': self._map_device_type_to_os(self.device_config.get('device_type')),
                    'connections': {
                        'default': {
                            'protocol': self.device_config.get('protocol', 'ssh'),
                            'ip': self.device_config['ip_address'],
                            'port': self.device_config.get('port', 22),
                            'username': self.device_config['connection_details']['username'],
                            'password': self.device_config['connection_details']['password'],
                        }
                    }
                }
            }
        }

        # Create temporary testbed file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(testbed_config, f)
            self.testbed_file = f.name

        # Load testbed
        self.testbed = load(self.testbed_file)
        self.device = self.testbed.devices[self.device_config['hostname']]

        # Discover supported parsers
        self._discover_supported_parsers()

    def _map_device_type_to_os(self, device_type: str) -> str:
        """Map device type to pyATS OS"""
        mapping = {
            'cisco_ios': 'ios',
            'cisco_iosxe': 'iosxe',
            'cisco_iosxr': 'iosxr',
            'cisco_nxos': 'nxos',
            'juniper_junos': 'junos',
            'arista_eos': 'eos'
        }
        return mapping.get(device_type, 'ios')

    def _discover_supported_parsers(self):
        """Discover available parsers for this device type"""
        try:
            os_type = self.device.os

            # Common commands to check for parser support
            common_commands = [
                'show version',
                'show interface',
                'show ip interface brief',
                'show ip route',
                'show running-config',
                'show inventory',
                'show processes',
                'show memory',
                'show bgp summary',
                'show ospf neighbor'
            ]

            for command in common_commands:
                try:
                    parser_class = get_parser(command, self.device)
                    if parser_class:
                        self.supported_parsers[command] = parser_class
                except Exception:
                    # Parser not available for this command/OS combination
                    pass

        except Exception as e:
            print(f"Warning: Could not discover parsers: {e}")

    async def connect(self) -> ConnectionResult:
        """Establish connection to device"""
        try:
            self.status = ConnectionStatus.CONNECTING

            # Connect using Unicon
            await asyncio.get_event_loop().run_in_executor(
                None, self.device.connect
            )

            self.status = ConnectionStatus.CONNECTED
            return ConnectionResult(
                success=True,
                message=f"Successfully connected to {self.device_config['hostname']}"
            )

        except ConnectionError as e:
            self.status = ConnectionStatus.ERROR
            return ConnectionResult(
                success=False,
                message="Connection failed",
                error=str(e)
            )
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            return ConnectionResult(
                success=False,
                message="Unexpected connection error",
                error=str(e)
            )

    async def disconnect(self) -> ConnectionResult:
        """Disconnect from device"""
        try:
            if self.device and self.device.is_connected():
                await asyncio.get_event_loop().run_in_executor(
                    None, self.device.disconnect
                )

            self.status = ConnectionStatus.DISCONNECTED

            # Clean up temporary testbed file
            if hasattr(self, 'testbed_file') and os.path.exists(self.testbed_file):
                os.unlink(self.testbed_file)

            return ConnectionResult(
                success=True,
                message="Successfully disconnected"
            )

        except Exception as e:
            return ConnectionResult(
                success=False,
                message="Disconnect failed",
                error=str(e)
            )

    async def execute_command(self, command: str) -> ConnectionResult:
        """Execute command with automatic parsing if available"""
        if not self.is_connected():
            return ConnectionResult(
                success=False,
                message="Device not connected",
                error="No active connection"
            )

        try:
            start_time = datetime.now()

            # Check if we have a parser for this command
            if command in self.supported_parsers:
                # Use Genie parser for structured output
                result = await self._execute_with_parser(command)
            else:
                # Fallback to raw command execution
                result = await self._execute_raw_command(command)

            execution_time = datetime.now() - start_time

            if result['success']:
                return ConnectionResult(
                    success=True,
                    message=f"Command executed successfully in {execution_time.total_seconds():.2f}s",
                    output=result['output']
                )
            else:
                return ConnectionResult(
                    success=False,
                    message="Command execution failed",
                    error=result.get('error', 'Unknown error')
                )

        except CommandTimeoutError as e:
            return ConnectionResult(
                success=False,
                message="Command timed out",
                error=str(e)
            )
        except Exception as e:
            return ConnectionResult(
                success=False,
                message="Command execution error",
                error=str(e)
            )

    async def _execute_with_parser(self, command: str) -> Dict[str, Any]:
        """Execute command with Genie parser"""
        try:
            parser_class = self.supported_parsers[command]
            parser = parser_class(device=self.device)

            # Execute and parse in thread pool
            parsed_output = await asyncio.get_event_loop().run_in_executor(
                None, parser.parse
            )

            return {
                'success': True,
                'output': {
                    'parsed': parsed_output,
                    'raw': getattr(parser, 'device_output', ''),
                    'command': command,
                    'parser_used': parser_class.__name__
                }
            }

        except Exception as e:
            # Fallback to raw execution if parsing fails
            return await self._execute_raw_command(command)

    async def _execute_raw_command(self, command: str) -> Dict[str, Any]:
        """Execute command without parsing"""
        try:
            output = await asyncio.get_event_loop().run_in_executor(
                None, self.device.execute, command
            )

            return {
                'success': True,
                'output': {
                    'raw': output,
                    'command': command,
                    'parser_used': None
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def send_config(self, config_commands: List[str]) -> ConnectionResult:
        """Send configuration commands to device"""
        if not self.is_connected():
            return ConnectionResult(
                success=False,
                message="Device not connected",
                error="No active connection"
            )

        try:
            # Enter configuration mode and send commands
            output = await asyncio.get_event_loop().run_in_executor(
                None, self.device.configure, config_commands
            )

            return ConnectionResult(
                success=True,
                message=f"Configuration applied successfully",
                output=output
            )

        except Exception as e:
            return ConnectionResult(
                success=False,
                message="Configuration failed",
                error=str(e)
            )

    def get_supported_commands(self) -> List[str]:
        """Get list of commands with parser support"""
        return list(self.supported_parsers.keys())

    def has_parser_support(self, command: str) -> bool:
        """Check if command has parser support"""
        return command in self.supported_parsers

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        if not self.device:
            return {}

        return {
            'hostname': self.device.name,
            'os': self.device.os,
            'type': self.device.type,
            'is_connected': self.device.is_connected() if hasattr(self.device, 'is_connected') else False,
            'supported_parsers': len(self.supported_parsers),
            'parser_commands': list(self.supported_parsers.keys())
        }
```

**Genie Parser Integration (src/network_layer/parsers/genie_parser.py)**
```python
from typing import Dict, Any, Optional, List
from genie.libs.parser.utils import get_parser
import json

class GenieParserManager:
    """Manage Genie parsers and provide unified interface"""

    def __init__(self):
        self.parser_cache = {}

    def get_available_parsers(self, device_os: str) -> Dict[str, str]:
        """Get available parsers for device OS"""
        # This would be expanded to dynamically discover parsers
        parser_map = {
            'ios': {
                'show version': 'ShowVersion',
                'show interface': 'ShowInterface',
                'show ip interface brief': 'ShowIpInterfaceBrief',
                'show ip route': 'ShowIpRoute',
                'show running-config': 'ShowRunningConfig',
                'show inventory': 'ShowInventory',
                'show processes': 'ShowProcesses',
                'show memory': 'ShowMemory'
            },
            'iosxe': {
                'show version': 'ShowVersion',
                'show interface': 'ShowInterface',
                'show ip interface brief': 'ShowIpInterfaceBrief',
                'show ip route': 'ShowIpRoute',
                'show running-config': 'ShowRunningConfig'
            },
            'nxos': {
                'show version': 'ShowVersion',
                'show interface': 'ShowInterface',
                'show interface brief': 'ShowInterfaceBrief',
                'show ip route': 'ShowIpRoute',
                'show running-config': 'ShowRunningConfig',
                'show vpc': 'ShowVpc'
            },
            'junos': {
                'show version': 'ShowVersion',
                'show interfaces': 'ShowInterfaces',
                'show interfaces terse': 'ShowInterfacesTerse',
                'show route': 'ShowRoute',
                'show configuration': 'ShowConfiguration'
            }
        }

        return parser_map.get(device_os, {})

    def parse_command_output(self, command: str, output: str, device_os: str) -> Dict[str, Any]:
        """Parse command output using appropriate Genie parser"""
        try:
            # Get parser class
            parser_class = get_parser(command, device_os)
            if not parser_class:
                return {
                    'success': False,
                    'error': f'No parser available for command: {command} on OS: {device_os}',
                    'raw_output': output
                }

            # Create parser instance and parse
            parser = parser_class()
            parsed_data = parser.parse(output=output)

            return {
                'success': True,
                'parsed_data': parsed_data,
                'raw_output': output,
                'parser_used': parser_class.__name__,
                'command': command
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Parser error: {str(e)}',
                'raw_output': output,
                'command': command
            }

    def format_parsed_data(self, parsed_data: Dict[str, Any], command: str) -> str:
        """Format parsed data for human consumption"""
        if not parsed_data.get('success'):
            return f"Parsing failed: {parsed_data.get('error', 'Unknown error')}"

        data = parsed_data['parsed_data']

        # Command-specific formatting
        if 'show version' in command:
            return self._format_version_data(data)
        elif 'show interface' in command:
            return self._format_interface_data(data)
        elif 'show ip route' in command:
            return self._format_route_data(data)
        else:
            # Generic JSON formatting
            return json.dumps(data, indent=2)

    def _format_version_data(self, data: Dict[str, Any]) -> str:
        """Format show version parsed data"""
        formatted = "## Device Version Information\n\n"

        version_info = data.get('version', {})
        if 'version' in version_info:
            formatted += f"**Software Version:** {version_info['version']}\n"
        if 'hostname' in version_info:
            formatted += f"**Hostname:** {version_info['hostname']}\n"
        if 'uptime' in version_info:
            formatted += f"**Uptime:** {version_info['uptime']}\n"
        if 'image' in version_info:
            formatted += f"**Image:** {version_info['image']}\n"

        return formatted

    def _format_interface_data(self, data: Dict[str, Any]) -> str:
        """Format show interface parsed data"""
        formatted = "## Interface Information\n\n"

        interfaces = data.get('interface', {})
        for intf_name, intf_data in interfaces.items():
            formatted += f"### {intf_name}\n"
            if 'oper_status' in intf_data:
                formatted += f"- **Status:** {intf_data['oper_status']}\n"
            if 'ipv4' in intf_data:
                for ip, ip_data in intf_data['ipv4'].items():
                    formatted += f"- **IP Address:** {ip}\n"
            formatted += "\n"

        return formatted

    def _format_route_data(self, data: Dict[str, Any]) -> str:
        """Format show ip route parsed data"""
        formatted = "## Routing Table\n\n"

        vrf_data = data.get('vrf', {})
        for vrf_name, vrf_info in vrf_data.items():
            formatted += f"### VRF: {vrf_name}\n"

            address_families = vrf_info.get('address_family', {})
            for af_name, af_data in address_families.items():
                routes = af_data.get('routes', {})
                formatted += f"**{af_name} Routes:** {len(routes)}\n"

                for route, route_data in list(routes.items())[:10]:  # Show first 10
                    formatted += f"- {route}\n"

                if len(routes) > 10:
                    formatted += f"... and {len(routes) - 10} more routes\n"

            formatted += "\n"

        return formatted
```

### Phase 3: LangChain Integration (Weeks 5-6)

#### 3.1 Natural Language Processing

**LangChain Processor (src/langchain_layer/processor.py)**
```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import BaseOutputParser
from typing import Dict, Any, List
import json
import re

class CommandOutputParser(BaseOutputParser):
    """Parse LLM output to extract command and parameters"""

    def parse(self, text: str) -> Dict[str, Any]:
        try:
            # Try to parse as JSON first
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback to regex parsing
            return self._regex_parse(text)

    def _regex_parse(self, text: str) -> Dict[str, Any]:
        """Fallback regex parsing for non-JSON responses"""
        command_match = re.search(r'command["\']?\s*:\s*["\']?([^"\']+)', text, re.IGNORECASE)
        device_match = re.search(r'device["\']?\s*:\s*["\']?([^"\']+)', text, re.IGNORECASE)
        params_match = re.search(r'parameters["\']?\s*:\s*\{([^}]+)\}', text, re.IGNORECASE)

        result = {}
        if command_match:
            result['command'] = command_match.group(1).strip()
        if device_match:
            result['device'] = device_match.group(1).strip()
        if params_match:
            # Simple parameter parsing
            params_str = params_match.group(1)
            params = {}
            for param in params_str.split(','):
                if ':' in param:
                    key, value = param.split(':', 1)
                    params[key.strip().strip('"\')] = value.strip().strip('"\'')
            result['parameters'] = params

        return result

class NaturalLanguageProcessor:
    """Process natural language input and convert to network commands"""

    def __init__(self, llm_api_key: str):
        self.llm = OpenAI(api_key=llm_api_key, temperature=0.1)
        self.output_parser = CommandOutputParser()
        self._setup_chains()

    def _setup_chains(self):
        """Setup LangChain chains for different types of processing"""

        # Command interpretation chain
        command_template = """
        You are a network automation assistant. Convert the user's natural language request
        into a structured command format.

        User request: {user_input}
        Available devices: {available_devices}
        Available commands: {available_commands}

        Respond with a JSON object containing:
        - "command": the command name to execute
        - "device": the target device (hostname or IP)
        - "parameters": object with any required parameters

        Example response:
        {{"command": "show_interface", "device": "router1", "parameters": {{"interface": "GigabitEthernet0/1"}}}}

        Response:
        """

        self.command_prompt = PromptTemplate(
            input_variables=["user_input", "available_devices", "available_commands"],
            template=command_template
        )

        self.command_chain = LLMChain(
            llm=self.llm,
            prompt=self.command_prompt,
            output_parser=self.output_parser
        )

        # Response formatting chain
        response_template = """
        Format the following network command output for the user in a clear, readable way.

        Original command: {command}
        Device: {device}
        Raw output: {raw_output}

        Provide a summary and highlight any important information:
        """

        self.response_prompt = PromptTemplate(
            input_variables=["command", "device", "raw_output"],
            template=response_template
        )

        self.response_chain = LLMChain(
            llm=self.llm,
            prompt=self.response_prompt
        )

    async def process_user_input(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process natural language input and return structured command"""
        try:
            result = await self.command_chain.arun(
                user_input=user_input,
                available_devices=context.get('devices', []),
                available_commands=context.get('commands', [])
            )
            return result
        except Exception as e:
            return {"error": f"Failed to process input: {str(e)}"}

    async def format_response(self, command: str, device: str, raw_output: str) -> str:
        """Format command output for user-friendly display"""
        try:
            formatted_response = await self.response_chain.arun(
                command=command,
                device=device,
                raw_output=raw_output
            )
            return formatted_response
        except Exception as e:
            return f"Error formatting response: {str(e)}\n\nRaw output:\n{raw_output}"

#### 3.2 Prompt Engineering

**Prompt Templates (src/langchain_layer/prompts.py)**
```python
from langchain.prompts import PromptTemplate
from typing import Dict, List

class NetworkPromptTemplates:
    """Collection of prompt templates for network automation tasks"""

    @staticmethod
    def get_command_interpretation_prompt() -> PromptTemplate:
        """Prompt for interpreting user commands"""
        template = """
        You are an expert network engineer and automation specialist. Your task is to interpret
        natural language requests and convert them into structured network commands.

        Context:
        - Available devices: {available_devices}
        - Available command templates: {available_commands}
        - Device capabilities: {device_capabilities}

        User Request: "{user_input}"

        Guidelines:
        1. Identify the target device(s) from the user request
        2. Determine the appropriate command template to use
        3. Extract any parameters needed for the command
        4. Validate that the device supports the requested operation

        Respond with a JSON object in this exact format:
        {{
            "command_name": "exact_command_template_name",
            "target_device": "device_hostname_or_ip",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "confidence": 0.95,
            "reasoning": "Brief explanation of the interpretation"
        }}

        If the request is unclear or cannot be fulfilled, respond with:
        {{
            "error": "Description of the issue",
            "suggestions": ["suggestion1", "suggestion2"]
        }}
        """

        return PromptTemplate(
            input_variables=["user_input", "available_devices", "available_commands", "device_capabilities"],
            template=template
        )

    @staticmethod
    def get_output_formatting_prompt() -> PromptTemplate:
        """Prompt for formatting command output"""
        template = """
        You are a network automation assistant. Format the following network command output
        for clear presentation to the user.

        Command Details:
        - Command: {command_name}
        - Device: {device_name}
        - Parameters: {parameters}
        - Execution Status: {status}

        Raw Output:
        {raw_output}

        Instructions:
        1. Provide a clear summary of what the command accomplished
        2. Highlight any important information, warnings, or errors
        3. Format tables and lists for readability
        4. Include relevant metrics or status information
        5. Suggest follow-up actions if appropriate

        Format your response as:
        ## Command Summary
        [Brief description of what was executed]

        ## Key Information
        [Highlighted important details]

        ## Formatted Output
        [Cleaned and formatted command output]

        ## Recommendations
        [Any suggested follow-up actions]
        """

        return PromptTemplate(
            input_variables=["command_name", "device_name", "parameters", "status", "raw_output"],
            template=template
        )

    @staticmethod
    def get_error_analysis_prompt() -> PromptTemplate:
        """Prompt for analyzing command errors"""
        template = """
        You are a network troubleshooting expert. Analyze the following command execution error
        and provide helpful guidance.

        Error Details:
        - Command: {command_name}
        - Device: {device_name}
        - Error Message: {error_message}
        - Device Type: {device_type}

        Context:
        - User Intent: {user_intent}
        - Command Parameters: {parameters}

        Provide:
        1. Root cause analysis of the error
        2. Possible solutions or workarounds
        3. Alternative commands that might achieve the user's goal
        4. Prevention strategies for similar errors

        Format as:
        ## Error Analysis
        [Root cause explanation]

        ## Recommended Solutions
        1. [Primary solution]
        2. [Alternative solution]

        ## Alternative Approaches
        [Other ways to achieve the user's goal]

        ## Prevention Tips
        [How to avoid this error in the future]
        """

        return PromptTemplate(
            input_variables=["command_name", "device_name", "error_message", "device_type", "user_intent", "parameters"],
            template=template
        )

#### 3.3 Response Formatting

**Response Formatter (src/langchain_layer/formatter.py)**
```python
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import re
import json

class ResponseType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class FormattedResponse:
    type: ResponseType
    summary: str
    details: str
    raw_output: str
    suggestions: List[str] = None
    metadata: Dict[str, Any] = None

class NetworkResponseFormatter:
    """Format network command responses for user consumption"""

    def __init__(self):
        self.parsers = {
            'show_version': self._parse_show_version,
            'show_interface': self._parse_show_interface,
            'show_ip_route': self._parse_show_ip_route,
            'show_running_config': self._parse_show_running_config,
        }

    def format_response(self, command_name: str, device_name: str,
                       raw_output: str, status: str) -> FormattedResponse:
        """Format command response based on command type"""

        if status.lower() == 'error':
            return self._format_error_response(command_name, device_name, raw_output)

        # Try specific parser first
        parser = self.parsers.get(command_name.lower())
        if parser:
            return parser(device_name, raw_output)

        # Fallback to generic formatting
        return self._format_generic_response(command_name, device_name, raw_output)

    def _format_error_response(self, command_name: str, device_name: str,
                              error_output: str) -> FormattedResponse:
        """Format error responses"""
        return FormattedResponse(
            type=ResponseType.ERROR,
            summary=f"Command '{command_name}' failed on {device_name}",
            details=f"Error executing command on device {device_name}",
            raw_output=error_output,
            suggestions=[
                "Check device connectivity",
                "Verify command syntax",
                "Ensure proper permissions"
            ]
        )

    def _parse_show_version(self, device_name: str, output: str) -> FormattedResponse:
        """Parse show version output"""
        lines = output.split('\n')
        version_info = {}

        for line in lines:
            if 'Version' in line and 'Software' in line:
                version_match = re.search(r'Version\s+([^\s,]+)', line)
                if version_match:
                    version_info['software_version'] = version_match.group(1)
            elif 'uptime' in line.lower():
                version_info['uptime'] = line.strip()
            elif 'System image file' in line:
                image_match = re.search(r'"([^"]+)"', line)
                if image_match:
                    version_info['image_file'] = image_match.group(1)

        summary = f"Device {device_name} - Version: {version_info.get('software_version', 'Unknown')}"

        details = "## Device Information\n"
        for key, value in version_info.items():
            details += f"- {key.replace('_', ' ').title()}: {value}\n"

        return FormattedResponse(
            type=ResponseType.SUCCESS,
            summary=summary,
            details=details,
            raw_output=output,
            metadata=version_info
        )

    def _parse_show_interface(self, device_name: str, output: str) -> FormattedResponse:
        """Parse show interface output"""
        interfaces = []
        current_interface = {}

        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Interface line
            if line.startswith(('GigabitEthernet', 'FastEthernet', 'Ethernet', 'Serial')):
                if current_interface:
                    interfaces.append(current_interface)
                current_interface = {'name': line.split()[0]}

            # Status information
            elif 'line protocol is' in line:
                status_match = re.search(r'(\w+),.*line protocol is (\w+)', line)
                if status_match:
                    current_interface['admin_status'] = status_match.group(1)
                    current_interface['protocol_status'] = status_match.group(2)

            # IP address
            elif 'Internet address is' in line:
                ip_match = re.search(r'Internet address is ([^\s]+)', line)
                if ip_match:
                    current_interface['ip_address'] = ip_match.group(1)

        if current_interface:
            interfaces.append(current_interface)

        summary = f"Found {len(interfaces)} interfaces on {device_name}"

        details = "## Interface Summary\n"
        for intf in interfaces:
            details += f"### {intf.get('name', 'Unknown')}\n"
            details += f"- Admin Status: {intf.get('admin_status', 'Unknown')}\n"
            details += f"- Protocol Status: {intf.get('protocol_status', 'Unknown')}\n"
            if 'ip_address' in intf:
                details += f"- IP Address: {intf['ip_address']}\n"
            details += "\n"

        return FormattedResponse(
            type=ResponseType.SUCCESS,
            summary=summary,
            details=details,
            raw_output=output,
            metadata={'interfaces': interfaces}
        )

    def _parse_show_ip_route(self, device_name: str, output: str) -> FormattedResponse:
        """Parse show ip route output"""
        routes = []

        for line in output.split('\n'):
            line = line.strip()
            if not line or line.startswith('Codes:') or line.startswith('Gateway'):
                continue

            # Route entry
            route_match = re.match(r'([CDSOR*])\s+([0-9./]+)\s+\[([0-9/]+)\]\s+via\s+([0-9.]+)', line)
            if route_match:
                routes.append({
                    'type': route_match.group(1),
                    'network': route_match.group(2),
                    'metric': route_match.group(3),
                    'next_hop': route_match.group(4)
                })

        summary = f"Found {len(routes)} routes on {device_name}"

        details = "## Routing Table Summary\n"
        route_types = {}
        for route in routes:
            route_type = route['type']
            route_types[route_type] = route_types.get(route_type, 0) + 1

        for route_type, count in route_types.items():
            details += f"- {route_type} routes: {count}\n"

        return FormattedResponse(
            type=ResponseType.SUCCESS,
            summary=summary,
            details=details,
            raw_output=output,
            metadata={'routes': routes, 'route_summary': route_types}
        )

    def _parse_show_running_config(self, device_name: str, output: str) -> FormattedResponse:
        """Parse show running-config output"""
        config_sections = {}
        current_section = None

        for line in output.split('\n'):
            line = line.strip()
            if not line or line.startswith('!'):
                continue

            # Section headers
            if not line.startswith(' '):
                current_section = line
                config_sections[current_section] = []
            elif current_section:
                config_sections[current_section].append(line)

        summary = f"Configuration retrieved from {device_name} - {len(config_sections)} sections"

        details = "## Configuration Summary\n"
        for section, lines in config_sections.items():
            details += f"### {section}\n"
            details += f"- {len(lines)} configuration lines\n\n"

        return FormattedResponse(
            type=ResponseType.SUCCESS,
            summary=summary,
            details=details,
            raw_output=output,
            metadata={'config_sections': list(config_sections.keys())}
        )

    def _format_generic_response(self, command_name: str, device_name: str,
                                output: str) -> FormattedResponse:
        """Generic response formatting"""
        lines = output.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        summary = f"Command '{command_name}' executed on {device_name} - {len(non_empty_lines)} lines of output"

        details = f"## Command Output\n```\n{output}\n```"

        return FormattedResponse(
            type=ResponseType.SUCCESS,
            summary=summary,
            details=details,
            raw_output=output
        )

### Phase 4: LangGraph Workflow Engine (Weeks 7-8)

#### 4.1 State Management

**Workflow State (src/langgraph_layer/state.py)**
```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    id: str
    name: str
    command: str
    device: str
    parameters: Dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class WorkflowState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStep] = field(default_factory=list)
    current_step_index: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)

    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current step being executed"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self):
        """Move to the next step"""
        self.current_step_index += 1

    def is_complete(self) -> bool:
        """Check if workflow is complete"""
        return self.current_step_index >= len(self.steps)

    def get_failed_steps(self) -> List[WorkflowStep]:
        """Get all failed steps"""
        return [step for step in self.steps if step.status == StepStatus.FAILED]

    def get_completed_steps(self) -> List[WorkflowStep]:
        """Get all completed steps"""
        return [step for step in self.steps if step.status == StepStatus.COMPLETED]

class WorkflowStateManager:
    """Manage workflow state persistence and retrieval"""

    def __init__(self):
        self._workflows: Dict[str, WorkflowState] = {}

    def create_workflow(self, name: str, description: str = "") -> WorkflowState:
        """Create a new workflow"""
        workflow = WorkflowState(name=name, description=description)
        self._workflows[workflow.id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow by ID"""
        return self._workflows.get(workflow_id)

    def update_workflow(self, workflow: WorkflowState):
        """Update workflow state"""
        self._workflows[workflow.id] = workflow

    def delete_workflow(self, workflow_id: str):
        """Delete workflow"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]

    def list_workflows(self) -> List[WorkflowState]:
        """List all workflows"""
        return list(self._workflows.values())

#### 4.2 Workflow Orchestration

**Workflow Engine (src/langgraph_layer/workflows.py)**
```python
from langgraph import StateGraph, END
from typing import Dict, Any, Callable, List
import asyncio
from datetime import datetime
import logging

from .state import WorkflowState, WorkflowStep, WorkflowStatus, StepStatus
from ..mcp_layer.command_manager import CommandManager
from ..langchain_layer.processor import NaturalLanguageProcessor

logger = logging.getLogger(__name__)

class NetworkWorkflowEngine:
    """LangGraph-based workflow engine for network automation"""

    def __init__(self, command_manager: CommandManager, nl_processor: NaturalLanguageProcessor):
        self.command_manager = command_manager
        self.nl_processor = nl_processor
        self.graph = self._build_workflow_graph()

    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""

        # Define the workflow graph
        workflow = StateGraph(WorkflowState)

        # Add nodes
        workflow.add_node("validate_workflow", self._validate_workflow)
        workflow.add_node("execute_step", self._execute_step)
        workflow.add_node("handle_error", self._handle_error)
        workflow.add_node("complete_workflow", self._complete_workflow)

        # Add edges
        workflow.add_edge("validate_workflow", "execute_step")
        workflow.add_conditional_edges(
            "execute_step",
            self._should_continue,
            {
                "continue": "execute_step",
                "error": "handle_error",
                "complete": "complete_workflow"
            }
        )
        workflow.add_conditional_edges(
            "handle_error",
            self._should_retry,
            {
                "retry": "execute_step",
                "fail": END,
                "skip": "execute_step"
            }
        )
        workflow.add_edge("complete_workflow", END)

        # Set entry point
        workflow.set_entry_point("validate_workflow")

        return workflow.compile()

    async def execute_workflow(self, workflow: WorkflowState) -> WorkflowState:
        """Execute a workflow using LangGraph"""
        try:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()

            # Execute the workflow graph
            result = await self.graph.ainvoke(workflow)

            return result
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = str(e)
            workflow.completed_at = datetime.now()
            return workflow

    async def _validate_workflow(self, state: WorkflowState) -> WorkflowState:
        """Validate workflow before execution"""
        logger.info(f"Validating workflow: {state.name}")

        if not state.steps:
            state.status = WorkflowStatus.FAILED
            state.error_message = "No steps defined in workflow"
            return state

        # Validate each step
        for step in state.steps:
            if not step.command or not step.device:
                state.status = WorkflowStatus.FAILED
                state.error_message = f"Invalid step configuration: {step.name}"
                return state

        logger.info("Workflow validation completed successfully")
        return state

    async def _execute_step(self, state: WorkflowState) -> WorkflowState:
        """Execute the current workflow step"""
        current_step = state.get_current_step()
        if not current_step:
            return state

        logger.info(f"Executing step: {current_step.name}")

        try:
            current_step.status = StepStatus.RUNNING
            current_step.started_at = datetime.now()

            # Execute the command
            result = await self.command_manager.execute_command(
                device_identifier=current_step.device,
                command_name=current_step.command,
                parameters=current_step.parameters
            )

            if result.success:
                current_step.status = StepStatus.COMPLETED
                current_step.output = result.output
                logger.info(f"Step completed successfully: {current_step.name}")
            else:
                current_step.status = StepStatus.FAILED
                current_step.error = result.error
                logger.error(f"Step failed: {current_step.name} - {result.error}")

            current_step.completed_at = datetime.now()

        except Exception as e:
            current_step.status = StepStatus.FAILED
            current_step.error = str(e)
            current_step.completed_at = datetime.now()
            logger.error(f"Step execution error: {current_step.name} - {e}")

        return state

    async def _handle_error(self, state: WorkflowState) -> WorkflowState:
        """Handle step execution errors"""
        current_step = state.get_current_step()
        if not current_step:
            return state

        logger.info(f"Handling error for step: {current_step.name}")

        current_step.retry_count += 1

        # Check if we should retry
        if current_step.retry_count <= current_step.max_retries:
            logger.info(f"Retrying step: {current_step.name} (attempt {current_step.retry_count})")
            current_step.status = StepStatus.PENDING
            return state

        # Max retries exceeded
        logger.error(f"Max retries exceeded for step: {current_step.name}")

        # Check if this is a critical step or if we can continue
        if self._is_critical_step(current_step):
            state.status = WorkflowStatus.FAILED
            state.error_message = f"Critical step failed: {current_step.name}"
        else:
            # Skip this step and continue
            current_step.status = StepStatus.SKIPPED
            state.advance_step()

        return state

    async def _complete_workflow(self, state: WorkflowState) -> WorkflowState:
        """Complete the workflow"""
        logger.info(f"Completing workflow: {state.name}")

        state.status = WorkflowStatus.COMPLETED
        state.completed_at = datetime.now()

        # Generate summary
        completed_steps = state.get_completed_steps()
        failed_steps = state.get_failed_steps()

        logger.info(f"Workflow completed - Success: {len(completed_steps)}, Failed: {len(failed_steps)}")

        return state

    def _should_continue(self, state: WorkflowState) -> str:
        """Determine if workflow should continue"""
        current_step = state.get_current_step()

        if not current_step:
            return "complete"

        if current_step.status == StepStatus.FAILED:
            return "error"

        if current_step.status == StepStatus.COMPLETED:
            state.advance_step()
            if state.is_complete():
                return "complete"
            return "continue"

        return "continue"

    def _should_retry(self, state: WorkflowState) -> str:
        """Determine if failed step should be retried"""
        current_step = state.get_current_step()

        if not current_step:
            return "fail"

        if current_step.retry_count < current_step.max_retries:
            return "retry"

        if self._is_critical_step(current_step):
            return "fail"

        return "skip"

    def _is_critical_step(self, step: WorkflowStep) -> bool:
        """Determine if a step is critical for workflow success"""
        # Define critical step patterns
        critical_patterns = [
            "backup",
            "save",
            "commit",
            "reload"
        ]

        return any(pattern in step.command.lower() for pattern in critical_patterns)

class WorkflowBuilder:
    """Builder class for creating complex workflows"""

    def __init__(self):
        self.steps: List[WorkflowStep] = []

    def add_command_step(self, name: str, command: str, device: str,
                        parameters: Dict[str, Any] = None, max_retries: int = 3) -> 'WorkflowBuilder':
        """Add a command execution step"""
        step = WorkflowStep(
            id=str(uuid.uuid4()),
            name=name,
            command=command,
            device=device,
            parameters=parameters or {},
            max_retries=max_retries
        )
        self.steps.append(step)
        return self

    def add_conditional_step(self, name: str, condition: Callable[[WorkflowState], bool],
                           true_command: str, false_command: str, device: str) -> 'WorkflowBuilder':
        """Add a conditional step (simplified for example)"""
        # This would be expanded to handle conditional logic
        step = WorkflowStep(
            id=str(uuid.uuid4()),
            name=name,
            command=true_command,  # Simplified
            device=device,
            parameters={}
        )
        self.steps.append(step)
        return self

    def build(self, name: str, description: str = "") -> WorkflowState:
        """Build the workflow"""
        workflow = WorkflowState(name=name, description=description)
        workflow.steps = self.steps.copy()
        return workflow

### Phase 5: MCP Integration (Weeks 9-10)

#### 5.1 Context Protocol Implementation

**MCP Context Manager (src/mcp_layer/context_manager.py)**
```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class DeviceContext:
    """Context information for a network device"""
    device_id: str
    hostname: str
    device_type: str
    capabilities: List[str]
    current_config: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)
    connection_status: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CommandContext:
    """Context information for command execution"""
    command_id: str
    command_name: str
    device_context: DeviceContext
    parameters: Dict[str, Any]
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    related_commands: List[str] = field(default_factory=list)

@dataclass
class WorkflowContext:
    """Context information for workflow execution"""
    workflow_id: str
    workflow_name: str
    device_contexts: List[DeviceContext]
    command_contexts: List[CommandContext]
    global_variables: Dict[str, Any] = field(default_factory=dict)
    execution_state: Dict[str, Any] = field(default_factory=dict)

class MCPContextManager:
    """Manage context information according to Model Context Protocol"""

    def __init__(self):
        self.device_contexts: Dict[str, DeviceContext] = {}
        self.command_contexts: Dict[str, CommandContext] = {}
        self.workflow_contexts: Dict[str, WorkflowContext] = {}

    def register_device_context(self, device_context: DeviceContext):
        """Register device context"""
        self.device_contexts[device_context.device_id] = device_context

    def get_device_context(self, device_id: str) -> Optional[DeviceContext]:
        """Get device context by ID"""
        return self.device_contexts.get(device_id)

    def update_device_context(self, device_id: str, updates: Dict[str, Any]):
        """Update device context"""
        if device_id in self.device_contexts:
            context = self.device_contexts[device_id]
            for key, value in updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)
            context.last_updated = datetime.now()

    def create_command_context(self, command_id: str, command_name: str,
                              device_id: str, parameters: Dict[str, Any]) -> CommandContext:
        """Create command execution context"""
        device_context = self.get_device_context(device_id)
        if not device_context:
            raise ValueError(f"Device context not found: {device_id}")

        command_context = CommandContext(
            command_id=command_id,
            command_name=command_name,
            device_context=device_context,
            parameters=parameters
        )

        self.command_contexts[command_id] = command_context
        return command_context

    def update_command_context(self, command_id: str, execution_result: Dict[str, Any]):
        """Update command context with execution results"""
        if command_id in self.command_contexts:
            context = self.command_contexts[command_id]
            context.execution_history.append({
                'timestamp': datetime.now().isoformat(),
                'result': execution_result
            })

    def create_workflow_context(self, workflow_id: str, workflow_name: str,
                               device_ids: List[str]) -> WorkflowContext:
        """Create workflow execution context"""
        device_contexts = []
        for device_id in device_ids:
            device_context = self.get_device_context(device_id)
            if device_context:
                device_contexts.append(device_context)

        workflow_context = WorkflowContext(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            device_contexts=device_contexts,
            command_contexts=[]
        )

        self.workflow_contexts[workflow_id] = workflow_context
        return workflow_context

    def get_contextual_recommendations(self, device_id: str,
                                     command_name: str) -> List[Dict[str, Any]]:
        """Get contextual recommendations based on device and command history"""
        device_context = self.get_device_context(device_id)
        if not device_context:
            return []

        recommendations = []

        # Check device capabilities
        if command_name not in device_context.capabilities:
            recommendations.append({
                'type': 'warning',
                'message': f'Command {command_name} may not be supported on {device_context.device_type}'
            })

        # Check related commands
        related_commands = self._find_related_commands(command_name)
        if related_commands:
            recommendations.append({
                'type': 'suggestion',
                'message': f'Consider running these related commands: {", ".join(related_commands)}'
            })

        return recommendations

    def _find_related_commands(self, command_name: str) -> List[str]:
        """Find commands related to the given command"""
        # Simple relationship mapping - could be enhanced with ML
        relationships = {
            'show_interface': ['show_ip_interface_brief', 'show_interface_status'],
            'show_version': ['show_inventory', 'show_license'],
            'show_running_config': ['show_startup_config', 'show_archive'],
        }

        return relationships.get(command_name, [])

#### 5.2 Device Context Management

**Device Context Handler (src/mcp_layer/device_context.py)**
```python
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from .context_manager import MCPContextManager, DeviceContext
from ..network_layer.connectors.base_connector import BaseConnector

class DeviceContextHandler:
    """Handle device context collection and management"""

    def __init__(self, context_manager: MCPContextManager):
        self.context_manager = context_manager
        self.context_refresh_interval = timedelta(minutes=30)

    async def initialize_device_context(self, device_config: Dict[str, Any],
                                       connector: BaseConnector) -> DeviceContext:
        """Initialize context for a new device"""

        # Gather basic device information
        device_info = await self._gather_device_info(connector)

        device_context = DeviceContext(
            device_id=device_config['id'],
            hostname=device_config['hostname'],
            device_type=device_config['device_type'],
            capabilities=await self._discover_capabilities(connector, device_config['device_type']),
            connection_status='connected' if connector.is_connected() else 'disconnected',
            metadata=device_info
        )

        self.context_manager.register_device_context(device_context)
        return device_context

    async def refresh_device_context(self, device_id: str, connector: BaseConnector):
        """Refresh device context information"""
        device_context = self.context_manager.get_device_context(device_id)
        if not device_context:
            return

        # Check if refresh is needed
        if datetime.now() - device_context.last_updated < self.context_refresh_interval:
            return

        # Gather updated information
        device_info = await self._gather_device_info(connector)

        updates = {
            'connection_status': 'connected' if connector.is_connected() else 'disconnected',
            'metadata': device_info
        }

        self.context_manager.update_device_context(device_id, updates)

    async def _gather_device_info(self, connector: BaseConnector) -> Dict[str, Any]:
        """Gather basic device information"""
        device_info = {}

        try:
            # Get version information
            version_result = await connector.execute_command('show version')
            if version_result.success:
                device_info['version_output'] = version_result.output
                device_info['last_version_check'] = datetime.now().isoformat()

            # Get interface summary
            interface_result = await connector.execute_command('show ip interface brief')
            if interface_result.success:
                device_info['interface_summary'] = interface_result.output
                device_info['interface_count'] = len([
                    line for line in interface_result.output.split('\n')
                    if line.strip() and not line.startswith('Interface')
                ])

        except Exception as e:
            device_info['error'] = f"Failed to gather device info: {str(e)}"

        return device_info

    async def _discover_capabilities(self, connector: BaseConnector,
                                   device_type: str) -> List[str]:
        """Discover device capabilities"""
        capabilities = []

        # Basic capabilities based on device type
        type_capabilities = {
            'cisco_ios': [
                'show_version', 'show_running_config', 'show_interface',
                'show_ip_route', 'show_ip_interface_brief', 'configure_terminal'
            ],
            'cisco_nxos': [
                'show_version', 'show_running_config', 'show_interface',
                'show_ip_route', 'show_interface_brief', 'configure_terminal'
            ],
            'juniper_junos': [
                'show_version', 'show_configuration', 'show_interfaces',
                'show_route', 'show_interfaces_terse', 'configure'
            ]
        }

        capabilities.extend(type_capabilities.get(device_type, []))

        # Test specific commands to verify capabilities
        test_commands = ['show version', 'show ?']
        for command in test_commands:
            try:
                result = await connector.execute_command(command)
                if result.success and 'invalid' not in result.output.lower():
                    capabilities.append(f"verified_{command.replace(' ', '_')}")
            except:
                pass

        return capabilities

#### 5.3 Command Context Handling

**Command Context Handler (src/mcp_layer/command_context.py)**
```python
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .context_manager import MCPContextManager, CommandContext
from ..core.models import Command, ExecutionLog

class CommandContextHandler:
    """Handle command execution context"""

    def __init__(self, context_manager: MCPContextManager):
        self.context_manager = context_manager

    async def prepare_command_context(self, command: Command, device_id: str,
                                    parameters: Dict[str, Any]) -> CommandContext:
        """Prepare context for command execution"""

        command_id = str(uuid.uuid4())

        # Create command context
        command_context = self.context_manager.create_command_context(
            command_id=command_id,
            command_name=command.command_name,
            device_id=device_id,
            parameters=parameters
        )

        # Add related commands based on context
        command_context.related_commands = self._get_related_commands(
            command.command_name,
            command_context.device_context
        )

        return command_context

    async def update_execution_context(self, command_context: CommandContext,
                                     execution_result: Dict[str, Any]):
        """Update context after command execution"""

        self.context_manager.update_command_context(
            command_context.command_id,
            execution_result
        )

        # Update device context if needed
        if execution_result.get('success'):
            await self._update_device_context_from_command(
                command_context,
                execution_result
            )

    def _get_related_commands(self, command_name: str,
                            device_context) -> List[str]:
        """Get commands related to the current command"""

        # Context-aware related commands
        related_map = {
            'show_interface': {
                'cisco_ios': ['show ip interface brief', 'show interface status'],
                'juniper_junos': ['show interfaces terse', 'show interfaces detail']
            },
            'show_running_config': {
                'cisco_ios': ['show startup-config', 'show archive'],
                'juniper_junos': ['show configuration', 'show system commit']
            }
        }

        device_type = device_context.device_type
        return related_map.get(command_name, {}).get(device_type, [])

    async def _update_device_context_from_command(self, command_context: CommandContext,
                                                execution_result: Dict[str, Any]):
        """Update device context based on command execution results"""

        command_name = command_context.command_name
        device_id = command_context.device_context.device_id
        output = execution_result.get('output', '')

        updates = {}

        # Update context based on specific commands
        if command_name == 'show_running_config':
            updates['current_config'] = output
        elif command_name == 'show_version':
            # Extract version information
            if 'Version' in output:
                updates['metadata'] = {
                    **command_context.device_context.metadata,
                    'last_version_output': output,
                    'version_last_checked': datetime.now().isoformat()
                }

        if updates:
            self.context_manager.update_device_context(device_id, updates)

### Phase 6: Testing and Validation (Weeks 11-12)

#### 6.1 Unit Testing

**Test Configuration (tests/conftest.py)**
```python
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.core.models import Base
from src.core.database import get_db
from src.api.main import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Create a test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_device_data():
    """Sample device data for testing"""
    return {
        "device_type": "cisco_ios",
        "hostname": "test-router-01",
        "ip_address": "192.168.1.1",
        "connection_details": {
            "username": "admin",
            "password": "password",
            "port": 22
        },
        "capabilities": ["show_version", "show_interface"]
    }

@pytest.fixture
def sample_command_data():
    """Sample command data for testing"""
    return {
        "command_name": "show_interface",
        "command_template": "show interface {interface}",
        "device_types": ["cisco_ios"],
        "parameters": {
            "interface": {
                "type": "string",
                "required": True,
                "description": "Interface name"
            }
        },
        "description": "Show interface information"
    }
```

**Device API Tests (tests/test_devices.py)**
```python
import pytest
from fastapi import status

def test_create_device(client, sample_device_data):
    """Test device creation"""
    response = client.post("/api/v1/devices/", json=sample_device_data)
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["hostname"] == sample_device_data["hostname"]
    assert data["device_type"] == sample_device_data["device_type"]
    assert "id" in data

def test_get_device(client, sample_device_data):
    """Test device retrieval"""
    # Create device
    create_response = client.post("/api/v1/devices/", json=sample_device_data)
    device_id = create_response.json()["id"]

    # Get device
    response = client.get(f"/api/v1/devices/{device_id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == device_id
    assert data["hostname"] == sample_device_data["hostname"]

def test_list_devices(client, sample_device_data):
    """Test device listing"""
    # Create multiple devices
    for i in range(3):
        device_data = sample_device_data.copy()
        device_data["hostname"] = f"test-router-{i:02d}"
        client.post("/api/v1/devices/", json=device_data)

    # List devices
    response = client.get("/api/v1/devices/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 3

def test_update_device(client, sample_device_data):
    """Test device update"""
    # Create device
    create_response = client.post("/api/v1/devices/", json=sample_device_data)
    device_id = create_response.json()["id"]

    # Update device
    updated_data = sample_device_data.copy()
    updated_data["hostname"] = "updated-router"

    response = client.put(f"/api/v1/devices/{device_id}", json=updated_data)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["hostname"] == "updated-router"

def test_delete_device(client, sample_device_data):
    """Test device deletion"""
    # Create device
    create_response = client.post("/api/v1/devices/", json=sample_device_data)
    device_id = create_response.json()["id"]

    # Delete device
    response = client.delete(f"/api/v1/devices/{device_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/api/v1/devices/{device_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

def test_create_duplicate_device(client, sample_device_data):
    """Test creating device with duplicate hostname"""
    # Create first device
    client.post("/api/v1/devices/", json=sample_device_data)

    # Try to create duplicate
    response = client.post("/api/v1/devices/", json=sample_device_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
```

**LangChain Integration Tests (tests/test_langchain.py)**
```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.langchain_layer.processor import NaturalLanguageProcessor

@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    mock = Mock()
    mock.arun = AsyncMock()
    return mock

@pytest.fixture
def nl_processor(mock_llm):
    """Natural language processor with mocked LLM"""
    processor = NaturalLanguageProcessor("test-api-key")
    processor.llm = mock_llm
    return processor

@pytest.mark.asyncio
async def test_process_user_input(nl_processor, mock_llm):
    """Test natural language input processing"""
    # Mock LLM response
    mock_llm.arun.return_value = {
        "command": "show_interface",
        "device": "router1",
        "parameters": {"interface": "GigabitEthernet0/1"}
    }

    context = {
        "devices": ["router1", "router2"],
        "commands": ["show_interface", "show_version"]
    }

    result = await nl_processor.process_user_input(
        "Show me the status of GigabitEthernet0/1 on router1",
        context
    )

    assert result["command"] == "show_interface"
    assert result["device"] == "router1"
    assert result["parameters"]["interface"] == "GigabitEthernet0/1"

@pytest.mark.asyncio
async def test_format_response(nl_processor, mock_llm):
    """Test response formatting"""
    mock_llm.arun.return_value = "Formatted response"

    result = await nl_processor.format_response(
        "show_interface",
        "router1",
        "Interface GigabitEthernet0/1 is up, line protocol is up"
    )

    assert result == "Formatted response"
    mock_llm.arun.assert_called_once()

#### 6.2 Integration Testing

**Workflow Integration Tests (tests/test_integration.py)**
```python
import pytest
from unittest.mock import Mock, AsyncMock
from src.langgraph_layer.workflows import NetworkWorkflowEngine, WorkflowBuilder
from src.langgraph_layer.state import WorkflowState, WorkflowStep, StepStatus

@pytest.fixture
def mock_command_manager():
    """Mock command manager"""
    mock = Mock()
    mock.execute_command = AsyncMock()
    return mock

@pytest.fixture
def mock_nl_processor():
    """Mock natural language processor"""
    mock = Mock()
    mock.process_user_input = AsyncMock()
    return mock

@pytest.fixture
def workflow_engine(mock_command_manager, mock_nl_processor):
    """Workflow engine with mocked dependencies"""
    return NetworkWorkflowEngine(mock_command_manager, mock_nl_processor)

@pytest.mark.asyncio
async def test_simple_workflow_execution(workflow_engine, mock_command_manager):
    """Test simple workflow execution"""
    # Mock successful command execution
    mock_command_manager.execute_command.return_value = Mock(
        success=True,
        output="Command executed successfully"
    )

    # Create simple workflow
    workflow = WorkflowBuilder() \
        .add_command_step("Check version", "show_version", "router1") \
        .add_command_step("Check interfaces", "show_interface", "router1") \
        .build("Test Workflow", "Simple test workflow")

    # Execute workflow
    result = await workflow_engine.execute_workflow(workflow)

    # Verify results
    assert result.status.value == "completed"
    assert len(result.get_completed_steps()) == 2
    assert len(result.get_failed_steps()) == 0

@pytest.mark.asyncio
async def test_workflow_with_failure(workflow_engine, mock_command_manager):
    """Test workflow handling of command failures"""
    # Mock command failure
    mock_command_manager.execute_command.return_value = Mock(
        success=False,
        error="Connection timeout"
    )

    # Create workflow with non-critical step
    workflow = WorkflowBuilder() \
        .add_command_step("Check version", "show_version", "router1", max_retries=1) \
        .build("Test Workflow", "Failure test workflow")

    # Execute workflow
    result = await workflow_engine.execute_workflow(workflow)

    # Verify failure handling
    assert result.status.value == "failed"
    assert len(result.get_failed_steps()) == 1

#### 6.3 End-to-End Testing

**E2E Test Suite (tests/test_e2e.py)**
```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.api.main import app

@pytest.mark.e2e
class TestEndToEndWorkflow:
    """End-to-end workflow tests"""

    def test_complete_device_management_workflow(self, client):
        """Test complete device management workflow"""

        # 1. Create device
        device_data = {
            "device_type": "cisco_ios",
            "hostname": "e2e-router",
            "ip_address": "192.168.1.100",
            "connection_details": {
                "username": "admin",
                "password": "password"
            },
            "capabilities": ["show_version", "show_interface"]
        }

        create_response = client.post("/api/v1/devices/", json=device_data)
        assert create_response.status_code == 201
        device_id = create_response.json()["id"]

        # 2. Create command template
        command_data = {
            "command_name": "show_interface_status",
            "command_template": "show interface {interface} status",
            "device_types": ["cisco_ios"],
            "parameters": {
                "interface": {
                    "type": "string",
                    "required": True
                }
            },
            "description": "Show interface status"
        }

        command_response = client.post("/api/v1/commands/", json=command_data)
        assert command_response.status_code == 201
        command_id = command_response.json()["id"]

        # 3. Render command with parameters
        render_response = client.post(
            f"/api/v1/commands/{command_id}/render",
            json={"interface": "GigabitEthernet0/1"}
        )
        assert render_response.status_code == 200
        rendered_command = render_response.json()["rendered_command"]
        assert "GigabitEthernet0/1" in rendered_command

        # 4. Clean up
        client.delete(f"/api/v1/devices/{device_id}")
        client.delete(f"/api/v1/commands/{command_id}")

#### 6.4 Performance Testing

**Performance Test Suite (tests/test_performance.py)**
```python
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

@pytest.mark.performance
class TestPerformance:
    """Performance test suite"""

    def test_device_creation_performance(self, client):
        """Test device creation performance"""
        start_time = time.time()

        # Create 100 devices
        for i in range(100):
            device_data = {
                "device_type": "cisco_ios",
                "hostname": f"perf-router-{i:03d}",
                "ip_address": f"192.168.1.{i+1}",
                "connection_details": {"username": "admin", "password": "password"},
                "capabilities": ["show_version"]
            }
            response = client.post("/api/v1/devices/", json=device_data)
            assert response.status_code == 201

        end_time = time.time()
        duration = end_time - start_time

        # Should create 100 devices in less than 10 seconds
        assert duration < 10.0
        print(f"Created 100 devices in {duration:.2f} seconds")

    def test_concurrent_api_requests(self, client):
        """Test concurrent API request handling"""

        def make_request(i):
            response = client.get("/api/v1/devices/")
            return response.status_code == 200

        start_time = time.time()

        # Make 50 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [future.result() for future in futures]

        end_time = time.time()
        duration = end_time - start_time

        # All requests should succeed
        assert all(results)

        # Should handle 50 concurrent requests in less than 5 seconds
        assert duration < 5.0
        print(f"Handled 50 concurrent requests in {duration:.2f} seconds")

---

## Integration Points

### 1. **LangChain ↔ LangGraph Integration**

**Workflow Trigger (src/integration/langchain_langgraph.py)**
```python
from typing import Dict, Any
from src.langchain_layer.processor import NaturalLanguageProcessor
from src.langgraph_layer.workflows import NetworkWorkflowEngine, WorkflowBuilder

class LangChainLangGraphBridge:
    """Bridge between LangChain and LangGraph components"""

    def __init__(self, nl_processor: NaturalLanguageProcessor,
                 workflow_engine: NetworkWorkflowEngine):
        self.nl_processor = nl_processor
        self.workflow_engine = workflow_engine

    async def process_natural_language_workflow(self, user_input: str,
                                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Process natural language input and create workflow"""

        # 1. Parse user input with LangChain
        parsed_input = await self.nl_processor.process_user_input(user_input, context)

        if "error" in parsed_input:
            return parsed_input

        # 2. Determine if this requires a workflow
        if self._requires_workflow(parsed_input):
            # Create workflow with LangGraph
            workflow = self._create_workflow_from_parsed_input(parsed_input)
            result = await self.workflow_engine.execute_workflow(workflow)

            # 3. Format results with LangChain
            formatted_result = await self._format_workflow_result(result)
            return formatted_result
        else:
            # Single command execution
            return await self._execute_single_command(parsed_input)

    def _requires_workflow(self, parsed_input: Dict[str, Any]) -> bool:
        """Determine if input requires workflow execution"""
        # Check for workflow indicators
        workflow_keywords = [
            "backup and configure",
            "check status then restart",
            "compare configurations",
            "deploy configuration"
        ]

        original_input = parsed_input.get("original_input", "").lower()
        return any(keyword in original_input for keyword in workflow_keywords)

    def _create_workflow_from_parsed_input(self, parsed_input: Dict[str, Any]):
        """Create workflow from parsed input"""
        builder = WorkflowBuilder()

        # Example: "backup and configure" workflow
        if "backup" in parsed_input.get("original_input", "").lower():
            builder.add_command_step(
                "Backup Configuration",
                "show_running_config",
                parsed_input["device"]
            ).add_command_step(
                "Apply Configuration",
                parsed_input["command"],
                parsed_input["device"],
                parsed_input.get("parameters", {})
            )

        return builder.build("Auto-generated Workflow")

### 2. **MCP ↔ Database Integration**

**Context Persistence (src/integration/mcp_database.py)**
```python
from sqlalchemy.orm import Session
from src.mcp_layer.context_manager import MCPContextManager, DeviceContext
from src.core.database import get_db

class MCPDatabaseBridge:
    """Bridge between MCP context and database persistence"""

    def __init__(self, context_manager: MCPContextManager):
        self.context_manager = context_manager

    async def persist_device_context(self, device_context: DeviceContext, db: Session):
        """Persist device context to database"""
        # Update device record with context information
        from src.core.models import Device

        device = db.query(Device).filter(Device.id == device_context.device_id).first()
        if device:
            # Update metadata with context information
            context_metadata = {
                "last_context_update": device_context.last_updated.isoformat(),
                "connection_status": device_context.connection_status,
                "context_metadata": device_context.metadata
            }

            # Merge with existing metadata
            if device.connection_details:
                device.connection_details.update(context_metadata)
            else:
                device.connection_details = context_metadata

            db.commit()

    async def load_device_context(self, device_id: str, db: Session) -> DeviceContext:
        """Load device context from database"""
        from src.core.models import Device

        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise ValueError(f"Device not found: {device_id}")

        # Create device context from database record
        device_context = DeviceContext(
            device_id=str(device.id),
            hostname=device.hostname,
            device_type=device.device_type,
            capabilities=device.capabilities or [],
            connection_status=device.connection_details.get("connection_status", "unknown"),
            metadata=device.connection_details.get("context_metadata", {})
        )

        # Register with context manager
        self.context_manager.register_device_context(device_context)
        return device_context

---

## Testing and Validation

### Test Execution Commands

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m "not performance and not e2e"  # Unit and integration tests
pytest -m performance                     # Performance tests
pytest -m e2e                            # End-to-end tests

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test files
pytest tests/test_devices.py
pytest tests/test_langchain.py
pytest tests/test_integration.py
```

### Validation Checklist

#### ✅ **Functional Validation**
- [ ] Device CRUD operations work correctly
- [ ] Command template management functions properly
- [ ] Natural language processing interprets commands accurately
- [ ] Workflow execution handles success and failure scenarios
- [ ] MCP context management maintains state correctly
- [ ] Database operations are atomic and consistent

#### ✅ **Integration Validation**
- [ ] LangChain → LangGraph workflow creation works
- [ ] MCP context integrates with database persistence
- [ ] FastAPI endpoints respond correctly
- [ ] Network connectors establish connections successfully
- [ ] Error handling propagates through all layers

#### ✅ **Performance Validation**
- [ ] API response times under 500ms for simple operations
- [ ] Database queries execute efficiently
- [ ] Concurrent request handling scales appropriately
- [ ] Memory usage remains stable under load
- [ ] Network connections are properly pooled and reused

#### ✅ **Security Validation**
- [ ] Database credentials are properly secured
- [ ] API authentication works correctly
- [ ] Network device credentials are encrypted
- [ ] Input validation prevents injection attacks
- [ ] Error messages don't leak sensitive information

---

## Deployment and Production Considerations

### Environment Configuration

```bash
# Production environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/network_automation"
export OPENAI_API_KEY="your-openai-api-key"
export SECRET_KEY="your-secret-key"
export ENVIRONMENT="production"
export LOG_LEVEL="INFO"
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Monitoring and Logging

```python
# Production logging configuration
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
```

---

## Conclusion

This comprehensive development procedure provides a structured approach to building a hybrid LangGraph/LangChain/MCP network automation system. The architecture leverages the strengths of each component:

- **LangChain** for natural language processing and user interaction
- **LangGraph** for complex workflow orchestration and state management
- **MCP** for standardized context management
- **PostgreSQL + FastAPI** for scalable data persistence and API services
- **pyATS/Genie** for robust network device connectivity and intelligent command parsing

The modular design ensures maintainability, scalability, and extensibility while providing a robust foundation for enterprise network automation requirements.
```
