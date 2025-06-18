# MCP Technical Walkthrough
## Model Context Protocol Implementation in Hybrid Network Automation System

### Architecture Clarification

Your understanding is **mostly correct** with some important refinements. Let me clarify the MCP architecture and how it integrates with our system:

## 1. MCP Architecture Integration

### **Corrected MCP Component Roles**

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangChain/LangGraph Layer                    │
│                      (MCP CLIENT)                               │
│  • Requests context for command interpretation                  │
│  • Consumes device capabilities and command history            │
│  • Provides workflow state updates                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ (MCP Protocol)
┌─────────────────────────────────────────────────────────────────┐
│                     MCP SERVER                                  │
│                  (FastAPI Application)                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Device Tools  │  │  Command Tools  │  │ Workflow Tools  │ │
│  │   • get_device  │  │  • execute_cmd  │  │ • save_state    │ │
│  │   • list_caps   │  │  • get_history  │  │ • get_context   │ │
│  │   • update_ctx  │  │  • validate_cmd │  │ • update_flow   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Database Integration Layer                     │
│                     (PostgreSQL)                               │
│  • Device inventory and capabilities                           │
│  • Command templates and execution history                     │
│  • Workflow state and context persistence                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Network Execution Layer                       │
│                    (pyATS/Genie)                              │
│  • Actual device connections and command execution             │
│  • Parser integration and structured output                    │
│  • Connection state management                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Architectural Points**:

1. **MCP Server = FastAPI Application**: Our FastAPI backend serves as the MCP server, exposing tools via HTTP endpoints
2. **MCP Client = LangChain/LangGraph**: These components consume MCP tools to get context and execute operations
3. **No Separate Bridge**: The FastAPI application directly integrates with PostgreSQL and pyATS/Genie
4. **Tool-Based Interface**: MCP tools are FastAPI endpoints that provide specific functionality

---

## 2. MCP Tool Implementation Examples

### **Device Management Tools**

```python
# src/mcp_server/device_tools.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..core.database import get_db
from ..core.models import Device
from ..network_layer.connectors.genie_connector import GenieConnector

router = APIRouter(prefix="/mcp/tools/devices", tags=["MCP Device Tools"])

class DeviceContextRequest(BaseModel):
    device_id: Optional[str] = None
    hostname: Optional[str] = None
    include_capabilities: bool = True
    include_status: bool = True

class DeviceContextResponse(BaseModel):
    device_id: str
    hostname: str
    device_type: str
    os_type: str
    capabilities: List[str]
    connection_status: str
    last_seen: Optional[str]
    metadata: Dict[str, Any]

@router.post("/get_device_context", response_model=DeviceContextResponse)
async def get_device_context(
    request: DeviceContextRequest,
    db: Session = Depends(get_db)
) -> DeviceContextResponse:
    """
    MCP Tool: Get comprehensive device context
    Used by LangChain to understand device capabilities before command interpretation
    """
    
    # Find device by ID or hostname
    query = db.query(Device)
    if request.device_id:
        device = query.filter(Device.id == int(request.device_id)).first()
    elif request.hostname:
        device = query.filter(Device.hostname == request.hostname).first()
    else:
        raise HTTPException(status_code=400, detail="Must provide device_id or hostname")
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get real-time connection status if requested
    connection_status = "unknown"
    if request.include_status:
        try:
            connector = GenieConnector(device.to_dict())
            connection_result = await connector.connect()
            connection_status = "connected" if connection_result.success else "disconnected"
            await connector.disconnect()
        except Exception:
            connection_status = "error"
    
    return DeviceContextResponse(
        device_id=str(device.id),
        hostname=device.hostname,
        device_type=device.device_type,
        os_type=device.os_type,
        capabilities=device.capabilities or [],
        connection_status=connection_status,
        last_seen=device.last_connected.isoformat() if device.last_connected else None,
        metadata=device.connection_details or {}
    )

@router.get("/list_device_capabilities/{device_id}")
async def list_device_capabilities(
    device_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    MCP Tool: List available capabilities for a device
    Used by LangChain to determine what commands are possible
    """
    
    device = db.query(Device).filter(Device.id == int(device_id)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get available parsers from Genie
    connector = GenieConnector(device.to_dict())
    available_parsers = connector.get_supported_commands()
    
    return {
        "device_id": device_id,
        "hostname": device.hostname,
        "device_type": device.device_type,
        "capabilities": {
            "commands": device.capabilities or [],
            "parsers": available_parsers,
            "protocols": ["ssh", "telnet"] if device.device_type.startswith("cisco") else ["ssh"],
            "features": {
                "config_management": True,
                "monitoring": True,
                "troubleshooting": True
            }
        }
    }

@router.post("/update_device_context")
async def update_device_context(
    device_id: str,
    context_updates: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    MCP Tool: Update device context after operations
    Used by LangGraph workflows to update device state
    """
    
    device = db.query(Device).filter(Device.id == int(device_id)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update connection details with new context
    if device.connection_details:
        device.connection_details.update(context_updates)
    else:
        device.connection_details = context_updates
    
    # Update last connected time if status changed to connected
    if context_updates.get("connection_status") == "connected":
        from datetime import datetime
        device.last_connected = datetime.now()
    
    db.commit()
    
    return {"status": "success", "message": "Device context updated"}
```

