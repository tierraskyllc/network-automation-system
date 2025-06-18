"""
Authentication Middleware

Middleware for JWT authentication and authorization.
"""

import structlog
from typing import List, Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db
from ...core.models.user import User, UserSession
from ...core.security.auth import JWTManager
from ...core.security.rbac import PermissionChecker

logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer()
jwt_manager = JWTManager()


class AuthMiddleware:
    """Authentication middleware for FastAPI"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation"""
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip auth for health checks and docs
            if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
                await self.app(scope, receive, send)
                return
            
            # Add user info to request state if authenticated
            try:
                auth_header = request.headers.get("authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    payload = jwt_manager.verify_token(token)
                    scope["state"]["user_id"] = int(payload["sub"])
                    scope["state"]["username"] = payload["username"]
                    scope["state"]["permissions"] = payload.get("permissions", [])
            except Exception as e:
                logger.debug("Auth middleware error", error=str(e))
                # Don't fail here, let the endpoint handle auth requirements
                pass
        
        await self.app(scope, receive, send)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        # Verify JWT token
        payload = jwt_manager.verify_token(credentials.credentials)
        user_id = int(payload["sub"])
        
        # Get user from database
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_permissions(required_permissions: List[str]):
    """Decorator to require specific permissions"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not PermissionChecker.has_all_permissions(current_user, required_permissions):
            missing_perms = set(required_permissions) - PermissionChecker.get_user_permissions(current_user)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_perms)}"
            )
        return current_user
    
    return permission_checker


def require_any_permission(required_permissions: List[str]):
    """Decorator to require any of the specified permissions"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not PermissionChecker.has_any_permission(current_user, required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing any of required permissions: {', '.join(required_permissions)}"
            )
        return current_user
    
    return permission_checker


def require_superuser():
    """Decorator to require superuser access"""
    def superuser_checker(current_user: User = Depends(get_current_user)):
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superuser access required"
            )
        return current_user
    
    return superuser_checker


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = jwt_manager.verify_token(token)
        user_id = int(payload["sub"])
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user and user.status == "active":
            return user
        
        return None
        
    except Exception:
        return None


class DeviceAccessChecker:
    """Check device access permissions"""
    
    def __init__(self, device_id: int):
        self.device_id = device_id
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        # Check if user has device access
        # This could be extended to check device-specific permissions
        if not PermissionChecker.has_permission(current_user, "device:read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Device access denied"
            )
        return current_user


class EnvironmentAccessChecker:
    """Check environment access permissions"""
    
    def __init__(self, environment: str):
        self.environment = environment
    
    def __call__(self, current_user: User = Depends(get_current_user)):
        # Production environment requires higher permissions
        if self.environment == "production":
            if not PermissionChecker.has_permission(current_user, "device:write"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Production environment access denied"
                )
        return current_user
