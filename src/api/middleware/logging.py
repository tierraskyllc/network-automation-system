"""
Logging Middleware

Middleware for request/response logging and audit trails.
"""

import time
import uuid
import structlog
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Extract request details
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        method = request.method
        url = str(request.url)
        path = request.url.path
        
        # Get user info if available
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)
        
        # Log request
        logger.info(
            "Request started",
            correlation_id=correlation_id,
            method=method,
            path=path,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent,
            user_id=user_id,
            username=username
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                correlation_id=correlation_id,
                method=method,
                path=path,
                status_code=response.status_code,
                process_time=process_time,
                user_id=user_id,
                username=username
            )
            
            # Add headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                correlation_id=correlation_id,
                method=method,
                path=path,
                error=str(e),
                process_time=process_time,
                user_id=user_id,
                username=username,
                exc_info=True
            )
            
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging of sensitive operations"""
    
    # Paths that require audit logging
    AUDIT_PATHS = [
        "/api/v1/devices",
        "/api/v1/commands",
        "/api/v1/workflows",
        "/api/v1/users",
        "/api/v1/auth"
    ]
    
    # Methods that require audit logging
    AUDIT_METHODS = ["POST", "PUT", "PATCH", "DELETE"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and create audit logs for sensitive operations"""
        should_audit = self._should_audit(request)
        
        if should_audit:
            # Capture request data for audit
            request_data = await self._capture_request_data(request)
            
        response = await call_next(request)
        
        if should_audit:
            # Create audit log entry
            await self._create_audit_log(request, response, request_data)
        
        return response
    
    def _should_audit(self, request: Request) -> bool:
        """Determine if request should be audited"""
        path = request.url.path
        method = request.method
        
        # Check if path matches audit patterns
        for audit_path in self.AUDIT_PATHS:
            if path.startswith(audit_path):
                return method in self.AUDIT_METHODS
        
        return False
    
    async def _capture_request_data(self, request: Request) -> dict:
        """Capture request data for audit logging"""
        try:
            # Note: This is a simplified version
            # In production, you'd want to be careful about logging sensitive data
            return {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                # "body": await request.body()  # Be careful with sensitive data
            }
        except Exception as e:
            logger.warning("Failed to capture request data for audit", error=str(e))
            return {}
    
    async def _create_audit_log(self, request: Request, response: Response, 
                              request_data: dict):
        """Create audit log entry"""
        try:
            # This would typically write to the audit_logs table
            # For now, just log to structured logger
            logger.info(
                "Audit log entry",
                correlation_id=getattr(request.state, "correlation_id", None),
                user_id=getattr(request.state, "user_id", None),
                username=getattr(request.state, "username", None),
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                client_ip=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", ""),
                request_data=request_data
            )
        except Exception as e:
            logger.error("Failed to create audit log", error=str(e))
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
