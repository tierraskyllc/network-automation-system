"""
Unit tests for authentication and authorization functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from src.core.security.auth import (
    AuthenticationService,
    AuthenticationResult,
    JWTManager,
    PasswordManager,
    MFAManager
)
from src.core.models.user import User, UserStatus


class TestPasswordManager:
    """Test password management functionality."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password_manager = PasswordManager()
        password = "testpassword123"
        
        hashed = password_manager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert password_manager.verify_password(password, hashed)
    
    def test_verify_password_success(self):
        """Test successful password verification."""
        password_manager = PasswordManager()
        password = "testpassword123"
        hashed = password_manager.hash_password(password)
        
        result = password_manager.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_failure(self):
        """Test failed password verification."""
        password_manager = PasswordManager()
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = password_manager.hash_password(password)
        
        result = password_manager.verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_generate_password(self):
        """Test password generation."""
        password_manager = PasswordManager()
        
        password = password_manager.generate_password(16)
        
        assert len(password) == 16
        assert password.isalnum() is False  # Should contain special characters
    
    def test_validate_password_strength_strong(self):
        """Test strong password validation."""
        password_manager = PasswordManager()
        strong_password = "StrongP@ssw0rd123"
        
        is_strong, errors = password_manager.validate_password_strength(strong_password)
        
        assert is_strong is True
        assert len(errors) == 0
    
    def test_validate_password_strength_weak(self):
        """Test weak password validation."""
        password_manager = PasswordManager()
        weak_password = "weak"
        
        is_strong, errors = password_manager.validate_password_strength(weak_password)
        
        assert is_strong is False
        assert len(errors) > 0


class TestJWTManager:
    """Test JWT token management."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        jwt_manager = JWTManager()
        user_id = 1
        username = "testuser"
        permissions = ["device:read", "command:execute"]
        
        token = jwt_manager.create_access_token(user_id, username, permissions)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        jwt_manager = JWTManager()
        user_id = 1
        
        token = jwt_manager.create_refresh_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test valid token verification."""
        jwt_manager = JWTManager()
        user_id = 1
        username = "testuser"
        permissions = ["device:read"]
        
        token = jwt_manager.create_access_token(user_id, username, permissions)
        payload = jwt_manager.verify_token(token)
        
        assert payload["sub"] == str(user_id)
        assert payload["username"] == username
        assert payload["permissions"] == permissions
        assert payload["type"] == "access"
    
    def test_verify_token_invalid(self):
        """Test invalid token verification."""
        jwt_manager = JWTManager()
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):  # Should raise HTTPException
            jwt_manager.verify_token(invalid_token)


class TestMFAManager:
    """Test multi-factor authentication."""
    
    def test_generate_secret(self):
        """Test MFA secret generation."""
        mfa_manager = MFAManager()
        
        secret = mfa_manager.generate_secret()
        
        assert isinstance(secret, str)
        assert len(secret) > 0
    
    def test_generate_qr_code_url(self):
        """Test QR code URL generation."""
        mfa_manager = MFAManager()
        secret = "JBSWY3DPEHPK3PXP"
        username = "testuser"
        
        qr_url = mfa_manager.generate_qr_code_url(secret, username)
        
        assert isinstance(qr_url, str)
        assert "otpauth://totp/" in qr_url
        assert username in qr_url
    
    def test_verify_totp_valid(self):
        """Test valid TOTP verification."""
        mfa_manager = MFAManager()
        secret = "JBSWY3DPEHPK3PXP"
        
        # Generate a valid token (this is a simplified test)
        import pyotp
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()
        
        result = mfa_manager.verify_totp(secret, valid_token)
        
        assert result is True
    
    def test_verify_totp_invalid(self):
        """Test invalid TOTP verification."""
        mfa_manager = MFAManager()
        secret = "JBSWY3DPEHPK3PXP"
        invalid_token = "000000"
        
        result = mfa_manager.verify_totp(secret, invalid_token)
        
        assert result is False


class TestAuthenticationService:
    """Test authentication service."""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Mock database session
        mock_db = AsyncMock()
        
        # Mock user
        password_manager = PasswordManager()
        mock_user = User(
            id=1,
            username="testuser",
            password_hash=password_manager.hash_password("testpassword"),
            status=UserStatus.ACTIVE.value,
            mfa_enabled=False,
            failed_login_attempts=0,
            locked_until=None
        )
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        auth_service = AuthenticationService(mock_db)
        
        result = await auth_service.authenticate_user("testuser", "testpassword")
        
        assert result.success is True
        assert result.user == mock_user
        assert result.error is None
        assert result.requires_mfa is False
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password."""
        # Mock database session
        mock_db = AsyncMock()
        
        # Mock user
        password_manager = PasswordManager()
        mock_user = User(
            id=1,
            username="testuser",
            password_hash=password_manager.hash_password("testpassword"),
            status=UserStatus.ACTIVE.value,
            mfa_enabled=False,
            failed_login_attempts=0,
            locked_until=None
        )
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        auth_service = AuthenticationService(mock_db)
        
        result = await auth_service.authenticate_user("testuser", "wrongpassword")
        
        assert result.success is False
        assert result.user is None
        assert result.error == "Invalid credentials"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user."""
        # Mock database session
        mock_db = AsyncMock()
        
        # Mock database query returning None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        auth_service = AuthenticationService(mock_db)
        
        result = await auth_service.authenticate_user("nonexistent", "password")
        
        assert result.success is False
        assert result.user is None
        assert result.error == "Invalid credentials"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_mfa_required(self):
        """Test authentication requiring MFA."""
        # Mock database session
        mock_db = AsyncMock()
        
        # Mock user with MFA enabled
        password_manager = PasswordManager()
        mock_user = User(
            id=1,
            username="testuser",
            password_hash=password_manager.hash_password("testpassword"),
            status=UserStatus.ACTIVE.value,
            mfa_enabled=True,
            mfa_secret="JBSWY3DPEHPK3PXP",
            failed_login_attempts=0,
            locked_until=None
        )
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        auth_service = AuthenticationService(mock_db)
        
        result = await auth_service.authenticate_user("testuser", "testpassword")
        
        assert result.success is False
        assert result.user is None
        assert result.requires_mfa is True
        assert result.error == "MFA token required"
