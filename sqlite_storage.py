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
import locale
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any, Union
from contextlib import contextmanager
from pathlib import Path

import dateutil.parser

# Try to import msgpack for faster serialization (fallback to JSON if not available)
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "msgpack not installed - using JSON for serialization. "
        "Install msgpack for 2-10x faster load times: pip install msgpack"
    )

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE SCHEMA AND MIGRATIONS
# ============================================================================

SCHEMA_VERSION = 2

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bank statement snapshots (OPTIMIZED SCHEMA v2)
-- Pre-calculated columns avoid recalculating on every load
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    year TEXT NOT NULL,
    bank TEXT NOT NULL,
    company TEXT NOT NULL,
    data_json TEXT,                           -- Legacy JSON storage (for backward compatibility)
    data_msgpack BLOB,                        -- MessagePack serialized data (faster)
    credit_bal TEXT,                          -- Pre-calculated credit balance
    debit_bal TEXT,                           -- Pre-calculated debit balance
    start_date TEXT,                          -- Pre-calculated start date (YYYY/MM/DD)
    end_date TEXT,                            -- Pre-calculated end date (YYYY/MM/DD)
    display_data_msgpack BLOB,                -- Pre-formatted display data (avoid format_table_data on load)
    row_count INTEGER DEFAULT 0,              -- Number of rows for quick access
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

# Schema migration SQL for upgrading from v1 to v2
MIGRATION_V1_TO_V2 = """
-- Add new columns for pre-computed data (SQLite doesn't support IF NOT EXISTS for columns)
-- These will fail silently if columns already exist
ALTER TABLE snapshots ADD COLUMN data_msgpack BLOB;
ALTER TABLE snapshots ADD COLUMN credit_bal TEXT;
ALTER TABLE snapshots ADD COLUMN debit_bal TEXT;
ALTER TABLE snapshots ADD COLUMN start_date TEXT;
ALTER TABLE snapshots ADD COLUMN end_date TEXT;
ALTER TABLE snapshots ADD COLUMN display_data_msgpack BLOB;
ALTER TABLE snapshots ADD COLUMN row_count INTEGER DEFAULT 0;
"""