### **Command Management Tools**

```python
# src/mcp_server/command_tools.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from ..core.database import get_db
from ..core.models import CommandTemplate, CommandExecution, Device
from ..network_layer.connectors.genie_connector import GenieConnector

router = APIRouter(prefix="/mcp/tools/commands", tags=["MCP Command Tools"])

class CommandExecutionRequest(BaseModel):
    command_name: str
    device_id: str
    parameters: Dict[str, Any] = {}
    workflow_id: Optional[str] = None
    execution_context: Dict[str, Any] = {}

class CommandExecutionResponse(BaseModel):
    execution_id: str
    success: bool
    output: Dict[str, Any]
    execution_time: float
    parser_used: Optional[str]
    error_message: Optional[str]

@router.post("/execute_command", response_model=CommandExecutionResponse)
async def execute_command(
    request: CommandExecutionRequest,
    db: Session = Depends(get_db)
) -> CommandExecutionResponse:
    """
    MCP Tool: Execute command on device with full context tracking
    Used by LangGraph workflows for actual command execution
    """
    
    # Get command template
    command_template = db.query(CommandTemplate).filter(
        CommandTemplate.command_name == request.command_name,
        CommandTemplate.is_active == True
    ).first()
    
    if not command_template:
        raise HTTPException(
            status_code=404, 
            detail=f"Active command template not found: {request.command_name}"
        )
    
    # Get device
    device = db.query(Device).filter(Device.id == int(request.device_id)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Validate device supports this command
    if (command_template.device_types and 
        device.device_type not in command_template.device_types):
        raise HTTPException(
            status_code=400,
            detail=f"Command {request.command_name} not supported on {device.device_type}"
        )
    
    # Render command with parameters
    try:
        rendered_command = command_template.command_template.format(**request.parameters)
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required parameter: {e}"
        )
    
    # Execute command
    start_time = datetime.now()
    
    try:
        connector = GenieConnector(device.to_dict())
        await connector.connect()
        
        result = await connector.execute_command(rendered_command)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Create execution record
        execution_record = CommandExecution(
            command_template_id=command_template.id,
            device_id=device.id,
            workflow_id=request.workflow_id,
            executed_command=rendered_command,
            parameters_used=request.parameters,
            execution_status='success' if result.success else 'failed',
            raw_output=result.output.get('raw', '') if result.success else '',
            parsed_output=result.output.get('parsed', {}) if result.success else {},
            parser_used=result.output.get('parser_used', '') if result.success else '',
            execution_time=datetime.now() - start_time,
            error_message=result.error if not result.success else None
        )
        
        db.add(execution_record)
        db.commit()
        db.refresh(execution_record)
        
        await connector.disconnect()
        
        return CommandExecutionResponse(
            execution_id=str(execution_record.id),
            success=result.success,
            output=result.output if result.success else {},
            execution_time=execution_time,
            parser_used=result.output.get('parser_used') if result.success else None,
            error_message=result.error if not result.success else None
        )
        
    except Exception as e:
        # Record failed execution
        execution_record = CommandExecution(
            command_template_id=command_template.id,
            device_id=device.id,
            workflow_id=request.workflow_id,
            executed_command=rendered_command,
            parameters_used=request.parameters,
            execution_status='error',
            error_message=str(e),
            execution_time=datetime.now() - start_time
        )
        
        db.add(execution_record)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")

@router.get("/get_command_history/{device_id}")
async def get_command_history(
    device_id: str,
    limit: int = 10,
    command_name: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    MCP Tool: Get command execution history for context
    Used by LangChain to understand previous operations and patterns
    """
    
    query = db.query(CommandExecution).filter(
        CommandExecution.device_id == int(device_id)
    )
    
    if command_name:
        query = query.join(CommandTemplate).filter(
            CommandTemplate.command_name == command_name
        )
    
    executions = query.order_by(
        CommandExecution.executed_at.desc()
    ).limit(limit).all()
    
    history = []
    for execution in executions:
        history.append({
            "execution_id": execution.id,
            "command_name": execution.command_template.command_name,
            "executed_command": execution.executed_command,
            "parameters": execution.parameters_used,
            "status": execution.execution_status,
            "execution_time": execution.execution_time.total_seconds() if execution.execution_time else 0,
            "executed_at": execution.executed_at.isoformat(),
            "parser_used": execution.parser_used,
            "has_parsed_output": bool(execution.parsed_output)
        })
    
    return history

@router.post("/validate_command")
async def validate_command(
    command_name: str,
    device_id: str,
    parameters: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    MCP Tool: Validate command before execution
    Used by LangChain to check if command is valid for device
    """
    
    # Get command template
    command_template = db.query(CommandTemplate).filter(
        CommandTemplate.command_name == command_name,
        CommandTemplate.is_active == True
    ).first()
    
    if not command_template:
        return {
            "valid": False,
            "error": f"Command template not found: {command_name}"
        }
    
    # Get device
    device = db.query(Device).filter(Device.id == int(device_id)).first()
    if not device:
        return {
            "valid": False,
            "error": "Device not found"
        }
    
    # Check device type compatibility
    if (command_template.device_types and 
        device.device_type not in command_template.device_types):
        return {
            "valid": False,
            "error": f"Command not supported on {device.device_type}"
        }
    
    # Validate parameters
    required_params = command_template.parameters or {}
    missing_params = []
    
    for param_name, param_config in required_params.items():
        if param_config.get("required", False) and param_name not in parameters:
            missing_params.append(param_name)
    
    if missing_params:
        return {
            "valid": False,
            "error": f"Missing required parameters: {', '.join(missing_params)}"
        }
    
    # Try to render command template
    try:
        rendered_command = command_template.command_template.format(**parameters)
        return {
            "valid": True,
            "rendered_command": rendered_command,
            "estimated_execution_time": 5.0  # Could be enhanced with ML prediction
        }
    except KeyError as e:
        return {
            "valid": False,
            "error": f"Parameter error: {str(e)}"
        }
```

