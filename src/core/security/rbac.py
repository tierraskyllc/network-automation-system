"""
Role-Based Access Control (RBAC)

Implementation of RBAC system for fine-grained access control.
"""

import structlog
from typing import Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from enum import Enum

from ..models.user import User, Role, Permission
from ..models.device import Device

logger = structlog.get_logger(__name__)


class NetworkPermissions(Enum):
    """Standard network automation permissions"""
    # Device permissions
    DEVICE_READ = "device:read"
    DEVICE_WRITE = "device:write"
    DEVICE_DELETE = "device:delete"
    DEVICE_CONNECT = "device:connect"
    
    # Command permissions
    COMMAND_READ = "command:read"
    COMMAND_EXECUTE = "command:execute"
    COMMAND_WRITE = "command:write"
    COMMAND_DELETE = "command:delete"
    
    # Workflow permissions
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_EXECUTE = "workflow:execute"
    WORKFLOW_WRITE = "workflow:write"
    WORKFLOW_DELETE = "workflow:delete"
    
    # Topology permissions
    TOPOLOGY_READ = "topology:read"
    TOPOLOGY_WRITE = "topology:write"
    TOPOLOGY_DISCOVER = "topology:discover"
    
    # User management permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    AUDIT_READ = "audit:read"
    CONFIG_WRITE = "config:write"


class NetworkRoles(Enum):
    """Standard network automation roles"""
    NETWORK_ADMIN = "network_admin"
    NETWORK_OPERATOR = "network_operator"
    NETWORK_VIEWER = "network_viewer"
    SECURITY_ADMIN = "security_admin"
    SYSTEM_ADMIN = "system_admin"


# Role-Permission mappings
ROLE_PERMISSIONS = {
    NetworkRoles.NETWORK_ADMIN: [
        NetworkPermissions.DEVICE_READ,
        NetworkPermissions.DEVICE_WRITE,
        NetworkPermissions.DEVICE_CONNECT,
        NetworkPermissions.COMMAND_READ,
        NetworkPermissions.COMMAND_EXECUTE,
        NetworkPermissions.COMMAND_WRITE,
        NetworkPermissions.WORKFLOW_READ,
        NetworkPermissions.WORKFLOW_EXECUTE,
        NetworkPermissions.WORKFLOW_WRITE,
        NetworkPermissions.TOPOLOGY_READ,
        NetworkPermissions.TOPOLOGY_WRITE,
        NetworkPermissions.TOPOLOGY_DISCOVER,
    ],
    NetworkRoles.NETWORK_OPERATOR: [
        NetworkPermissions.DEVICE_READ,
        NetworkPermissions.DEVICE_CONNECT,
        NetworkPermissions.COMMAND_READ,
        NetworkPermissions.COMMAND_EXECUTE,
        NetworkPermissions.WORKFLOW_READ,
        NetworkPermissions.WORKFLOW_EXECUTE,
        NetworkPermissions.TOPOLOGY_READ,
    ],
    NetworkRoles.NETWORK_VIEWER: [
        NetworkPermissions.DEVICE_READ,
        NetworkPermissions.COMMAND_READ,
        NetworkPermissions.WORKFLOW_READ,
        NetworkPermissions.TOPOLOGY_READ,
    ],
    NetworkRoles.SECURITY_ADMIN: [
        NetworkPermissions.DEVICE_READ,
        NetworkPermissions.USER_READ,
        NetworkPermissions.USER_WRITE,
        NetworkPermissions.AUDIT_READ,
        NetworkPermissions.CONFIG_WRITE,
    ],
    NetworkRoles.SYSTEM_ADMIN: [
        NetworkPermissions.SYSTEM_ADMIN,
        NetworkPermissions.USER_READ,
        NetworkPermissions.USER_WRITE,
        NetworkPermissions.USER_DELETE,
        NetworkPermissions.CONFIG_WRITE,
        NetworkPermissions.AUDIT_READ,
    ],
}


