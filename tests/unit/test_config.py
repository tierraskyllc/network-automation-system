"""
Unit tests for configuration management.
"""

import pytest
from src.core.config import Settings, get_settings


class TestSettings:
    """Test the Settings configuration class."""
    
    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()
        
        assert settings.APP_NAME == "Network Automation System"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.API_HOST == "0.0.0.0"
        assert settings.API_PORT == 8000
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"
    
    def test_database_settings(self):
        """Test database configuration settings."""
        settings = Settings()
        
        assert "postgresql+asyncpg" in settings.DATABASE_URL
        assert settings.DATABASE_HOST == "localhost"
        assert settings.DATABASE_PORT == 5432
        assert settings.DATABASE_NAME == "network_automation"
        assert settings.DATABASE_POOL_SIZE == 20
    
    def test_redis_settings(self):
        """Test Redis configuration settings."""
        settings = Settings()
        
        assert "redis://localhost:6379" in settings.REDIS_URL
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379
        assert settings.REDIS_DB == 0
    
    def test_security_settings(self):
        """Test security configuration settings."""
        settings = Settings()
        
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS == 7
        assert "localhost" in settings.ALLOWED_HOSTS
    
    def test_cors_settings_parsing(self):
        """Test CORS settings parsing from string."""
        settings = Settings(CORS_ORIGINS="http://localhost:3000,http://localhost:8080")
        
        assert isinstance(settings.CORS_ORIGINS, list)
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:8080" in settings.CORS_ORIGINS
    
    def test_feature_flags(self):
        """Test feature flag settings."""
        settings = Settings()
        
        assert settings.FEATURE_MULTI_VENDOR_SUPPORT is True
        assert settings.FEATURE_ADVANCED_WORKFLOWS is True
        assert settings.FEATURE_ML_ANALYTICS is False
    
    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2  # Same instance due to lru_cache
