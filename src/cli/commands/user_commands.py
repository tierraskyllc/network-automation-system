"""
User Management CLI Commands
"""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from sqlalchemy import select
from typing import Optional

from ...core.database import AsyncSessionLocal
from ...core.models.user import User, Role
from ...core.security.auth import PasswordManager
from ...core.security.rbac import RoleBasedAccessControl

app = typer.Typer()
console = Console()


@app.command()
def create(
    username: str = typer.Option(..., "--username", "-u", help="Username"),
    email: str = typer.Option(..., "--email", "-e", help="Email address"),
    full_name: str = typer.Option("", "--name", "-n", help="Full name"),
    password: str = typer.Option("", "--password", "-p", help="Password (will prompt if not provided)"),
    role: str = typer.Option("network_viewer", "--role", "-r", help="Initial role"),
    superuser: bool = typer.Option(False, "--superuser", help="Create as superuser"),
):
    """Create a new user."""
    console.print(f"[bold blue]Creating user: {username}[/bold blue]")
    
    # Prompt for password if not provided
    if not password:
        password = Prompt.ask("Password", password=True)
        password_confirm = Prompt.ask("Confirm password", password=True)
        
        if password != password_confirm:
            console.print("[bold red]❌ Passwords do not match![/bold red]")
            raise typer.Exit(1)
    
    async def _create_user():
        try:
            async with AsyncSessionLocal() as db:
                # Check if username exists
                stmt = select(User).where(User.username == username)
                result = await db.execute(stmt)
                if result.scalar_one_or_none():
                    console.print(f"[bold red]❌ Username '{username}' already exists![/bold red]")
                    raise typer.Exit(1)
                
                # Check if email exists
                stmt = select(User).where(User.email == email)
                result = await db.execute(stmt)
                if result.scalar_one_or_none():
                    console.print(f"[bold red]❌ Email '{email}' already exists![/bold red]")
                    raise typer.Exit(1)
                
                # Validate password
                password_manager = PasswordManager()
                is_strong, errors = password_manager.validate_password_strength(password)
                if not is_strong:
                    console.print("[bold red]❌ Password does not meet requirements:[/bold red]")
                    for error in errors:
                        console.print(f"  • {error}")
                    raise typer.Exit(1)
                
                # Create user
                user = User(
                    username=username,
                    email=email,
                    full_name=full_name or None,
                    password_hash=password_manager.hash_password(password),
                    status="active",
                    is_verified=True,
                    is_superuser=superuser
                )
                
                db.add(user)
                await db.flush()
                
                # Assign role
                if not superuser and role:
                    rbac = RoleBasedAccessControl(db)
                    await rbac.assign_role_to_user(user, role)
                
                await db.commit()
                
                console.print(f"[bold green]✅ User '{username}' created successfully![/bold green]")
                if role and not superuser:
                    console.print(f"[green]   Role assigned: {role}[/green]")
                if superuser:
                    console.print(f"[yellow]   Superuser privileges granted[/yellow]")
                
        except Exception as e:
            console.print(f"[bold red]❌ Failed to create user: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_create_user())


@app.command()
def list(
    active_only: bool = typer.Option(True, "--active-only", help="Show only active users"),
    role_filter: str = typer.Option("", "--role", help="Filter by role"),
):
    """List all users."""
    console.print("[bold blue]Users[/bold blue]")
    
    async def _list_users():
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(User)
                
                if active_only:
                    stmt = stmt.where(User.status == "active")
                
                result = await db.execute(stmt)
                users = result.scalars().all()
                
                if not users:
                    console.print("[yellow]No users found.[/yellow]")
                    return
                
                # Create table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("ID", style="cyan")
                table.add_column("Username", style="green")
                table.add_column("Email")
                table.add_column("Full Name")
                table.add_column("Status")
                table.add_column("Superuser")
                table.add_column("MFA")
                table.add_column("Roles")
                
                for user in users:
                    # Filter by role if specified
                    if role_filter:
                        user_roles = [role.name for role in user.roles]
                        if role_filter not in user_roles:
                            continue
                    
                    roles_str = ", ".join([role.name for role in user.roles])
                    
                    table.add_row(
                        str(user.id),
                        user.username,
                        user.email,
                        user.full_name or "",
                        user.status,
                        "✅" if user.is_superuser else "❌",
                        "✅" if user.mfa_enabled else "❌",
                        roles_str
                    )
                
                console.print(table)
                
        except Exception as e:
            console.print(f"[bold red]❌ Failed to list users: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_list_users())


@app.command()
def show(
    username: str = typer.Argument(..., help="Username to show")
):
    """Show detailed user information."""
    console.print(f"[bold blue]User Details: {username}[/bold blue]")
    
    async def _show_user():
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(User).where(User.username == username)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    console.print(f"[bold red]❌ User '{username}' not found![/bold red]")
                    raise typer.Exit(1)
                
                # Create details table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("ID", str(user.id))
                table.add_row("Username", user.username)
                table.add_row("Email", user.email)
                table.add_row("Full Name", user.full_name or "")
                table.add_row("Status", user.status)
                table.add_row("Verified", "✅" if user.is_verified else "❌")
                table.add_row("Superuser", "✅" if user.is_superuser else "❌")
                table.add_row("MFA Enabled", "✅" if user.mfa_enabled else "❌")
                table.add_row("Failed Logins", str(user.failed_login_attempts))
                table.add_row("Last Login", str(user.last_login) if user.last_login else "Never")
                table.add_row("Created", str(user.created_at))
                
                console.print(table)
                
                # Show roles
                if user.roles:
                    console.print("\n[bold blue]Roles:[/bold blue]")
                    roles_table = Table(show_header=True, header_style="bold magenta")
                    roles_table.add_column("Role", style="cyan")
                    roles_table.add_column("Display Name", style="green")
                    roles_table.add_column("Description")
                    
                    for role in user.roles:
                        roles_table.add_row(
                            role.name,
                            role.display_name or "",
                            role.description or ""
                        )
                    
                    console.print(roles_table)
                
        except Exception as e:
            console.print(f"[bold red]❌ Failed to show user: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_show_user())


@app.command()
def update(
    username: str = typer.Argument(..., help="Username to update"),
    email: str = typer.Option("", "--email", help="New email address"),
    full_name: str = typer.Option("", "--name", help="New full name"),
    status: str = typer.Option("", "--status", help="New status (active, inactive, suspended)"),
):
    """Update user information."""
    console.print(f"[bold blue]Updating user: {username}[/bold blue]")
    
    async def _update_user():
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(User).where(User.username == username)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    console.print(f"[bold red]❌ User '{username}' not found![/bold red]")
                    raise typer.Exit(1)
                
                # Update fields
                updated_fields = []
                
                if email:
                    user.email = email
                    updated_fields.append("email")
                
                if full_name:
                    user.full_name = full_name
                    updated_fields.append("full_name")
                
                if status:
                    if status not in ["active", "inactive", "suspended"]:
                        console.print(f"[bold red]❌ Invalid status: {status}[/bold red]")
                        raise typer.Exit(1)
                    user.status = status
                    updated_fields.append("status")
                
                if not updated_fields:
                    console.print("[yellow]No fields to update.[/yellow]")
                    return
                
                await db.commit()
                
                console.print(f"[bold green]✅ User '{username}' updated successfully![/bold green]")
                console.print(f"[green]   Updated fields: {', '.join(updated_fields)}[/green]")
                
        except Exception as e:
            console.print(f"[bold red]❌ Failed to update user: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_update_user())


@app.command()
def delete(
    username: str = typer.Argument(..., help="Username to delete"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Delete a user."""
    if not confirm:
        console.print(f"[bold red]⚠️ This will permanently delete user '{username}'![/bold red]")
        
        if not typer.confirm("Are you sure you want to continue?"):
            console.print("Operation cancelled.")
            raise typer.Exit(0)
    
    console.print(f"[bold blue]Deleting user: {username}[/bold blue]")
    
    async def _delete_user():
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(User).where(User.username == username)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    console.print(f"[bold red]❌ User '{username}' not found![/bold red]")
                    raise typer.Exit(1)
                
                await db.delete(user)
                await db.commit()
                
                console.print(f"[bold green]✅ User '{username}' deleted successfully![/bold green]")
                
        except Exception as e:
            console.print(f"[bold red]❌ Failed to delete user: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_delete_user())


@app.command()
def reset_password(
    username: str = typer.Argument(..., help="Username"),
    password: str = typer.Option("", "--password", help="New password (will prompt if not provided)"),
):
    """Reset user password."""
    console.print(f"[bold blue]Resetting password for: {username}[/bold blue]")
    
    # Prompt for password if not provided
    if not password:
        password = Prompt.ask("New password", password=True)
        password_confirm = Prompt.ask("Confirm password", password=True)
        
        if password != password_confirm:
            console.print("[bold red]❌ Passwords do not match![/bold red]")
            raise typer.Exit(1)
    
    async def _reset_password():
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(User).where(User.username == username)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user:
                    console.print(f"[bold red]❌ User '{username}' not found![/bold red]")
                    raise typer.Exit(1)
                
                # Validate password
                password_manager = PasswordManager()
                is_strong, errors = password_manager.validate_password_strength(password)
                if not is_strong:
                    console.print("[bold red]❌ Password does not meet requirements:[/bold red]")
                    for error in errors:
                        console.print(f"  • {error}")
                    raise typer.Exit(1)
                
                # Update password
                user.password_hash = password_manager.hash_password(password)
                user.failed_login_attempts = 0
                user.locked_until = None
                
                await db.commit()
                
                console.print(f"[bold green]✅ Password reset for '{username}' successfully![/bold green]")
                
        except Exception as e:
            console.print(f"[bold red]❌ Failed to reset password: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_reset_password())
