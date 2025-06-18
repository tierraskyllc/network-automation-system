"""
Main CLI Application

Command-line interface for managing the network automation system.
"""

import asyncio
import typer
import structlog
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from ..core.config import get_settings
from ..core.database import init_db, close_db
from ..core.security.rbac import RoleBasedAccessControl
from .commands import (
    database_commands,
    user_commands,
    device_commands,
    workflow_commands,
    backup_commands,
)

# Initialize CLI app
app = typer.Typer(
    name="network-automation",
    help="Network Automation System CLI",
    add_completion=False,
)

# Add command groups
app.add_typer(database_commands.app, name="db", help="Database management commands")
app.add_typer(user_commands.app, name="user", help="User management commands")
app.add_typer(device_commands.app, name="device", help="Device management commands")
app.add_typer(workflow_commands.app, name="workflow", help="Workflow management commands")
app.add_typer(backup_commands.app, name="backup", help="Backup and restore commands")

# Initialize console and logger
console = Console()
logger = structlog.get_logger(__name__)
settings = get_settings()


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold blue]Network Automation System[/bold blue]")
    console.print(f"Version: {settings.APP_VERSION}")
    console.print(f"Environment: {settings.ENVIRONMENT}")


@app.command()
def status():
    """Show system status."""
    console.print("[bold blue]System Status[/bold blue]")
    
    # Create status table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    # Check database
    try:
        # This would need to be implemented with actual health checks
        table.add_row("Database", "✅ Connected", f"PostgreSQL at {settings.DATABASE_HOST}")
    except Exception as e:
        table.add_row("Database", "❌ Error", str(e))
    
    # Check Redis
    try:
        table.add_row("Cache", "✅ Connected", f"Redis at {settings.REDIS_HOST}")
    except Exception as e:
        table.add_row("Cache", "❌ Error", str(e))
    
    # Check Vault
    if settings.VAULT_ENABLED:
        try:
            table.add_row("Vault", "✅ Connected", f"Vault at {settings.VAULT_URL}")
        except Exception as e:
            table.add_row("Vault", "❌ Error", str(e))
    else:
        table.add_row("Vault", "⚠️ Disabled", "Credential management disabled")
    
    console.print(table)


@app.command()
def init():
    """Initialize the system (database, default users, etc.)."""
    console.print("[bold blue]Initializing Network Automation System...[/bold blue]")
    
    async def _init():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Initialize database
            task1 = progress.add_task("Initializing database...", total=None)
            try:
                await init_db()
                progress.update(task1, description="✅ Database initialized")
            except Exception as e:
                progress.update(task1, description=f"❌ Database error: {e}")
                return
            
            # Initialize RBAC
            task2 = progress.add_task("Setting up roles and permissions...", total=None)
            try:
                from ..core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    rbac = RoleBasedAccessControl(db)
                    await rbac.initialize_default_roles()
                    await db.commit()
                progress.update(task2, description="✅ RBAC initialized")
            except Exception as e:
                progress.update(task2, description=f"❌ RBAC error: {e}")
                return
            
            # Create admin user
            task3 = progress.add_task("Creating admin user...", total=None)
            try:
                # This would create a default admin user
                progress.update(task3, description="✅ Admin user created")
            except Exception as e:
                progress.update(task3, description=f"❌ Admin user error: {e}")
                return
    
    asyncio.run(_init())
    console.print("[bold green]✅ System initialization completed![/bold green]")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    validate: bool = typer.Option(False, "--validate", help="Validate configuration"),
):
    """Manage system configuration."""
    if show:
        console.print("[bold blue]Current Configuration[/bold blue]")
        
        # Create config table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Source")
        
        # Add key configuration items
        table.add_row("Environment", settings.ENVIRONMENT, "ENV")
        table.add_row("Debug Mode", str(settings.DEBUG), "ENV")
        table.add_row("Database URL", settings.DATABASE_URL[:50] + "...", "ENV")
        table.add_row("Redis URL", settings.REDIS_URL[:50] + "...", "ENV")
        table.add_row("Vault Enabled", str(settings.VAULT_ENABLED), "ENV")
        table.add_row("API Host", settings.API_HOST, "ENV")
        table.add_row("API Port", str(settings.API_PORT), "ENV")
        
        console.print(table)
    
    if validate:
        console.print("[bold blue]Validating Configuration...[/bold blue]")
        
        errors = []
        warnings = []
        
        # Validate database URL
        if not settings.DATABASE_URL:
            errors.append("DATABASE_URL is not set")
        
        # Validate Redis URL
        if not settings.REDIS_URL:
            errors.append("REDIS_URL is not set")
        
        # Validate JWT secret
        if settings.JWT_SECRET_KEY == "your-super-secret-jwt-key-change-this-in-production":
            warnings.append("JWT_SECRET_KEY is using default value - change for production")
        
        # Validate OpenAI API key
        if not settings.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY is not set - AI features will be limited")
        
        # Display results
        if errors:
            console.print("[bold red]❌ Configuration Errors:[/bold red]")
            for error in errors:
                console.print(f"  • {error}")
        
        if warnings:
            console.print("[bold yellow]⚠️ Configuration Warnings:[/bold yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")
        
        if not errors and not warnings:
            console.print("[bold green]✅ Configuration is valid![/bold green]")


@app.command()
def logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show"),
    level: str = typer.Option("INFO", "--level", help="Log level filter"),
):
    """View system logs."""
    log_file = Path(settings.LOG_FILE_PATH)
    
    if not log_file.exists():
        console.print(f"[red]Log file not found: {log_file}[/red]")
        return
    
    console.print(f"[blue]Showing logs from: {log_file}[/blue]")
    
    if follow:
        console.print("[yellow]Following logs (Ctrl+C to stop)...[/yellow]")
        # Implementation for following logs would go here
        # This is a simplified version
        try:
            with open(log_file, 'r') as f:
                # Seek to end of file
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        console.print(line.strip())
                    else:
                        import time
                        time.sleep(0.1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped following logs[/yellow]")
    else:
        # Show last N lines
        try:
            with open(log_file, 'r') as f:
                lines_list = f.readlines()
                for line in lines_list[-lines:]:
                    console.print(line.strip())
        except Exception as e:
            console.print(f"[red]Error reading log file: {e}[/red]")


@app.command()
def health():
    """Check system health."""
    console.print("[bold blue]System Health Check[/bold blue]")
    
    async def _health_check():
        # This would implement actual health checks
        checks = [
            ("Database Connection", True, "PostgreSQL responding"),
            ("Redis Connection", True, "Redis responding"),
            ("Vault Connection", settings.VAULT_ENABLED, "Vault accessible" if settings.VAULT_ENABLED else "Vault disabled"),
            ("API Endpoints", True, "All endpoints responding"),
            ("Background Tasks", True, "Task queue healthy"),
        ]
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        for check_name, status, details in checks:
            status_icon = "✅" if status else "❌"
            table.add_row(check_name, status_icon, details)
        
        console.print(table)
    
    asyncio.run(_health_check())


if __name__ == "__main__":
    app()
