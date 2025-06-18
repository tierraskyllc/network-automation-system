"""
Database Management CLI Commands
"""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from sqlalchemy import text
from alembic.config import Config
from alembic import command

from ...core.database import AsyncSessionLocal, init_db, close_db
from ...core.config import get_settings

app = typer.Typer()
console = Console()
settings = get_settings()


@app.command()
def init():
    """Initialize database tables."""
    console.print("[bold blue]Initializing database...[/bold blue]")
    
    async def _init():
        try:
            await init_db()
            console.print("[bold green]✅ Database initialized successfully![/bold green]")
        except Exception as e:
            console.print(f"[bold red]❌ Database initialization failed: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_init())


@app.command()
def migrate():
    """Run database migrations."""
    console.print("[bold blue]Running database migrations...[/bold blue]")
    
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        console.print("[bold green]✅ Migrations completed successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Migration failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def rollback(
    revision: str = typer.Option("", help="Revision to rollback to (default: previous)")
):
    """Rollback database migrations."""
    target = revision if revision else "-1"
    console.print(f"[bold yellow]Rolling back database to: {target}[/bold yellow]")
    
    try:
        alembic_cfg = Config("alembic.ini")
        command.downgrade(alembic_cfg, target)
        console.print("[bold green]✅ Rollback completed successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Rollback failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show database status and migration history."""
    console.print("[bold blue]Database Status[/bold blue]")
    
    async def _status():
        try:
            async with AsyncSessionLocal() as db:
                # Check database connection
                result = await db.execute(text("SELECT version()"))
                version = result.scalar()
                
                # Get table count
                result = await db.execute(text("""
                    SELECT count(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                table_count = result.scalar()
                
                # Create status table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Connection", "✅ Connected")
                table.add_row("Database", settings.DATABASE_NAME)
                table.add_row("Host", settings.DATABASE_HOST)
                table.add_row("Version", version.split()[1] if version else "Unknown")
                table.add_row("Tables", str(table_count))
                
                console.print(table)
                
        except Exception as e:
            console.print(f"[bold red]❌ Database connection failed: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_status())


@app.command()
def backup(
    output_file: str = typer.Option("", help="Output file path"),
    compress: bool = typer.Option(True, help="Compress backup file")
):
    """Create database backup."""
    import subprocess
    from datetime import datetime
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"backup_{settings.DATABASE_NAME}_{timestamp}.sql"
        if compress:
            output_file += ".gz"
    
    console.print(f"[bold blue]Creating database backup: {output_file}[/bold blue]")
    
    try:
        cmd = [
            "pg_dump",
            f"--host={settings.DATABASE_HOST}",
            f"--port={settings.DATABASE_PORT}",
            f"--username={settings.DATABASE_USER}",
            f"--dbname={settings.DATABASE_NAME}",
            "--verbose",
            "--clean",
            "--no-owner",
            "--no-privileges",
        ]
        
        if compress:
            cmd.extend(["--compress=9"])
        
        cmd.extend([f"--file={output_file}"])
        
        env = {"PGPASSWORD": settings.DATABASE_PASSWORD}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating backup...", total=None)
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                progress.update(task, description="✅ Backup completed")
                console.print(f"[bold green]✅ Backup created: {output_file}[/bold green]")
            else:
                progress.update(task, description="❌ Backup failed")
                console.print(f"[bold red]❌ Backup failed: {result.stderr}[/bold red]")
                raise typer.Exit(1)
                
    except FileNotFoundError:
        console.print("[bold red]❌ pg_dump not found. Please install PostgreSQL client tools.[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]❌ Backup failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def restore(
    backup_file: str = typer.Argument(..., help="Backup file to restore"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt")
):
    """Restore database from backup."""
    import subprocess
    from pathlib import Path
    
    backup_path = Path(backup_file)
    if not backup_path.exists():
        console.print(f"[bold red]❌ Backup file not found: {backup_file}[/bold red]")
        raise typer.Exit(1)
    
    if not confirm:
        console.print(f"[bold yellow]⚠️ This will restore database '{settings.DATABASE_NAME}' from: {backup_file}[/bold yellow]")
        console.print("[bold red]⚠️ This operation will overwrite existing data![/bold red]")
        
        if not typer.confirm("Are you sure you want to continue?"):
            console.print("Operation cancelled.")
            raise typer.Exit(0)
    
    console.print(f"[bold blue]Restoring database from: {backup_file}[/bold blue]")
    
    try:
        cmd = [
            "psql",
            f"--host={settings.DATABASE_HOST}",
            f"--port={settings.DATABASE_PORT}",
            f"--username={settings.DATABASE_USER}",
            f"--dbname={settings.DATABASE_NAME}",
            f"--file={backup_file}",
            "--verbose"
        ]
        
        env = {"PGPASSWORD": settings.DATABASE_PASSWORD}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Restoring backup...", total=None)
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                progress.update(task, description="✅ Restore completed")
                console.print(f"[bold green]✅ Database restored from: {backup_file}[/bold green]")
            else:
                progress.update(task, description="❌ Restore failed")
                console.print(f"[bold red]❌ Restore failed: {result.stderr}[/bold red]")
                raise typer.Exit(1)
                
    except FileNotFoundError:
        console.print("[bold red]❌ psql not found. Please install PostgreSQL client tools.[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]❌ Restore failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def reset(
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt")
):
    """Reset database (drop all tables and recreate)."""
    if not confirm:
        console.print("[bold red]⚠️ This will delete ALL data in the database![/bold red]")
        console.print(f"Database: {settings.DATABASE_NAME}")
        
        if not typer.confirm("Are you sure you want to continue?"):
            console.print("Operation cancelled.")
            raise typer.Exit(0)
    
    console.print("[bold blue]Resetting database...[/bold blue]")
    
    async def _reset():
        try:
            from ...core.database import Base, engine
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                
                # Drop all tables
                task1 = progress.add_task("Dropping tables...", total=None)
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
                progress.update(task1, description="✅ Tables dropped")
                
                # Recreate tables
                task2 = progress.add_task("Creating tables...", total=None)
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                progress.update(task2, description="✅ Tables created")
            
            console.print("[bold green]✅ Database reset completed![/bold green]")
            
        except Exception as e:
            console.print(f"[bold red]❌ Database reset failed: {e}[/bold red]")
            raise typer.Exit(1)
    
    asyncio.run(_reset())
