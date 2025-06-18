"""
FastAPI Main Application

This module contains the main FastAPI application setup with all routers,
middleware, and configuration.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from typing import Dict, Any

from ..core.config import get_settings
from ..core.database import init_db, close_db
from ..core.security.rbac import RoleBasedAccessControl
from .endpoints import (
    auth_router,
    devices_router,
    commands_router,
    workflows_router,
    topology_router,
    users_router,
    health_router,
)
from .middleware.auth import AuthMiddleware
from .middleware.logging import LoggingMiddleware, AuditLoggingMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Get application settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Network Automation System",
    description="Hybrid LangGraph/LangChain/MCP Network Automation System with pyATS/Genie",
    version="0.1.0",
    docs_url="/docs" if settings.ENABLE_SWAGGER_UI else None,
    redoc_url="/redoc" if settings.ENABLE_REDOC else None,
    openapi_url="/openapi.json",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts_list
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(AuthMiddleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": request.url.path,
            "method": request.method
        }
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Network Automation System")

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Initialize RBAC if needed
        if settings.ENVIRONMENT == "development":
            from ..core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                rbac = RoleBasedAccessControl(db)
                await rbac.initialize_default_roles()
                await db.commit()
            logger.info("RBAC initialized")

        logger.info("Application startup completed")

    except Exception as e:
        logger.error("Application startup failed", error=str(e))
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Network Automation System")

    try:
        await close_db()
        logger.info("Database connections closed")

    except Exception as e:
        logger.error("Application shutdown error", error=str(e))

    logger.info("Application shutdown completed")


# Include routers
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(commands_router, prefix="/api/v1/commands", tags=["Commands"])
app.include_router(workflows_router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(topology_router, prefix="/api/v1/topology", tags=["Topology"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "message": "Network Automation System API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=1 if settings.API_RELOAD else settings.API_WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