---

## 3. Context Flow Analysis

### **Step-by-Step Context Flow: Cisco WLC Command Execution**

Let's trace the complete context flow for the user request: *"Show me the status of all access points on WLC-CORP-01"*

#### **Step 1: User Input Processing**
```python
# User input received by CLI/Web interface
user_input = "Show me the status of all access points on WLC-CORP-01"

# FastAPI endpoint receives request
@app.post("/api/v1/natural-language/process")
async def process_natural_language(request: NLProcessRequest):
    # LangChain (MCP Client) requests device context
    device_context = await mcp_client.call_tool(
        "get_device_context",
        {"hostname": "WLC-CORP-01", "include_capabilities": True}
    )

    # LangChain processes with context
    parsed_command = await langchain_processor.process_with_context(
        user_input, device_context
    )

    return parsed_command
```

#### **Step 2: MCP Device Context Retrieval**
```python
# MCP Server (FastAPI) processes device context request
@router.post("/mcp/tools/devices/get_device_context")
async def get_device_context(request: DeviceContextRequest, db: Session = Depends(get_db)):

    # Query PostgreSQL for device information
    device = db.query(Device).filter(Device.hostname == "WLC-CORP-01").first()

    # Real-time status check via pyATS/Genie
    connector = GenieConnector(device.to_dict())
    connection_result = await connector.connect()

    # Return comprehensive context
    return DeviceContextResponse(
        device_id="1001",
        hostname="WLC-CORP-01",
        device_type="cisco_wlc",
        os_type="aireos",
        capabilities=["show_ap_summary", "show_ap_config", "show_client_summary"],
        connection_status="connected",
        metadata={
            "software_version": "8.10.185.0",
            "model": "AIR-CT5520-K9",
            "ap_count": 24,
            "supported_parsers": ["show_ap_summary", "show_wlan_summary"]
        }
    )
```

#### **Step 3: LangChain Command Interpretation**
```python
# LangChain processes user input with device context
class NetworkCommandProcessor:
    async def process_with_context(self, user_input: str, device_context: Dict[str, Any]):

        # Create context-aware prompt
        prompt = f"""
        User Request: {user_input}

        Device Context:
        - Hostname: {device_context['hostname']}
        - Type: {device_context['device_type']}
        - Available Commands: {device_context['capabilities']}
        - Connection Status: {device_context['connection_status']}

        Determine the appropriate command and parameters.
        """

        # LLM processing with context
        result = await self.llm.arun(prompt)

        # Parse LLM response
        return {
            "command_name": "show_ap_summary",
            "device_id": device_context['device_id'],
            "parameters": {},
            "confidence": 0.95,
            "reasoning": "User wants AP status, device supports show_ap_summary"
        }
```

#### **Step 4: Command Validation via MCP**
```python
# LangChain validates command before execution
validation_result = await mcp_client.call_tool(
    "validate_command",
    {
        "command_name": "show_ap_summary",
        "device_id": "1001",
        "parameters": {}
    }
)

# MCP Server validates command
@router.post("/mcp/tools/commands/validate_command")
async def validate_command(command_name: str, device_id: str, parameters: Dict[str, Any]):

    # Check command template exists
    command_template = db.query(CommandTemplate).filter(
        CommandTemplate.command_name == command_name,
        CommandTemplate.is_active == True
    ).first()

    # Check device compatibility
    device = db.query(Device).filter(Device.id == int(device_id)).first()

    # Validate parameters and render command
    rendered_command = command_template.command_template.format(**parameters)

    return {
        "valid": True,
        "rendered_command": "show ap summary",
        "estimated_execution_time": 3.0
    }
```

