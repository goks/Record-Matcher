# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys
import json
import threading
import dateutil.parser
import atexit
from concurrent.futures import ThreadPoolExecutor
import weakref
import logging
import traceback
from typing import Optional, List, Tuple, Dict, Any

from PySide2.QtGui import QGuiApplication, QIcon
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QBitArray, QObject, SIGNAL, Slot, Signal, Property, QDate

import core as C
from core import TableOperations, TableSnapshot, InfiChequeStatement
from core import TableSnapshotCollection

# Import new architecture components
from services import (
    StateManagementService,
    FileOperationService,
    TablePopulationService,
    SearchService,
    SyncService,
    ChequeReportService
)
from repositories import (
    PickleSnapshotRepository,
    PickleChequeReportRepository,
    JsonConfigRepository,
    get_snapshot_repository,  # Factory function for SQLite/pickle auto-selection
    get_cheque_report_repository  # Factory function for SQLite/pickle auto-selection
)
from models import (
    ApplicationState,
    UIDisplayData,
    ValidationResult,
    SearchResult
)

# Import memory optimization utilities
from memory_optimizer import (
    Paginator,
    LazyDataLoader,
    WeakValueCache,
    managed_excel_workbook,
    clear_large_objects,
    format_table_generator
)

# Import UI/UX optimization utilities
from ui_optimizer import (
    SignalBatcher,
    PropertyUpdateBatcher,
    BindingOptimizer,
    UIPerformanceMonitor,
    UIOptimizationMixin
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('record_matcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Custom exception classes for better error handling
class ValidationError(Exception):
    """Raised when validation fails."""
    pass

class FileOperationError(Exception):
    """Raised when file operations fail."""
    pass

class SnapshotError(Exception):
    """Raised when snapshot operations fail."""
    pass

class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass

# Validation error messages
VALIDATION_ERRORS = {
    1: "Company and year must be selected",
    2: "Failed to save cheque report to collection",
    3: "Bank and month must be selected for bank statement",
    4: "No table snapshot available for export",
    5: "Invalid file format or corrupted file",
    6: "File not found or inaccessible",
    7: "Export operation failed",
    8: "Data validation failed"
}

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QObject, UIOptimizationMixin):
    """Main application window and controller for Record Matcher.
    
    This class serves as the central controller for the bank statement reconciliation
    application. It manages:
    - User interface state and data bindings (QML integration)
    - File upload/export operations (cheque reports and bank statements)
    - Table data population and search functionality
    - Firebase database synchronization
    - Thread pool management for background operations
    - Application lifecycle and cleanup
    
    The class uses PySide2's Signal/Slot mechanism to communicate with the QML UI
    and employs threading for long-running operations to maintain UI responsiveness.
    
    Thread Safety:
        Uses three locks for protecting shared state:
        - _state_lock: Protects selection state (month, year, bank, company)
        - _snapshot_lock: Protects table snapshot data
        - _data_lock: Protects UI display data
    
    Attributes:
        hdfcBankChequeStatement: HDFC bank statement processor
        iciciBankChequeStatement: ICICI bank statement processor
        tableOperations: Core table operations handler
        tableSnapshot: Current table snapshot being worked on
        current_month/year/bank/company: Current user selections
        chequeReportActivated: Whether in cheque report mode
        _thread_pool: ThreadPoolExecutor for background operations
    
    Signals:
        Various Qt signals for UI communication (see individual signal definitions)
    """
    def __init__(self):
        QObject.__init__(self)
        UIOptimizationMixin.init_ui_optimization(self)
        
        # Legacy components (kept for backward compatibility during migration)
        self.hdfcBankChequeStatement = C.HDFCBankChequeStatement()
        self.iciciBankChequeStatement = C.ICICIBankChequeStatement() 
        self.tableOperations = C.TableOperations()
        
        # Initialize repositories
        # Automatically uses SQLite if available, falls back to pickle
        # This provides better performance and data integrity with zero code changes
        self.snapshot_repository = get_snapshot_repository()  # SQLite > pickle
        self.cheque_repository = get_cheque_report_repository()  # SQLite > pickle
        self.config_repository = JsonConfigRepository(os.path.join(CURRENT_DIR, "data.json"))
        
        # Initialize services
        self.state_service = StateManagementService()
        self.file_service = FileOperationService(self.tableOperations)
        self.table_service = TablePopulationService(self.tableOperations, self.snapshot_repository)
        self.search_service = SearchService(self.tableOperations)
        self.sync_service = SyncService(self.tableOperations)
        self.cheque_service = ChequeReportService(self.tableOperations, self.cheque_repository)
        
        # Snapshot data (legacy - still needed for some operations)
        self.tableSnapshot = None
        self.masterDisplayTableData = list()
        self.infiChequeStatement = None
        
        # UI display state - NOW MANAGED BY STATE_SERVICE
        # Access via: state_service.get_table_data(), state_service.get_selected_rows(), etc.
        self.populate_left_menu(True)
        self._header = self.tableOperations.get_header()
        
        # Progress indicators (not in state service - UI specific)
        self._progressBarValue = 0.0
        self._fullScreenLoadingInfo1 = ''
        self._fullScreenLoadingInfo2 = ''
        
        # Temporary state for backward compatibility - REMOVE these after full migration
        # These should be accessed via state_service.get_state() instead
        self.current_month = ''  # USE: state_service.get_state().current_month
        self.current_bank = ''   # USE: state_service.get_state().current_bank
        self.current_year = ''   # USE: state_service.get_state().current_year
        self.current_company = '' # USE: state_service.get_state().current_company
        self.chequeReportActivated  = False  # USE: state_service.get_state().cheque_report_activated
        self.searchModeOffFirsttime = False  # USE: state_service.get_state().search_mode_off_first_time
        self.tallyExportBoxActivated = False
        
        # Thread lifecycle management
        self._thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="MainWindow")
        self._active_futures = weakref.WeakSet()
        self._shutdown_lock = threading.Lock()
        self._is_shutting_down = False
        
        # Thread synchronization locks for shared state
        self._state_lock = threading.Lock()  # Protects current_month, current_year, current_bank, current_company
        self._snapshot_lock = threading.Lock()  # Protects tableSnapshot and masterDisplayTableData
        self._data_lock = threading.Lock()  # Protects _tableData, _creditBal, _debitBal
        
        # Register cleanup on exit
        atexit.register(self._cleanup_threads)
        
        logger.info("MainWindow initialized with service layer architecture")
        return
    
    def _sync_state_to_service(self) -> None:
        """Synchronize current state to StateManagementService.
        
        This helper method updates the service layer with current UI state.
        Used during initialization and when state changes.
        """
        with self._state_lock:
            self.state_service.update_month(self.current_month)
            self.state_service.update_year(self.current_year)
            self.state_service.update_bank(self.current_bank)
            self.state_service.update_company(self.current_company)
            self.state_service.set_cheque_report_mode(self.chequeReportActivated)
            self.state_service.set_tally_export_mode(self.tallyExportBoxActivated)
    
    def _sync_state_from_service(self) -> None:
        """Synchronize state from StateManagementService to local variables.
        
        This helper method retrieves state from service layer and updates UI state.
        Used when we want to ensure UI reflects service layer state.
        """
        state = self.state_service.get_state()
        with self._state_lock:
            self.current_month = state.current_month
            self.current_year = state.current_year
            self.current_bank = state.current_bank
            self.current_company = state.current_company
            self.chequeReportActivated = state.cheque_report_activated
            self.tallyExportBoxActivated = state.tally_export_activated
    
    def _thread_exception_wrapper(self, func, operation_name):
        """Wrapper to handle exceptions in threaded operations."""
        def wrapper(*args, **kwargs):
            try:
                logger.debug(f"Starting threaded operation: {operation_name}")
                result = func(*args, **kwargs)
                logger.debug(f"Completed threaded operation: {operation_name}")
                return result
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                stack_trace = traceback.format_exc()
                logger.error(f"Thread operation '{operation_name}' failed: {error_msg}")
                logger.error(f"Stack trace:\n{stack_trace}")
                # Emit signal to notify UI of error
                self.threadExceptionOccurred.emit(operation_name, error_msg)
                raise  # Re-raise to ensure thread pool tracks the failure
        return wrapper
    
    def populate_left_menu(self, first_time: bool = False) -> None:
        """Populate left menu with company, bank, year, and month data.
        
        Args:
            first_time: Whether this is the first time populating the menu
        """
        json_path = os.path.join(CURRENT_DIR, "data.json")
        with open(json_path) as f:
            data = json.load(f)
        self._monthDict = data['Months']    
        self._yearDict = data['Years']    
        self._bankDict = data['Banks'] 
        self._companyDict = data['Companies']
        self._adminPassword = data['AdminPassword']  
        if not first_time:
            self.monthDict_changed.emit()
            self.yearDict_changed.emit()
            self.bankDict_changed.emit()
            self.companyDict_changed.emit()
            self.adminPassword_changed.emit()
        return

    # Signal for thread exceptions
    threadExceptionOccurred = Signal(str, str, arguments=['operation', 'error'])
    
    chequeReportsButtonClicked = Signal(bool,int,str, arguments=['selected','status','time'])
    tallyExportButtonClicked = Signal(bool, arguments=['selected'])
    showTablePage = Signal()
    showUploadBankStatementPage = Signal()
    showChooseOptionsPage = Signal()
    validationError = Signal(int, arguments=['type'])
    dayBookExportHandlingError = Signal(int,str, arguments=['type', 'data'])
    checkReportUploadSuccess = Signal()
    showChequeReportPage = Signal(int,str, arguments=['status','time'])
    showTallyExportPage = Signal()
    bankStatementUploadSuccess = Signal()
    statementExportSuccess = Signal()
    snapshotDeleteSuccess = Signal()
    snapshotDeleteFail = Signal()
    chequeReportDeleteSuccess = Signal()
    chequeReportDeleteFail = Signal()
    fullScreenLoadingStart = Signal()
    fullScreenLoadingEnd = Signal()
    fullScreenLoading2Start = Signal()
    fullScreenLoading2End = Signal()
    showMainScreenLoadingIndicator = Signal()
    hideMainScreenLoadingIndicator = Signal()
    
    def save_snapshot(self) -> None:
        """Save current table snapshot to persistent storage.
        
        Raises:
            SnapshotError: If snapshot save fails
        """
        """Save current snapshot with lock protection."""
        with self._snapshot_lock:
            snapshot = self.tableSnapshot
            selected_rows = self._selectedRows.copy() if self._selectedRows else []
        
        if snapshot:
            logger.info(f"Saving snapshot with {len(selected_rows)} selected rows")
            try:
                snapshot.set_master_selected_rows(selected_rows)
                self.tableOperations.save_snapshot_to_table(snapshot)
                logger.debug("Snapshot saved successfully")
            except Exception as e:
                logger.error(f"Failed to save snapshot: {e}")
                logger.error(traceback.format_exc())
                raise SnapshotError(f"Snapshot save failed: {e}") from e
        else:
            logger.debug("No snapshot to save")   

    @Slot()
    def delete_table(self):
        if not self.chequeReportActivated:
            if not self.tableSnapshot:
                self.snapshotDeleteFail.emit()
                return
            self.tableSnapshot = None
            if self.tableOperations.delete_table_from_collection(self.current_month, self.current_year, self.current_bank, self.current_company):
                self.snapshotDeleteSuccess.emit()
                self.populate_table()
            else:
                self.snapshotDeleteFail.emit()
            return
        if not self.infiChequeStatement:     
            self.chequeReportDeleteFail.emit()
            return
        self.infiChequeStatement = None  
        if self.tableOperations.delete_chequeReport_from_collection(self.current_year, self.current_company):
            self.chequeReportDeleteSuccess.emit()
            status, data = self.populateChequeReports()
            self.showChequeReportPage.emit(status, data ) 
        else: 
            self.chequeReportDeleteFail.emit()    
    @Slot(str)
    def uploadFile(self, fileUrl: str) -> None:
        """Upload file (cheque report or bank statement) for processing.
        
        Args:
            fileUrl: File URL from QML (format: file:///path/to/file)
        """
        # Sync current UI state to service
        self._sync_state_to_service()
        
        # Validate state using service layer
        validation_result = self.state_service.validate_for_upload()
        if not validation_result.is_valid:
            error_code = validation_result.error_code or 1
            logger.warning(f"Upload validation failed: {validation_result.error_message}")
            self.validationError.emit(error_code)
            return
        
        try:
            fileUrl = fileUrl.split('///')[1]
            logger.info(f"File upload initiated: {fileUrl}")
        except (IndexError, AttributeError) as e:
            logger.error(f"Invalid file URL format: {fileUrl}")
            logger.error(traceback.format_exc())
            self.validationError.emit(6)
            return
        
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.threadedUploadFile, "File Upload")
            future = self._thread_pool.submit(wrapped_func, fileUrl)
            self._active_futures.add(future)
        else:
            logger.warning("Upload rejected: application is shutting down")
        return
    
    def threadedUploadFile(self, fileUrl: str) -> None:
        """Thread worker for file upload with lock protection.
        
        Args:
            fileUrl: Local file path to upload
        """
        with self._state_lock:
            cheque_activated = self.chequeReportActivated
        
        logger.debug(f"Processing file upload: {fileUrl} (cheque_mode={cheque_activated})")
        
        if cheque_activated:
            try:
                if not self.tableOperations.save_chequeReport_to_collection(fileUrl):
                    error_msg = VALIDATION_ERRORS.get(2, "Cheque report save failed")
                    logger.error(f"Cheque report upload failed: {error_msg}")
                    self.validationError.emit(2)
                else:
                    logger.info("Cheque report uploaded successfully")
                    self.checkReportUploadSuccess.emit()
            except Exception as e:
                logger.error(f"Exception during cheque report upload: {e}")
                logger.error(traceback.format_exc())
                self.validationError.emit(2)
            return
        
        # Add snapshot to table (may modify shared state)
        try:
            success, status_code = self.tableOperations.add_snapshot_to_table(fileUrl)
            if not success:
                error_msg = VALIDATION_ERRORS.get(status_code, f"Upload failed with code {status_code}")
                logger.error(f"File upload failed: {error_msg} (code: {status_code})")
                self.validationError.emit(status_code)
            else:
                logger.info(f"Bank statement uploaded successfully: {fileUrl}")
                self.bankStatementUploadSuccess.emit()
        except Exception as e:
            logger.error(f"Exception during bank statement upload: {e}")
            logger.error(traceback.format_exc())
            self.validationError.emit(5)
        return
    @Slot(str)
    def exportFile(self, fileURL: str) -> None:
        """Export current table snapshot to Excel file.
        
        Args:
            fileURL: Destination file URL from QML
        """
        # Validate snapshot exists
        validation_result = self.state_service.validate_for_export()
        if not validation_result.is_valid:
            error_code = validation_result.error_code or 4
            logger.error(f"Export failed: {validation_result.error_message}")
            self.validationError.emit(error_code)
            return
        
        with self._snapshot_lock:
            # Create a reference to current snapshot
            snapshot = self.tableSnapshot
        
        try:     
            fileURL = fileURL.split('///')[1]
            logger.debug(f"Parsed file URL: {fileURL}")
        except (IndexError, AttributeError) as e:
            logger.warning(f"Failed to parse file URL, using as-is: {e}")
            # fileURL remains unchanged
        
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.threadedExportFile, "File Export")
            future = self._thread_pool.submit(wrapped_func, fileURL, snapshot)
            self._active_futures.add(future)
            logger.info(f"Export task submitted for file: {fileURL}")
        return    
    def threadedExportFile(self, fileURL, snapshot):
        """Thread worker for file export with lock protection."""
        logger.debug(f"Exporting to file: {fileURL}")
        try:
            status, status_code = self.tableOperations.export_to_excel(fileURL, snapshot)
            if not status:
                error_msg = VALIDATION_ERRORS.get(status_code, f"Export failed with code {status_code}")
                logger.error(f"File export failed: {error_msg} (code: {status_code})")
                self.validationError.emit(status_code)
            else:
                logger.info(f"File exported successfully: {fileURL}")
                self.statementExportSuccess.emit()
        except Exception as e:
            logger.error(f"Exception during file export: {e}")
            logger.error(traceback.format_exc())
            self.validationError.emit(7)
        return  

    @Slot(str, str, str, str)
    def createIntermediateDaybook(self, daybookURL, fromDate, toDate, company):
        logger.info(f"Creating intermediate daybook - From: {fromDate}, To: {toDate}, Company: {company}")
        logger.debug(f"Daybook URL: {daybookURL}")
        
        try:
            status, code = self.tableOperations.validateIntermediateDaybook(daybookURL, fromDate, toDate, company)
            logger.debug(f"Validation result: status={status}, code={code}")
            
            if not status:
                logger.warning(f"Daybook validation failed with code: {code}")
                self.dayBookExportHandlingError.emit(code, '')            
                return
            
            status, code, data = self.tableOperations.generateIntermediateDaybook()
            if not status:
                logger.error(f"Daybook generation failed - Code: {code}, Data: {data}")
                self.dayBookExportHandlingError.emit(code, data)
            else:
                logger.info("Intermediate daybook created successfully")
        except Exception as e:
            logger.error(f"Exception during daybook creation: {e}")
            logger.error(traceback.format_exc())
            self.dayBookExportHandlingError.emit(99, str(e))

    @Slot(list)
    def createTallyXMLVoucher(self, propertyArray: List[Any]) -> None:
        """Generate Tally-compatible XML voucher file from daybook data.
        
        Creates an XML file that can be directly imported into Tally accounting software.
        The XML follows Tally's voucher import format specification.
        
        Args:
            propertyArray: Array containing [fileURL, fromDate, toDate, company]
                - fileURL: Output XML file path
                - fromDate: Start date for voucher generation
                - toDate: End date for voucher generation
                - company: Company name for vouchers
        
        The XML includes:
        - Voucher headers (type, date, number)
        - Ledger entries (account names, amounts)
        - Narration and reference details
        """
        logger.info(f"Creating Tally XML voucher with {len(propertyArray)} properties")
        logger.debug(f"Properties: {propertyArray}")
        try:
            # Implementation pending
            logger.warning("Tally XML voucher creation not yet implemented")
        except Exception as e:
            logger.error(f"Tally XML creation failed: {e}")
            logger.error(traceback.format_exc())        

    def populate_table(self):
        self.showMainScreenLoadingIndicator.emit()
        
        # Sync state and validate using service layer
        self._sync_state_to_service()
        validation_result = self.state_service.validate_for_populate_table()
        
        if not validation_result.is_valid:
            logger.warning(f"Cannot populate table: {validation_result.error_message}")
            self.showChooseOptionsPage.emit()
            self.hideMainScreenLoadingIndicator.emit()
            return -1
        
        with self._state_lock:
            self.searchModeOffFirsttime = False
        
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.threadedPopulate_table, "Table Population")
            future = self._thread_pool.submit(wrapped_func)
            self._active_futures.add(future)
            logger.info("Table population task submitted")
        else:
            logger.warning("Table population rejected: application is shutting down")
        return 1
    
    def threadedPopulate_table(self):
        """Thread worker for table population with lock protection."""
        try:
            self.save_snapshot()
        except Exception as e:
            logger.warning(f"Failed to save previous snapshot: {e}")
        
        logger.info("Starting table population...")
        
        # Get current state safely
        with self._state_lock:
            month = self.current_month
            year = self.current_year
            bank = self.current_bank
            company = self.current_company
        
        # Load data from collection (may take time, no lock needed)
        try:
            logger.debug(f"Loading table data: {bank}/{company}/{month}/{year}")
            tableSnapshot, masterDisplayTableData, credit_bal, debit_bal, start_date, end_date = \
                self.tableOperations.get_table_from_collection(month, year, bank, company)
        except Exception as e:
            logger.error(f"Failed to load table from collection: {e}")
            logger.error(traceback.format_exc())
            self.showUploadBankStatementPage.emit()
            self.hideMainScreenLoadingIndicator.emit()
            return 0
        
        if not tableSnapshot:
            self.showUploadBankStatementPage.emit()
            logger.info("No table snapshot found in collection")
            self.hideMainScreenLoadingIndicator.emit()
            return 0
        
        logger.debug("Snapshot loaded, updating application state...")
        
        # Update shared state with lock
        try:
            with self._snapshot_lock:
                self.tableSnapshot = tableSnapshot
                self.masterDisplayTableData = masterDisplayTableData
            
            # Update table data in state service (thread-safe)
            self.state_service.update_table_data(masterDisplayTableData, credit_bal, debit_bal)
            
            # OPTIMIZED: Batch signal emissions (reduces UI recalculations)
            with self.batch_properties() as batch:
                batch.queue_signal(self.table_data_changed)
                batch.queue_signal(self.creditBal_changed)
                batch.queue_signal(self.debitBal_changed)
            
            logger.debug(f"Date range: {start_date} to {end_date}")
            # Update date range in state service
            self.state_service.update_date_range(start_date, end_date)
            # Keep QDate objects for backward compatibility
            self._startDateCalendar = QDate(int(start_date.split('/')[0]), int(start_date.split('/')[1]), int(start_date.split('/')[2]))
            self.startDateCalendar_changed.emit()
            self._endDateCalendar = QDate(int(end_date.split('/')[0]), int(end_date.split('/')[1]), int(end_date.split('/')[2]))
            self.endDateCalendar_changed.emit()
            
            # Update selected rows in state service
            selected_rows = tableSnapshot.get_master_selected_rows()
            self.state_service.update_selected_rows(selected_rows)
            # Keep for backward compatibility
            with self._snapshot_lock:
                self._selectedRows = selected_rows
            self.selectedRows_changed.emit()
            
            self.showTablePage.emit()
            self.hideMainScreenLoadingIndicator.emit()
            logger.info("Table population completed successfully")
            return 1
        except Exception as e:
            logger.error(f"Failed to update UI state: {e}")
            logger.error(traceback.format_exc())
            self.hideMainScreenLoadingIndicator.emit()
            raise

    def callBackFunction_for_Updating_fullScreenLoading(self, text1, text2, prograssbarVal):
        self._fullScreenLoadingInfo1 = text1
        self._fullScreenLoadingInfo2 = text2
        self._progressBarValue = prograssbarVal
        self.fullScreenLoadingInfo1_changed.emit()
        self.fullScreenLoadingInfo2_changed.emit()
        self.progressBarValue_changed.emit()
        return

    def populateChequeReports(self) -> Tuple[int, str]:
        """Get list of available cheque reports using cheque service.
        
        Returns:
            Tuple of (status_code, json_data_string)
        """
        # Sync and validate state
        self._sync_state_to_service()
        
        with self._state_lock:
            company = self.current_company
            year = self.current_year
        
        if '' in [company, year]:
            logger.warning("Cannot populate cheque reports: company or year not selected")
            return -1, ''
        
        try:
            self.save_snapshot()
        except Exception as e:
            logger.warning(f"Failed to save snapshot before loading cheque reports: {e}")
        
        logger.info("Loading cheque reports...")
        try:
            # Use cheque service to load report (returns status_code, timestamp)
            status_code, timestamp = self.cheque_service.load_cheque_report(year, company)
            
            # Also get the actual cheque entry for display
            if status_code == 1:
                with self._snapshot_lock:
                    self.infiChequeStatement = self.tableOperations.get_chequeReport_from_collection(year, company)
                logger.info(f"Cheque report loaded successfully (timestamp: {timestamp})")
            elif status_code == 0:
                logger.info("No cheque report found in collection")
            else:
                logger.error("Failed to load cheque report")
            
            return status_code, timestamp
        except Exception as e:
            logger.error(f"Failed to load cheque reports: {e}")
            logger.error(traceback.format_exc())
            return -1, ''
    @Slot(str, str)    
    def search(self, searchQuery, searchMode):
        """Search table data using search service.
        
        Args:
            searchQuery: Search query string
            searchMode: Search mode ('off' to reset, or specific mode)
        """
        logger.debug(f"Search initiated - Query: '{searchQuery}', Mode: {searchMode}")
        
        # Check if we need to repopulate when turning search off
        if searchMode == "off" and self.searchModeOffFirsttime:
            self.populate_table()
            return
        
        self.searchModeOffFirsttime = False
        
        # Validate snapshot exists
        if not self.tableSnapshot:
            logger.warning("Search aborted: no table snapshot available")
            return
        
        try:
            # Use search service
            search_result = self.search_service.search(
                query=searchQuery,
                mode=searchMode,
                master_table=self.tableSnapshot.get_master_table(),
                master_display_data=self.masterDisplayTableData
            )
            
            # Update state service with search results (thread-safe)
            self.state_service.update_table_data(
                search_result.filtered_data,
                search_result.credit_balance,
                search_result.debit_balance
            )
            
            # OPTIMIZED: Batch signal emissions for search results
            with self.batch_properties() as batch:
                batch.queue_signal(self.table_data_changed)
                batch.queue_signal(self.creditBal_changed)
                batch.queue_signal(self.debitBal_changed)
            logger.debug(f"Search completed - Results: {len(search_result.filtered_data)} rows")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            logger.error(traceback.format_exc())
        return
    
    @Slot(bool)
    def showChequeReportsSelection(self, selected):
        status, data = self.populateChequeReports()
        self.chequeReportsButtonClicked.emit(selected, status, data )
    @Slot(bool)
    def showTallyExportBox(self, selected):
        self.tallyExportButtonClicked.emit(selected)
    
    def _cleanup_threads(self):
        """Properly shutdown all managed threads."""
        with self._shutdown_lock:
            if self._is_shutting_down:
                return
            self._is_shutting_down = True
        
        logger.info("Initiating thread pool shutdown...")
        
        # Wait for active futures to complete (with timeout)
        active_count = len(self._active_futures)
        if active_count > 0:
            logger.info(f"Waiting for {active_count} active tasks to complete...")
            # Give threads reasonable time to finish
            import time
            max_wait = 10.0  # seconds
            start_time = time.time()
            
            while len(self._active_futures) > 0 and (time.time() - start_time) < max_wait:
                time.sleep(0.1)
            
            remaining = len(self._active_futures)
            if remaining > 0:
                logger.warning(f"{remaining} tasks did not complete within {max_wait}s timeout")
        
        # Shutdown thread pool gracefully
        try:
            self._thread_pool.shutdown(wait=True, cancel_futures=False)
            logger.info("Thread pool shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during thread pool shutdown: {e}")
            logger.error(traceback.format_exc())
    
    @Slot()
    def beginWindowExitRoutine(self):
        """Enhanced exit routine with proper thread cleanup."""
        logger.info("Application exit routine initiated")
        try:
            self.save_snapshot()
        except Exception as e:
            logger.error(f"Failed to save snapshot during exit: {e}")
            logger.error(traceback.format_exc())
        
        self._cleanup_threads()
        logger.info("Exit routine completed")
    
    @Slot()
    def downloadfromDb(self):
        self.fullScreenLoadingStart.emit()
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.downloadfromDbThreaded, "Firebase Download")
            future = self._thread_pool.submit(wrapped_func)
            self._active_futures.add(future)
            logger.info("Firebase download task submitted")
        else:
            logger.warning("Firebase download rejected: application is shutting down")
    
    def downloadfromDbThreaded(self):
        """Thread worker for Firebase download with exception handling."""
        logger.info("Starting Firebase download operation...")
        try:
            self.tableOperations.get_data_from_firebase_db(self.callBackFunction_for_Updating_fullScreenLoading)
            logger.info("Firebase download completed successfully")
        except Exception as e:
            logger.error(f"Firebase download failed: {e}")
            logger.error(traceback.format_exc())
            raise DatabaseError(f"Firebase download failed: {e}") from e
        finally:
            self.fullScreenLoadingEnd.emit()
        return    
    
    @Slot()
    def uploadtoDb(self):
        self.fullScreenLoadingStart.emit()
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.uploadtoDbThreaded, "Firebase Upload")
            future = self._thread_pool.submit(wrapped_func)
            self._active_futures.add(future)
            logger.info("Firebase upload task submitted")
        else:
            logger.warning("Firebase upload rejected: application is shutting down")
    
    def uploadtoDbThreaded(self):
        """Thread worker for Firebase upload with exception handling."""
        logger.info("Starting Firebase upload operation...")
        try:
            self.tableOperations.upload_data_to_firebase_db(self.callBackFunction_for_Updating_fullScreenLoading)
            logger.info("Firebase upload completed successfully")
        except Exception as e:
            logger.error(f"Firebase upload failed: {e}")
            logger.error(traceback.format_exc())
            raise DatabaseError(f"Firebase upload failed: {e}") from e
        finally:
            self.fullScreenLoadingEnd.emit()
        return
    @Slot()
    def createTallyXMLFromDaybook(self):
        self.fullScreenLoading2Start.emit()
        print("Create TALLY XML here")


    @Slot(str, str)
    def companyChanged(self, companyname, screenName):
        """Handle company selection change.
        
        Args:
            companyname: Selected company name
            screenName: Screen name for display
        """
        # Update service layer state
        self.state_service.update_company(companyname)
        # Sync back to UI state
        self._sync_state_from_service()
        
        with self._state_lock:
            self._companyData = screenName
            cheque_activated = self.chequeReportActivated
            tally_activated = self.tallyExportBoxActivated
        
        self.companyData_changed.emit()
        
        if cheque_activated:
            status, data = self.populateChequeReports()
            self.showChequeReportPage.emit(status, data)
            return
        elif tally_activated:
            self.showTallyExportBox.emit()
            return
        
        self.populate_table()
    @Slot(str, str)
    def bankChanged(self, bankname, screenName):
        """Handle bank selection change.
        
        Args:
            bankname: Selected bank name
            screenName: Screen name for display
        """
        # Update service layer state
        self.state_service.update_bank(bankname)
        # Sync back to UI state
        self._sync_state_from_service()
        
        with self._state_lock:
            self._bankData = screenName
        self.bankData_changed.emit()
        self.populate_table()
    @Slot(str)
    def yearChanged(self, year):
        """Handle year selection change.
        
        Args:
            year: Selected year
        """
        # Update service layer state
        self.state_service.update_year(year)
        # Sync back to UI state
        self._sync_state_from_service()
        
        with self._state_lock:
            cheque_activated = self.chequeReportActivated
            tally_activated = self.tallyExportBoxActivated
        
        self.update_monthYearData()
        
        if cheque_activated:
            status, data = self.populateChequeReports()
            self.showChequeReportPage.emit(status, data)
            return
        elif tally_activated:
            self.showTallyExportBox.emit()
            return
        
        self.populate_table()
    @Slot(str, str)
    def monthChanged(self, month, screenNane):
        """Handle month selection change.
        
        Args:
            month: Selected month name
            screenNane: Screen name for display
        """
        # Update service layer state
        self.state_service.update_month(month)
        # Sync back to UI state
        self._sync_state_from_service()
        
        self.update_monthYearData()
        self.populate_table()
    def update_monthYearData(self):
        with self._state_lock:
            cheque_activated = self.chequeReportActivated
            current_year = self.current_year
            current_month = self.current_month
        
        if cheque_activated:
            if current_year:
                self._monthYearData = f"{current_year} - {int(current_year)+1}"
            else:
                self._monthYearData = ''
        else:
            self._monthYearData = f"{current_month.capitalize()} {current_year}"
        
        self.monthYearData_changed.emit()
    @Slot(list)
    def selectedRowsChanged(self, updatedRows):
        self._selectedRows = updatedRows
    @Slot(bool)
    def setChequeReportActivated(self,status):
        self.chequeReportActivated = status
        self.update_monthYearData()
        print("STATUS: ",status)
    @Slot(bool)
    def setTallyExportBoxActivated(self,status):
        self.tallyExportBoxActivated = status
        print("STATUS: ",status)    
    @Slot()
    def call_populate_table(self):
        self.populate_table()    
    

    @Signal
    def monthDict_changed(self):
        pass
    def get_monthDict(self):
        return self._monthDict 
    @Signal       
    def yearDict_changed(self):
        pass
    def get_yearDict(self):
        return self._yearDict 
    @Signal    
    def bankDict_changed(self):
        pass
    def get_bankDict(self):
        return self._bankDict 
    @Signal
    def companyDict_changed(self):
        pass
    def get_companyDict(self):
        return self._companyDict
    @Signal
    def table_data_changed(self):
        print('table_data_changed')
        return
    def get_table_data(self):
        """Get table data from state service."""
        table_data, _, _ = self.state_service.get_table_data()
        return table_data 
    @Signal
    def creditBal_changed(self):
        print('creditBal_changed')
        return
    def get_creditBal(self):
        """Get credit balance from state service."""
        _, credit_bal, _ = self.state_service.get_table_data()
        return credit_bal
    @Signal
    def debitBal_changed(self):
        print('debitBal_changed')
        return
    def get_debitBal(self):
        """Get debit balance from state service."""
        _, _, debit_bal = self.state_service.get_table_data()
        return debit_bal         
    @Signal
    def header_changed(self):
        print('header_changed')
        return
    def get_header(self):
        return self._header    
    @Signal
    def monthYearData_changed(self):
        print('monthYearData_changed')
        return
    def get_monthYearData(self):
        return self._monthYearData
    @Signal
    def companyData_changed(self):
        print('companyData_changed')
        return
    def get_companyData(self):
        return self._companyData 
    @Signal
    def bankData_changed(self):
        print('bankData_changed')
        return
    def get_bankData(self):
        return self._bankData
    @Signal
    def selectedRows_changed(self):
        print('selectedRows_changed')
        return
    def get_selectedRows(self):
        return self._selectedRows  
    @Signal
    def startDateCalendar_changed(self):
        return
    def get_startDateCalendar(self):
        return self._startDateCalendar  
    @Signal
    def endDateCalendar_changed(self):
        return
    def get_endDateCalendar(self):
        return self._endDateCalendar
    @Signal
    def progressBarValue_changed(self):
        return
    def get_progressBarValue(self):
        return self._progressBarValue
    @Signal
    def fullScreenLoadingInfo1_changed(self):
        return
    def get_fullScreenLoadingInfo1(self):
        return self._fullScreenLoadingInfo1 
    @Signal
    def fullScreenLoadingInfo2_changed(self):
        return
    def get_fullScreenLoadingInfo2(self):
        return self._fullScreenLoadingInfo2  
    @Signal
    def adminPassword_changed(self):
        return
    def get_adminPassword(self):
        return self._adminPassword      


    startDateCalendar = Property(QDate, get_startDateCalendar, notify=startDateCalendar_changed)
    endDateCalendar = Property(QDate, get_endDateCalendar, notify=endDateCalendar_changed)
    companyDict = Property('QVariantList', get_companyDict, notify=companyDict_changed)
    bankDict = Property('QVariantList', get_bankDict, notify=bankDict_changed)
    yearDict = Property('QVariantList', get_yearDict, notify=yearDict_changed)
    monthDict = Property('QVariantList', get_monthDict, notify=monthDict_changed)
    tableData = Property('QVariantList', get_table_data, notify=table_data_changed)
    creditBal = Property(str, get_creditBal, notify=creditBal_changed)
    debitBal = Property(str, get_debitBal, notify=debitBal_changed)
    header = Property('QVariantList', get_header, notify=header_changed)
    monthYearData = Property(str, get_monthYearData, notify=monthYearData_changed)
    companyData = Property(str, get_companyData, notify=companyData_changed)
    bankData = Property(str, get_bankData, notify=bankData_changed)
    selectedRows = Property('QVariantList', get_selectedRows, notify=selectedRows_changed)
    progressBarValue = Property(float, get_progressBarValue, notify=progressBarValue_changed)
    fullScreenLoadingInfo1 = Property(str, get_fullScreenLoadingInfo1, notify=fullScreenLoadingInfo1_changed)
    fullScreenLoadingInfo2 = Property(str, get_fullScreenLoadingInfo2, notify=fullScreenLoadingInfo2_changed)
    adminPassword = Property(str, get_adminPassword, notify=adminPassword_changed)


