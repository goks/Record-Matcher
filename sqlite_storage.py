"""
SQLite Storage Implementation for Record Matcher

This module provides SQLite-based storage for bank statement snapshots and cheque reports.
Replaces inefficient pickle storage with a proper relational database for:
- Better performance (indexed queries, partial loads)
- Data integrity (ACID transactions, schema validation)
- Maintainability (SQL queries, easy inspection)
- Security (no arbitrary code execution risk like pickle)
- Scalability (handles large datasets efficiently)

Database Schema:
    snapshots: Table for bank statement snapshots
        - id: Primary key
        - month, year, bank, company: Composite business key
        - data_json: Snapshot data as JSON
        - created_at, updated_at: Timestamps
        - checksum: Data integrity verification
        
    cheque_reports: Table for cheque reports
        - id: Primary key
        - year, company: Composite business key
        - data_json: Report data as JSON
        - created_at, updated_at: Timestamps
        - checksum: Data integrity verification

Usage:
    # Initialize repository
    from sqlite_storage import SQLiteSnapshotRepository
    repo = SQLiteSnapshotRepository()
    
    # Save snapshot
    success, error_code = repo.save(snapshot_obj)
    
    # Load snapshot
    snapshot = repo.load(month='January', year='2025', bank='HDFC', company='ABC')
    
    # Migrate from pickle
    from sqlite_storage import migrate_pickle_to_sqlite
    migrate_pickle_to_sqlite(pickle_path, sqlite_path)

Author: Code Change Documenter Agent
Date: December 9, 2025
"""

import sqlite3
import json
import os
import hashlib
import logging
import threading
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any, Union
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE SCHEMA AND MIGRATIONS
# ============================================================================

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bank statement snapshots
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    year TEXT NOT NULL,
    bank TEXT NOT NULL,
    company TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT NOT NULL,
    UNIQUE(month, year, bank, company)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_snapshots_composite 
    ON snapshots(company, year, month, bank);
CREATE INDEX IF NOT EXISTS idx_snapshots_year 
    ON snapshots(year);
CREATE INDEX IF NOT EXISTS idx_snapshots_company 
    ON snapshots(company);

-- Cheque reports
CREATE TABLE IF NOT EXISTS cheque_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year TEXT NOT NULL,
    company TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT NOT NULL,
    UNIQUE(year, company)
);

-- Indexes for cheque reports
CREATE INDEX IF NOT EXISTS idx_cheque_reports_composite 
    ON cheque_reports(company, year);

-- Migration history (for future schema changes)
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL,
    description TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(version)
);
"""


def _calculate_checksum(data: str) -> str:
    """Calculate SHA-256 checksum for data integrity verification.
    
    Args:
        data: String data to checksum
        
    Returns:
        Hexadecimal checksum string
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


# ============================================================================
# BASE SQLITE REPOSITORY
# ============================================================================