#### **Step 5: Command Execution via MCP**
```python
# LangGraph workflow executes command via MCP
execution_result = await mcp_client.call_tool(
    "execute_command",
    {
        "command_name": "show_ap_summary",
        "device_id": "1001",
        "parameters": {},
        "workflow_id": "wf_12345",
        "execution_context": {"user_session": "session_abc"}
    }
)

# MCP Server executes command
@router.post("/mcp/tools/commands/execute_command")
async def execute_command(request: CommandExecutionRequest):

    # Get device and command template from PostgreSQL
    device = db.query(Device).filter(Device.id == int(request.device_id)).first()
    command_template = db.query(CommandTemplate).filter(
        CommandTemplate.command_name == request.command_name
    ).first()

    # Execute via pyATS/Genie
    connector = GenieConnector(device.to_dict())
    await connector.connect()

    result = await connector.execute_command("show ap summary")

    # Store execution record in PostgreSQL
    execution_record = CommandExecution(
        command_template_id=command_template.id,
        device_id=device.id,
        workflow_id=request.workflow_id,
        executed_command="show ap summary",
        execution_status='success',
        raw_output=result.output['raw'],
        parsed_output=result.output['parsed'],
        parser_used=result.output['parser_used']
    )
    db.add(execution_record)
    db.commit()

    return CommandExecutionResponse(
        execution_id=str(execution_record.id),
        success=True,
        output=result.output,
        execution_time=2.3,
        parser_used="ShowApSummary"
    )
```

#### **Step 6: Context Update and Response Formatting**
```python
# Update device context after successful execution
await mcp_client.call_tool(
    "update_device_context",
    {
        "device_id": "1001",
        "context_updates": {
            "last_command_execution": datetime.now().isoformat(),
            "last_successful_command": "show_ap_summary",
            "connection_status": "connected"
        }
    }
)

# LangChain formats response with context
formatted_response = await langchain_processor.format_response(
    command="show_ap_summary",
    device="WLC-CORP-01",
    raw_output=execution_result['output']['raw'],
    parsed_output=execution_result['output']['parsed'],
    execution_context={
        "execution_time": execution_result['execution_time'],
        "parser_used": execution_result['parser_used']
    }
)
```

### **Context Flow Diagram**
```
User Input
    ↓
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Gateway                             │
│  /api/v1/natural-language/process                          │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│              LangChain Processor                            │
│              (MCP CLIENT)                                   │
│  1. Request device context via MCP                         │
│  2. Process natural language with context                  │
│  3. Generate structured command                             │
└─────────────────────────────────────────────────────────────┘
    ↓ MCP Tool Calls
┌─────────────────────────────────────────────────────────────┐
│                MCP SERVER                                   │
│              (FastAPI Tools)                                │
│  /mcp/tools/devices/get_device_context                     │
│  /mcp/tools/commands/validate_command                      │
│  /mcp/tools/commands/execute_command                       │
└─────────────────────────────────────────────────────────────┘
    ↓ Database Queries
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                            │
│  • Device table (capabilities, connection details)         │
│  • CommandTemplate table (command definitions)             │
│  • CommandExecution table (execution history)              │
└─────────────────────────────────────────────────────────────┘
    ↓ Network Operations
┌─────────────────────────────────────────────────────────────┐
│              pyATS/Genie Layer                             │
│  • Dynamic testbed generation                              │
│  • Device connection management                            │
│  • Command execution with parsing                          │
└─────────────────────────────────────────────────────────────┘
    ↓ Results Flow Back
┌─────────────────────────────────────────────────────────────┐
│              Response Processing                            │
│  • Store execution results in PostgreSQL                   │
│  • Update device context via MCP                           │
│  • Format response with LangChain                          │
│  • Return to user via FastAPI                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Database Integration Strategy

### **MCP Context Synchronization with PostgreSQL**

#### **Context Data Model**
```python
# Enhanced database models for MCP integration
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DeviceContext(Base):
    """Persistent storage for MCP device context"""
    __tablename__ = "device_contexts"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), unique=True)

    # MCP Context Data
    current_context = Column(JSON)  # Live context state
    context_history = Column(JSON)  # Historical context changes

    # Connection State
    connection_status = Column(String(20))
    last_connection_attempt = Column(DateTime)
    connection_metadata = Column(JSON)

    # Command Context
    last_executed_command = Column(String(100))
    command_execution_count = Column(Integer, default=0)
    average_execution_time = Column(Float)

    # Workflow Context
    active_workflows = Column(JSON)  # Currently running workflows
    workflow_history = Column(JSON)  # Completed workflows

    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class CommandContext(Base):
    """Persistent storage for MCP command context"""
    __tablename__ = "command_contexts"

    id = Column(Integer, primary_key=True)
    command_template_id = Column(Integer, ForeignKey('command_templates.id'))
    device_id = Column(Integer, ForeignKey('devices.id'))

    # Execution Context
    execution_patterns = Column(JSON)  # Common parameter patterns
    success_rate = Column(Float)
    average_execution_time = Column(Float)

    # Parameter Context
    common_parameters = Column(JSON)  # Frequently used parameters
    parameter_validation_rules = Column(JSON)

    # Error Context
    common_errors = Column(JSON)  # Error patterns and solutions
    troubleshooting_steps = Column(JSON)

    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### **Context Synchronization Service**
