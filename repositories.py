"""Repository pattern implementations for data access abstraction.

This module implements the Repository pattern to abstract all data persistence
operations behind clean interfaces. This provides:
- Decoupling of business logic from data storage implementation
- Easy testing through mock repositories
- Flexibility to change storage mechanisms without affecting business logic
- Centralized data access logic
- Clear separation of concerns

The module includes both abstract base classes (interfaces) and concrete
implementations for:
- Table snapshot persistence (pickle files)
- Cheque report persistence (pickle files)
- Configuration data access (JSON files)
- Firebase cloud storage

Repository Hierarchy:
    IRepository (ABC)
    ├── ISnapshotRepository
    │   └── PickleSnapshotRepository
    ├── IChequeReportRepository
    │   └── PickleChequeReportRepository
    ├── IConfigRepository
    │   └── JsonConfigRepository
    └── IFirebaseRepository
        └── FirebaseCloudRepository
"""

import os
import json
import pickle
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from models import TableSnapshotData, ValidationResult

logger = logging.getLogger(__name__)


class IRepository(ABC):
    """Base repository interface.
    
    Defines the minimal contract that all repositories must implement.
    """
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if repository is accessible and operational.
        
        Returns:
            True if repository is healthy, False otherwise
        """
        pass


class ISnapshotRepository(IRepository):
    """Interface for table snapshot persistence operations.
    
    Defines the contract for storing and retrieving table snapshots
    regardless of the underlying storage mechanism.
    """
    
    @abstractmethod
    def save(self, snapshot: Any) -> Tuple[bool, int]:
        """Save a table snapshot.
        
        Args:
            snapshot: TableSnapshot object to save
            
        Returns:
            Tuple of (success: bool, error_code: int)
            error_code is 0 on success, non-zero on failure
        """
        pass
    
    @abstractmethod
    def load(self, month: str, year: str, bank: str, company: str) -> Optional[Any]:
        """Load a table snapshot by its identifiers.
        
        Args:
            month: Month name (lowercase)
            year: Year as string
            bank: Bank name (lowercase)
            company: Company name (lowercase)
            
        Returns:
            TableSnapshot object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, month: str, year: str, bank: str, company: str) -> bool:
        """Delete a table snapshot.
        
        Args:
            month: Month name (lowercase)
            year: Year as string
            bank: Bank name (lowercase)
            company: Company name (lowercase)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, month: str, year: str, bank: str, company: str) -> bool:
        """Check if a snapshot exists.
        
        Args:
            month: Month name (lowercase)
            year: Year as string
            bank: Bank name (lowercase)
            company: Company name (lowercase)
            
        Returns:
            True if snapshot exists, False otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[Tuple[str, str, str, str]]:
        """List all stored snapshots.
        
        Returns:
            List of tuples (month, year, bank, company) for all snapshots
        """
        pass


class IChequeReportRepository(IRepository):
    """Interface for cheque report persistence operations."""
    
    @abstractmethod
    def save(self, cheque_report: Any) -> Tuple[bool, int]:
        """Save a cheque report.
        
        Args:
            cheque_report: InfiChequeStatement object to save
            
        Returns:
            Tuple of (success: bool, error_code: int)
        """
        pass
    
    @abstractmethod
    def load(self, year: str, company: str) -> Optional[Any]:
        """Load a cheque report by year and company.
        
        Args:
            year: Year as string
            company: Company name (lowercase)
            
        Returns:
            InfiChequeStatement object if found, None otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, year: str, company: str) -> bool:
        """Delete a cheque report.
        
        Args:
            year: Year as string
            company: Company name (lowercase)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, year: str, company: str) -> bool:
        """Check if a cheque report exists.
        
        Args:
            year: Year as string
            company: Company name (lowercase)
            
        Returns:
            True if report exists, False otherwise
        """
        pass


