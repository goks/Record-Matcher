"""Business logic services for the Record Matcher application.

This module contains service classes that encapsulate business logic previously
embedded in the MainWindow UI controller. By extracting business logic into
dedicated service classes, we achieve:
- Clear separation of concerns (UI vs business logic)
- Improved testability (services can be tested without UI)
- Better code organization and maintainability
- Reusability across different UI layers (desktop, web, CLI)
- Easier mocking and dependency injection for testing

Service Classes:
    StateManagementService: Manages application state and validation
    FileOperationService: Handles file upload/export operations
    TablePopulationService: Manages table data loading and display
    SearchService: Provides search and filtering capabilities
    SyncService: Coordinates Firebase synchronization operations
"""

import logging
import threading
from typing import Optional, List, Tuple, Callable, Any
from datetime import datetime
from PySide2.QtCore import QDate

from models import (
    ApplicationState,
    UIDisplayData,
    ValidationResult,
    ValidationErrorType,
    SearchResult,
    ExportConfig,
    DaybookConfig,
    FirebaseSyncProgress
)
from repositories import (
    ISnapshotRepository,
    IChequeReportRepository,
    IConfigRepository
)

logger = logging.getLogger(__name__)


class StateManagementService:
    """Service for managing application state and validation.
    
    This service centralizes all state management logic that was previously
    scattered across MainWindow. It maintains the current application state
    and provides validation methods.
    
    Attributes:
        state: Current application state
        _state_lock: Thread lock for state access
    """
    
    def __init__(self):
        """Initialize state management service."""
        self.state = ApplicationState()
        self._state_lock = threading.Lock()
        logger.debug("StateManagementService initialized")
    
    def get_state(self) -> ApplicationState:
        """Get current application state (thread-safe).
        
        Returns:
            Copy of current ApplicationState
        """
        with self._state_lock:
            # Create a copy to avoid external mutation
            return ApplicationState(
                current_month=self.state.current_month,
                current_year=self.state.current_year,
                current_bank=self.state.current_bank,
                current_company=self.state.current_company,
                cheque_report_activated=self.state.cheque_report_activated,
                tally_export_activated=self.state.tally_export_activated,
                search_mode_off_first_time=self.state.search_mode_off_first_time
            )
    
    def update_month(self, month: str) -> None:
        """Update selected month.
        
        Args:
            month: Month name
        """
        with self._state_lock:
            self.state.current_month = month
            logger.debug(f"Month updated: {month}")
    
    def update_year(self, year: str) -> None:
        """Update selected year.
        
        Args:
            year: Year as string
        """
        with self._state_lock:
            self.state.current_year = year
            logger.debug(f"Year updated: {year}")
    
    def update_bank(self, bank: str) -> None:
        """Update selected bank.
        
        Args:
            bank: Bank name
        """
        with self._state_lock:
            self.state.current_bank = bank
            logger.debug(f"Bank updated: {bank}")
    
    def update_company(self, company: str) -> None:
        """Update selected company.
        
        Args:
            company: Company name
        """
        with self._state_lock:
            self.state.current_company = company
            logger.debug(f"Company updated: {company}")
    
    def set_cheque_report_mode(self, activated: bool) -> None:
        """Set cheque report mode.
        
        Args:
            activated: Whether cheque report mode is active
        """
        with self._state_lock:
            self.state.cheque_report_activated = activated
            logger.debug(f"Cheque report mode: {activated}")
    
    def set_tally_export_mode(self, activated: bool) -> None:
        """Set Tally export mode.
        
        Args:
            activated: Whether Tally export mode is active
        """
        with self._state_lock:
            self.state.tally_export_activated = activated
            logger.debug(f"Tally export mode: {activated}")
    
    def validate_for_upload(self) -> ValidationResult:
        """Validate state for file upload operation.
        
        Returns:
            ValidationResult indicating if state is valid for upload
        """
        with self._state_lock:
            error_type = self.state.get_validation_error()
            
            if error_type:
                error_code = error_type.value
                error_msg = self._get_validation_message(error_type)
                logger.warning(f"Upload validation failed: {error_msg}")
                return ValidationResult.failure(error_code, error_msg)
            
            logger.debug("Upload validation passed")
            return ValidationResult.success()
    
    def validate_for_export(self, has_snapshot: bool) -> ValidationResult:
        """Validate state for file export operation.
        
        Args:
            has_snapshot: Whether a table snapshot exists
            
        Returns:
            ValidationResult indicating if state is valid for export
        """
        if not has_snapshot:
            error_type = ValidationErrorType.NO_SNAPSHOT_AVAILABLE
            error_code = error_type.value
            error_msg = self._get_validation_message(error_type)
            logger.warning(f"Export validation failed: {error_msg}")
            return ValidationResult.failure(error_code, error_msg)
        
        logger.debug("Export validation passed")
        return ValidationResult.success()
    
    def validate_for_populate_table(self) -> ValidationResult:
        """Validate state for table population.
        
        Returns:
            ValidationResult indicating if state is valid
        """
        with self._state_lock:
            if not self.state.is_ready_for_bank_statement():
                error_msg = "Month, year, bank, and company must all be selected"
                logger.warning(f"Table population validation failed: {error_msg}")
                return ValidationResult.failure(-1, error_msg)
            
            logger.debug("Table population validation passed")
            return ValidationResult.success()
    
    @staticmethod
    def _get_validation_message(error_type: ValidationErrorType) -> str:
        """Get human-readable validation error message.
        
        Args:
            error_type: ValidationErrorType enum
            
        Returns:
            Error message string
        """
        messages = {
            ValidationErrorType.COMPANY_YEAR_MISSING: "Company and year must be selected",
            ValidationErrorType.BANK_MONTH_MISSING: "Bank and month must be selected for bank statement",
            ValidationErrorType.NO_SNAPSHOT_AVAILABLE: "No table snapshot available for export",
            ValidationErrorType.CHEQUE_REPORT_SAVE_FAILED: "Failed to save cheque report",
            ValidationErrorType.INVALID_FILE_FORMAT: "Invalid file format or corrupted file",
            ValidationErrorType.FILE_NOT_FOUND: "File not found or inaccessible",
            ValidationErrorType.EXPORT_FAILED: "Export operation failed",
            ValidationErrorType.DATA_VALIDATION_FAILED: "Data validation failed"
        }
        return messages.get(error_type, "Validation error")
    
    def generate_month_year_display(self) -> str:
        """Generate display string for month/year.
        
        Returns:
            Formatted month/year string
        """
        with self._state_lock:
            if self.state.cheque_report_activated:
                if self.state.current_year:
                    # For cheque reports, show fiscal year
                    return f"{self.state.current_year} - {int(self.state.current_year) + 1}"
                else:
                    return ''
            else:
                # For bank statements, show month and year
                if self.state.current_month and self.state.current_year:
                    return f"{self.state.current_month.capitalize()} {self.state.current_year}"
                else:
                    return ''