```python
# src/mcp_server/context_sync.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

class MCPContextSynchronizer:
    """Synchronize MCP context with PostgreSQL storage"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.sync_interval = timedelta(minutes=5)

    async def sync_device_context(self, device_id: str, context_data: Dict[str, Any]):
        """Sync device context to database"""

        # Get or create device context record
        device_context = self.db.query(DeviceContext).filter(
            DeviceContext.device_id == int(device_id)
        ).first()

        if not device_context:
            device_context = DeviceContext(device_id=int(device_id))
            self.db.add(device_context)

        # Update context data
        current_context = device_context.current_context or {}
        current_context.update(context_data)
        device_context.current_context = current_context

        # Update connection status
        if 'connection_status' in context_data:
            device_context.connection_status = context_data['connection_status']
            device_context.last_connection_attempt = datetime.now()

        # Update command execution stats
        if 'last_executed_command' in context_data:
            device_context.last_executed_command = context_data['last_executed_command']
            device_context.command_execution_count += 1

        # Store context history
        context_history = device_context.context_history or []
        context_history.append({
            'timestamp': datetime.now().isoformat(),
            'changes': context_data
        })

        # Keep only last 100 context changes
        device_context.context_history = context_history[-100:]

        self.db.commit()

    async def get_device_context(self, device_id: str) -> Dict[str, Any]:
        """Get device context from database"""

        device_context = self.db.query(DeviceContext).filter(
            DeviceContext.device_id == int(device_id)
        ).first()

        if not device_context:
            return {}

        return {
            'current_context': device_context.current_context or {},
            'connection_status': device_context.connection_status,
            'last_connection_attempt': device_context.last_connection_attempt.isoformat() if device_context.last_connection_attempt else None,
            'command_stats': {
                'last_executed_command': device_context.last_executed_command,
                'execution_count': device_context.command_execution_count,
                'average_execution_time': device_context.average_execution_time
            },
            'active_workflows': device_context.active_workflows or [],
            'context_history': device_context.context_history or []
        }

    async def sync_command_context(self, command_template_id: str, device_id: str,
                                 execution_data: Dict[str, Any]):
        """Sync command execution context"""

        # Get or create command context
        command_context = self.db.query(CommandContext).filter(
            CommandContext.command_template_id == int(command_template_id),
            CommandContext.device_id == int(device_id)
        ).first()

        if not command_context:
            command_context = CommandContext(
                command_template_id=int(command_template_id),
                device_id=int(device_id)
            )
            self.db.add(command_context)

        # Update execution patterns
        execution_patterns = command_context.execution_patterns or {}
        parameters_used = execution_data.get('parameters', {})

        for param, value in parameters_used.items():
            if param not in execution_patterns:
                execution_patterns[param] = []
            execution_patterns[param].append(value)
            # Keep only last 50 values
            execution_patterns[param] = execution_patterns[param][-50:]

        command_context.execution_patterns = execution_patterns

        # Update success rate
        success = execution_data.get('success', False)
        current_success_rate = command_context.success_rate or 0.0
        execution_count = command_context.command_execution_count or 0

        new_success_rate = ((current_success_rate * execution_count) + (1 if success else 0)) / (execution_count + 1)
        command_context.success_rate = new_success_rate

        # Update average execution time
        execution_time = execution_data.get('execution_time', 0.0)
        current_avg_time = command_context.average_execution_time or 0.0

        new_avg_time = ((current_avg_time * execution_count) + execution_time) / (execution_count + 1)
        command_context.average_execution_time = new_avg_time

        self.db.commit()

---

## 5. API Design Specifications

### **Complete MCP Tool API Specification**

#### **Workflow Management Tools**

```python
# src/mcp_server/workflow_tools.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/mcp/tools/workflows", tags=["MCP Workflow Tools"])