class TableBackend(QObject):
    tableRowSelected = Signal(list)

    def __init__(self):
        QObject.__init__(self)
        return
    @Slot(int, list)
    def tableRowSelectedNotify(self, currentRow, selectedRows):
        self.checkedRows = selectedRows
        print("currentRow " , currentRow)
        print('Before: ',self.checkedRows)
        if currentRow in self.checkedRows:
            self.checkedRows.remove(currentRow)
            print('After: ',self.checkedRows)
            self.tableRowSelected.emit(self.checkedRows)
        else:
            self.checkedRows.append(currentRow)
            print('After: ',self.checkedRows)
            self.tableRowSelected.emit(self.checkedRows)

if __name__ == "__main__":

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    # correction for auto-py-to-exe
    try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    logo_path = os.path.join(base_path, 'logo.png')
    app.setWindowIcon(QIcon(logo_path))
    app.setOrganizationName('Neo Productions')
    app.setOrganizationDomain('Fly fly fly')
       
    #Get Context
    main = MainWindow()
    engine.rootContext().setContextProperty("backend", main)

    tableBackend = TableBackend()
    engine.rootContext().setContextProperty("tableBackend", tableBackend)


    #Load QML File
    engine.load(os.fspath(Path(__file__).resolve().parent / "qml/main.qml"))
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec_())
