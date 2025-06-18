"""
Application Configuration

This module handles all application configuration using Pydantic settings
with environment variable support.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Network Automation System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://netauto:password@localhost:5432/network_automation"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "network_automation"
    DATABASE_USER: str = "netauto"
    DATABASE_PASSWORD: str = "password"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Security
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Network Security
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    TRUSTED_PROXIES: List[str] = ["127.0.0.1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    
    # AI/ML
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 2000
    
    # Ollama (alternative to OpenAI)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    
    # LangChain
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "network-automation"
    
    # Network Devices
    DEFAULT_DEVICE_USERNAME: str = "admin"
    DEFAULT_DEVICE_PASSWORD: str = "admin"
    DEFAULT_DEVICE_ENABLE_PASSWORD: str = "enable"
    DEVICE_CONNECTION_TIMEOUT: int = 30
    DEVICE_COMMAND_TIMEOUT: int = 60
    DEVICE_MAX_CONCURRENT_CONNECTIONS: int = 10
    
    # pyATS/Genie
    PYATS_LOG_LEVEL: str = "INFO"
    PYATS_ARCHIVE_DIR: str = "./logs/pyats"
    GENIE_TESTBED_FILE: str = "./configs/testbed.yaml"
    
    # MCP
    MCP_SERVER_HOST: str = "localhost"
    MCP_SERVER_PORT: int = 8001
    MCP_CLIENT_TIMEOUT: int = 30
    MCP_CONTEXT_CACHE_TTL: int = 3600
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    PROMETHEUS_METRICS_PATH: str = "/metrics"
    
    # Logging
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: str = "./logs/app.log"
    LOG_ROTATION_SIZE: str = "100MB"
    LOG_RETENTION_DAYS: int = 30
    
    # External Integrations
    VAULT_ENABLED: bool = False
    VAULT_URL: str = "http://localhost:8200"
    VAULT_TOKEN: Optional[str] = None
    VAULT_MOUNT_PATH: str = "secret"
    
    # CMDB
    CMDB_ENABLED: bool = False
    CMDB_TYPE: str = "servicenow"
    CMDB_URL: Optional[str] = None
    CMDB_USERNAME: Optional[str] = None
    CMDB_PASSWORD: Optional[str] = None
    
    # Workflows
    WORKFLOW_MAX_STEPS: int = 50
    WORKFLOW_TIMEOUT_MINUTES: int = 30
    WORKFLOW_RETRY_ATTEMPTS: int = 3
    WORKFLOW_PARALLEL_EXECUTION: bool = True
    
    # Topology Discovery
    TOPOLOGY_SCAN_INTERVAL_MINUTES: int = 60
    TOPOLOGY_FULL_SCAN_INTERVAL_HOURS: int = 24
    TOPOLOGY_DISCOVERY_ENABLED: bool = True
    TOPOLOGY_AUTO_DISCOVERY: bool = True
    
    # Backup & Recovery
    CONFIG_BACKUP_ENABLED: bool = True
    CONFIG_BACKUP_INTERVAL_HOURS: int = 6
    CONFIG_BACKUP_RETENTION_DAYS: int = 90
    CONFIG_BACKUP_STORAGE_PATH: str = "./backups/configs"
    
    # Development
    ENABLE_SWAGGER_UI: bool = True
    ENABLE_REDOC: bool = True
    ENABLE_DEBUG_TOOLBAR: bool = False
    
    # Testing
    TEST_DATABASE_URL: str = "postgresql+asyncpg://test:test@localhost:5433/test_network_automation"
    TEST_REDIS_URL: str = "redis://localhost:6379/15"
    MOCK_DEVICES_ENABLED: bool = False
    MOCK_DEVICE_COUNT: int = 5
    
    # Performance
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    REDIS_CONNECTION_POOL_SIZE: int = 50
    CACHE_TTL_SECONDS: int = 3600
    CACHE_MAX_SIZE: int = 1000
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST_SIZE: int = 20
    
    # Feature Flags
    FEATURE_MULTI_VENDOR_SUPPORT: bool = True
    FEATURE_ADVANCED_WORKFLOWS: bool = True
    FEATURE_ML_ANALYTICS: bool = False
    FEATURE_PREDICTIVE_MAINTENANCE: bool = False
    FEATURE_AUTOMATED_REMEDIATION: bool = False
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("CORS_METHODS", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @field_validator("CORS_HEADERS", mode="before")
    @classmethod
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(",")]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @field_validator("TRUSTED_PROXIES", mode="before")
    @classmethod
    def parse_trusted_proxies(cls, v):
        if isinstance(v, str):
            return [proxy.strip() for proxy in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