class WorkflowStateRequest(BaseModel):
    workflow_id: str
    workflow_name: str
    workflow_type: str
    device_ids: List[str]
    steps: List[Dict[str, Any]]
    context: Dict[str, Any] = {}

class WorkflowStateResponse(BaseModel):
    workflow_id: str
    status: str
    current_step: int
    completed_steps: List[str]
    failed_steps: List[str]
    context: Dict[str, Any]
    created_at: str
    updated_at: str

@router.post("/create_workflow", response_model=WorkflowStateResponse)
async def create_workflow(
    request: WorkflowStateRequest,
    db: Session = Depends(get_db)
) -> WorkflowStateResponse:
    """
    MCP Tool: Create new workflow with context tracking
    Used by LangGraph to initialize workflow state
    """

    # Create workflow state record
    workflow_state = WorkflowState(
        id=request.workflow_id,
        name=request.workflow_name,
        workflow_type=request.workflow_type,
        device_ids=request.device_ids,
        steps=request.steps,
        status='pending',
        current_step=0,
        context=request.context,
        created_at=datetime.now()
    )

    db.add(workflow_state)
    db.commit()

    # Initialize device contexts for workflow
    for device_id in request.device_ids:
        await sync_device_workflow_context(device_id, request.workflow_id, 'started')

    return WorkflowStateResponse(
        workflow_id=workflow_state.id,
        status=workflow_state.status,
        current_step=workflow_state.current_step,
        completed_steps=[],
        failed_steps=[],
        context=workflow_state.context,
        created_at=workflow_state.created_at.isoformat(),
        updated_at=workflow_state.updated_at.isoformat()
    )

