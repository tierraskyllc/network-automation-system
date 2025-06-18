#!/usr/bin/env python3
"""
Network Automation System Setup Script

This script sets up the complete network automation system including:
- Database initialization
- Default users and roles
- Environment configuration
- Docker containers
- Initial data seeding
"""

import asyncio
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config import get_settings
from core.database import init_db, AsyncSessionLocal
from core.security.auth import PasswordManager
from core.security.rbac import RoleBasedAccessControl
from core.models.user import User


async def setup_database():
    """Initialize database and run migrations"""
    print("🔧 Setting up database...")
    
    try:
        # Initialize database
        await init_db()
        print("✅ Database tables created")
        
        # Run Alembic migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✅ Database migrations completed")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise


async def setup_rbac():
    """Initialize roles and permissions"""
    print("🔧 Setting up RBAC...")
    
    try:
        async with AsyncSessionLocal() as db:
            rbac = RoleBasedAccessControl(db)
            await rbac.initialize_default_roles()
            await db.commit()
        
        print("✅ RBAC roles and permissions created")
        
    except Exception as e:
        print(f"❌ RBAC setup failed: {e}")
        raise


async def create_admin_user(username: str = "admin", password: str = "admin123", email: str = "admin@example.com"):
    """Create default admin user"""
    print("🔧 Creating admin user...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Check if admin user already exists
            from sqlalchemy import select
            stmt = select(User).where(User.username == username)
            result = await db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"⚠️ Admin user '{username}' already exists")
                return
            
            # Create admin user
            password_manager = PasswordManager()
            admin_user = User(
                username=username,
                email=email,
                full_name="System Administrator",
                password_hash=password_manager.hash_password(password),
                status="active",
                is_verified=True,
                is_superuser=True
            )
            
            db.add(admin_user)
            await db.flush()
            
            # Assign admin role
            rbac = RoleBasedAccessControl(db)
            await rbac.assign_role_to_user(admin_user, "system_admin")
            
            await db.commit()
            
        print(f"✅ Admin user '{username}' created")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print("   ⚠️ Please change the default password after first login!")
        
    except Exception as e:
        print(f"❌ Admin user creation failed: {e}")
        raise


def setup_environment():
    """Setup environment configuration"""
    print("🔧 Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        # Copy .env.example to .env
        env_file.write_text(env_example.read_text())
        print("✅ Environment file created from .env.example")
        print("   ⚠️ Please review and update .env with your configuration!")
    elif env_file.exists():
        print("✅ Environment file already exists")
    else:
        print("❌ No .env.example file found")


def setup_docker():
    """Setup Docker containers"""
    print("🔧 Setting up Docker containers...")
    
    try:
        # Check if Docker is available
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
        
        # Start Docker containers
        subprocess.run(["docker-compose", "up", "-d", "postgres", "redis", "vault"], check=True)
        print("✅ Docker containers started")
        
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        import time
        time.sleep(10)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker setup failed: {e}")
        print("   Please ensure Docker and Docker Compose are installed")
        raise
    except FileNotFoundError:
        print("❌ Docker or Docker Compose not found")
        print("   Please install Docker and Docker Compose")
        raise


def create_directories():
    """Create necessary directories"""
    print("🔧 Creating directories...")
    
    directories = [
        "logs",
        "backups",
        "configs",
        "data",
        "uploads",
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created")


def install_dependencies():
    """Install Python dependencies"""
    print("🔧 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        raise


async def seed_sample_data():
    """Seed sample data for development"""
    print("🔧 Seeding sample data...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Add sample devices
            from core.models.device import Device, DeviceType
            
            sample_devices = [
                {
                    "hostname": "router-01",
                    "ip_address": "192.168.1.1",
                    "device_type": DeviceType.ROUTER,
                    "vendor": "cisco",
                    "model": "ISR4331",
                    "os_version": "16.09.04",
                    "site": "headquarters",
                    "environment": "production"
                },
                {
                    "hostname": "switch-01", 
                    "ip_address": "192.168.1.2",
                    "device_type": DeviceType.SWITCH,
                    "vendor": "cisco",
                    "model": "C9300-24T",
                    "os_version": "16.12.05",
                    "site": "headquarters",
                    "environment": "production"
                }
            ]
            
            for device_data in sample_devices:
                device = Device(**device_data)
                db.add(device)
            
            await db.commit()
        
        print("✅ Sample data seeded")
        
    except Exception as e:
        print(f"❌ Sample data seeding failed: {e}")
        raise


async def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Network Automation System Setup")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker setup")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-sample-data", action="store_true", help="Skip sample data seeding")
    parser.add_argument("--admin-username", default="admin", help="Admin username")
    parser.add_argument("--admin-password", default="admin123", help="Admin password")
    parser.add_argument("--admin-email", default="admin@example.com", help="Admin email")
    
    args = parser.parse_args()
    
    print("🚀 Network Automation System Setup")
    print("=" * 50)
    
    try:
        # Create directories
        create_directories()
        
        # Setup environment
        setup_environment()
        
        # Install dependencies
        if not args.skip_deps:
            install_dependencies()
        
        # Setup Docker
        if not args.skip_docker:
            setup_docker()
        
        # Setup database
        await setup_database()
        
        # Setup RBAC
        await setup_rbac()
        
        # Create admin user
        await create_admin_user(
            username=args.admin_username,
            password=args.admin_password,
            email=args.admin_email
        )
        
        # Seed sample data
        if not args.skip_sample_data:
            await seed_sample_data()
        
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Review and update .env configuration")
        print("2. Start the application: python -m src.api.main")
        print("3. Access the API docs: http://localhost:8000/docs")
        print(f"4. Login with admin credentials: {args.admin_username}/{args.admin_password}")
        print("\n⚠️ Remember to change the default admin password!")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
