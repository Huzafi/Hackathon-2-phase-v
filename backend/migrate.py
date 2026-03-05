"""Database migration runner script.

This script runs SQL migrations in order and tracks which migrations have been applied.
Usage:
    python migrate.py          # Run all pending migrations
    python migrate.py status   # Show migration status
    python migrate.py rollback # Rollback last migration
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlmodel import SQLModel, Session, Field, select
from typing import Optional
from datetime import datetime as dt


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MigrationLog(SQLModel, table=True):
    """Track which migrations have been applied."""
    
    __tablename__ = "migration_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    migration_name: str = Field(unique=True, index=True)
    applied_at: dt = Field(default_factory=dt.utcnow)


def get_migration_files() -> list:
    """Get all migration SQL files in order."""
    migrations_dir = Path(__file__).parent
    migration_files = sorted(migrations_dir.glob("*.sql"))
    return [f.name for f in migration_files]


def get_applied_migrations(session: Session) -> set:
    """Get set of already applied migrations."""
    statement = select(MigrationLog.migration_name)
    return set(session.exec(statement).all())


def run_migration(session: Session, migration_name: str) -> bool:
    """Run a single migration file.
    
    Args:
        session: Database session
        migration_name: Name of migration file to run
    
    Returns:
        True if successful, False otherwise
    """
    migration_path = Path(__file__).parent / migration_name
    
    try:
        # Read migration SQL
        with open(migration_path, 'r') as f:
            sql_content = f.read()
        
        # Remove rollback comments for execution
        # (Everything after "-- ============================================" with "Migration Rollback")
        rollback_marker = "-- ============================================\n-- Migration Rollback"
        if rollback_marker in sql_content:
            sql_content = sql_content.split(rollback_marker)[0]
        
        # Execute migration
        from ..core.database import engine
        
        with engine.connect() as conn:
            # Split by semicolons and execute each statement
            statements = sql_content.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    conn.execute(statement)
            conn.commit()
        
        # Log migration
        migration_log = MigrationLog(migration_name=migration_name)
        session.add(migration_log)
        session.commit()
        
        logger.info(f"✓ Applied migration: {migration_name}")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Failed to apply migration {migration_name}: {e}")
        return False


def run_migrations():
    """Run all pending migrations."""
    from ..core.database import engine, create_db_and_tables
    
    logger.info("Starting database migrations...")
    
    # Create tables first
    create_db_and_tables()
    
    # Get migrations
    migration_files = get_migration_files()
    logger.info(f"Found {len(migration_files)} migration files")
    
    # Connect and run
    with Session(engine) as session:
        applied = get_applied_migrations(session)
        pending = [m for m in migration_files if m not in applied]
        
        if not pending:
            logger.info("✓ All migrations are up to date")
            return True
        
        logger.info(f"Running {len(pending)} pending migrations...")
        
        success_count = 0
        for migration_name in pending:
            if run_migration(session, migration_name):
                success_count += 1
            else:
                logger.error("Migration failed. Stopping.")
                return False
        
        logger.info(f"✓ Successfully applied {success_count}/{len(pending)} migrations")
        return True


def show_status():
    """Show migration status."""
    from ..core.database import engine
    
    migration_files = get_migration_files()
    
    with Session(engine) as session:
        applied = get_applied_migrations(session)
    
    print("\nMigration Status:")
    print("=" * 60)
    
    for migration in migration_files:
        status = "✓ Applied" if migration in applied else "○ Pending"
        print(f"{status:12} {migration}")
    
    print("=" * 60)
    print(f"Total: {len(migration_files)} | Applied: {len(applied)} | Pending: {len(migration_files) - len(applied)}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            show_status()
        elif command == "rollback":
            logger.error("Rollback not implemented yet. Please rollback manually using the SQL comments in migration files.")
            sys.exit(1)
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Usage: python migrate.py [status|rollback]")
            sys.exit(1)
    else:
        # Run migrations
        success = run_migrations()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