@router.put("/update_workflow_state/{workflow_id}")
async def update_workflow_state(
    workflow_id: str,
    state_updates: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    MCP Tool: Update workflow execution state
    Used by LangGraph during workflow execution
    """

    workflow_state = db.query(WorkflowState).filter(
        WorkflowState.id == workflow_id
    ).first()

    if not workflow_state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Update workflow state
    for key, value in state_updates.items():
        if hasattr(workflow_state, key):
            setattr(workflow_state, key, value)

    workflow_state.updated_at = datetime.now()

    # Update context
    if 'context_updates' in state_updates:
        current_context = workflow_state.context or {}
        current_context.update(state_updates['context_updates'])
        workflow_state.context = current_context

    db.commit()

    return {"status": "success", "message": "Workflow state updated"}

@router.get("/get_workflow_context/{workflow_id}")
async def get_workflow_context(
    workflow_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    MCP Tool: Get workflow context and state
    Used by LangGraph to resume or check workflow status
    """

    workflow_state = db.query(WorkflowState).filter(
        WorkflowState.id == workflow_id
    ).first()

    if not workflow_state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get device contexts for workflow
    device_contexts = {}
    for device_id in workflow_state.device_ids:
        device_context = await get_device_context_for_workflow(device_id, workflow_id)
        device_contexts[device_id] = device_context

    # Get execution history for workflow
    execution_history = db.query(CommandExecution).filter(
        CommandExecution.workflow_id == workflow_id
    ).order_by(CommandExecution.executed_at).all()

    return {
        "workflow_id": workflow_state.id,
        "workflow_name": workflow_state.name,
        "status": workflow_state.status,
        "current_step": workflow_state.current_step,
        "total_steps": len(workflow_state.steps),
        "context": workflow_state.context,
        "device_contexts": device_contexts,
        "execution_history": [
            {
                "execution_id": exec.id,
                "command": exec.executed_command,
                "device_id": exec.device_id,
                "status": exec.execution_status,
                "executed_at": exec.executed_at.isoformat()
            }
            for exec in execution_history
        ],
        "created_at": workflow_state.created_at.isoformat(),
        "updated_at": workflow_state.updated_at.isoformat()
    }
```

#### **Cisco WLC Specific Tools**

```python
# src/mcp_server/cisco_wlc_tools.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/mcp/tools/cisco-wlc", tags=["MCP Cisco WLC Tools"])

class APStatusRequest(BaseModel):
    device_id: str
    ap_name: Optional[str] = None
    include_clients: bool = False
    include_config: bool = False

class APStatusResponse(BaseModel):
    device_id: str
    device_hostname: str
    total_aps: int
    online_aps: int
    offline_aps: int
    ap_details: List[Dict[str, Any]]
    summary: Dict[str, Any]

@router.post("/get_ap_status", response_model=APStatusResponse)
async def get_ap_status(
    request: APStatusRequest,
    db: Session = Depends(get_db)
) -> APStatusResponse:
    """
    MCP Tool: Get comprehensive AP status from Cisco WLC
    Specialized tool for wireless controller management
    """

    # Get device information
    device = db.query(Device).filter(Device.id == int(request.device_id)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.device_type != 'cisco_wlc':
        raise HTTPException(status_code=400, detail="Device is not a Cisco WLC")

    # Execute AP summary command
    execution_result = await execute_command_via_mcp(
        command_name="show_ap_summary",
        device_id=request.device_id,
        parameters={"ap_name": request.ap_name} if request.ap_name else {}
    )

    if not execution_result['success']:
        raise HTTPException(status_code=500, detail="Failed to get AP status")

    # Parse AP data from Genie output
    parsed_data = execution_result['output']['parsed']
    ap_summary = parsed_data.get('ap_summary', {})

    ap_details = []
    online_count = 0
    offline_count = 0

    for ap_name, ap_info in ap_summary.items():
        status = ap_info.get('status', 'unknown')
        if status.lower() == 'up':
            online_count += 1
        elif status.lower() == 'down':
            offline_count += 1

        ap_detail = {
            'ap_name': ap_name,
            'status': status,
            'model': ap_info.get('model', 'unknown'),
            'location': ap_info.get('location', 'unknown'),
            'uptime': ap_info.get('uptime', 'unknown'),
            'clients': ap_info.get('clients', 0)
        }

        # Get additional client info if requested
        if request.include_clients and status.lower() == 'up':
            client_info = await get_ap_client_details(request.device_id, ap_name)
            ap_detail['client_details'] = client_info

        # Get AP configuration if requested
        if request.include_config:
            config_info = await get_ap_configuration(request.device_id, ap_name)
            ap_detail['configuration'] = config_info

        ap_details.append(ap_detail)

    return APStatusResponse(
        device_id=request.device_id,
        device_hostname=device.hostname,
        total_aps=len(ap_details),
        online_aps=online_count,
        offline_aps=offline_count,
        ap_details=ap_details,
        summary={
            'health_percentage': (online_count / len(ap_details)) * 100 if ap_details else 0,
            'total_clients': sum(ap['clients'] for ap in ap_details),
            'average_uptime': calculate_average_uptime(ap_details),
            'models_distribution': get_model_distribution(ap_details)
        }
    )

@router.post("/diagnose_offline_aps")
async def diagnose_offline_aps(
    device_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    MCP Tool: Diagnose offline APs and provide troubleshooting steps
    Intelligent diagnostic tool for WLC management
    """

    # Get offline APs
    ap_status = await get_ap_status(
        APStatusRequest(device_id=device_id),
        db
    )

    offline_aps = [ap for ap in ap_status.ap_details if ap['status'].lower() == 'down']

    if not offline_aps:
        return {
            "status": "healthy",
            "message": "All APs are online",
            "offline_count": 0
        }

    # Diagnose each offline AP
    diagnostics = []
    for ap in offline_aps:
        ap_name = ap['ap_name']

        # Get detailed AP configuration
        config_result = await execute_command_via_mcp(
            command_name="show_ap_config",
            device_id=device_id,
            parameters={"ap_name": ap_name}
        )

        # Analyze configuration for issues
        diagnosis = analyze_ap_configuration(config_result['output']['parsed'])

        # Get historical data
        history = await get_ap_history(device_id, ap_name)

        diagnostics.append({
            "ap_name": ap_name,
            "last_seen": ap.get('last_seen', 'unknown'),
            "diagnosis": diagnosis,
            "history": history,
            "recommended_actions": generate_troubleshooting_steps(diagnosis)
        })

    return {
        "status": "issues_found",
        "offline_count": len(offline_aps),
        "diagnostics": diagnostics,
        "summary": {
            "common_issues": identify_common_issues(diagnostics),
            "priority_actions": get_priority_actions(diagnostics)
        }
    }

async def analyze_ap_configuration(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze AP configuration for potential issues"""

    issues = []
    recommendations = []

    # Check power status
    power_status = config_data.get('power', {}).get('status', 'unknown')
    if power_status.lower() in ['lost', 'insufficient']:
        issues.append({
            "type": "power",
            "severity": "high",
            "description": f"Power status: {power_status}"
        })
        recommendations.append("Check PoE switch port or power injector")

    # Check network connectivity
    network_status = config_data.get('network', {}).get('status', 'unknown')
    if network_status.lower() in ['unreachable', 'timeout']:
        issues.append({
            "type": "network",
            "severity": "high",
            "description": f"Network status: {network_status}"
        })
        recommendations.append("Check network cable and switch port")

    # Check firmware version
    firmware_version = config_data.get('firmware', {}).get('version', '')
    if firmware_version and is_firmware_outdated(firmware_version):
        issues.append({
            "type": "firmware",
            "severity": "medium",
            "description": f"Outdated firmware: {firmware_version}"
        })
        recommendations.append("Consider firmware upgrade")

    return {
        "issues": issues,
        "recommendations": recommendations,
        "health_score": calculate_ap_health_score(issues)
    }
```

#### **MCP Client Integration**

```python
# src/langchain_layer/mcp_client.py
import httpx
from typing import Dict, Any, Optional
import asyncio

class MCPClient:
    """Client for calling MCP tools from LangChain/LangGraph"""

    def __init__(self, mcp_server_url: str = "http://localhost:8000"):
        self.base_url = mcp_server_url
        self.client = httpx.AsyncClient()

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool and return result"""

        # Map tool names to endpoints
        tool_endpoints = {
            "get_device_context": "/mcp/tools/devices/get_device_context",
            "list_device_capabilities": "/mcp/tools/devices/list_device_capabilities",
            "update_device_context": "/mcp/tools/devices/update_device_context",
            "execute_command": "/mcp/tools/commands/execute_command",
            "validate_command": "/mcp/tools/commands/validate_command",
            "get_command_history": "/mcp/tools/commands/get_command_history",
            "create_workflow": "/mcp/tools/workflows/create_workflow",
            "update_workflow_state": "/mcp/tools/workflows/update_workflow_state",
            "get_workflow_context": "/mcp/tools/workflows/get_workflow_context",
            "get_ap_status": "/mcp/tools/cisco-wlc/get_ap_status",
            "diagnose_offline_aps": "/mcp/tools/cisco-wlc/diagnose_offline_aps"
        }

        endpoint = tool_endpoints.get(tool_name)
        if not endpoint:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

        url = f"{self.base_url}{endpoint}"

        try:
            if tool_name.startswith("get_") or tool_name.startswith("list_"):
                # GET request for read operations
                response = await self.client.get(url, params=parameters)
            else:
                # POST request for write operations
                response = await self.client.post(url, json=parameters)

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            raise Exception(f"MCP tool call failed: {str(e)}")

    async def get_device_context(self, device_id: Optional[str] = None,
                               hostname: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for getting device context"""
        return await self.call_tool("get_device_context", {
            "device_id": device_id,
            "hostname": hostname,
            "include_capabilities": True,
            "include_status": True
        })

    async def execute_command(self, command_name: str, device_id: str,
                            parameters: Dict[str, Any] = {},
                            workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method for command execution"""
        return await self.call_tool("execute_command", {
            "command_name": command_name,
            "device_id": device_id,
            "parameters": parameters,
            "workflow_id": workflow_id
        })

# Integration with LangChain
class MCPEnhancedLangChainProcessor:
    """LangChain processor enhanced with MCP context"""

    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.llm = OpenAI(temperature=0.1)

    async def process_with_mcp_context(self, user_input: str,
                                     device_hint: Optional[str] = None) -> Dict[str, Any]:
        """Process user input with MCP context enhancement"""

        # Get device context if device is specified
        device_context = {}
        if device_hint:
            try:
                device_context = await self.mcp_client.get_device_context(hostname=device_hint)
            except Exception as e:
                print(f"Warning: Could not get device context: {e}")

        # Create context-aware prompt
        prompt = f"""
        User Request: {user_input}

        Device Context: {device_context if device_context else 'No specific device context'}

        Based on the user request and available device context, determine:
        1. The appropriate command to execute
        2. Target device (if not specified, suggest based on context)
        3. Required parameters
        4. Whether this requires a workflow or single command

        Respond in JSON format with: command_name, device_id, parameters, workflow_required
        """

        result = await self.llm.arun(prompt)

        # Parse and validate result
        parsed_result = json.loads(result)

        # Validate command if device is known
        if device_context and parsed_result.get('command_name'):
            validation = await self.mcp_client.call_tool("validate_command", {
                "command_name": parsed_result['command_name'],
                "device_id": device_context['device_id'],
                "parameters": parsed_result.get('parameters', {})
            })

            parsed_result['validation'] = validation

        return parsed_result
```

---

## Summary and Implementation Roadmap

### **Key Clarifications**

1. **MCP Server = FastAPI Application**: Your FastAPI backend serves as the MCP server
2. **MCP Tools = FastAPI Endpoints**: Each tool is a specific endpoint providing functionality
3. **MCP Client = LangChain/LangGraph**: These components consume MCP tools for context and execution
4. **Database Integration**: Direct PostgreSQL integration within MCP tools, no separate bridge needed

### **Implementation Priority**

1. **Phase 1**: Core MCP tools (device context, command execution)
2. **Phase 2**: Workflow management tools
3. **Phase 3**: Cisco WLC specific tools
4. **Phase 4**: Advanced analytics and diagnostics

### **Benefits of This Architecture**

- **Unified API**: Single FastAPI application serves both user requests and MCP tools
- **Rich Context**: Deep integration with PostgreSQL provides comprehensive context
- **Scalable**: Tool-based architecture allows easy extension
- **Type Safe**: Pydantic models ensure data consistency
- **Observable**: Built-in logging and monitoring for all MCP operations

This MCP implementation provides the intelligent context management needed for sophisticated network automation while maintaining clean separation of concerns and scalability.
```