class RoleBasedAccessControl:
    """RBAC implementation for network automation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def initialize_default_roles(self):
        """Initialize default roles and permissions"""
        logger.info("Initializing default RBAC roles and permissions")
        
        # Create default permissions
        for permission in NetworkPermissions:
            resource, action = permission.value.split(":")
            await self._create_permission_if_not_exists(
                name=permission.value,
                resource=resource,
                action=action,
                description=f"Permission to {action} {resource}"
            )
        
        # Create default roles
        for role_enum, permissions in ROLE_PERMISSIONS.items():
            role = await self._create_role_if_not_exists(
                name=role_enum.value,
                display_name=role_enum.value.replace("_", " ").title(),
                description=f"Default {role_enum.value} role",
                is_system_role=True
            )
            
            # Assign permissions to role
            for permission_enum in permissions:
                await self._assign_permission_to_role(role, permission_enum.value)
        
        await self.db.commit()
        logger.info("Default RBAC roles and permissions initialized")
    
    async def _create_permission_if_not_exists(self, name: str, resource: str, 
                                             action: str, description: str) -> Permission:
        """Create permission if it doesn't exist"""
        stmt = select(Permission).where(Permission.name == name)
        result = await self.db.execute(stmt)
        permission = result.scalar_one_or_none()
        
        if not permission:
            permission = Permission(
                name=name,
                resource=resource,
                action=action,
                description=description,
                is_system_permission=True
            )
            self.db.add(permission)
            await self.db.flush()
        
        return permission
    
    async def _create_role_if_not_exists(self, name: str, display_name: str,
                                       description: str, is_system_role: bool = False) -> Role:
        """Create role if it doesn't exist"""
        stmt = select(Role).where(Role.name == name)
        result = await self.db.execute(stmt)
        role = result.scalar_one_or_none()
        
        if not role:
            role = Role(
                name=name,
                display_name=display_name,
                description=description,
                is_system_role=is_system_role
            )
            self.db.add(role)
            await self.db.flush()
        
        return role
    
    async def _assign_permission_to_role(self, role: Role, permission_name: str):
        """Assign permission to role"""
        stmt = select(Permission).where(Permission.name == permission_name)
        result = await self.db.execute(stmt)
        permission = result.scalar_one_or_none()
        
        if permission and permission not in role.permissions:
            role.permissions.append(permission)
    
    async def create_custom_role(self, name: str, display_name: str,
                               description: str, permissions: List[str]) -> Role:
        """Create custom role with specified permissions"""
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            is_system_role=False
        )
        self.db.add(role)
        await self.db.flush()
        
        # Assign permissions
        for permission_name in permissions:
            await self._assign_permission_to_role(role, permission_name)
        
        await self.db.commit()
        return role
    
    async def assign_role_to_user(self, user: User, role_name: str):
        """Assign role to user"""
        stmt = select(Role).where(Role.name == role_name)
        result = await self.db.execute(stmt)
        role = result.scalar_one_or_none()
        
        if not role:
            raise ValueError(f"Role {role_name} not found")
        
        if role not in user.roles:
            user.roles.append(role)
            await self.db.commit()
    
    async def remove_role_from_user(self, user: User, role_name: str):
        """Remove role from user"""
        stmt = select(Role).where(Role.name == role_name)
        result = await self.db.execute(stmt)
        role = result.scalar_one_or_none()
        
        if role and role in user.roles:
            user.roles.remove(role)
            await self.db.commit()


class PermissionChecker:
    """Utility class for checking permissions"""
    
    @staticmethod
    def has_permission(user: User, required_permission: str) -> bool:
        """Check if user has specific permission"""
        if user.is_superuser:
            return True
        
        for role in user.roles:
            for permission in role.permissions:
                if permission.name == required_permission:
                    return True
        
        return False
    
    @staticmethod
    def has_any_permission(user: User, required_permissions: List[str]) -> bool:
        """Check if user has any of the required permissions"""
        if user.is_superuser:
            return True
        
        user_permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                user_permissions.add(permission.name)
        
        return bool(user_permissions.intersection(set(required_permissions)))
    
    @staticmethod
    def has_all_permissions(user: User, required_permissions: List[str]) -> bool:
        """Check if user has all required permissions"""
        if user.is_superuser:
            return True
        
        user_permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                user_permissions.add(permission.name)
        
        return set(required_permissions).issubset(user_permissions)
    
    @staticmethod
    def get_user_permissions(user: User) -> Set[str]:
        """Get all permissions for user"""
        if user.is_superuser:
            return {perm.value for perm in NetworkPermissions}
        
        permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        
        return permissions


class ResourceAccessControl:
    """Resource-specific access control"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_device_access(self, user: User, device: Device) -> bool:
        """Check if user has access to specific device"""
        # Basic permission check
        if not PermissionChecker.has_permission(user, NetworkPermissions.DEVICE_READ.value):
            return False
        
        # Environment-based access control
        if device.environment == "production":
            return PermissionChecker.has_permission(user, NetworkPermissions.DEVICE_WRITE.value)
        
        # Site-based access control (example)
        # This could be extended to check user's assigned sites
        
        return True
    
    async def check_command_execution_access(self, user: User, device: Device, 
                                           command: str) -> bool:
        """Check if user can execute command on device"""
        # Check basic execute permission
        if not PermissionChecker.has_permission(user, NetworkPermissions.COMMAND_EXECUTE.value):
            return False
        
        # Check device access
        if not await self.check_device_access(user, device):
            return False
        
        # Risk-based command authorization
        high_risk_commands = ["reload", "shutdown", "erase", "format", "delete"]
        if any(risk_cmd in command.lower() for risk_cmd in high_risk_commands):
            return PermissionChecker.has_permission(user, NetworkPermissions.SYSTEM_ADMIN.value)
        
        return True
