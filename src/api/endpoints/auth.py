"""
Authentication Endpoints

User authentication, registration, and session management endpoints.
"""

import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from ...core.database import get_db
from ...core.models.user import User, UserStatus
from ...core.security.auth import AuthenticationService, PasswordManager, MFAManager
from ...core.security.rbac import RoleBasedAccessControl
from ..middleware.auth import get_current_user, get_optional_user

logger = structlog.get_logger(__name__)

router = APIRouter()


# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_token: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    status: str
    is_verified: bool
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime]


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class EnableMFAResponse(BaseModel):
    secret: str
    qr_code_url: str
    backup_codes: list[str]


class VerifyMFARequest(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens"""
    auth_service = AuthenticationService(db)
    
    # Get client IP
    client_ip = request.client.host if request.client else None
    
    # Authenticate user
    auth_result = await auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password,
        mfa_token=login_data.mfa_token,
        ip_address=client_ip
    )
    
    if not auth_result.success:
        if auth_result.requires_mfa:
            raise HTTPException(
                status_code=status.HTTP_200_OK,  # Special case for MFA
                detail={
                    "requires_mfa": True,
                    "message": "MFA token required"
                }
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_result.error or "Authentication failed"
        )
    
    # Create session and tokens
    user_agent = request.headers.get("user-agent")
    access_token, refresh_token = await auth_service.create_session(
        user=auth_result.user,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=auth_service.jwt_manager.access_token_expire_minutes * 60,
        user={
            "id": auth_result.user.id,
            "username": auth_result.user.username,
            "email": auth_result.user.email,
            "full_name": auth_result.user.full_name,
            "mfa_enabled": auth_result.user.mfa_enabled
        }
    )


@router.post("/register", response_model=UserResponse)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register new user account"""
    # Check if username already exists
    stmt = select(User).where(User.username == register_data.username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    stmt = select(User).where(User.email == register_data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    password_manager = PasswordManager()
    is_strong, errors = password_manager.validate_password_strength(register_data.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "errors": errors}
        )
    
    # Create user
    user = User(
        username=register_data.username,
        email=register_data.email,
        full_name=register_data.full_name,
        password_hash=password_manager.hash_password(register_data.password),
        status=UserStatus.ACTIVE.value,
        password_changed_at=datetime.utcnow()
    )
    
    db.add(user)
    await db.flush()
    
    # Assign default role
    rbac = RoleBasedAccessControl(db)
    await rbac.assign_role_to_user(user, "network_viewer")
    
    await db.commit()
    
    logger.info("User registered", username=user.username, user_id=user.id)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        is_verified=user.is_verified,
        mfa_enabled=user.mfa_enabled,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        status=current_user.status,
        is_verified=current_user.is_verified,
        mfa_enabled=current_user.mfa_enabled,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    password_manager = PasswordManager()
    
    # Verify current password
    if not password_manager.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_strong, errors = password_manager.validate_password_strength(password_data.new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "New password does not meet requirements", "errors": errors}
        )
    
    # Update password
    current_user.password_hash = password_manager.hash_password(password_data.new_password)
    current_user.password_changed_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info("Password changed", username=current_user.username, user_id=current_user.id)
    
    return {"message": "Password changed successfully"}


@router.post("/enable-mfa", response_model=EnableMFAResponse)
async def enable_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable multi-factor authentication"""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )
    
    mfa_manager = MFAManager()
    
    # Generate MFA secret
    secret = mfa_manager.generate_secret()
    qr_code_url = mfa_manager.generate_qr_code_url(secret, current_user.username)
    
    # Generate backup codes (simplified)
    backup_codes = [f"BACKUP-{i:04d}" for i in range(10)]
    
    # Store secret (encrypted in production)
    current_user.mfa_secret = secret
    
    await db.commit()
    
    logger.info("MFA setup initiated", username=current_user.username, user_id=current_user.id)
    
    return EnableMFAResponse(
        secret=secret,
        qr_code_url=qr_code_url,
        backup_codes=backup_codes
    )


@router.post("/verify-mfa")
async def verify_mfa(
    mfa_data: VerifyMFARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify MFA setup and enable it"""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled"
        )
    
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup not initiated"
        )
    
    mfa_manager = MFAManager()
    
    # Verify TOTP token
    if not mfa_manager.verify_totp(current_user.mfa_secret, mfa_data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token"
        )
    
    # Enable MFA
    current_user.mfa_enabled = True
    await db.commit()
    
    logger.info("MFA enabled", username=current_user.username, user_id=current_user.id)
    
    return {"message": "MFA enabled successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout user and invalidate session"""
    # In a full implementation, you would invalidate the JWT token
    # This could be done by maintaining a blacklist or using shorter-lived tokens
    
    logger.info("User logged out", username=current_user.username, user_id=current_user.id)
    
    return {"message": "Logged out successfully"}