class FileOperationService:
    """Service for file upload and export operations.
    
    Handles all file-related business logic including validation,
    processing, and coordination with data services.
    
    Attributes:
        table_operations: Core table operations handler from existing code
        _lock: Thread lock for file operations
    """
    
    def __init__(self, table_operations: Any):
        """Initialize file operation service.
        
        Args:
            table_operations: TableOperations instance
        """
        self.table_operations = table_operations
        self._lock = threading.Lock()
        logger.debug("FileOperationService initialized")
    
    def process_upload(self, file_path: str, is_cheque_report: bool) -> Tuple[bool, int]:
        """Process file upload (bank statement or cheque report).
        
        Args:
            file_path: Path to file to upload
            is_cheque_report: Whether this is a cheque report (vs bank statement)
            
        Returns:
            Tuple of (success: bool, status_code: int)
        """
        with self._lock:
            logger.info(f"Processing upload: {file_path} (cheque_report={is_cheque_report})")
            
            try:
                if is_cheque_report:
                    success = self.table_operations.save_chequeReport_to_collection(file_path)
                    status_code = 0 if success else ValidationErrorType.CHEQUE_REPORT_SAVE_FAILED.value
                    return success, status_code
                else:
                    success, status_code = self.table_operations.add_snapshot_to_table(file_path)
                    return success, status_code
            except FileNotFoundError:
                logger.error(f"File not found: {file_path}")
                return False, ValidationErrorType.FILE_NOT_FOUND.value
            except Exception as e:
                logger.error(f"Upload failed: {e}", exc_info=True)
                return False, ValidationErrorType.INVALID_FILE_FORMAT.value
    
    def process_export(self, output_path: str, snapshot: Any) -> Tuple[bool, int]:
        """Process table export to Excel.
        
        Args:
            output_path: Destination file path
            snapshot: TableSnapshot to export
            
        Returns:
            Tuple of (success: bool, status_code: int)
        """
        with self._lock:
            logger.info(f"Processing export: {output_path}")
            
            try:
                success, status_code = self.table_operations.export_to_excel(output_path, snapshot)
                return success, status_code
            except Exception as e:
                logger.error(f"Export failed: {e}", exc_info=True)
                return False, ValidationErrorType.EXPORT_FAILED.value
    
    def validate_daybook_inputs(self, config: DaybookConfig) -> ValidationResult:
        """Validate inputs for daybook generation.
        
        Args:
            config: DaybookConfig with all parameters
            
        Returns:
            ValidationResult indicating if inputs are valid
        """
        logger.debug(f"Validating daybook inputs: {config.from_date} to {config.to_date}")
        
        # Validate date format and range
        date_validation = config.validate_dates()
        if not date_validation.is_valid:
            return date_validation
        
        # Delegate to existing validation logic
        try:
            status, code = self.table_operations.validateIntermediateDaybook(
                config.output_path,
                config.from_date,
                config.to_date,
                config.company
            )
            
            if status:
                return ValidationResult.success()
            else:
                return ValidationResult.failure(code, "Daybook validation failed")
        except Exception as e:
            logger.error(f"Daybook validation error: {e}", exc_info=True)
            return ValidationResult.failure(
                ValidationErrorType.DATA_VALIDATION_FAILED.value,
                f"Validation error: {str(e)}"
            )
    
    def generate_daybook(self) -> Tuple[bool, int, Any]:
        """Generate intermediate daybook.
        
        Returns:
            Tuple of (success: bool, status_code: int, data: Any)
        """
        logger.info("Generating intermediate daybook")
        
        try:
            status, code, data = self.table_operations.generateIntermediateDaybook()
            return status, code, data
        except Exception as e:
            logger.error(f"Daybook generation failed: {e}", exc_info=True)
            return False, 99, str(e)