def _calculate_checksum(data: Union[str, bytes]) -> str:
    """Calculate SHA-256 checksum for data integrity verification.
    
    Args:
        data: String or bytes data to checksum
        
    Returns:
        Hexadecimal checksum string
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def _serialize_data(data: Dict, use_msgpack: bool = True) -> Tuple[bytes, str]:
    """Serialize data using MessagePack (preferred) or JSON (fallback).
    
    MessagePack is 2-10x faster than JSON for serialization/deserialization
    and produces smaller output.
    
    Args:
        data: Dictionary to serialize
        use_msgpack: Whether to prefer MessagePack (falls back to JSON if not available)
        
    Returns:
        Tuple of (serialized_data: bytes, format: 'msgpack' or 'json')
    """
    if use_msgpack and MSGPACK_AVAILABLE:
        serialized = msgpack.packb(data, use_bin_type=True)
        return serialized, 'msgpack'
    else:
        serialized = json.dumps(data, default=str, ensure_ascii=False).encode('utf-8')
        return serialized, 'json'


def _deserialize_data(data: bytes, format_hint: str = 'auto') -> Dict:
    """Deserialize data from MessagePack or JSON format.
    
    Args:
        data: Serialized bytes data
        format_hint: 'msgpack', 'json', or 'auto' (auto-detect)
        
    Returns:
        Deserialized dictionary
    """
    if data is None:
        return {}
    
    # If it's a string, convert to bytes
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Auto-detect format
    if format_hint == 'auto':
        # JSON starts with { or [, MessagePack has different magic bytes
        if data and (data[0:1] == b'{' or data[0:1] == b'['):
            format_hint = 'json'
        else:
            format_hint = 'msgpack'
    
    if format_hint == 'msgpack' and MSGPACK_AVAILABLE:
        try:
            return msgpack.unpackb(data, raw=False)
        except Exception:
            # Fall back to JSON if msgpack fails
            pass
    
    # JSON fallback
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return json.loads(data)


def _calculate_balances_and_dates(master_table: List[Dict]) -> Tuple[str, str, str, str]:
    """Pre-calculate credit/debit balances and date range for storage.
    
    This is calculated once during save() to avoid recalculating on every load().
    Mirrors the logic in core.py DataProcessor.calculate_balances_and_dates()
    
    Args:
        master_table: Table data from snapshot
        
    Returns:
        Tuple of (credit_bal_str, debit_bal_str, start_date_str, end_date_str)
    """
    credit_bal = 0.0
    debit_bal = 0.0
    start_date = None
    end_date = None
    
    for each in master_table:
        # Parse date
        try:
            bank_date = dateutil.parser.parse(each.get('Bank Date', ''), dayfirst=True)
        except Exception:
            # Skip entries with invalid dates (like 'double' meta entries)
            if each.get('meta') == 'double':
                continue
            # If date is empty or invalid, skip date calculations
            bank_date = None
        
        # Update date range
        if bank_date is not None:
            if start_date is None or start_date > bank_date:
                start_date = bank_date
            if end_date is None or end_date < bank_date:
                end_date = bank_date
        
        # Sum balances
        credit_val = each.get('Credit', '')
        if credit_val != '' and credit_val is not None:
            try:
                credit_bal += float(credit_val)
            except (ValueError, TypeError):
                pass
        
        debit_val = each.get('Debit', '')
        if debit_val != '' and debit_val is not None:
            try:
                debit_bal += float(debit_val)
            except (ValueError, TypeError):
                pass
    
    # Format results
    credit_bal_str = locale.format_string("%.2f", credit_bal, grouping=True)
    debit_bal_str = locale.format_string("%.2f", debit_bal, grouping=True)
    
    if start_date:
        start_date_str = start_date.strftime("%Y/%m/%d")
    else:
        start_date_str = ""
    
    if end_date:
        end_date_str = end_date.strftime("%Y/%m/%d")
    else:
        end_date_str = ""
    
    return credit_bal_str, debit_bal_str, start_date_str, end_date_str


def _format_table_data_for_cache(table_data: List[Dict]) -> List[Dict]:
    """Format table data for display cache.
    
    Pre-formats number fields with locale formatting so we don't have to
    do it on every load.
    
    Args:
        table_data: Raw table data
        
    Returns:
        Formatted table data with locale-formatted numbers
    """
    format_fields = ['Credit', 'Debit', 'Closing Balance']
    result = []
    
    for row in table_data:
        # Shallow copy the row
        new_row = dict(row)
        
        # Format number fields
        for field in format_fields:
            value = new_row.get(field, '')
            if value != '' and value is not None:
                try:
                    numeric_val = float(value)
                    new_row[field] = locale.format_string("%.2f", numeric_val, grouping=True)
                except (ValueError, TypeError):
                    pass
        
        result.append(new_row)
    
    return result


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
    
    def __init__(self, db_path: Optional[str] = None, app_name: str = "Record Matcher"):
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
        Handles migration from older schema versions.
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
                
                # Insert schema version if not exists (fresh database)
                if current_version == 0:
                    conn.execute(
                        "INSERT INTO schema_version (version) VALUES (?)",
                        (SCHEMA_VERSION,)
                    )
                    conn.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        (SCHEMA_VERSION, "Schema v2 with pre-computed columns and MessagePack")
                    )
                    conn.commit()
                    logger.info(f"Database schema initialized (version {SCHEMA_VERSION})")
                elif current_version < SCHEMA_VERSION:
                    # Perform schema migration
                    self._migrate_schema(conn, current_version)
                elif current_version > SCHEMA_VERSION:
                    logger.warning(
                        f"Database schema version ({current_version}) is newer than "
                        f"application version ({SCHEMA_VERSION}). Some features may not work."
                    )
                
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize schema: {e}")
                raise
    
    def _migrate_schema(self, conn: sqlite3.Connection, from_version: int):
        """Migrate database schema from older version.
        
        Args:
            conn: Database connection
            from_version: Current database schema version
        """
        logger.info(f"Migrating database schema from v{from_version} to v{SCHEMA_VERSION}")
        
        if from_version < 2:
            # Migrate from v1 to v2: Add pre-computed columns
            logger.info("Applying migration v1 -> v2: Adding pre-computed columns")
            
            # Add new columns (ignore errors if they already exist)
            new_columns = [
                ("data_msgpack", "BLOB"),
                ("credit_bal", "TEXT"),
                ("debit_bal", "TEXT"),
                ("start_date", "TEXT"),
                ("end_date", "TEXT"),
                ("display_data_msgpack", "BLOB"),
                ("row_count", "INTEGER DEFAULT 0"),
            ]
            
            for col_name, col_type in new_columns:
                try:
                    conn.execute(f"ALTER TABLE snapshots ADD COLUMN {col_name} {col_type}")
                    logger.debug(f"Added column: {col_name} {col_type}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        logger.debug(f"Column {col_name} already exists")
                    else:
                        raise
            
            # Update schema version
            conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (2,)
            )
            conn.execute(
                "INSERT INTO migrations (version, description) VALUES (?, ?)",
                (2, "Added pre-computed columns (credit_bal, debit_bal, dates) and MessagePack")
            )
            conn.commit()
            logger.info("Migration to v2 complete")
            
            # Flag that existing data needs to be migrated
            logger.info(
                "NOTE: Existing snapshots still use JSON format. "
                "Run optimize_existing_snapshots() to convert to optimized format."
            )
    
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
    - MessagePack serialization (2-10x faster than JSON)
    - Pre-calculated balances and dates (avoids recalculating on every load)
    - Pre-formatted display data (avoids formatting on every load)
    - Checksum verification for data integrity
    - ACID transactions for consistency
    
    OPTIMIZED STORAGE FORMAT (v2):
    - data_msgpack: MessagePack serialized snapshot data
    - credit_bal, debit_bal: Pre-calculated balance strings
    - start_date, end_date: Pre-calculated date range
    - display_data_msgpack: Pre-formatted table data for display
    - row_count: Number of rows for quick access
    
    Falls back to JSON storage for backward compatibility.
    """
    
    def save(self, snapshot: Any) -> Tuple[bool, int]:
        """Save a table snapshot to database with pre-computed values.
        
        OPTIMIZATION: Calculates and stores balances, dates, and display data
        during save() so load() doesn't have to recalculate them.
        
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
            # Extract snapshot metadata and normalize to lowercase
            month = snapshot.get_month().lower() if snapshot.get_month() else ''
            year = snapshot.get_year()
            bank = snapshot.get_bank().lower() if snapshot.get_bank() else ''
            company = snapshot.get_company().lower() if snapshot.get_company() else ''
            
            # Validate required fields
            if not all([month, year, bank, company]):
                logger.error("Missing required snapshot fields")
                return False, -3
            
            # Convert snapshot to dictionary
            try:
                if hasattr(snapshot, 'to_dict'):
                    snapshot_dict = snapshot.to_dict()
                else:
                    snapshot_dict = vars(snapshot)
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to convert snapshot to dict: {e}")
                return False, -1
            
            # Get master_table for pre-calculations
            master_table = snapshot_dict.get('master_table', [])
            row_count = len(master_table)
            
            # Pre-calculate balances and dates (OPTIMIZATION)
            try:
                credit_bal, debit_bal, start_date, end_date = _calculate_balances_and_dates(master_table)
            except Exception as e:
                logger.warning(f"Failed to pre-calculate balances/dates: {e}. Using empty values.")
                credit_bal, debit_bal, start_date, end_date = '', '', '', ''
            
            # Pre-format display data (OPTIMIZATION)
            try:
                display_data = _format_table_data_for_cache(master_table)
            except Exception as e:
                logger.warning(f"Failed to pre-format display data: {e}. Will be calculated on load.")
                display_data = None
            
            # Serialize data - always store JSON for backward compatibility,
            # and also store MessagePack if available for faster loading
            try:
                # Always create JSON (for backward compatibility with NOT NULL constraint)
                data_json = json.dumps(snapshot_dict, default=str, ensure_ascii=False)
                
                # Also create MessagePack if available (faster loading)
                if MSGPACK_AVAILABLE:
                    data_msgpack = msgpack.packb(snapshot_dict, use_bin_type=True)
                    # Use msgpack for checksum since it's the primary format for loading
                    data_serialized = data_msgpack
                else:
                    data_msgpack = None
                    data_serialized = data_json.encode('utf-8')
                
                # Serialize display data with MessagePack if available
                if display_data and MSGPACK_AVAILABLE:
                    display_data_msgpack = msgpack.packb(display_data, use_bin_type=True)
                else:
                    display_data_msgpack = None
                    
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize snapshot: {e}")
                return False, -1
            
            # Calculate checksum (use primary serialized data)
            checksum = _calculate_checksum(data_serialized)
            
            # Save to database with transaction
            with self._transaction() as conn:
                conn.execute("""
                    INSERT INTO snapshots (
                        month, year, bank, company, 
                        data_json, data_msgpack, 
                        credit_bal, debit_bal, start_date, end_date,
                        display_data_msgpack, row_count,
                        checksum, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(month, year, bank, company) DO UPDATE SET
                        data_json = excluded.data_json,
                        data_msgpack = excluded.data_msgpack,
                        credit_bal = excluded.credit_bal,
                        debit_bal = excluded.debit_bal,
                        start_date = excluded.start_date,
                        end_date = excluded.end_date,
                        display_data_msgpack = excluded.display_data_msgpack,
                        row_count = excluded.row_count,
                        checksum = excluded.checksum,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    month, year, bank, company,
                    data_json, data_msgpack,
                    credit_bal, debit_bal, start_date, end_date,
                    display_data_msgpack, row_count,
                    checksum
                ))
            
            format_info = f"msgpack" if data_msgpack else "json"
            logger.info(f"Saved snapshot: {company}/{year}/{month}/{bank} ({row_count} rows, {format_info})")
            return True, 0
            
        except sqlite3.Error as e:
            logger.error(f"Database error saving snapshot: {e}")
            return False, -2
        except Exception as e:
            logger.error(f"Unexpected error saving snapshot: {e}")
            return False, -2
    
    def load(self, month: str, year: str, bank: str, company: str) -> Optional[Dict[str, Any]]:
        """Load a snapshot from database with pre-computed values.
        
        OPTIMIZATION: Returns pre-calculated values directly, avoiding
        expensive calculations during load.
        
        Args:
            month: Month name
            year: Year string
            bank: Bank name
            company: Company name
        
        Returns:
            Dictionary with:
            - Standard snapshot dict keys (master_table, master_selected_rows, metadata)
            - Pre-computed keys (_credit_bal, _debit_bal, _start_date, _end_date)
            - Pre-formatted display data (_display_data) if available
            Returns None if not found
        """
        try:
            # Debug: log original values
            logger.debug(f"load() called with: month={repr(month)}, year={repr(year)}, bank={repr(bank)}, company={repr(company)}")
            
            # Normalize to lowercase for query
            month = month.lower() if month else ''
            bank = bank.lower() if bank else ''
            company = company.lower() if company else ''
            
            logger.debug(f"Normalized values: month={repr(month)}, year={repr(year)}, bank={repr(bank)}, company={repr(company)}")
            
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT data_json, data_msgpack, checksum,
                       credit_bal, debit_bal, start_date, end_date,
                       display_data_msgpack, row_count
                FROM snapshots
                WHERE month = ? AND year = ? AND bank = ? AND company = ?
            """, (month, year, bank, company))
            
            row = cursor.fetchone()
            if row is None:
                logger.debug(f"Snapshot not found: {company}/{year}/{month}/{bank}")
                return None
            
            data_json = row[0]
            data_msgpack = row[1]
            stored_checksum = row[2]
            credit_bal = row[3]
            debit_bal = row[4]
            start_date = row[5]
            end_date = row[6]
            display_data_msgpack = row[7]
            row_count = row[8]
            
            # Deserialize data (prefer msgpack if available)
            if data_msgpack is not None and MSGPACK_AVAILABLE:
                # Verify checksum against msgpack data
                calculated_checksum = _calculate_checksum(data_msgpack)
                if calculated_checksum != stored_checksum:
                    logger.error(
                        f"Checksum mismatch for snapshot {company}/{year}/{month}/{bank}. "
                        f"Data may be corrupted!"
                    )
                    return None
                
                snapshot_dict = _deserialize_data(data_msgpack, 'msgpack')
                logger.debug(f"Loaded snapshot using MessagePack: {company}/{year}/{month}/{bank}")
            elif data_json is not None:
                # Fallback to JSON
                calculated_checksum = _calculate_checksum(data_json)
                if calculated_checksum != stored_checksum:
                    logger.error(
                        f"Checksum mismatch for snapshot {company}/{year}/{month}/{bank}. "
                        f"Data may be corrupted!"
                    )
                    return None
                
                snapshot_dict = _deserialize_data(data_json.encode('utf-8'), 'json')
                logger.debug(f"Loaded snapshot using JSON: {company}/{year}/{month}/{bank}")
            else:
                logger.error(f"No data found for snapshot: {company}/{year}/{month}/{bank}")
                return None
            
            # Inject pre-calculated values into result (OPTIMIZATION)
            # These start with _ to indicate they're cached values
            if credit_bal is not None:
                snapshot_dict['_credit_bal'] = credit_bal
            if debit_bal is not None:
                snapshot_dict['_debit_bal'] = debit_bal
            if start_date is not None:
                snapshot_dict['_start_date'] = start_date
            if end_date is not None:
                snapshot_dict['_end_date'] = end_date
            if row_count is not None:
                snapshot_dict['_row_count'] = row_count
            
            # Deserialize pre-formatted display data if available
            if display_data_msgpack is not None and MSGPACK_AVAILABLE:
                try:
                    snapshot_dict['_display_data'] = msgpack.unpackb(display_data_msgpack, raw=False)
                except Exception as e:
                    logger.warning(f"Failed to deserialize display data: {e}")
            
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
            # Normalize to lowercase for query
            month = month.lower() if month else ''
            bank = bank.lower() if bank else ''
            company = company.lower() if company else ''
            
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
    
    def optimize_existing_snapshots(self, progress_callback=None) -> Tuple[int, int, List[str]]:
        """Migrate existing JSON-only snapshots to optimized format.
        
        Converts snapshots that only have data_json to the new format with:
        - MessagePack serialization (data_msgpack)
        - Pre-calculated balances and dates
        - Pre-formatted display data
        
        Args:
            progress_callback: Optional callback(current, total, message) for progress updates
        
        Returns:
            Tuple of (success_count, failed_count, error_messages)
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        try:
            conn = self._get_connection()
            
            # Find snapshots that need optimization (have data_json but no data_msgpack)
            cursor = conn.execute("""
                SELECT id, month, year, bank, company, data_json
                FROM snapshots
                WHERE data_json IS NOT NULL AND data_msgpack IS NULL
            """)
            
            rows = cursor.fetchall()
            total = len(rows)
            
            if total == 0:
                logger.info("All snapshots are already optimized")
                return 0, 0, []
            
            logger.info(f"Optimizing {total} snapshots...")
            
            for i, row in enumerate(rows):
                snapshot_id = row[0]
                month = row[1]
                year = row[2]
                bank = row[3]
                company = row[4]
                data_json = row[5]
                
                if progress_callback:
                    progress_callback(i + 1, total, f"Optimizing {company}/{year}/{month}/{bank}")
                
                try:
                    # Deserialize JSON
                    snapshot_dict = json.loads(data_json)
                    
                    # Get master_table
                    master_table = snapshot_dict.get('master_table', [])
                    row_count = len(master_table)
                    
                    # Pre-calculate balances and dates
                    credit_bal, debit_bal, start_date, end_date = _calculate_balances_and_dates(master_table)
                    
                    # Pre-format display data
                    display_data = _format_table_data_for_cache(master_table)
                    
                    # Serialize with MessagePack
                    if MSGPACK_AVAILABLE:
                        data_msgpack = msgpack.packb(snapshot_dict, use_bin_type=True)
                        display_data_msgpack = msgpack.packb(display_data, use_bin_type=True)
                        checksum = _calculate_checksum(data_msgpack)
                    else:
                        data_msgpack = None
                        display_data_msgpack = None
                        checksum = _calculate_checksum(data_json)
                    
                    # Update the row
                    conn.execute("""
                        UPDATE snapshots SET
                            data_msgpack = ?,
                            credit_bal = ?,
                            debit_bal = ?,
                            start_date = ?,
                            end_date = ?,
                            display_data_msgpack = ?,
                            row_count = ?,
                            checksum = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        data_msgpack, credit_bal, debit_bal, start_date, end_date,
                        display_data_msgpack, row_count, checksum, snapshot_id
                    ))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to optimize {company}/{year}/{month}/{bank}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    failed_count += 1
            
            # Commit all updates
            conn.commit()
            
            logger.info(f"Optimization complete: {success_count} success, {failed_count} failed")
            return success_count, failed_count, errors
            
        except Exception as e:
            logger.error(f"Error during optimization: {e}")
            return success_count, failed_count, errors + [str(e)]
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get status of snapshot optimization.
        
        Returns:
            Dictionary with:
            - total: Total number of snapshots
            - optimized: Number using MessagePack format
            - legacy: Number still using JSON-only
            - percent_optimized: Percentage optimized
        """
        try:
            conn = self._get_connection()
            
            cursor = conn.execute("SELECT COUNT(*) FROM snapshots")
            total = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM snapshots WHERE data_msgpack IS NOT NULL
            """)
            optimized = cursor.fetchone()[0]
            
            legacy = total - optimized
            percent = (optimized / total * 100) if total > 0 else 100
            
            return {
                'total': total,
                'optimized': optimized,
                'legacy': legacy,
                'percent_optimized': round(percent, 1)
            }
        except Exception as e:
            logger.error(f"Error getting optimization status: {e}")
            return {'total': 0, 'optimized': 0, 'legacy': 0, 'percent_optimized': 0}


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

def _backup_pickle_files_after_migration(snapshot_path: str, cheque_path: str) -> None:
    """Backup (rename) pickle files after successful migration.
    
    Renames pickle files to .migrated extension so they won't be detected
    as pending migration anymore, but can still be recovered if needed.
    
    Args:
        snapshot_path: Path to snapshot pickle file
        cheque_path: Path to cheque report pickle file
    """
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for path in [snapshot_path, cheque_path]:
        if path and os.path.exists(path):
            try:
                backup_path = f"{path}.migrated_{timestamp}"
                shutil.move(path, backup_path)
                logger.info(f"Backed up pickle file: {path} -> {backup_path}")
            except Exception as e:
                logger.warning(f"Could not backup pickle file {path}: {e}")


def migrate_pickle_to_sqlite(
    pickle_snapshot_path: Optional[str] = None,
    pickle_cheque_path: Optional[str] = None,
    sqlite_db_path: Optional[str] = None,
    app_name: str = "Record Matcher",
    dry_run: bool = False,
    progress_callback: Optional[callable] = None
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
        progress_callback: Optional callback function(item_type, item_name, current, total)
    
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
    snapshot_items = []
    cheque_items = []
    
    # First, collect all items to count total
    if os.path.exists(pickle_snapshot_path):
        try:
            with open(pickle_snapshot_path, 'rb') as f:
                snapshot_data = pickle.load(f)
            snapshot_items = [(k, v) for k, v in snapshot_data.items() if v is not None]
            logger.info(f"Found {len(snapshot_items)} snapshots in pickle file")
        except Exception as e:
            msg = f"Error reading snapshot pickle file: {e}"
            logger.error(msg)
            results['errors'].append(msg)
    
    if os.path.exists(pickle_cheque_path):
        try:
            with open(pickle_cheque_path, 'rb') as f:
                cheque_data = pickle.load(f)
            cheque_items = [(k, v) for k, v in cheque_data.items() if v is not None]
            logger.info(f"Found {len(cheque_items)} cheque reports in pickle file")
        except Exception as e:
            msg = f"Error reading cheque report pickle file: {e}"
            logger.error(msg)
            results['errors'].append(msg)
    
    total_items = len(snapshot_items) + len(cheque_items)
    current_item = 0
    
    # Migrate snapshots
    if snapshot_items:
        for key, snapshot in snapshot_items:
            current_item += 1
            
            if progress_callback:
                progress_callback("snapshot", str(key), current_item, total_items)
            
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] Would migrate snapshot: {key}")
                    results['snapshots_migrated'] += 1
                else:
                    success, error_code = snapshot_repo.save(snapshot)
                    if success:
                        results['snapshots_migrated'] += 1
                        logger.info(f"[OK] Migrated snapshot: {key}")
                    else:
                        error_msg = f"Failed to migrate snapshot {key}: error code {error_code}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            except Exception as e:
                error_msg = f"Error migrating snapshot {key}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
    elif not os.path.exists(pickle_snapshot_path):
        msg = f"Snapshot pickle file does not exist: {pickle_snapshot_path}"
        logger.warning(msg)
        results['errors'].append(msg)
    
    # Migrate cheque reports
    logger.info(f"\nMigrating cheque reports from: {pickle_cheque_path}")
    if cheque_items:
        for key, report in cheque_items:
            current_item += 1
            
            if progress_callback:
                progress_callback("cheque_report", str(key), current_item, total_items)
            
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
                            logger.info(f"[OK] Migrated cheque report: {key}")
                        else:
                            error_msg = f"Failed to migrate cheque report {key}: error code {error_code}"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
            except Exception as e:
                error_msg = f"Error migrating cheque report {key}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
    elif not os.path.exists(pickle_cheque_path):
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
        logger.info("\n[OK] MIGRATION COMPLETED SUCCESSFULLY")
        # Backup pickle files after successful migration
        _backup_pickle_files_after_migration(pickle_snapshot_path, pickle_cheque_path)
    else:
        logger.warning("\n[WARNING] MIGRATION COMPLETED WITH ERRORS")
        # Still backup if we migrated at least some items
        if results['snapshots_migrated'] > 0 or results['cheque_reports_migrated'] > 0:
            _backup_pickle_files_after_migration(pickle_snapshot_path, pickle_cheque_path)
    
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
