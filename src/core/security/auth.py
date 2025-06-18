"""
Authentication and Authorization Services

Core authentication and authorization functionality for the network automation system.
"""

import jwt
import bcrypt
import pyotp
import secrets
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from passlib.context import CryptContext

from ..models.user import User, UserSession, UserStatus
from ..models.audit import AuditLog, AuditAction, AuditResource
from ..config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationResult:
    """Authentication result container"""
    def __init__(self, success: bool, user: Optional[User] = None, 
                 error: Optional[str] = None, requires_mfa: bool = False):
        self.success = success
        self.user = user
        self.error = error
        self.requires_mfa = requires_mfa


class AuthorizationResult:
    """Authorization result container"""
    def __init__(self, allowed: bool, reason: Optional[str] = None):
        self.allowed = allowed
        self.reason = reason


class JWTManager:
    """JWT token management"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, user_id: int, username: str, 
                          permissions: List[str] = None) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "username": username,
            "permissions": permissions or [],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


class PasswordManager:
    """Password management utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_password(length: int = 16) -> str:
        """Generate secure random password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors


class MFAManager:
    """Multi-Factor Authentication management"""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code_url(secret: str, username: str, issuer: str = "Network Automation") -> str:
        """Generate QR code URL for TOTP setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(username, issuer_name=issuer)
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 1 window tolerance


class AuthenticationService:
    """Main authentication service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jwt_manager = JWTManager()
        self.password_manager = PasswordManager()
        self.mfa_manager = MFAManager()
    
    async def authenticate_user(self, username: str, password: str, 
                              mfa_token: Optional[str] = None,
                              ip_address: Optional[str] = None) -> AuthenticationResult:
        """Authenticate user with username/password and optional MFA"""
        try:
            # Get user from database
            stmt = select(User).where(User.username == username)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                await self._log_auth_failure(username, "User not found", ip_address)
                return AuthenticationResult(False, error="Invalid credentials")
            
            # Check user status
            if user.status != UserStatus.ACTIVE.value:
                await self._log_auth_failure(username, f"User status: {user.status}", ip_address)
                return AuthenticationResult(False, error="Account is not active")
            
            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                await self._log_auth_failure(username, "Account locked", ip_address)
                return AuthenticationResult(False, error="Account is temporarily locked")
            
            # Verify password
            if not self.password_manager.verify_password(password, user.password_hash):
                await self._handle_failed_login(user, ip_address)
                return AuthenticationResult(False, error="Invalid credentials")
            
            # Check MFA if enabled
            if user.mfa_enabled:
                if not mfa_token:
                    return AuthenticationResult(False, requires_mfa=True, 
                                              error="MFA token required")
                
                if not self.mfa_manager.verify_totp(user.mfa_secret, mfa_token):
                    await self._log_auth_failure(username, "Invalid MFA token", ip_address)
                    return AuthenticationResult(False, error="Invalid MFA token")
            
            # Reset failed login attempts on successful auth
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            user.login_count += 1
            
            await self.db.commit()
            
            await self._log_auth_success(user, ip_address)
            return AuthenticationResult(True, user=user)
            
        except Exception as e:
            logger.error("Authentication error", error=str(e), username=username)
            return AuthenticationResult(False, error="Authentication failed")
    
    async def create_session(self, user: User, ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> Tuple[str, str]:
        """Create user session and return access/refresh tokens"""
        # Get user permissions
        permissions = await self._get_user_permissions(user)
        
        # Create tokens
        access_token = self.jwt_manager.create_access_token(
            user.id, user.username, permissions
        )
        refresh_token = self.jwt_manager.create_refresh_token(user.id)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(minutes=self.jwt_manager.access_token_expire_minutes)
        )
        
        self.db.add(session)
        await self.db.commit()
        
        return access_token, refresh_token
    
    async def _get_user_permissions(self, user: User) -> List[str]:
        """Get user permissions from roles"""
        permissions = []
        for role in user.roles:
            for permission in role.permissions:
                perm_name = f"{permission.resource}:{permission.action}"
                if perm_name not in permissions:
                    permissions.append(perm_name)
        return permissions
    
    async def _handle_failed_login(self, user: User, ip_address: Optional[str]):
        """Handle failed login attempt"""
        user.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            logger.warning("Account locked due to failed login attempts", 
                         username=user.username, ip_address=ip_address)
        
        await self.db.commit()
        await self._log_auth_failure(user.username, "Invalid password", ip_address)
    
    async def _log_auth_success(self, user: User, ip_address: Optional[str]):
        """Log successful authentication"""
        audit_log = AuditLog(
            event_id=secrets.token_urlsafe(16),
            user_id=user.id,
            username=user.username,
            user_ip=ip_address,
            action=AuditAction.LOGIN,
            resource_type=AuditResource.USER,
            resource_id=str(user.id),
            description=f"User {user.username} logged in successfully",
            success=True
        )
        self.db.add(audit_log)
    
    async def _log_auth_failure(self, username: str, reason: str, ip_address: Optional[str]):
        """Log failed authentication"""
        audit_log = AuditLog(
            event_id=secrets.token_urlsafe(16),
            username=username,
            user_ip=ip_address,
            action=AuditAction.LOGIN,
            resource_type=AuditResource.USER,
            description=f"Failed login attempt for {username}: {reason}",
            success=False,
            error_message=reason
        )
        self.db.add(audit_log)
        await self.db.commit()


class AuthorizationService:
    """Authorization service for resource access control"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_permission(self, user: User, resource: str, 
                             action: str) -> AuthorizationResult:
        """Check if user has permission for resource action"""
        if user.is_superuser:
            return AuthorizationResult(True)
        
        required_permission = f"{resource}:{action}"
        
        for role in user.roles:
            for permission in role.permissions:
                perm_name = f"{permission.resource}:{permission.action}"
                if perm_name == required_permission:
                    return AuthorizationResult(True)
        
        return AuthorizationResult(False, f"Missing permission: {required_permission}")
    
    async def check_device_access(self, user: User, device_id: int) -> AuthorizationResult:
        """Check if user has access to specific device"""
        # Implement device-specific access control logic
        # This could be based on device tags, location, environment, etc.
        return AuthorizationResult(True)  # Placeholder implementation
