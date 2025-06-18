"""
Health Check Endpoints

Health check and system status endpoints.
"""

import asyncio
import structlog
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from ...core.database import get_db
from ...core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "network-automation-system",
        "version": "0.1.0"
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependency status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "network-automation-system",
        "version": "0.1.0",
        "dependencies": {}
    }
    
    overall_healthy = True
    
    # Check database connectivity
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["dependencies"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0  # Could measure actual response time
        }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        health_status["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check Redis connectivity
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        health_status["dependencies"]["redis"] = {
            "status": "healthy"
        }
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        health_status["dependencies"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check external services if configured
    if settings.VAULT_ENABLED:
        health_status["dependencies"]["vault"] = await _check_vault_health()
        if health_status["dependencies"]["vault"]["status"] != "healthy":
            overall_healthy = False
    
    # Set overall status
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    # Return appropriate HTTP status
    if not overall_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes readiness probe endpoint"""
    try:
        # Check if database is accessible
        await db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


async def _check_vault_health() -> Dict[str, Any]:
    """Check HashiCorp Vault health"""
    try:
        import hvac
        
        client = hvac.Client(url=settings.VAULT_URL)
        if settings.VAULT_TOKEN:
            client.token = settings.VAULT_TOKEN
        
        # Check if Vault is sealed/unsealed
        health_response = client.sys.read_health_status()
        
        return {
            "status": "healthy" if not health_response.get("sealed", True) else "sealed",
            "sealed": health_response.get("sealed", True),
            "version": health_response.get("version", "unknown")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/metrics", response_model=Dict[str, Any])
async def basic_metrics():
    """Basic application metrics"""
    # This could be extended to include more detailed metrics
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": 0,  # Could track actual uptime
        "memory_usage": {},   # Could include memory metrics
        "cpu_usage": {},      # Could include CPU metrics
        "request_count": 0,   # Could track request counts
        "error_count": 0      # Could track error counts
    }
