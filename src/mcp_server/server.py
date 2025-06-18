"""
MCP Server Implementation

Main MCP server for handling tool and resource requests from LangChain/LangGraph.
"""

import asyncio
import json
import structlog
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.database import get_db
from .tools import MCPToolRegistry
from .resources import MCPResourceManager
from .context import MCPContextManager

logger = structlog.get_logger(__name__)
settings = get_settings()


class MCPRequest(BaseModel):
    """MCP request model"""
    id: str = Field(..., description="Request ID")
    method: str = Field(..., description="Method name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Request parameters")


class MCPResponse(BaseModel):
    """MCP response model"""
    id: str = Field(..., description="Request ID")
    result: Optional[Dict[str, Any]] = Field(None, description="Response result")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information")


class MCPError(BaseModel):
    """MCP error model"""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional error data")


class MCPServer:
    """MCP server implementation"""
    
    def __init__(self):
        """Initialize MCP server"""
        self.app = FastAPI(
            title="Network Automation MCP Server",
            description="Model Context Protocol server for network automation",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize components
        self.tool_registry = MCPToolRegistry()
        self.resource_manager = MCPResourceManager()
        self.context_manager = MCPContextManager()
        
        # Active connections
        self.connections: Dict[str, WebSocket] = {}
        
        # Method handlers
        self.handlers: Dict[str, Callable] = {
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
            "resources/list": self._handle_list_resources,
            "resources/read": self._handle_read_resource,
            "context/create": self._handle_create_context,
            "context/update": self._handle_update_context,
            "context/get": self._handle_get_context,
            "context/delete": self._handle_delete_context,
            "ping": self._handle_ping,
        }
        
        # Setup routes
        self._setup_routes()
        
        self.logger = logger.bind(component="mcp_server")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.websocket("/mcp")
        async def websocket_endpoint(websocket: WebSocket):
            await self._handle_websocket(websocket)
        
        @self.app.post("/mcp/request", response_model=MCPResponse)
        async def http_request(request: MCPRequest):
            return await self._handle_http_request(request)
        
        @self.app.get("/mcp/tools")
        async def list_tools():
            """List available tools"""
            return await self._handle_list_tools({})
        
        @self.app.get("/mcp/resources")
        async def list_resources():
            """List available resources"""
            return await self._handle_list_resources({})
        
        @self.app.get("/mcp/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "connections": len(self.connections),
                "tools": len(self.tool_registry.get_all_tools()),
                "resources": len(await self.resource_manager.list_resources())
            }
    
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection"""
        await websocket.accept()
        connection_id = f"ws_{id(websocket)}"
        self.connections[connection_id] = websocket
        
        self.logger.info("WebSocket connection established", connection_id=connection_id)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                
                try:
                    request_data = json.loads(data)
                    request = MCPRequest(**request_data)
                    
                    # Process request
                    response = await self._process_request(request)
                    
                    # Send response
                    await websocket.send_text(response.json())
                    
                except json.JSONDecodeError as e:
                    error_response = MCPResponse(
                        id="unknown",
                        error=MCPError(
                            code=-32700,
                            message="Parse error",
                            data={"details": str(e)}
                        ).dict()
                    )
                    await websocket.send_text(error_response.json())
                
                except Exception as e:
                    self.logger.error("WebSocket request processing error", error=str(e))
                    error_response = MCPResponse(
                        id=getattr(request, "id", "unknown"),
                        error=MCPError(
                            code=-32603,
                            message="Internal error",
                            data={"details": str(e)}
                        ).dict()
                    )
                    await websocket.send_text(error_response.json())
        
        except WebSocketDisconnect:
            self.logger.info("WebSocket connection closed", connection_id=connection_id)
        
        except Exception as e:
            self.logger.error("WebSocket error", connection_id=connection_id, error=str(e))
        
        finally:
            # Clean up connection
            if connection_id in self.connections:
                del self.connections[connection_id]
    
    async def _handle_http_request(self, request: MCPRequest) -> MCPResponse:
        """Handle HTTP request"""
        try:
            return await self._process_request(request)
        except Exception as e:
            self.logger.error("HTTP request processing error", error=str(e))
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=-32603,
                    message="Internal error",
                    data={"details": str(e)}
                ).dict()
            )
    
    async def _process_request(self, request: MCPRequest) -> MCPResponse:
        """Process MCP request"""
        self.logger.info(
            "Processing MCP request",
            request_id=request.id,
            method=request.method
        )
        
        # Check if method is supported
        if request.method not in self.handlers:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=-32601,
                    message="Method not found",
                    data={"method": request.method}
                ).dict()
            )
        
        try:
            # Call handler
            handler = self.handlers[request.method]
            result = await handler(request.params)
            
            return MCPResponse(
                id=request.id,
                result=result
            )
            
        except Exception as e:
            self.logger.error(
                "Request handler error",
                request_id=request.id,
                method=request.method,
                error=str(e)
            )
            
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=-32603,
                    message="Internal error",
                    data={"details": str(e)}
                ).dict()
            )
    
    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools = self.tool_registry.get_all_tools()
        
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "output_schema": tool.output_schema
                }
                for tool in tools
            ]
        }
    
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        tool_input = params.get("input", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        # Get tool
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Execute tool
        result = await tool.execute(tool_input)
        
        return {
            "result": result,
            "tool": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request"""
        resources = await self.resource_manager.list_resources()
        
        return {
            "resources": [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mime_type": resource.mime_type
                }
                for resource in resources
            ]
        }
    
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("Resource URI is required")
        
        # Read resource
        resource = await self.resource_manager.read_resource(uri)
        
        return {
            "contents": [
                {
                    "uri": resource.uri,
                    "mime_type": resource.mime_type,
                    "text": resource.content
                }
            ]
        }
    
    async def _handle_create_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context/create request"""
        context_data = params.get("context", {})
        context_type = params.get("type", "general")
        
        context = await self.context_manager.create_context(context_type, context_data)
        
        return {
            "context_id": context.context_id,
            "created_at": context.created_at.isoformat()
        }
    
    async def _handle_update_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context/update request"""
        context_id = params.get("context_id")
        updates = params.get("updates", {})
        
        if not context_id:
            raise ValueError("Context ID is required")
        
        context = await self.context_manager.update_context(context_id, updates)
        
        return {
            "context_id": context.context_id,
            "updated_at": context.updated_at.isoformat()
        }
    
    async def _handle_get_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context/get request"""
        context_id = params.get("context_id")
        
        if not context_id:
            raise ValueError("Context ID is required")
        
        context = await self.context_manager.get_context(context_id)
        
        return {
            "context_id": context.context_id,
            "context_type": context.context_type,
            "context_data": context.context_data,
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat()
        }
    
    async def _handle_delete_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context/delete request"""
        context_id = params.get("context_id")
        
        if not context_id:
            raise ValueError("Context ID is required")
        
        await self.context_manager.delete_context(context_id)
        
        return {
            "context_id": context_id,
            "deleted": True
        }
    
    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request"""
        return {
            "pong": True,
            "timestamp": datetime.utcnow().isoformat(),
            "server": "network-automation-mcp"
        }
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connections:
            return
        
        message_str = json.dumps(message)
        
        # Send to all connections
        disconnected = []
        for connection_id, websocket in self.connections.items():
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                self.logger.warning(
                    "Failed to send message to connection",
                    connection_id=connection_id,
                    error=str(e)
                )
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            if connection_id in self.connections:
                del self.connections[connection_id]
    
    def get_app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.app