class IConfigRepository(IRepository):
    """Interface for configuration data access."""
    
    @abstractmethod
    def get_companies(self) -> List[str]:
        """Get list of available companies."""
        pass
    
    @abstractmethod
    def get_banks(self) -> List[str]:
        """Get list of available banks."""
        pass
    
    @abstractmethod
    def get_years(self) -> List[str]:
        """Get list of available years."""
        pass
    
    @abstractmethod
    def get_months(self) -> List[str]:
        """Get list of available months."""
        pass
    
    @abstractmethod
    def get_admin_password(self) -> str:
        """Get admin password."""
        pass
    
    @abstractmethod
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration data."""
        pass
    
    @abstractmethod
    def reload(self) -> bool:
        """Reload configuration from source.
        
        Returns:
            True if reload successful, False otherwise
        """
        pass


class IFirebaseRepository(IRepository):
    """Interface for Firebase cloud storage operations."""
    
    @abstractmethod
    def upload_snapshot(self, snapshot: Any, progress_callback=None) -> Tuple[bool, int]:
        """Upload a snapshot to Firebase.
        
        Args:
            snapshot: TableSnapshot to upload
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success: bool, error_code: int)
        """
        pass
    
    @abstractmethod
    def download_snapshot(self, month: str, year: str, bank: str, company: str,
                         progress_callback=None) -> Optional[Any]:
        """Download a snapshot from Firebase.
        
        Args:
            month: Month name
            year: Year as string
            bank: Bank name
            company: Company name
            progress_callback: Optional callback for progress updates
            
        Returns:
            TableSnapshot if found, None otherwise
        """
        pass
    
    @abstractmethod
    def upload_config(self, config_data: Dict[str, Any], progress_callback=None) -> Tuple[bool, int]:
        """Upload configuration to Firebase.
        
        Args:
            config_data: Configuration dictionary
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success: bool, error_code: int)
        """
        pass
    
    @abstractmethod
    def download_config(self, progress_callback=None) -> Optional[Dict[str, Any]]:
        """Download configuration from Firebase.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            Configuration dictionary if successful, None otherwise
        """
        pass


# ============================================================================
# CONCRETE IMPLEMENTATIONS
# ============================================================================


class PickleSnapshotRepository(ISnapshotRepository):
    """Pickle-based implementation of snapshot repository.
    
    Stores table snapshots in a pickle file using a dictionary structure.
    Compatible with existing TableSnapshotCollection implementation.
    
    Attributes:
        save_path: Path to the pickle file
        _cache: In-memory cache of snapshots
        _loaded: Whether cache has been loaded from disk
    """
    
    def __init__(self, save_path: Optional[str] = None, app_name: str = "RecordMatcher"):
        """Initialize pickle snapshot repository.
        
        Args:
            save_path: Custom save path (uses APPDATA if None)
            app_name: Application name for default path
        """
        if save_path is None:
            appdata = os.getenv('APPDATA', '.')
            self.save_path = os.path.join(appdata, app_name, "tableSnapshotCollection.filv2")
        else:
            self.save_path = save_path
        
        self._cache: Dict[str, Any] = {}
        self._loaded = False
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        logger.debug(f"PickleSnapshotRepository initialized with path: {self.save_path}")
    
    def _ensure_loaded(self) -> bool:
        """Ensure data is loaded into cache.
        
        Returns:
            True if data is loaded, False if load failed
        """
        if self._loaded:
            return True
        
        try:
            with open(self.save_path, 'rb') as f:
                self._cache = pickle.load(f)
            self._loaded = True
            logger.info(f"Loaded {len(self._cache)} snapshots from {self.save_path}")
            return True
        except FileNotFoundError:
            logger.info(f"No existing snapshot file found at {self.save_path}, starting fresh")
            self._cache = {}
            self._loaded = True
            return True
        except Exception as e:
            logger.error(f"Failed to load snapshots: {e}")
            return False
    
    def _get_key(self, month: str, year: str, bank: str, company: str) -> str:
        """Generate dictionary key for snapshot.
        
        Args:
            month: Month name
            year: Year as string
            bank: Bank name
            company: Company name
            
        Returns:
            Dictionary key in format: company_month_year_bank
        """
        return f"{company.lower()}_{month.lower()}_{year}_{bank.lower()}"
    
    def _persist(self) -> Tuple[bool, int]:
        """Save cache to disk.
        
        Returns:
            Tuple of (success: bool, error_code: int)
        """
        try:
            with open(self.save_path, 'wb') as f:
                pickle.dump(self._cache, f)
            logger.debug(f"Persisted {len(self._cache)} snapshots to disk")
            return True, 0
        except TypeError as e:
            logger.error(f"Serialization error: {e}")
            return False, -1
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"File access error: {e}")
            return False, -2
        except Exception as e:
            logger.error(f"Unexpected error during persist: {e}")
            return False, -3
    
    def health_check(self) -> bool:
        """Check repository health."""
        return self._ensure_loaded()
    
    def save(self, snapshot: Any) -> Tuple[bool, int]:
        """Save a table snapshot."""
        if not self._ensure_loaded():
            return False, -1
        
        try:
            month = snapshot.get_month()
            year = snapshot.get_year()
            bank = snapshot.get_bank()
            company = snapshot.get_company()
            
            key = self._get_key(month, year, bank, company)
            self._cache[key] = snapshot
            
            logger.info(f"Saving snapshot: {key}")
            return self._persist()
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False, -1
    
    def load(self, month: str, year: str, bank: str, company: str) -> Optional[Any]:
        """Load a table snapshot."""
        if not self._ensure_loaded():
            return None
        
        key = self._get_key(month, year, bank, company)
        snapshot = self._cache.get(key)
        
        if snapshot:
            logger.debug(f"Loaded snapshot: {key}")
        else:
            logger.debug(f"Snapshot not found: {key}")
        
        return snapshot
    
    def delete(self, month: str, year: str, bank: str, company: str) -> bool:
        """Delete a table snapshot."""
        if not self._ensure_loaded():
            return False
        
        key = self._get_key(month, year, bank, company)
        
        if key in self._cache:
            self._cache[key] = None  # Set to None instead of deleting (existing behavior)
            success, _ = self._persist()
            if success:
                logger.info(f"Deleted snapshot: {key}")
            return success
        else:
            logger.warning(f"Cannot delete non-existent snapshot: {key}")
            return False
    
    def exists(self, month: str, year: str, bank: str, company: str) -> bool:
        """Check if a snapshot exists."""
        if not self._ensure_loaded():
            return False
        
        key = self._get_key(month, year, bank, company)
        return key in self._cache and self._cache[key] is not None
    
    def list_all(self) -> List[Tuple[str, str, str, str]]:
        """List all stored snapshots."""
        if not self._ensure_loaded():
            return []
        
        snapshots = []
        for key, value in self._cache.items():
            if value is not None:
                # Parse key: company_month_year_bank
                parts = key.split('_')
                if len(parts) >= 4:
                    company = parts[0]
                    month = parts[1]
                    year = parts[2]
                    bank = '_'.join(parts[3:])  # Handle bank names with underscores
                    snapshots.append((month, year, bank, company))
        
        return snapshots


class PickleChequeReportRepository(IChequeReportRepository):
    """Pickle-based implementation of cheque report repository.
    
    Stores cheque reports in a pickle file using dictionary structure.
    Compatible with existing ChequeReportCollection implementation.
    """
    
    def __init__(self, save_path: Optional[str] = None, app_name: str = "RecordMatcher"):
        """Initialize pickle cheque report repository.
        
        Args:
            save_path: Custom save path (uses APPDATA if None)
            app_name: Application name for default path
        """
        if save_path is None:
            appdata = os.getenv('APPDATA', '.')
            self.save_path = os.path.join(appdata, app_name, "ChequeReportCollection.fil")
        else:
            self.save_path = save_path
        
        self._cache: Dict[str, Any] = {}
        self._loaded = False
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        logger.debug(f"PickleChequeReportRepository initialized with path: {self.save_path}")
    
    def _ensure_loaded(self) -> bool:
        """Ensure data is loaded into cache."""
        if self._loaded:
            return True
        
        try:
            with open(self.save_path, 'rb') as f:
                self._cache = pickle.load(f)
            self._loaded = True
            logger.info(f"Loaded {len(self._cache)} cheque reports from {self.save_path}")
            return True
        except FileNotFoundError:
            logger.info(f"No existing cheque report file found, starting fresh")
            self._cache = {}
            self._loaded = True
            return True
        except Exception as e:
            logger.error(f"Failed to load cheque reports: {e}")
            return False
    
    def _get_key(self, year: str, company: str) -> str:
        """Generate dictionary key for cheque report.
        
        Args:
            year: Year as string
            company: Company name
            
        Returns:
            Dictionary key in format: company__year
        """
        return f"{company.lower()}__year"
    
    def _persist(self) -> Tuple[bool, int]:
        """Save cache to disk."""
        try:
            with open(self.save_path, 'wb') as f:
                pickle.dump(self._cache, f)
            logger.debug(f"Persisted {len(self._cache)} cheque reports to disk")
            return True, 0
        except TypeError as e:
            logger.error(f"Serialization error: {e}")
            return False, -1
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"File access error: {e}")
            return False, -2
        except Exception as e:
            logger.error(f"Unexpected error during persist: {e}")
            return False, -3
    
    def health_check(self) -> bool:
        """Check repository health."""
        return self._ensure_loaded()
    
    def save(self, cheque_report: Any) -> Tuple[bool, int]:
        """Save a cheque report."""
        if not self._ensure_loaded():
            return False, -1
        
        try:
            year = cheque_report.get_year()
            company = cheque_report.get_company()
            
            key = self._get_key(year, company)
            self._cache[key] = cheque_report
            
            logger.info(f"Saving cheque report: {key}")
            return self._persist()
        except Exception as e:
            logger.error(f"Failed to save cheque report: {e}")
            return False, -1
    
    def load(self, year: str, company: str) -> Optional[Any]:
        """Load a cheque report."""
        if not self._ensure_loaded():
            return None
        
        key = self._get_key(year, company)
        report = self._cache.get(key)
        
        if report:
            logger.debug(f"Loaded cheque report: {key}")
        else:
            logger.debug(f"Cheque report not found: {key}")
        
        return report
    
    def delete(self, year: str, company: str) -> bool:
        """Delete a cheque report."""
        if not self._ensure_loaded():
            return False
        
        key = self._get_key(year, company)
        
        if key in self._cache:
            self._cache[key] = None  # Set to None (existing behavior)
            success, _ = self._persist()
            if success:
                logger.info(f"Deleted cheque report: {key}")
            return success
        else:
            logger.warning(f"Cannot delete non-existent cheque report: {key}")
            return False
    
    def exists(self, year: str, company: str) -> bool:
        """Check if a cheque report exists."""
        if not self._ensure_loaded():
            return False
        
        key = self._get_key(year, company)
        return key in self._cache and self._cache[key] is not None


class JsonConfigRepository(IConfigRepository):
    """JSON-based configuration repository.
    
    Reads configuration from a JSON file containing companies, banks, years, months.
    """
    
    def __init__(self, json_path: str = 'data.json'):
        """Initialize JSON config repository.
        
        Args:
            json_path: Path to JSON configuration file
        """
        self.json_path = json_path
        self._config: Dict[str, Any] = {}
        self._loaded = False
        logger.debug(f"JsonConfigRepository initialized with path: {json_path}")
    
    def _ensure_loaded(self) -> bool:
        """Ensure configuration is loaded."""
        if self._loaded:
            return True
        
        return self.reload()
    
    def health_check(self) -> bool:
        """Check repository health."""
        return os.path.exists(self.json_path) and self._ensure_loaded()
    
    def reload(self) -> bool:
        """Reload configuration from JSON file."""
        try:
            with open(self.json_path, 'r') as f:
                self._config = json.load(f)
            self._loaded = True
            logger.info(f"Loaded configuration from {self.json_path}")
            return True
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.json_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def get_companies(self) -> List[str]:
        """Get list of available companies."""
        if not self._ensure_loaded():
            return []
        return self._config.get('Companies', [])
    
    def get_banks(self) -> List[str]:
        """Get list of available banks."""
        if not self._ensure_loaded():
            return []
        return self._config.get('Banks', [])
    
    def get_years(self) -> List[str]:
        """Get list of available years."""
        if not self._ensure_loaded():
            return []
        return self._config.get('Years', [])
    
    def get_months(self) -> List[str]:
        """Get list of available months."""
        if not self._ensure_loaded():
            return []
        return self._config.get('Months', [])
    
    def get_admin_password(self) -> str:
        """Get admin password."""
        if not self._ensure_loaded():
            return ""
        return self._config.get('AdminPassword', "")
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration data."""
        if not self._ensure_loaded():
            return {}
        return self._config.copy()


# Note: FirebaseCloudRepository implementation would go here
# For now, keeping Firebase operations in the service layer since they
# have complex dependencies on Firebase SDK