class SQLiteRepository:
    """Base class for SQLite repositories with common functionality.
    
    Provides:
    - Database initialization and schema management
    - Connection pooling (thread-local connections)
    - Transaction management
    - Error handling
    - Data integrity verification
    
    Attributes:
        db_path: Path to SQLite database file
        _local: Thread-local storage for connections
        _lock: Thread lock for initialization
    """
    
    def __init__(self, db_path: Optional[str] = None, app_name: str = "RecordMatcher"):
        """Initialize SQLite repository.
        
        Args:
            db_path: Custom database path (uses APPDATA if None)
            app_name: Application name for default path
        """
        if db_path is None:
            appdata = os.getenv('APPDATA', '.')
            db_dir = os.path.join(appdata, app_name)
            os.makedirs(db_dir, exist_ok=True)
            self.db_path = os.path.join(db_dir, "recordmatcher.db")
        else:
            self.db_path = db_path
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialized = False
        
        logger.info(f"SQLiteRepository initialized with database: {self.db_path}")
        
        # Initialize schema
        self._initialize_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection.
        
        Creates a new connection for each thread to ensure thread safety.
        Enables foreign keys and WAL mode for better concurrency.
        
        Returns:
            sqlite3.Connection for current thread
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            
            # Use memory for temp storage (faster)
            conn.execute("PRAGMA temp_store = MEMORY")
            
            # Configure row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            self._local.connection = conn
            logger.debug(f"Created new database connection for thread {threading.current_thread().name}")
        
        return self._local.connection
    
    @contextmanager
    def _transaction(self):
        """Context manager for database transactions.
        
        Automatically commits on success or rolls back on exception.
        
        Yields:
            sqlite3.Connection
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    def _initialize_schema(self):
        """Initialize database schema if needed.
        
        Creates all tables, indexes, and inserts initial schema version.
        Thread-safe initialization using lock.
        """
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:  # Double-check after acquiring lock
                return
            
            try:
                conn = self._get_connection()
                
                # Execute schema SQL
                conn.executescript(SCHEMA_SQL)
                
                # Check schema version
                cursor = conn.execute("SELECT MAX(version) as ver FROM schema_version")
                row = cursor.fetchone()
                current_version = row[0] if row[0] is not None else 0
                
                # Insert schema version if not exists
                if current_version == 0:
                    conn.execute(
                        "INSERT INTO schema_version (version) VALUES (?)",
                        (SCHEMA_VERSION,)
                    )
                    conn.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        (SCHEMA_VERSION, "Initial schema creation")
                    )
                    conn.commit()
                    logger.info(f"Database schema initialized (version {SCHEMA_VERSION})")
                elif current_version != SCHEMA_VERSION:
                    logger.warning(
                        f"Schema version mismatch: database={current_version}, "
                        f"expected={SCHEMA_VERSION}"
                    )
                
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize schema: {e}")
                raise
    
    def health_check(self) -> bool:
        """Check database health.
        
        Verifies:
        - Database file exists
        - Connection can be established
        - Tables exist
        - Simple query executes
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"Database file not found: {self.db_path}")
                return False
            
            conn = self._get_connection()
            
            # Check if tables exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('snapshots', 'cheque_reports')"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            if len(tables) != 2:
                logger.warning(f"Missing tables. Found: {tables}")
                return False
            
            # Simple query test
            conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()
            
            logger.debug("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.
        
        Returns:
            Dictionary with:
            - snapshot_count: Number of snapshots
            - cheque_report_count: Number of cheque reports
            - db_size_bytes: Database file size
            - created_snapshots_today: Snapshots created today
        """
        try:
            conn = self._get_connection()
            
            # Count snapshots
            cursor = conn.execute("SELECT COUNT(*) FROM snapshots")
            snapshot_count = cursor.fetchone()[0]
            
            # Count cheque reports
            cursor = conn.execute("SELECT COUNT(*) FROM cheque_reports")
            cheque_count = cursor.fetchone()[0]
            
            # Database size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            # Today's snapshots
            cursor = conn.execute(
                "SELECT COUNT(*) FROM snapshots WHERE DATE(created_at) = DATE('now')"
            )
            today_count = cursor.fetchone()[0]
            
            return {
                'snapshot_count': snapshot_count,
                'cheque_report_count': cheque_count,
                'db_size_bytes': db_size,
                'db_size_mb': round(db_size / (1024 * 1024), 2),
                'created_snapshots_today': today_count
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def close(self):
        """Close database connection for current thread."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("Closed database connection")


# ============================================================================
# SNAPSHOT REPOSITORY
# ============================================================================

class SQLiteSnapshotRepository(SQLiteRepository):
    """SQLite implementation of snapshot repository.
    
    Stores bank statement snapshots in SQLite database with:
    - Indexed queries for fast retrieval
    - JSON storage for complex data structures
    - Checksum verification for data integrity
    - ACID transactions for consistency
    
    Replaces PickleSnapshotRepository with better performance and safety.
    """
    
    def save(self, snapshot: Any) -> Tuple[bool, int]:
        """Save a table snapshot to database.
        
        Args:
            snapshot: Snapshot object with get_month(), get_year(), 
                     get_bank(), get_company(), and to_dict() methods
        
        Returns:
            Tuple of (success: bool, error_code: int)
            Error codes:
                0: Success
                -1: Serialization error
                -2: Database error
                -3: Invalid snapshot data
        """
        try:
            # Extract snapshot metadata
            month = snapshot.get_month()
            year = snapshot.get_year()
            bank = snapshot.get_bank()
            company = snapshot.get_company()
            
            # Validate required fields
            if not all([month, year, bank, company]):
                logger.error("Missing required snapshot fields")
                return False, -3
            
            # Serialize snapshot to JSON
            try:
                if hasattr(snapshot, 'to_dict'):
                    snapshot_dict = snapshot.to_dict()
                else:
                    # Fallback: convert using __dict__ (may not work for all objects)
                    snapshot_dict = vars(snapshot)
                
                data_json = json.dumps(snapshot_dict, default=str, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize snapshot: {e}")
                return False, -1
            
            # Calculate checksum
            checksum = _calculate_checksum(data_json)
            
            # Save to database with transaction
            with self._transaction() as conn:
                conn.execute("""
                    INSERT INTO snapshots (month, year, bank, company, data_json, checksum, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(month, year, bank, company) DO UPDATE SET
                        data_json = excluded.data_json,
                        checksum = excluded.checksum,
                        updated_at = CURRENT_TIMESTAMP
                """, (month, year, bank, company, data_json, checksum))
            
            logger.info(f"Saved snapshot: {company}/{year}/{month}/{bank}")
            return True, 0
            
        except sqlite3.Error as e:
            logger.error(f"Database error saving snapshot: {e}")
            return False, -2
        except Exception as e:
            logger.error(f"Unexpected error saving snapshot: {e}")
            return False, -2
    
    def load(self, month: str, year: str, bank: str, company: str) -> Optional[Dict[str, Any]]:
        """Load a snapshot from database.
        
        Args:
            month: Month name
            year: Year string
            bank: Bank name
            company: Company name
        
        Returns:
            Dictionary representation of snapshot, or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT data_json, checksum FROM snapshots
                WHERE month = ? AND year = ? AND bank = ? AND company = ?
            """, (month, year, bank, company))
            
            row = cursor.fetchone()
            if row is None:
                logger.debug(f"Snapshot not found: {company}/{year}/{month}/{bank}")
                return None
            
            data_json = row[0]
            stored_checksum = row[1]
            
            # Verify checksum
            calculated_checksum = _calculate_checksum(data_json)
            if calculated_checksum != stored_checksum:
                logger.error(
                    f"Checksum mismatch for snapshot {company}/{year}/{month}/{bank}. "
                    f"Data may be corrupted!"
                )
                return None
            
            # Deserialize JSON
            snapshot_dict = json.loads(data_json)
            logger.debug(f"Loaded snapshot: {company}/{year}/{month}/{bank}")
            return snapshot_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize snapshot: {e}")
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error loading snapshot: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading snapshot: {e}")
            return None
    
    def delete(self, month: str, year: str, bank: str, company: str) -> bool:
        """Delete a snapshot from database.
        
        Args:
            month: Month name
            year: Year string
            bank: Bank name
            company: Company name
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            with self._transaction() as conn:
                cursor = conn.execute("""
                    DELETE FROM snapshots
                    WHERE month = ? AND year = ? AND bank = ? AND company = ?
                """, (month, year, bank, company))
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted snapshot: {company}/{year}/{month}/{bank}")
                else:
                    logger.warning(f"Snapshot not found for deletion: {company}/{year}/{month}/{bank}")
                
                return deleted
        except sqlite3.Error as e:
            logger.error(f"Database error deleting snapshot: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting snapshot: {e}")
            return False
    
    def exists(self, month: str, year: str, bank: str, company: str) -> bool:
        """Check if a snapshot exists in database.
        
        Args:
            month: Month name
            year: Year string
            bank: Bank name
            company: Company name
        
        Returns:
            True if exists, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT 1 FROM snapshots
                WHERE month = ? AND year = ? AND bank = ? AND company = ?
                LIMIT 1
            """, (month, year, bank, company))
            
            exists = cursor.fetchone() is not None
            return exists
        except sqlite3.Error as e:
            logger.error(f"Database error checking existence: {e}")
            return False
    
    def list_all(self) -> List[Tuple[str, str, str, str]]:
        """List all snapshots in database.
        
        Returns:
            List of tuples: (month, year, bank, company)
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT month, year, bank, company FROM snapshots
                ORDER BY company, year DESC, month, bank
            """)
            
            snapshots = [(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()]
            logger.debug(f"Listed {len(snapshots)} snapshots")
            return snapshots
        except sqlite3.Error as e:
            logger.error(f"Database error listing snapshots: {e}")
            return []
    
    def list_by_filters(
        self, 
        company: Optional[str] = None,
        year: Optional[str] = None,
        bank: Optional[str] = None
    ) -> List[Tuple[str, str, str, str]]:
        """List snapshots with optional filters.
        
        Args:
            company: Filter by company (None = all)
            year: Filter by year (None = all)
            bank: Filter by bank (None = all)
        
        Returns:
            List of tuples: (month, year, bank, company)
        """
        try:
            conn = self._get_connection()
            
            # Build dynamic query
            query = "SELECT month, year, bank, company FROM snapshots WHERE 1=1"
            params = []
            
            if company is not None:
                query += " AND company = ?"
                params.append(company)
            if year is not None:
                query += " AND year = ?"
                params.append(year)
            if bank is not None:
                query += " AND bank = ?"
                params.append(bank)
            
            query += " ORDER BY company, year DESC, month, bank"
            
            cursor = conn.execute(query, params)
            snapshots = [(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()]
            logger.debug(f"Filtered query returned {len(snapshots)} snapshots")
            return snapshots
        except sqlite3.Error as e:
            logger.error(f"Database error in filtered list: {e}")
            return []


# ============================================================================
# CHEQUE REPORT REPOSITORY
# ============================================================================

class SQLiteChequeReportRepository(SQLiteRepository):
    """SQLite implementation of cheque report repository.
    
    Stores cheque reports in SQLite database with similar benefits as
    snapshot repository. Replaces PickleChequeReportRepository.
    """
    
    def save(self, year: str, company: str, report_data: Any) -> Tuple[bool, int]:
        """Save a cheque report to database.
        
        Args:
            year: Year string
            company: Company name
            report_data: Report data (dict or object with to_dict())
        
        Returns:
            Tuple of (success: bool, error_code: int)
        """
        try:
            # Validate required fields
            if not all([year, company]):
                logger.error("Missing required cheque report fields")
                return False, -3
            
            # Serialize to JSON
            try:
                if isinstance(report_data, dict):
                    report_dict = report_data
                elif hasattr(report_data, 'to_dict'):
                    report_dict = report_data.to_dict()
                else:
                    report_dict = vars(report_data)
                
                data_json = json.dumps(report_dict, default=str, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize cheque report: {e}")
                return False, -1
            
            # Calculate checksum
            checksum = _calculate_checksum(data_json)
            
            # Save to database
            with self._transaction() as conn:
                conn.execute("""
                    INSERT INTO cheque_reports (year, company, data_json, checksum, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(year, company) DO UPDATE SET
                        data_json = excluded.data_json,
                        checksum = excluded.checksum,
                        updated_at = CURRENT_TIMESTAMP
                """, (year, company, data_json, checksum))
            
            logger.info(f"Saved cheque report: {company}/{year}")
            return True, 0
            
        except sqlite3.Error as e:
            logger.error(f"Database error saving cheque report: {e}")
            return False, -2
        except Exception as e:
            logger.error(f"Unexpected error saving cheque report: {e}")
            return False, -2
    
    def load(self, year: str, company: str) -> Optional[Dict[str, Any]]:
        """Load a cheque report from database.
        
        Args:
            year: Year string
            company: Company name
        
        Returns:
            Dictionary representation of report, or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT data_json, checksum FROM cheque_reports
                WHERE year = ? AND company = ?
            """, (year, company))
            
            row = cursor.fetchone()
            if row is None:
                logger.debug(f"Cheque report not found: {company}/{year}")
                return None
            
            data_json = row[0]
            stored_checksum = row[1]
            
            # Verify checksum
            calculated_checksum = _calculate_checksum(data_json)
            if calculated_checksum != stored_checksum:
                logger.error(
                    f"Checksum mismatch for cheque report {company}/{year}. "
                    f"Data may be corrupted!"
                )
                return None
            
            # Deserialize JSON
            report_dict = json.loads(data_json)
            logger.debug(f"Loaded cheque report: {company}/{year}")
            return report_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize cheque report: {e}")
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error loading cheque report: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading cheque report: {e}")
            return None
    
    def delete(self, year: str, company: str) -> bool:
        """Delete a cheque report from database.
        
        Args:
            year: Year string
            company: Company name
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            with self._transaction() as conn:
                cursor = conn.execute("""
                    DELETE FROM cheque_reports
                    WHERE year = ? AND company = ?
                """, (year, company))
                
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted cheque report: {company}/{year}")
                else:
                    logger.warning(f"Cheque report not found for deletion: {company}/{year}")
                
                return deleted
        except sqlite3.Error as e:
            logger.error(f"Database error deleting cheque report: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting cheque report: {e}")
            return False
    
    def exists(self, year: str, company: str) -> bool:
        """Check if a cheque report exists.
        
        Args:
            year: Year string
            company: Company name
        
        Returns:
            True if exists, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT 1 FROM cheque_reports
                WHERE year = ? AND company = ?
                LIMIT 1
            """, (year, company))
            
            exists = cursor.fetchone() is not None
            return exists
        except sqlite3.Error as e:
            logger.error(f"Database error checking existence: {e}")
            return False
    
    def list_all(self) -> List[Tuple[str, str]]:
        """List all cheque reports.
        
        Returns:
            List of tuples: (year, company)
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT year, company FROM cheque_reports
                ORDER BY company, year DESC
            """)
            
            reports = [(row[0], row[1]) for row in cursor.fetchall()]
            logger.debug(f"Listed {len(reports)} cheque reports")
            return reports
        except sqlite3.Error as e:
            logger.error(f"Database error listing cheque reports: {e}")
            return []