class TablePopulationService:
    """Service for table data loading and population.
    
    Handles the business logic for loading snapshots from repositories
    and preparing data for UI display.
    
    Attributes:
        table_operations: Core table operations handler
        snapshot_repository: Repository for snapshot persistence
        _lock: Thread lock for data operations
    """
    
    def __init__(self, table_operations: Any, snapshot_repository: ISnapshotRepository):
        """Initialize table population service.
        
        Args:
            table_operations: TableOperations instance
            snapshot_repository: ISnapshotRepository implementation
        """
        self.table_operations = table_operations
        self.snapshot_repository = snapshot_repository
        self._lock = threading.Lock()
        logger.debug("TablePopulationService initialized")
    
    def load_table_data(self, month: str, year: str, bank: str, company: str) -> Optional[Tuple[Any, List, str, str, str, str]]:
        """Load table data for display.
        
        Args:
            month: Month name
            year: Year as string
            bank: Bank name
            company: Company name
            
        Returns:
            Tuple of (snapshot, display_data, credit_bal, debit_bal, start_date, end_date)
            or None if no snapshot found
        """
        with self._lock:
            logger.info(f"Loading table data: {bank}/{company}/{month}/{year}")
            
            try:
                result = self.table_operations.get_table_from_collection(
                    month, year, bank, company
                )
                
                if result[0] is None:  # No snapshot found
                    logger.info("No snapshot found in collection")
                    return None
                
                logger.debug("Table data loaded successfully")
                return result
            except Exception as e:
                logger.error(f"Failed to load table data: {e}", exc_info=True)
                return None
    
    def prepare_ui_display_data(
        self,
        snapshot: Any,
        display_data: List,
        credit_bal: str,
        debit_bal: str,
        start_date: str,
        end_date: str,
        header: List[str]
    ) -> UIDisplayData:
        """Prepare data for UI display.
        
        Args:
            snapshot: TableSnapshot object
            display_data: Table data for display
            credit_bal: Credit balance string
            debit_bal: Debit balance string
            start_date: Start date string (DD/MM/YYYY)
            end_date: End date string (DD/MM/YYYY)
            header: Column headers
            
        Returns:
            UIDisplayData with all display information
        """
        ui_data = UIDisplayData(
            table_data=display_data,
            credit_balance=credit_bal,
            debit_balance=debit_bal,
            header=header,
            selected_rows=snapshot.get_master_selected_rows() if snapshot else [],
            start_date=start_date,
            end_date=end_date
        )
        
        logger.debug(f"Prepared UI display data: {len(ui_data.table_data)} rows")
        return ui_data
    
    def save_snapshot(self, snapshot: Any, selected_rows: List[int]) -> bool:
        """Save current snapshot with selected rows.
        
        Args:
            snapshot: TableSnapshot to save
            selected_rows: List of selected row indices
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not snapshot:
            logger.debug("No snapshot to save")
            return False
        
        with self._lock:
            try:
                logger.info(f"Saving snapshot with {len(selected_rows)} selected rows")
                snapshot.set_master_selected_rows(selected_rows)
                self.table_operations.save_snapshot_to_table(snapshot)
                logger.debug("Snapshot saved successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to save snapshot: {e}", exc_info=True)
                return False


class SearchService:
    """Service for search and filtering operations.
    
    Provides search functionality across table data with various modes
    (cheque number, date, amount, etc.).
    
    Attributes:
        table_operations: Core table operations handler
        _lock: Thread lock for search operations
    """
    
    def __init__(self, table_operations: Any):
        """Initialize search service.
        
        Args:
            table_operations: TableOperations instance
        """
        self.table_operations = table_operations
        self._lock = threading.Lock()
        logger.debug("SearchService initialized")
    
    def search(
        self,
        query: str,
        mode: str,
        master_table: List,
        master_display_data: List
    ) -> SearchResult:
        """Perform search on table data.
        
        Args:
            query: Search query string
            mode: Search mode (e.g., 'chqno', 'date', 'amount', 'off')
            master_table: Full table data
            master_display_data: Display-formatted table data
            
        Returns:
            SearchResult with filtered data and balances
        """
        with self._lock:
            logger.debug(f"Search: query='{query}', mode={mode}")
            
            try:
                if mode == "off":
                    # Return original data
                    filtered_data = master_display_data
                    logger.debug("Search mode off, returning full data")
                else:
                    # Perform search using existing logic
                    filtered_data = self.table_operations.search(master_table, query, mode)
                    logger.debug(f"Search completed: {len(filtered_data)} results")
                
                # Calculate balances (simplified - actual logic might be in TableOperations)
                # For now, returning placeholder values
                # In a full implementation, we'd calculate these from filtered_data
                credit_bal = "Credit Bal"
                debit_bal = "Debit Bal"
                
                return SearchResult(
                    filtered_data=filtered_data,
                    credit_balance=credit_bal,
                    debit_balance=debit_bal
                )
            except Exception as e:
                logger.error(f"Search failed: {e}", exc_info=True)
                # Return empty result on error
                return SearchResult(
                    filtered_data=[],
                    credit_balance="0.00",
                    debit_balance="0.00"
                )


class SyncService:
    """Service for Firebase synchronization operations.
    
    Coordinates upload and download operations to/from Firebase,
    providing progress tracking and error handling.
    
    Attributes:
        table_operations: Core table operations handler
        _lock: Thread lock for sync operations
    """
    
    def __init__(self, table_operations: Any):
        """Initialize sync service.
        
        Args:
            table_operations: TableOperations instance
        """
        self.table_operations = table_operations
        self._lock = threading.Lock()
        logger.debug("SyncService initialized")
    
    def download_from_firebase(self, progress_callback: Optional[Callable] = None) -> bool:
        """Download data from Firebase.
        
        Args:
            progress_callback: Optional callback for progress updates
                Signature: callback(stage: str, details: str, progress: float)
        
        Returns:
            True if download successful, False otherwise
        """
        with self._lock:
            logger.info("Starting Firebase download")
            
            try:
                self.table_operations.get_data_from_firebase_db(progress_callback)
                logger.info("Firebase download completed successfully")
                return True
            except Exception as e:
                logger.error(f"Firebase download failed: {e}", exc_info=True)
                return False
    
    def upload_to_firebase(self, progress_callback: Optional[Callable] = None) -> bool:
        """Upload data to Firebase.
        
        Args:
            progress_callback: Optional callback for progress updates
                Signature: callback(stage: str, details: str, progress: float)
        
        Returns:
            True if upload successful, False otherwise
        """
        with self._lock:
            logger.info("Starting Firebase upload")
            
            try:
                self.table_operations.upload_data_to_firebase_db(progress_callback)
                logger.info("Firebase upload completed successfully")
                return True
            except Exception as e:
                logger.error(f"Firebase upload failed: {e}", exc_info=True)
                return False


class ChequeReportService:
    """Service for cheque report operations.
    
    Handles business logic related to cheque report loading and management.
    
    Attributes:
        table_operations: Core table operations handler
        cheque_repository: Repository for cheque report persistence
        _lock: Thread lock for operations
    """
    
    def __init__(self, table_operations: Any, cheque_repository: IChequeReportRepository):
        """Initialize cheque report service.
        
        Args:
            table_operations: TableOperations instance
            cheque_repository: IChequeReportRepository implementation
        """
        self.table_operations = table_operations
        self.cheque_repository = cheque_repository
        self._lock = threading.Lock()
        logger.debug("ChequeReportService initialized")
    
    def load_cheque_report(self, year: str, company: str) -> Tuple[int, str]:
        """Load cheque report for display.
        
        Args:
            year: Year as string
            company: Company name
            
        Returns:
            Tuple of (status_code, timestamp_string)
            status_code: 1 if found, 0 if not found, -1 on error
        """
        with self._lock:
            logger.info(f"Loading cheque report: {company}/{year}")
            
            try:
                cheque_statement = self.table_operations.get_chequeReport_from_collection(year, company)
                
                if not cheque_statement:
                    logger.info("No cheque report found")
                    return 0, ''
                
                timestamp = cheque_statement.get_time_stamp()
                logger.info(f"Cheque report loaded (timestamp: {timestamp})")
                return 1, timestamp
            except Exception as e:
                logger.error(f"Failed to load cheque report: {e}", exc_info=True)
                return -1, ''
    
    def delete_cheque_report(self, year: str, company: str) -> bool:
        """Delete cheque report.
        
        Args:
            year: Year as string
            company: Company name
            
        Returns:
            True if deleted successfully, False otherwise
        """
        with self._lock:
            logger.info(f"Deleting cheque report: {company}/{year}")
            
            try:
                success = self.table_operations.delete_chequeReport_from_collection(year, company)
                if success:
                    logger.info("Cheque report deleted successfully")
                else:
                    logger.warning("Cheque report deletion failed")
                return success
            except Exception as e:
                logger.error(f"Failed to delete cheque report: {e}", exc_info=True)
                return False
