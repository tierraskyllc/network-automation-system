"""
Security Module

This module provides authentication, authorization, and security utilities
for the network automation system.
"""

from .auth import (
    AuthenticationService,
    AuthorizationService,
    JWTManager,
    PasswordManager,
    MFAManager,
)
from .rbac import (
    RoleBasedAccessControl,
    PermissionChecker,
    ResourceAccessControl,
)
# from .vault import (
#     VaultManager,
#     CredentialManager,
#     SecretManager,
# )
# from .encryption import (
#     EncryptionManager,
#     CryptoUtils,
# )

__all__ = [
    # Authentication
    "AuthenticationService",
    "AuthorizationService", 
    "JWTManager",
    "PasswordManager",
    "MFAManager",
    
    # Authorization
    "RoleBasedAccessControl",
    "PermissionChecker",
    "ResourceAccessControl",
    
    # Credential Management
    # "VaultManager",
    # "CredentialManager",
    # "SecretManager",

    # Encryption
    # "EncryptionManager",
    # "CryptoUtils",
]