# ============================================================================
# MIGRATION UTILITIES
# ============================================================================

def migrate_pickle_to_sqlite(
    pickle_snapshot_path: Optional[str] = None,
    pickle_cheque_path: Optional[str] = None,
    sqlite_db_path: Optional[str] = None,
    app_name: str = "RecordMatcher",
    dry_run: bool = False
) -> Dict[str, Any]:
    """Migrate data from pickle files to SQLite database.
    
    This function reads existing pickle files and migrates all data to
    SQLite database. Useful for one-time migration from old storage format.
    
    Args:
        pickle_snapshot_path: Path to pickle snapshot file (auto-detect if None)
        pickle_cheque_path: Path to pickle cheque report file (auto-detect if None)
        sqlite_db_path: Path to SQLite database (auto-create if None)
        app_name: Application name for default paths
        dry_run: If True, report what would be migrated without actually migrating
    
    Returns:
        Dictionary with migration results:
            - snapshots_migrated: Number of snapshots migrated
            - cheque_reports_migrated: Number of cheque reports migrated
            - errors: List of error messages
            - success: Overall success status
    """
    import pickle
    
    results = {
        'snapshots_migrated': 0,
        'cheque_reports_migrated': 0,
        'errors': [],
        'success': False,
        'dry_run': dry_run
    }
    
    logger.info("=" * 60)
    logger.info("PICKLE TO SQLITE MIGRATION")
    logger.info("=" * 60)
    
    # Auto-detect paths if not provided
    if pickle_snapshot_path is None:
        appdata = os.getenv('APPDATA', '.')
        pickle_snapshot_path = os.path.join(appdata, app_name, "tableSnapshotCollection.filv2")
    
    if pickle_cheque_path is None:
        appdata = os.getenv('APPDATA', '.')
        pickle_cheque_path = os.path.join(appdata, app_name, "ChequeReportCollection.fil")
    
    # Initialize SQLite repositories
    snapshot_repo = SQLiteSnapshotRepository(db_path=sqlite_db_path, app_name=app_name)
    cheque_repo = SQLiteChequeReportRepository(db_path=sqlite_db_path, app_name=app_name)
    
    # Migrate snapshots
    logger.info(f"\nMigrating snapshots from: {pickle_snapshot_path}")
    if os.path.exists(pickle_snapshot_path):
        try:
            with open(pickle_snapshot_path, 'rb') as f:
                snapshot_data = pickle.load(f)
            
            logger.info(f"Found {len(snapshot_data)} snapshots in pickle file")
            
            for key, snapshot in snapshot_data.items():
                if snapshot is None:
                    continue
                
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would migrate snapshot: {key}")
                        results['snapshots_migrated'] += 1
                    else:
                        success, error_code = snapshot_repo.save(snapshot)
                        if success:
                            results['snapshots_migrated'] += 1
                            logger.info(f"✓ Migrated snapshot: {key}")
                        else:
                            error_msg = f"Failed to migrate snapshot {key}: error code {error_code}"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                except Exception as e:
                    error_msg = f"Error migrating snapshot {key}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
        except FileNotFoundError:
            msg = f"Snapshot pickle file not found: {pickle_snapshot_path}"
            logger.warning(msg)
            results['errors'].append(msg)
        except Exception as e:
            msg = f"Error reading snapshot pickle file: {e}"
            logger.error(msg)
            results['errors'].append(msg)
    else:
        msg = f"Snapshot pickle file does not exist: {pickle_snapshot_path}"
        logger.warning(msg)
        results['errors'].append(msg)
    
    # Migrate cheque reports
    logger.info(f"\nMigrating cheque reports from: {pickle_cheque_path}")
    if os.path.exists(pickle_cheque_path):
        try:
            with open(pickle_cheque_path, 'rb') as f:
                cheque_data = pickle.load(f)
            
            logger.info(f"Found {len(cheque_data)} cheque reports in pickle file")
            
            for key, report in cheque_data.items():
                if report is None:
                    continue
                
                try:
                    # Parse key: company_year
                    parts = key.split('_')
                    if len(parts) >= 2:
                        company = parts[0]
                        year = parts[1]
                        
                        if dry_run:
                            logger.info(f"[DRY RUN] Would migrate cheque report: {key}")
                            results['cheque_reports_migrated'] += 1
                        else:
                            success, error_code = cheque_repo.save(year, company, report)
                            if success:
                                results['cheque_reports_migrated'] += 1
                                logger.info(f"✓ Migrated cheque report: {key}")
                            else:
                                error_msg = f"Failed to migrate cheque report {key}: error code {error_code}"
                                logger.error(error_msg)
                                results['errors'].append(error_msg)
                except Exception as e:
                    error_msg = f"Error migrating cheque report {key}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
        except FileNotFoundError:
            msg = f"Cheque report pickle file not found: {pickle_cheque_path}"
            logger.warning(msg)
            results['errors'].append(msg)
        except Exception as e:
            msg = f"Error reading cheque report pickle file: {e}"
            logger.error(msg)
            results['errors'].append(msg)
    else:
        msg = f"Cheque report pickle file does not exist: {pickle_cheque_path}"
        logger.warning(msg)
        results['errors'].append(msg)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Snapshots migrated: {results['snapshots_migrated']}")
    logger.info(f"Cheque reports migrated: {results['cheque_reports_migrated']}")
    logger.info(f"Errors: {len(results['errors'])}")
    
    if results['errors']:
        logger.warning("\nErrors encountered:")
        for error in results['errors']:
            logger.warning(f"  - {error}")
    
    # Consider migration successful if at least one item migrated and no critical errors
    results['success'] = (
        (results['snapshots_migrated'] > 0 or results['cheque_reports_migrated'] > 0) and
        len(results['errors']) == 0
    )
    
    if dry_run:
        logger.info("\n[DRY RUN COMPLETE] No actual changes made to database")
    elif results['success']:
        logger.info("\n✓ MIGRATION COMPLETED SUCCESSFULLY")
    else:
        logger.warning("\n⚠ MIGRATION COMPLETED WITH ERRORS")
    
    logger.info("=" * 60)
    
    return results


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("SQLite Storage Module - Example Usage")
    print("=" * 60)
    
    # Test snapshot repository
    print("\n1. Testing SQLiteSnapshotRepository...")
    snapshot_repo = SQLiteSnapshotRepository(db_path="./test_recordmatcher.db")
    
    # Health check
    if snapshot_repo.health_check():
        print("✓ Snapshot repository health check passed")
    else:
        print("✗ Snapshot repository health check failed")
    
    # Statistics
    stats = snapshot_repo.get_statistics()
    print(f"✓ Database statistics: {stats}")
    
    # List all snapshots
    all_snapshots = snapshot_repo.list_all()
    print(f"✓ Found {len(all_snapshots)} existing snapshots")
    
    print("\n2. Testing SQLiteChequeReportRepository...")
    cheque_repo = SQLiteChequeReportRepository(db_path="./test_recordmatcher.db")
    
    # Health check
    if cheque_repo.health_check():
        print("✓ Cheque report repository health check passed")
    else:
        print("✗ Cheque report repository health check failed")
    
    # List all reports
    all_reports = cheque_repo.list_all()
    print(f"✓ Found {len(all_reports)} existing cheque reports")
    
    print("\n3. Migration Test (Dry Run)...")
    print("NOTE: Run migrate_pickle_to_sqlite() to migrate from existing pickle files")
    print("Example:")
    print("  results = migrate_pickle_to_sqlite(dry_run=True)")
    print("  # Review results, then run with dry_run=False to actually migrate")
    
    print("\n" + "=" * 60)
    print("SQLite Storage Module - Ready to Use")
    print("=" * 60)
