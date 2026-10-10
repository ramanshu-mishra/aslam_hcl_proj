"""Database connection and initialization."""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from src.config import settings


class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        if db_path is None:
            db_path = settings.store_dir / "university.db"
        
        self.db_path = db_path
        self._ensure_initialized()
    
    def _ensure_initialized(self):
        """Create tables if they don't exist."""
        schema_path = Path(__file__).parent / "schema.sql"
        
        with open(schema_path) as f:
            schema_sql = f.read()
        
        conn = self.get_connection()
        try:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a new database connection."""
        conn = sqlite3.Connection(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# Global database instance
db = Database()


def get_db() -> Database:
    """Dependency injection for FastAPI."""
    return db
