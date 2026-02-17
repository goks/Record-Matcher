# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys
import json
import math
import threading
import dateutil.parser
import atexit
from concurrent.futures import ThreadPoolExecutor
import weakref
import logging
import traceback
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from urllib.parse import unquote

# Use a non-native Qt Quick Controls style so custom background/contentItem
# overrides in QML controls are supported (avoids Windows style warnings).
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QBitArray, QObject, SIGNAL, Slot, Signal, Property, QDate, QAbstractTableModel, Qt, QModelIndex, QByteArray, QTimer

import core as C
from core import TableOperations, TableSnapshot, InfiChequeStatement
from core import TableSnapshotCollection
import reconcilation_module as RM

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
        self._erpBankMapping = self._load_erp_bank_mapping()
        self._erpBankOptions = {}
        # NOTE: Do NOT set default selections - user must explicitly select options
        # Table will only populate when user selects company, bank, year, and month
        self._header = self.tableOperations.get_header()
        
        # Initialize UI state variables
        self._monthYearData = ''
        self._companyData = ''
        self._bankData = ''
        self._selectedRows = []
        self._startDateCalendar = QDate.currentDate()
        self._endDateCalendar = QDate.currentDate()
        
        # Progress indicators (not in state service - UI specific)
        self._progressBarValue = 0.0
        self._fullScreenLoadingInfo1 = ''
        self._fullScreenLoadingInfo2 = ''
        self._tableAvailable = False
        
        # Firebase sync state (new repository-based sync)
        self._lastSyncUpload = self._load_sync_timestamp('last_sync_upload')
        self._lastSyncDownload = self._load_sync_timestamp('last_sync_download')
        self._reconciliationOutputEnabled = self._load_reconciliation_output_enabled()
        self._isSyncing = False
        self._syncCancelled = False
        
        # Migration state
        self._migrationStatus = "checking"  # checking, pending, in_progress, completed, error
        self._migrationProgressText = ""
        self._migrationCurrent = 0
        self._migrationTotal = 0
        self._pickleSnapshotCount = 0
        self._pickleChequeCount = 0
        self._databasePath = ""
        self._totalSnapshotCount = 0
        self._totalChequeReportCount = 0
        self._isMigrating = False
        
        # Check migration status on startup
        QTimer.singleShot(500, self._check_migration_status)
        
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
        self._skip_snapshot_presave_once = False
        self._populate_request_id = 0
        self._populate_request_lock = threading.Lock()
        self._populate_debounce_timer = QTimer(self)
        self._populate_debounce_timer.setSingleShot(True)
        self._populate_debounce_timer.setInterval(120)
        self._populate_debounce_timer.timeout.connect(self._run_coalesced_populate)
        
        # Thread synchronization locks for shared state
        self._state_lock = threading.Lock()  # Protects current_month, current_year, current_bank, current_company
        self._snapshot_lock = threading.Lock()  # Protects tableSnapshot and masterDisplayTableData
        self._data_lock = threading.Lock()  # Protects _tableData, _creditBal, _debitBal
        
        # Register cleanup on exit
        atexit.register(self._cleanup_threads)
        
        logger.info("MainWindow initialized with service layer architecture")
        # Table model for native Qt6 TableView (exposed to QML)
        self.tableModel = TableModel(self)
        self.tableModelUpdateRequested.connect(self._apply_table_model_update, Qt.QueuedConnection)
        self.progressUpdateRequested.connect(self._apply_progress_update, Qt.QueuedConnection)

        # NOTE: Table data should only be populated when user selects options
        # The StackView will show selectOptionsComponent as initial item
        # Table will be shown only after user selects company, bank, year, month

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

    def _next_populate_request_id(self) -> int:
        with self._populate_request_lock:
            self._populate_request_id += 1
            return self._populate_request_id

    def _is_latest_populate_request(self, request_id: int) -> bool:
        with self._populate_request_lock:
            return request_id == self._populate_request_id

    def request_table_populate(self, immediate: bool = False) -> None:
        """Coalesce rapid populate requests triggered by selection changes."""
        if immediate:
            if self._populate_debounce_timer.isActive():
                self._populate_debounce_timer.stop()
            self._run_coalesced_populate()
            return
        self._populate_debounce_timer.start()

    @Slot()
    def _run_coalesced_populate(self) -> None:
        self.populate_table()
    
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
        if hasattr(self, "_erpBankMapping"):
            self._erpBankMapping = self._load_erp_bank_mapping()
            self.erpBankMapping_changed.emit()
        if not first_time:
            self.monthDict_changed.emit()
            self.yearDict_changed.emit()
            self.bankDict_changed.emit()
            self.companyDict_changed.emit()
            self.adminPassword_changed.emit()
        return

    @Slot(str)
    def addFinancialYear(self, year_value: str) -> None:
        """Add a new financial year to data.json and refresh left menu immediately."""
        year = str(year_value or "").strip()
        if len(year) != 4 or not year.isdigit():
            self.financialYearAddFailed.emit("Enter a valid 4-digit year (e.g., 2026).")
            return

        json_path = os.path.join(CURRENT_DIR, "data.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load data.json for year add: {e}")
            self.financialYearAddFailed.emit("Could not read year configuration.")
            return

        years = data.get("Years", [])
        existing = {
            str(item.get("value", "")).strip()
            for item in years if isinstance(item, dict)
        }
        if year in existing:
            self.financialYearAddFailed.emit(f"Financial year {year} already exists.")
            return

        years.append({"name": year, "value": year})
        years.sort(key=lambda item: int(str(item.get("value", "0"))))
        data["Years"] = years

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save data.json for year add: {e}")
            self.financialYearAddFailed.emit("Could not save year configuration.")
            return

        # Refresh menu and runtime caches so new year is usable immediately.
        try:
            C.JsonDataLoader.clear_cache()
            self.populate_left_menu(first_time=False)
            if hasattr(self.tableOperations, "storageManager"):
                sm = self.tableOperations.storageManager
                if hasattr(sm, "tableSnapshotCollection") and year not in sm.tableSnapshotCollection.years:
                    sm.tableSnapshotCollection.years.append(year)
                if hasattr(sm, "chequeReportCollection") and year not in sm.chequeReportCollection.years:
                    sm.chequeReportCollection.years.append(year)
            logger.info(f"Financial year added: {year}")
            self.financialYearAdded.emit(year)
        except Exception as e:
            logger.warning(f"Year added but runtime refresh had warnings: {e}")
            self.financialYearAdded.emit(year)

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
    reconciliationSuccess = Signal(str, arguments=['outputPath'])
    reconciliationFailed = Signal(str, arguments=['error'])
    statementExportSuccess = Signal()
    snapshotDeleteSuccess = Signal()
    snapshotDeleteFail = Signal()
    chequeReportDeleteSuccess = Signal()
    chequeReportDeleteFail = Signal()
    financialYearAdded = Signal(str, arguments=['year'])
    financialYearAddFailed = Signal(str, arguments=['error'])
    fullScreenLoadingStart = Signal()
    fullScreenLoadingEnd = Signal()
    fullScreenLoading2Start = Signal()
    fullScreenLoading2End = Signal()
    showMainScreenLoadingIndicator = Signal()
    hideMainScreenLoadingIndicator = Signal()
    
    # Firebase sync signals (new repository-based sync)
    syncProgressUpdated = Signal(int, int, str, str, arguments=['current', 'total', 'itemName', 'status'])
    syncCompleted = Signal(bool, str, arguments=['success', 'message'])
    showSettingsPage = Signal()
    erpBankMappingSaved = Signal(str, arguments=['message'])
    erpBankMappingSaveFailed = Signal(str, arguments=['error'])
    reconciliationOutputEnabled_changed = Signal()
    lastSyncUpload_changed = Signal()
    lastSyncDownload_changed = Signal()
    isSyncing_changed = Signal()
    
    # Migration signals
    migrationStatus_changed = Signal()
    migrationProgressText_changed = Signal()
    migrationCurrent_changed = Signal()
    migrationTotal_changed = Signal()
    pickleSnapshotCount_changed = Signal()
    pickleChequeCount_changed = Signal()
    databasePath_changed = Signal()
    totalSnapshotCount_changed = Signal()
    totalChequeReportCount_changed = Signal()
    tableModelUpdateRequested = Signal(object, object)
    progressUpdateRequested = Signal(float, str, str)
    
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
            logger.info(f"Saving snapshot with {len(selected_rows)} selected rows to SQLite")
            try:
                snapshot.set_master_selected_rows(selected_rows)
                # Save to SQLite repository
                success, error_code = self.snapshot_repository.save(snapshot)
                if success:
                    logger.debug("Snapshot saved to SQLite successfully")
                else:
                    logger.error(f"Failed to save snapshot to SQLite: error code {error_code}")
                    raise SnapshotError(f"Snapshot save failed with error code: {error_code}")
            except SnapshotError:
                raise
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
            # Delete from SQLite repository
            if self.snapshot_repository.delete(self.current_month, self.current_year, self.current_bank, self.current_company):
                logger.info(f"Snapshot deleted from SQLite: {self.current_company}/{self.current_year}/{self.current_month}/{self.current_bank}")
                self.snapshotDeleteSuccess.emit()
                self.populate_table()
            else:
                logger.error("Failed to delete snapshot from SQLite")
                self.snapshotDeleteFail.emit()
            return
        if not self.infiChequeStatement:     
            self.chequeReportDeleteFail.emit()
            return
        self.infiChequeStatement = None  
        # Delete cheque report from SQLite repository
        if self.cheque_repository.delete(self.current_year, self.current_company):
            logger.info(f"Cheque report deleted from SQLite: {self.current_company}/{self.current_year}")
            self.chequeReportDeleteSuccess.emit()
            status, data = self.populateChequeReports()
            self.showChequeReportPage.emit(status, data ) 
        else:
            logger.error("Failed to delete cheque report from SQLite")
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
            if isinstance(fileUrl, str) and fileUrl.startswith("file:///"):
                fileUrl = unquote(fileUrl.replace("file:///", "", 1))
            fileUrl = str(fileUrl or "").strip()
            if not fileUrl:
                raise ValueError("Empty file URL/path")
            logger.info(f"File upload initiated: {fileUrl}")
        except Exception:
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
                # Parse Excel file and create InfiChequeStatement
                cheque_stmt = InfiChequeStatement()
                if not cheque_stmt.setPath(fileUrl):
                    logger.error(f"Invalid cheque report file path: {fileUrl}")
                    self.validationError.emit(2)
                    return
                
                cheque_stmt.grab_data()
                cheque_stmt.set_year(self.current_year)
                cheque_stmt.set_company(self.current_company)
                
                # Save to SQLite repository
                success, error_code = self.cheque_repository.save(
                    self.current_year, 
                    self.current_company, 
                    cheque_stmt
                )
                
                if not success:
                    error_msg = VALIDATION_ERRORS.get(2, "Cheque report save failed")
                    logger.error(f"Cheque report upload failed: {error_msg} (code: {error_code})")
                    self.validationError.emit(2)
                else:
                    logger.info("Cheque report uploaded to SQLite successfully")
                    self.checkReportUploadSuccess.emit()
            except Exception as e:
                logger.error(f"Exception during cheque report upload: {e}")
                logger.error(traceback.format_exc())
                self.validationError.emit(2)
            return
        
        # Add snapshot to table (processes the bank statement file)
        try:
            with self._state_lock:
                month = str(self.current_month or "").strip()
                year = str(self.current_year or "").strip()
                bank = str(self.current_bank or "").strip()
                company = str(self.current_company or "").strip()

            # Guard against invalid/null selection state to prevent deep-core crashes.
            if not all([month, year, bank, company]):
                logger.warning(
                    "Upload blocked: missing selection context (company=%s, bank=%s, year=%s, month=%s)",
                    company, bank, year, month
                )
                self.validationError.emit(3)
                return

            if not year.isdigit():
                logger.warning("Upload blocked: invalid year value '%s'", year)
                self.validationError.emit(3)
                return

            # Set operation context explicitly for backward-compatible core API.
            self.tableOperations.month = month
            self.tableOperations.year = year
            self.tableOperations.bank = bank
            self.tableOperations.company = company

            success, status_code = self.tableOperations.add_snapshot_to_table(fileUrl)
            if not success:
                error_msg = VALIDATION_ERRORS.get(status_code, f"Upload failed with code {status_code}")
                logger.error(f"File upload failed: {error_msg} (code: {status_code})")
                self.validationError.emit(status_code)
            else:
                # Get the created snapshot from tableOperations and save to SQLite
                # Retrieve the snapshot that was just created (stored in tableOperations.storageManager)
                snapshot = self.tableOperations.storageManager.get_table_snapshot(month, year, bank, company)
                if snapshot:
                    # Save to SQLite repository
                    sqlite_success, sqlite_error = self.snapshot_repository.save(snapshot)
                    if sqlite_success:
                        logger.info(f"Bank statement uploaded and saved to SQLite: {fileUrl}")
                    else:
                        logger.warning(f"Bank statement uploaded but SQLite save failed: {sqlite_error}")
                else:
                    logger.warning("Bank statement processed but snapshot not found for SQLite save")
                
                self.bankStatementUploadSuccess.emit()
        except Exception as e:
            logger.error(f"Exception during bank statement upload: {e}")
            logger.error(traceback.format_exc())
            self.validationError.emit(5)
        return

    @Slot()
    def runReconciliation(self) -> None:
        """Run reconciliation based on selected scope.

        Scope resolution:
        - company + year only: all banks, all months in FY
        - company + year + bank: selected bank, all months in FY
        - company + year + bank + month: selected bank + selected month
        """
        logger.debug("runReconciliation() called from UI")
        self.showMainScreenLoadingIndicator.emit()
        self._sync_state_to_service()
        with self._state_lock:
            month = self.current_month
            year = self.current_year
            bank = self.current_bank
            company = self.current_company
            logger.debug(
                "Current reconciliation selection: company=%s, year=%s, month=%s, bank=%s",
                company,
                year,
                month,
                bank,
            )

        if not company or not year:
            logger.warning("Reconciliation validation failed: company/year not selected")
            self.validationError.emit(1)
            self.hideMainScreenLoadingIndicator.emit()
            return

        if month and not bank:
            msg = "Select a bank before reconciling a specific month."
            logger.warning(msg)
            self.reconciliationFailed.emit(msg)
            self.hideMainScreenLoadingIndicator.emit()
            return

        targets = self._get_reconciliation_targets(company, year, bank, month)
        if not targets:
            msg = f"No saved bank statements found for selected scope ({company}/{year})."
            logger.warning(msg)
            self.reconciliationFailed.emit(msg)
            self.hideMainScreenLoadingIndicator.emit()
            return

        self._set_reconciliation_progress(
            0.01,
            "Reconciliation started",
            f"Queued 0/{len(targets)} batches",
        )

        if not self._is_shutting_down:
            logger.debug("Submitting reconciliation job to thread pool")
            wrapped_func = self._thread_exception_wrapper(
                lambda: self.threadedRunReconciliation(targets),
                "Run Reconciliation"
            )
            future = self._thread_pool.submit(wrapped_func)
            self._active_futures.add(future)
        else:
            logger.warning("Reconciliation rejected: application is shutting down")
            logger.debug("Reconciliation blocked: application shutting down")
            self.hideMainScreenLoadingIndicator.emit()

    def threadedRunReconciliation(self, targets: List[Tuple[str, str, str, str]]) -> None:
        """Thread worker for scope-based reconciliation."""
        logger.debug("threadedRunReconciliation() started with %s targets", len(targets))
        try:
            bank_mapping = self._get_erp_bank_mapping_by_company()
            output_dir = os.path.join(CURRENT_DIR, "output")
            total_batches = len(targets)
            success_batches = 0
            failed_batches: List[str] = []
            total_rows = 0
            matched_rows = 0
            unmatched_rows = 0
            last_output_file = ""
            last_updated_snapshot_obj = None

            for idx, (month, year, bank, company) in enumerate(targets, start=1):
                self._set_reconciliation_progress(
                    (idx - 1) / total_batches,
                    "Reconciling statements",
                    f"{idx}/{total_batches} | {company.upper()} | {bank.upper()} | {month.title()} {year}",
                )

                snapshot_dict = self.snapshot_repository.load(month, year, bank, company)
                if not snapshot_dict:
                    failed_batches.append(f"{company}/{year}/{month}/{bank}: snapshot missing")
                    continue

                try:
                    result = RM.run_reconciliation_from_snapshot(
                        snapshot_dict,
                        output_dir=output_dir,
                        bank_mapping=bank_mapping,
                        write_output=self._reconciliationOutputEnabled
                    )
                    updated_snapshot_data = result.get("updated_snapshot_data", snapshot_dict)
                    updated_snapshot_obj = TableSnapshot(updated_snapshot_data)
                    save_ok, save_code = self.snapshot_repository.save(updated_snapshot_obj)
                    if not save_ok:
                        failed_batches.append(f"{company}/{year}/{month}/{bank}: save failed ({save_code})")
                        continue

                    success_batches += 1
                    total_rows += int(result.get("total_rows", 0) or 0)
                    matched_rows += int(result.get("matched_rows", 0) or 0)
                    unmatched_rows += int(result.get("unmatched_rows", 0) or 0)
                    last_output_file = result.get("output_file", "") or last_output_file
                    last_updated_snapshot_obj = updated_snapshot_obj
                except Exception as batch_ex:
                    failed_batches.append(f"{company}/{year}/{month}/{bank}: {batch_ex}")
                    logger.error(f"Reconciliation batch failed for {company}/{year}/{month}/{bank}: {batch_ex}")
                    logger.error(traceback.format_exc())
                    continue

                self._set_reconciliation_progress(
                    idx / total_batches,
                    "Reconciling statements",
                    f"Completed {idx}/{total_batches} batches",
                )

            if success_batches == 0:
                msg = "Reconciliation failed for all selected statements."
                if failed_batches:
                    msg += f" First error: {failed_batches[0]}"
                self.reconciliationFailed.emit(msg)
                return

            # Keep in-memory snapshot aligned with latest persisted item.
            if last_updated_snapshot_obj is not None:
                with self._snapshot_lock:
                    self.tableSnapshot = last_updated_snapshot_obj
                    self._skip_snapshot_presave_once = True

            with self._state_lock:
                current_company = self.current_company
                current_year = self.current_year
                current_bank = self.current_bank
                current_month = self.current_month
                cheque_activated = self.chequeReportActivated

            if all([current_company, current_year, current_bank, current_month]) and not cheque_activated:
                logger.debug("Triggering table reload to show reconciled data")
                self.populate_table()

            last_reconciled = datetime.now().strftime("%d %b %Y, %H:%M")
            summary = (
                f"Reconciliation complete. Last reconciled: {last_reconciled}. "
                f"Batches: {success_batches}/{total_batches}, Matched: {matched_rows}, "
                f"Unmatched: {unmatched_rows}."
            )
            if failed_batches:
                summary += f" Failed batches: {len(failed_batches)}."
            if self._reconciliationOutputEnabled and last_output_file:
                summary += f" Output: {last_output_file}"
            elif not self._reconciliationOutputEnabled:
                summary += " Excel output: disabled in Settings."
            self._set_reconciliation_progress(1.0, "Reconciliation completed", f"{success_batches}/{total_batches} done")
            self.reconciliationSuccess.emit(summary)
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            logger.error(traceback.format_exc())
            logger.debug("Reconciliation exception: %s", e)
            self.reconciliationFailed.emit(str(e))
        finally:
            self.hideMainScreenLoadingIndicator.emit()
            self._set_reconciliation_progress(0.0, "", "")

    def _get_reconciliation_targets(
        self,
        company: str,
        year: str,
        bank: str = "",
        month: str = "",
    ) -> List[Tuple[str, str, str, str]]:
        """Resolve reconciliation targets from saved snapshots."""
        all_snapshots = self.snapshot_repository.list_all()
        company_l = company.lower().strip()
        year_s = str(year).strip()
        bank_l = bank.lower().strip()
        month_l = month.lower().strip()

        targets: List[Tuple[str, str, str, str]] = []
        for item in all_snapshots:
            if len(item) != 4:
                continue
            item_month, item_year, item_bank, item_company = item
            if str(item_company).lower().strip() != company_l:
                continue
            if str(item_year).strip() != year_s:
                continue
            if bank_l and str(item_bank).lower().strip() != bank_l:
                continue
            if month_l and str(item_month).lower().strip() != month_l:
                continue
            targets.append((str(item_month), str(item_year), str(item_bank), str(item_company)))

        month_order = {
            "april": 1, "may": 2, "june": 3, "july": 4, "august": 5, "september": 6,
            "october": 7, "november": 8, "december": 9, "january": 10, "february": 11, "march": 12,
        }
        targets.sort(key=lambda t: (t[2], month_order.get(str(t[0]).lower(), 99), t[0]))
        return targets

    def _set_reconciliation_progress(self, progress: float, text1: str, text2: str) -> None:
        """Update shared progress fields used by QML progress UI."""
        progress = max(0.0, min(1.0, float(progress)))
        self.progressUpdateRequested.emit(progress, str(text1), str(text2))

    def _set_table_available(self, available: bool, clear_ui_data: bool = False) -> None:
        """Track whether current selection has a table to display."""
        self._tableAvailable = bool(available)
        if clear_ui_data:
            self.state_service.update_table_data([], '', '')
            # Keep native Qt table model in sync with cleared UI data.
            self._update_table_model(self._header, [])
            self.table_data_changed.emit()
            self.creditBal_changed.emit()
            self.debitBal_changed.emit()
        self.tableAvailable_changed.emit()

    def _update_table_model(self, headers, data) -> None:
        """Queue table model updates on the Qt main thread."""
        self.tableModelUpdateRequested.emit(headers, data)

    @Slot(object, object)
    def _apply_table_model_update(self, headers, data) -> None:
        """Apply queued table model updates (runs in UI thread)."""
        self.tableModel.set_table_data(headers, data)

    @Slot(float, str, str)
    def _apply_progress_update(self, progress: float, text1: str, text2: str) -> None:
        """Apply progress UI state updates on the Qt UI thread."""
        self._progressBarValue = progress
        self._fullScreenLoadingInfo1 = text1
        self._fullScreenLoadingInfo2 = text2
        self.progressBarValue_changed.emit()
        self.fullScreenLoadingInfo1_changed.emit()
        self.fullScreenLoadingInfo2_changed.emit()

    @Slot(str, str, bool)
    def exportFile(self, fileURL: str, export_format: str = "excel", include_highlights: bool = True) -> None:
        """Export current table snapshot to Excel or PDF file.
        
        Args:
            fileURL: Destination file URL from QML
            export_format: Requested output format ("excel" or "pdf")
            include_highlights: Whether selected-row highlights should be exported
        """
        # Validate snapshot exists
        validation_result = self.state_service.validate_for_export(self.tableSnapshot is not None)
        if not validation_result.is_valid:
            error_code = validation_result.error_code or 4
            logger.error(f"Export failed: {validation_result.error_message}")
            self.validationError.emit(error_code)
            return
        
        with self._snapshot_lock:
            # Sync latest UI selection into snapshot before exporting.
            snapshot = self.tableSnapshot
            selected_rows = self._selectedRows.copy() if self._selectedRows else []
            if snapshot:
                try:
                    snapshot.set_master_selected_rows(selected_rows)
                except Exception as e:
                    logger.warning(f"Failed to apply selected rows to snapshot before export: {e}")

        # Persist latest highlights so export reflects current view even before sheet switches.
        if snapshot:
            try:
                save_ok, save_code = self.snapshot_repository.save(snapshot)
                if not save_ok:
                    logger.warning(
                        f"Pre-export snapshot save failed (code={save_code}); proceeding with in-memory snapshot"
                    )
            except Exception as e:
                logger.warning(f"Pre-export snapshot save failed; proceeding with in-memory snapshot: {e}")
        
        try:
            if isinstance(fileURL, str) and fileURL.startswith("file:///"):
                fileURL = unquote(fileURL.replace("file:///", "", 1))
            logger.debug(f"Parsed file URL: {fileURL}")
        except Exception as e:
            logger.warning(f"Failed to parse file URL, using as-is: {e}")

        normalized_format = (export_format or "").strip().lower()
        if normalized_format not in ("excel", "pdf"):
            normalized_format = "pdf" if str(fileURL).lower().endswith(".pdf") else "excel"
        
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.threadedExportFile, "File Export")
            future = self._thread_pool.submit(wrapped_func, fileURL, snapshot, normalized_format, bool(include_highlights))
            self._active_futures.add(future)
            logger.info(
                f"Export task submitted for file: {fileURL} "
                f"(format={normalized_format}, include_highlights={include_highlights})"
            )
        return    
    def threadedExportFile(self, fileURL, snapshot, export_format, include_highlights):
        """Thread worker for file export with lock protection."""
        logger.debug(
            f"Exporting to file: {fileURL} "
            f"(format={export_format}, include_highlights={include_highlights})"
        )
        try:
            if export_format == "pdf":
                status, status_code = self.tableOperations.export_to_pdf(fileURL, snapshot, include_highlights)
            else:
                status, status_code = self.tableOperations.export_to_excel(fileURL, snapshot, include_highlights)
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
        request_id = self._next_populate_request_id()
        self.showMainScreenLoadingIndicator.emit()
        
        # Sync state and validate using service layer
        self._sync_state_to_service()
        validation_result = self.state_service.validate_for_populate_table()
        
        if not validation_result.is_valid:
            logger.warning(f"Cannot populate table: {validation_result.error_message}")
            self._set_table_available(False, clear_ui_data=True)
            self.showChooseOptionsPage.emit()
            self.hideMainScreenLoadingIndicator.emit()
            return -1
        
        with self._state_lock:
            self.searchModeOffFirsttime = False
        
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.threadedPopulate_table, "Table Population")
            future = self._thread_pool.submit(wrapped_func, request_id)
            self._active_futures.add(future)
            logger.info(f"Table population task submitted (request_id={request_id})")
        else:
            logger.warning("Table population rejected: application is shutting down")
        return 1
    
    def threadedPopulate_table(self, request_id: int):
        """Thread worker for table population with lock protection.
        
        OPTIMIZED: Uses pre-calculated values from SQLite storage when available,
        avoiding expensive recalculations on every load.
        """
        if not self._is_latest_populate_request(request_id):
            logger.debug(f"Skipping stale table population request before start: {request_id}")
            return 0
        should_presave = True
        with self._snapshot_lock:
            if self._skip_snapshot_presave_once:
                should_presave = False
                self._skip_snapshot_presave_once = False
        if should_presave:
            try:
                self.save_snapshot()
            except Exception as e:
                logger.warning(f"Failed to save previous snapshot: {e}")
        else:
            logger.debug("Skipping one-time presave (post-reconciliation refresh)")
        
        logger.info("Starting table population...")
        
        # Get current state safely
        with self._state_lock:
            month = self.current_month
            year = self.current_year
            bank = self.current_bank
            company = self.current_company
        
        # Load data from SQLite repository (may take time, no lock needed)
        try:
            logger.debug(f"Loading table data from SQLite: {bank}/{company}/{month}/{year}")
            
            # Load snapshot dictionary from SQLite (repository normalizes values to lowercase)
            # Returns pre-computed values: _credit_bal, _debit_bal, _start_date, _end_date, _display_data
            snapshot_dict = self.snapshot_repository.load(month, year, bank, company)
            
            if not snapshot_dict:
                tableSnapshot = None
                masterDisplayTableData = ''
                credit_bal = ''
                debit_bal = ''
                start_date = ''
                end_date = ''
            else:
                # Reconstruct TableSnapshot from dictionary
                tableSnapshot = TableSnapshot(snapshot_dict)
                
                # OPTIMIZATION: Use pre-calculated values if available
                if '_credit_bal' in snapshot_dict and '_start_date' in snapshot_dict:
                    # Use cached values (fast path)
                    credit_bal = snapshot_dict['_credit_bal']
                    debit_bal = snapshot_dict['_debit_bal']
                    start_date = snapshot_dict['_start_date']
                    end_date = snapshot_dict['_end_date']
                    logger.debug("Using pre-calculated balances/dates from cache")
                else:
                    # Fall back to calculating on the fly (legacy data)
                    master_table = tableSnapshot.get_master_table()
                    credit_bal, debit_bal, start_date, end_date = self.tableOperations.dataProcessor.calculate_balances_and_dates(master_table)
                    logger.debug("Calculated balances/dates (legacy format)")
                
                # OPTIMIZATION: Use pre-formatted display data if available
                if '_display_data' in snapshot_dict:
                    masterDisplayTableData = snapshot_dict['_display_data']
                    logger.debug("Using pre-formatted display data from cache")
                else:
                    # Fall back to formatting on the fly (legacy data)
                    master_table = tableSnapshot.get_master_table()
                    masterDisplayTableData = self.tableOperations.dataProcessor.format_table_data(master_table)
                    logger.debug("Formatted display data (legacy format)")
                
                row_count = snapshot_dict.get('_row_count', len(tableSnapshot.get_master_table()) if tableSnapshot else 0)
                logger.debug(f"Loaded snapshot from SQLite: {row_count} rows")
        except Exception as e:
            logger.error(f"Failed to load table from SQLite: {e}")
            logger.error(traceback.format_exc())
            if not self._is_latest_populate_request(request_id):
                logger.debug(f"Ignoring load failure from stale request: {request_id}")
                return 0
            self._set_table_available(False, clear_ui_data=True)
            self.showUploadBankStatementPage.emit()
            self.hideMainScreenLoadingIndicator.emit()
            return 0
        
        if not tableSnapshot:
            if not self._is_latest_populate_request(request_id):
                logger.debug(f"Ignoring missing snapshot from stale request: {request_id}")
                return 0
            self._set_table_available(False, clear_ui_data=True)
            self.showUploadBankStatementPage.emit()
            logger.info("No table snapshot found in collection")
            self.hideMainScreenLoadingIndicator.emit()
            return 0
        
        logger.debug("Snapshot loaded, updating application state...")
        
        # Update shared state with lock
        try:
            if not self._is_latest_populate_request(request_id):
                logger.debug(f"Skipping stale table population request before UI apply: {request_id}")
                return 0
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
            
            # Update native Qt TableModel used by QML TableView
            try:
                # self._header already set earlier; masterDisplayTableData is list of lists
                self._update_table_model(self._header, masterDisplayTableData)
            except Exception as e:
                logger.debug(f"TableModel update skipped: {e}")
            
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
            self._set_table_available(True)
            self.hideMainScreenLoadingIndicator.emit()
            logger.info("Table population completed successfully")
            return 1
        except Exception as e:
            logger.error(f"Failed to update UI state: {e}")
            logger.error(traceback.format_exc())
            if not self._is_latest_populate_request(request_id):
                logger.debug(f"Ignoring UI apply failure from stale request: {request_id}")
                return 0
            self._set_table_available(False, clear_ui_data=True)
            self.hideMainScreenLoadingIndicator.emit()
            raise

    def callBackFunction_for_Updating_fullScreenLoading(self, text1, text2, prograssbarVal):
        try:
            progress = float(prograssbarVal)
        except Exception:
            progress = 0.0
        progress = max(0.0, min(1.0, progress))
        self.progressUpdateRequested.emit(progress, str(text1), str(text2))
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
            
            # Load the actual cheque report from SQLite repository
            if status_code == 1:
                with self._snapshot_lock:
                    # Load from SQLite repository
                    report_dict = self.cheque_repository.load(year, company)
                    if report_dict:
                        # Reconstruct InfiChequeStatement from dictionary
                        self.infiChequeStatement = InfiChequeStatement()
                        self.infiChequeStatement.entry_list = report_dict.get('entry_list', [])
                        self.infiChequeStatement.year = report_dict.get('year', year)
                        self.infiChequeStatement.company = report_dict.get('company', company)
                        logger.info(f"Cheque report loaded from SQLite successfully (timestamp: {timestamp})")
                    else:
                        self.infiChequeStatement = None
                        logger.warning("Cheque report not found in SQLite despite status_code=1")
            elif status_code == 0:
                logger.info("No cheque report found in SQLite")
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
            try:
                # Keep native table model in sync with filtered search results.
                self._update_table_model(self._header, search_result.filtered_data)
            except Exception as e:
                logger.debug(f"TableModel search update skipped: {e}")
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
    
    # ===== NEW REPOSITORY-BASED FIREBASE SYNC METHODS =====
    
    def _load_sync_timestamp(self, key: str) -> str:
        """Load sync timestamp from config file."""
        try:
            config_path = os.path.join(CURRENT_DIR, "config.local.toml")
            if os.path.exists(config_path):
                import toml
                with open(config_path, "r") as f:
                    config = toml.load(f)
                    return config.get('firebase', {}).get(key, '')
        except Exception as e:
            logger.debug(f"Could not load sync timestamp {key}: {e}")
        return ''

    def _load_reconciliation_output_enabled(self) -> bool:
        """Load reconciliation Excel output toggle from config."""
        try:
            config_path = os.path.join(CURRENT_DIR, "config.local.toml")
            if os.path.exists(config_path):
                import toml
                with open(config_path, "r") as f:
                    config = toml.load(f)
                return bool(config.get('reconciliation', {}).get('output_excel_enabled', True))
        except Exception as e:
            logger.debug(f"Could not load reconciliation output setting: {e}")
        return True

    def _save_reconciliation_output_enabled(self, enabled: bool) -> None:
        """Save reconciliation Excel output toggle to config."""
        try:
            config_path = os.path.join(CURRENT_DIR, "config.local.toml")
            config = {}
            if os.path.exists(config_path):
                import toml
                with open(config_path, "r") as f:
                    config = toml.load(f)
            if 'reconciliation' not in config:
                config['reconciliation'] = {}
            config['reconciliation']['output_excel_enabled'] = bool(enabled)
            import toml
            with open(config_path, "w") as f:
                toml.dump(config, f)
        except Exception as e:
            logger.error(f"Could not save reconciliation output setting: {e}")

    def _default_erp_bank_mapping(self) -> List[Dict[str, str]]:
        mapping_rows = []
        for company in self._companyDict:
            mapping_rows.append({
                "company": str(company.get("value", "")).strip().lower(),
                "company_name": str(company.get("name", "")).strip(),
                "hdfc_code": "",
                "icici_code": "",
            })
        return mapping_rows

    def _load_erp_bank_mapping(self) -> List[Dict[str, str]]:
        default_rows = self._default_erp_bank_mapping()
        default_by_company = {row["company"]: row for row in default_rows}
        try:
            config_path = os.path.join(CURRENT_DIR, "config.local.toml")
            if os.path.exists(config_path):
                import toml
                with open(config_path, "r") as f:
                    config = toml.load(f)
                raw = config.get("erp_bank_mapping", {})
                if isinstance(raw, dict):
                    for company_key, company_data in raw.items():
                        key = str(company_key).strip().lower()
                        if key not in default_by_company:
                            continue
                        if isinstance(company_data, dict):
                            default_by_company[key]["hdfc_code"] = str(company_data.get("hdfc_code", "")).strip()
                            default_by_company[key]["icici_code"] = str(company_data.get("icici_code", "")).strip()
        except Exception as e:
            logger.error(f"Could not load ERP bank mapping: {e}")
        return list(default_by_company.values())

    def _get_erp_bank_mapping_by_company(self) -> Dict[str, Dict[str, str]]:
        mapping = {}
        for row in self._erpBankMapping:
            company = str(row.get("company", "")).strip().lower()
            if not company:
                continue
            mapping[company] = {
                "hdfc_code": str(row.get("hdfc_code", "")).strip(),
                "icici_code": str(row.get("icici_code", "")).strip(),
            }
        return mapping

    def _load_erp_bank_options(self) -> Dict[str, Dict[str, Any]]:
        """Load ERP bank master options (latest FY per company) for Settings dropdowns."""
        options_by_company: Dict[str, Dict[str, Any]] = {}
        try:
            company_values = [str(c.get("value", "")).strip().lower() for c in self._companyDict]
            company_values = [c for c in company_values if c]
            if not company_values:
                return {}

            company_year_df = RM.load_company_year_options(RM.DB_SERVER)
            if company_year_df is None or company_year_df.empty:
                logger.warning("ERP bank options: no company-year data available")
                return {}

            # Reuse company resolver logic from reconciliation module to keep mapping consistent.
            for app_company in company_values:
                try:
                    # Pick latest available FY for this app company.
                    candidates = []
                    for fy_start in sorted(company_year_df["FYStart"].unique(), reverse=True):
                        try:
                            resolved = RM._resolve_company_year_db(app_company, int(fy_start), company_year_df)
                            candidates.append(resolved)
                        except Exception:
                            continue
                    if not candidates:
                        continue

                    selected = candidates[0]
                    year_db = str(selected.get("YearDb", "")).strip()
                    fy_start = int(selected.get("FYStart"))
                    fy_label = f"{fy_start}-{fy_start + 1}"

                    banks_df = RM.load_bank_accounts(RM.DB_SERVER, year_db)
                    hdfc_options = []
                    icici_options = []
                    for _, row in banks_df.iterrows():
                        display_name = str(row.get("DisplayName", "")).strip()
                        code = str(row.get("Code", "")).strip()
                        try:
                            btype = RM.detect_bank_type(display_name).lower()
                        except Exception:
                            continue
                        item = {"name": f"{display_name} (Code: {code})", "code": code}
                        if btype == "hdfc":
                            hdfc_options.append(item)
                        elif btype == "icici":
                            icici_options.append(item)

                    options_by_company[app_company] = {
                        "year_db": year_db,
                        "financial_year": fy_label,
                        "hdfc": hdfc_options,
                        "icici": icici_options,
                    }
                except Exception as e:
                    logger.warning(f"Failed loading ERP bank options for {app_company}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Could not load ERP bank options: {e}")
        return options_by_company

    @Slot()
    def refreshErpBankOptions(self) -> None:
        """Refresh ERP bank dropdown options for Settings."""
        self._erpBankOptions = self._load_erp_bank_options()
        self.erpBankOptions_changed.emit()
        logger.info(f"ERP bank options refreshed for {len(self._erpBankOptions)} companies")

    @Slot(str, str, str)
    def updateErpBankMapping(self, company: str, bank: str, bankCode: str) -> None:
        """Update in-memory ERP bank code mapping for one company+bank."""
        company_key = str(company).strip().lower()
        bank_key = str(bank).strip().lower()
        code = str(bankCode).strip()
        if bank_key not in {"hdfc", "icici"}:
            self.erpBankMappingSaveFailed.emit(f"Unsupported bank in mapping update: {bank}")
            return

        updated = False
        for row in self._erpBankMapping:
            if str(row.get("company", "")).strip().lower() == company_key:
                row[f"{bank_key}_code"] = code
                updated = True
                break

        if not updated:
            self._erpBankMapping.append({
                "company": company_key,
                "company_name": company_key,
                "hdfc_code": code if bank_key == "hdfc" else "",
                "icici_code": code if bank_key == "icici" else "",
            })
        self.erpBankMapping_changed.emit()

    @Slot()
    def saveErpBankMapping(self) -> None:
        """Persist ERP bank mappings to config.local.toml."""
        try:
            config_path = os.path.join(CURRENT_DIR, "config.local.toml")
            config = {}
            if os.path.exists(config_path):
                import toml
                with open(config_path, "r") as f:
                    config = toml.load(f)

            mapping_section = {}
            for row in self._erpBankMapping:
                company = str(row.get("company", "")).strip().lower()
                if not company:
                    continue
                mapping_section[company] = {
                    "hdfc_code": str(row.get("hdfc_code", "")).strip(),
                    "icici_code": str(row.get("icici_code", "")).strip(),
                }
            config["erp_bank_mapping"] = mapping_section

            import toml
            with open(config_path, "w") as f:
                toml.dump(config, f)
            logger.info("ERP bank mapping saved")
            self.erpBankMappingSaved.emit("ERP bank mapping saved")
        except Exception as e:
            logger.error(f"Could not save ERP bank mapping: {e}")
            self.erpBankMappingSaveFailed.emit(str(e))
    
    def _save_sync_timestamp(self, key: str, value: str) -> None:
        """Save sync timestamp to config file."""
        try:
            config_path = os.path.join(CURRENT_DIR, "config.local.toml")
            config = {}
            if os.path.exists(config_path):
                import toml
                with open(config_path, "r") as f:
                    config = toml.load(f)
            
            if 'firebase' not in config:
                config['firebase'] = {}
            config['firebase'][key] = value
            
            # Write back
            import toml
            with open(config_path, "w") as f:
                toml.dump(config, f)
        except Exception as e:
            logger.error(f"Could not save sync timestamp {key}: {e}")
    
    def _sync_progress_callback(self, current: int, total: int, item_name: str, status: str):
        """Progress callback for sync operations - called from background thread."""
        if self._syncCancelled:
            raise Exception("Sync cancelled by user")
        self.syncProgressUpdated.emit(current, total, item_name, status)
    
    @Slot()
    def syncUploadToFirebase(self):
        """Start Firebase upload using repository pattern (called from Settings page)."""
        if self._isSyncing:
            logger.warning("Sync already in progress")
            return
        
        logger.info("Starting repository-based Firebase upload")
        self._isSyncing = True
        self._syncCancelled = False
        self.isSyncing_changed.emit()
        
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(
                self._syncUploadToFirebaseThreaded, "Repository Firebase Upload"
            )
            future = self._thread_pool.submit(wrapped_func)
            self._active_futures.add(future)
        else:
            logger.warning("Firebase upload rejected: application is shutting down")
            self._isSyncing = False
            self.isSyncing_changed.emit()
    
    def _syncUploadToFirebaseThreaded(self):
        """Thread worker for repository-based Firebase upload."""
        try:
            firebase_service = self.tableOperations.firebaseService
            results = firebase_service.upload_with_repositories(
                self.snapshot_repository,
                self.cheque_repository,
                self._sync_progress_callback
            )
            
            if results['success']:
                # Save timestamp
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                self._save_sync_timestamp('last_sync_upload', timestamp)
                self._lastSyncUpload = timestamp
                self.lastSyncUpload_changed.emit()
                
                message = (f"Upload complete: {results['snapshots_uploaded']} snapshots, "
                          f"{results['cheque_reports_uploaded']} cheque reports")
                logger.info(message)
                self.syncCompleted.emit(True, message)
            else:
                error_msg = "; ".join(results['errors']) if results['errors'] else "Unknown error"
                logger.error(f"Upload failed: {error_msg}")
                self.syncCompleted.emit(False, f"Upload failed: {error_msg}")
                
        except Exception as e:
            if "cancelled" in str(e).lower():
                logger.info("Upload cancelled by user")
                self.syncCompleted.emit(False, "Upload cancelled")
            else:
                logger.error(f"Upload error: {e}")
                logger.error(traceback.format_exc())
                self.syncCompleted.emit(False, f"Upload error: {str(e)}")
        finally:
            self._isSyncing = False
            self.isSyncing_changed.emit()
    
    @Slot()
    def syncDownloadFromFirebase(self):
        """Start Firebase download using repository pattern (called from Settings page)."""
        if self._isSyncing:
            logger.warning("Sync already in progress")
            return
        
        logger.info("Starting repository-based Firebase download")
        self._isSyncing = True
        self._syncCancelled = False
        self.isSyncing_changed.emit()
        
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(
                self._syncDownloadFromFirebaseThreaded, "Repository Firebase Download"
            )
            future = self._thread_pool.submit(wrapped_func)
            self._active_futures.add(future)
        else:
            logger.warning("Firebase download rejected: application is shutting down")
            self._isSyncing = False
            self.isSyncing_changed.emit()
    
    def _syncDownloadFromFirebaseThreaded(self):
        """Thread worker for repository-based Firebase download."""
        try:
            firebase_service = self.tableOperations.firebaseService
            results = firebase_service.download_with_repositories(
                self.snapshot_repository,
                self.cheque_repository,
                self._sync_progress_callback,
                overwrite_newer=True  # User explicitly requested download
            )
            
            if results['success']:
                # Save timestamp
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                self._save_sync_timestamp('last_sync_download', timestamp)
                self._lastSyncDownload = timestamp
                self.lastSyncDownload_changed.emit()
                
                message = (f"Download complete: {results['snapshots_downloaded']} snapshots, "
                          f"{results['cheque_reports_downloaded']} cheque reports")
                logger.info(message)
                self.syncCompleted.emit(True, message)
                
                # Refresh UI after download
                self.populate_left_menu()
                self.populate_table()
            else:
                error_msg = "; ".join(results['errors']) if results['errors'] else "Unknown error"
                logger.error(f"Download failed: {error_msg}")
                self.syncCompleted.emit(False, f"Download failed: {error_msg}")
                
        except Exception as e:
            if "cancelled" in str(e).lower():
                logger.info("Download cancelled by user")
                self.syncCompleted.emit(False, "Download cancelled")
            else:
                logger.error(f"Download error: {e}")
                logger.error(traceback.format_exc())
                self.syncCompleted.emit(False, f"Download error: {str(e)}")
        finally:
            self._isSyncing = False
            self.isSyncing_changed.emit()
    
    @Slot()
    def cancelSync(self):
        """Cancel ongoing sync operation."""
        if self._isSyncing:
            logger.info("User requested sync cancellation")
            self._syncCancelled = True
    
    @Slot()
    def openSettingsPage(self):
        """Signal to open settings page."""
        self.refreshErpBankOptions()
        self.showSettingsPage.emit()

    @Slot(bool)
    def setReconciliationOutputEnabled(self, enabled: bool):
        self._reconciliationOutputEnabled = bool(enabled)
        self._save_reconciliation_output_enabled(self._reconciliationOutputEnabled)
        self.reconciliationOutputEnabled_changed.emit()
    
    # Sync property getters
    def get_lastSyncUpload(self):
        return self._lastSyncUpload
    
    def get_lastSyncDownload(self):
        return self._lastSyncDownload
    
    def get_isSyncing(self):
        return self._isSyncing
    
    def get_reconciliationOutputEnabled(self):
        return self._reconciliationOutputEnabled
    
    # Migration property getters
    def get_migrationStatus(self):
        return self._migrationStatus
    
    def get_migrationProgressText(self):
        return self._migrationProgressText
    
    def get_migrationCurrent(self):
        return self._migrationCurrent
    
    def get_migrationTotal(self):
        return self._migrationTotal
    
    def get_pickleSnapshotCount(self):
        return self._pickleSnapshotCount
    
    def get_pickleChequeCount(self):
        return self._pickleChequeCount
    
    def get_databasePath(self):
        return self._databasePath
    
    def get_totalSnapshotCount(self):
        return self._totalSnapshotCount
    
    def get_totalChequeReportCount(self):
        return self._totalChequeReportCount
    
    def _check_migration_status(self):
        """Check if there are pickle files that need migration."""
        try:
            from pathlib import Path
            import os
            
            # Get pickle directory
            appdata = os.environ.get('APPDATA', '')
            pickle_dir = Path(appdata) / 'Record Matcher'
            
            # Get database path from config
            from config import get_config
            cfg = get_config()
            db_path = cfg.paths.database_path if hasattr(cfg, 'paths') and hasattr(cfg.paths, 'database_path') else 'recordmatcher.db'
            self._databasePath = str(db_path)
            self.databasePath_changed.emit()
            
            # Count pickle files
            snapshot_count = 0
            cheque_count = 0
            
            if pickle_dir.exists():
                # Count snapshot files (.fil and .filv2)
                for f in pickle_dir.glob('*.fil'):
                    snapshot_count += 1
                for f in pickle_dir.glob('*.filv2'):
                    snapshot_count += 1
                
                # Count cheque report files
                for f in pickle_dir.glob('*.cheque'):
                    cheque_count += 1
                for f in pickle_dir.glob('*.chequev2'):
                    cheque_count += 1
            
            self._pickleSnapshotCount = snapshot_count
            self._pickleChequeCount = cheque_count
            self.pickleSnapshotCount_changed.emit()
            self.pickleChequeCount_changed.emit()
            
            # Get database counts using list_all method
            if hasattr(self, 'snapshot_repository'):
                try:
                    all_snapshots = self.snapshot_repository.list_all()
                    self._totalSnapshotCount = len(all_snapshots) if all_snapshots else 0
                except Exception as e:
                    logger.warning(f"Could not get snapshot count: {e}")
                    self._totalSnapshotCount = 0
            else:
                self._totalSnapshotCount = 0
            
            if hasattr(self, 'cheque_repository'):
                try:
                    all_reports = self.cheque_repository.list_all()
                    self._totalChequeReportCount = len(all_reports) if all_reports else 0
                except Exception as e:
                    logger.warning(f"Could not get cheque report count: {e}")
                    self._totalChequeReportCount = 0
            else:
                self._totalChequeReportCount = 0
            
            self.totalSnapshotCount_changed.emit()
            self.totalChequeReportCount_changed.emit()
            
            # Determine migration status
            if snapshot_count > 0 or cheque_count > 0:
                self._migrationStatus = "pending"
                self._migrationProgressText = f"{snapshot_count + cheque_count} legacy files found"
            else:
                self._migrationStatus = "completed"
                self._migrationProgressText = "All data migrated to SQLite"
            
            self.migrationStatus_changed.emit()
            self.migrationProgressText_changed.emit()
            
            logger.info(f"Migration status: {self._migrationStatus}, pickle files: {snapshot_count} snapshots, {cheque_count} cheque reports")
            
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            self._migrationStatus = "error"
            self._migrationProgressText = f"Error: {str(e)}"
            self.migrationStatus_changed.emit()
            self.migrationProgressText_changed.emit()
    
    @Slot()
    def startMigration(self):
        """Start the pickle to SQLite migration."""
        if self._isMigrating:
            logger.warning("Migration already in progress")
            return
        
        if self._migrationStatus == "completed":
            logger.info("Migration already completed")
            return
        
        logger.info("Starting pickle to SQLite migration...")
        self._isMigrating = True
        self._migrationStatus = "in_progress"
        self._migrationCurrent = 0
        self._migrationTotal = self._pickleSnapshotCount + self._pickleChequeCount
        self._migrationProgressText = "Starting migration..."
        
        self.migrationStatus_changed.emit()
        self.migrationCurrent_changed.emit()
        self.migrationTotal_changed.emit()
        self.migrationProgressText_changed.emit()
        
        # Run migration in background thread
        future = self._thread_pool.submit(self._run_migration)
        self._active_futures.add(future)
    
    def _run_migration(self):
        """Run the migration in a background thread."""
        try:
            from sqlite_storage import migrate_pickle_to_sqlite
            
            def progress_callback(item_type: str, item_name: str, current: int, total: int):
                """Callback to update progress in UI."""
                self._migrationCurrent = current
                self._migrationTotal = total
                self._migrationProgressText = f"Migrating {item_type}: {item_name}"
                
                # Use QTimer to emit signals on main thread
                QTimer.singleShot(0, self.migrationCurrent_changed.emit)
                QTimer.singleShot(0, self.migrationTotal_changed.emit)
                QTimer.singleShot(0, self.migrationProgressText_changed.emit)
            
            # Run migration with progress callback
            migrate_pickle_to_sqlite(progress_callback=progress_callback)
            
            # Migration completed successfully
            self._migrationStatus = "completed"
            self._migrationProgressText = "Migration completed successfully!"
            self._pickleSnapshotCount = 0
            self._pickleChequeCount = 0
            
            # Refresh database counts
            self._check_migration_status()
            
            logger.info("Migration completed successfully")
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            logger.error(traceback.format_exc())
            self._migrationStatus = "error"
            self._migrationProgressText = f"Error: {str(e)}"
        finally:
            self._isMigrating = False
            QTimer.singleShot(0, self.migrationStatus_changed.emit)
            QTimer.singleShot(0, self.migrationProgressText_changed.emit)
            QTimer.singleShot(0, self.pickleSnapshotCount_changed.emit)
            QTimer.singleShot(0, self.pickleChequeCount_changed.emit)

    @Slot()
    def createTallyXMLFromDaybook(self):
        self.fullScreenLoading2Start.emit()
        logger.debug("createTallyXMLFromDaybook invoked")


    @Slot(str, str)
    def companyChanged(self, companyname, screenName):
        """Handle company selection change.
        
        Args:
            companyname: Selected company name
            screenName: Screen name for display
        """
        logger.debug(f"companyChanged: companyname={companyname}, screenName={screenName}")
        # Update service layer state
        self.state_service.update_company(companyname)
        # Sync back to UI state
        self._sync_state_from_service()
        
        with self._state_lock:
            self._companyData = screenName
            logger.debug(f"_companyData set to: {self._companyData}")
            cheque_activated = self.chequeReportActivated
            tally_activated = self.tallyExportBoxActivated
        
        self.companyData_changed.emit()
        logger.debug("companyData_changed emitted")
        
        if cheque_activated:
            status, data = self.populateChequeReports()
            self.showChequeReportPage.emit(status, data)
            return
        elif tally_activated:
            self.showTallyExportBox.emit()
            return
        self._set_table_available(False, clear_ui_data=True)
        self.request_table_populate()
    @Slot(str, str)
    def bankChanged(self, bankname, screenName):
        """Handle bank selection change.
        
        Args:
            bankname: Selected bank name
            screenName: Screen name for display
        """
        logger.debug(f"bankChanged: bankname={bankname}, screenName={screenName}")
        # Update service layer state
        self.state_service.update_bank(bankname)
        # Sync back to UI state
        self._sync_state_from_service()
        
        with self._state_lock:
            self._bankData = screenName
            logger.debug(f"_bankData set to: {self._bankData}")
        self.bankData_changed.emit()
        logger.debug("bankData_changed emitted")
        self._set_table_available(False, clear_ui_data=True)
        self.request_table_populate()
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
        self._set_table_available(False, clear_ui_data=True)
        self.request_table_populate()
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
        self._set_table_available(False, clear_ui_data=True)
        self.request_table_populate()
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
        """Called from QML when user selection changes.
        Synchronize selection into the StateManagementService and notify QML listeners.
        """
        self._selectedRows = updatedRows
        try:
            # Update service layer so selection is globally available
            self.state_service.update_selected_rows(updatedRows)
        except Exception as e:
            logger.debug(f"Failed to update selected rows in state service: {e}")
        # Emit notify so QML bindings remain consistent
        self.selectedRows_changed.emit()
    @Slot(bool)
    def setChequeReportActivated(self,status):
        self.chequeReportActivated = status
        self.update_monthYearData()
        logger.debug(f"Cheque report mode status: {status}")
    @Slot(bool)
    def setTallyExportBoxActivated(self,status):
        self.tallyExportBoxActivated = status
        logger.debug(f"Tally export mode status: {status}")
    @Slot()
    def call_populate_table(self):
        self.request_table_populate(immediate=True)
    

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
        return
    def get_table_data(self):
        """Get table data from state service."""
        table_data, _, _ = self.state_service.get_table_data()
        return table_data 
    @Signal
    def creditBal_changed(self):
        return
    def get_creditBal(self):
        """Get credit balance from state service."""
        _, credit_bal, _ = self.state_service.get_table_data()
        return credit_bal
    @Signal
    def debitBal_changed(self):
        return
    def get_debitBal(self):
        """Get debit balance from state service."""
        _, _, debit_bal = self.state_service.get_table_data()
        return debit_bal         
    @Signal
    def header_changed(self):
        return
    def get_header(self):
        return self._header    
    @Signal
    def monthYearData_changed(self):
        return
    def get_monthYearData(self):
        return self._monthYearData
    @Signal
    def companyData_changed(self):
        return
    def get_companyData(self):
        return self._companyData 
    @Signal
    def bankData_changed(self):
        return
    def get_bankData(self):
        return self._bankData
    @Signal
    def selectedRows_changed(self):
        return
    def get_selectedRows(self):
        return self._selectedRows  
    @Signal
    def tableAvailable_changed(self):
        return
    def get_tableAvailable(self):
        return self._tableAvailable
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
    @Signal
    def erpBankMapping_changed(self):
        return
    def get_erpBankMapping(self):
        return self._erpBankMapping
    @Signal
    def erpBankOptions_changed(self):
        return
    def get_erpBankOptions(self):
        return self._erpBankOptions


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
    tableAvailable = Property(bool, get_tableAvailable, notify=tableAvailable_changed)
    adminPassword = Property(str, get_adminPassword, notify=adminPassword_changed)
    erpBankMapping = Property('QVariantList', get_erpBankMapping, notify=erpBankMapping_changed)
    erpBankOptions = Property('QVariantMap', get_erpBankOptions, notify=erpBankOptions_changed)
    
    # Firebase sync properties
    reconciliationOutputEnabled = Property(bool, get_reconciliationOutputEnabled, notify=reconciliationOutputEnabled_changed)
    lastSyncUpload = Property(str, get_lastSyncUpload, notify=lastSyncUpload_changed)
    lastSyncDownload = Property(str, get_lastSyncDownload, notify=lastSyncDownload_changed)
    isSyncing = Property(bool, get_isSyncing, notify=isSyncing_changed)
    
    # Migration properties
    migrationStatus = Property(str, get_migrationStatus, notify=migrationStatus_changed)
    migrationProgressText = Property(str, get_migrationProgressText, notify=migrationProgressText_changed)
    migrationCurrent = Property(int, get_migrationCurrent, notify=migrationCurrent_changed)
    migrationTotal = Property(int, get_migrationTotal, notify=migrationTotal_changed)
    pickleSnapshotCount = Property(int, get_pickleSnapshotCount, notify=pickleSnapshotCount_changed)
    pickleChequeCount = Property(int, get_pickleChequeCount, notify=pickleChequeCount_changed)
    databasePath = Property(str, get_databasePath, notify=databasePath_changed)
    totalSnapshotCount = Property(int, get_totalSnapshotCount, notify=totalSnapshotCount_changed)
    totalChequeReportCount = Property(int, get_totalChequeReportCount, notify=totalChequeReportCount_changed)


class TableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._headers = []
        self._data = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if self._headers:
            return len(self._headers)
        return len(self._data[0]) if self._data else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            try:
                return str(self._data[row][col])
            except Exception:
                return ''
        # Named roles for QML TableViewColumns (col0, col1, ...)
        if role >= Qt.UserRole + 1:
            col_idx = role - (Qt.UserRole + 1)
            try:
                return str(self._data[row][col_idx])
            except Exception:
                return ''
        return None

    def roleNames(self):
        roles = {}
        for i in range(self.columnCount()):
            roles[Qt.UserRole + 1 + i] = QByteArray(f"col{i}".encode())
        return roles

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section < len(self._headers):
                return self._headers[section]
        return None

    @Slot('QVariantList', 'QVariantList')
    def set_table_data(self, headers, data):
        def _display_value(value):
            if value is None:
                return ''
            if isinstance(value, float) and math.isnan(value):
                return ''
            text = str(value)
            if text.strip().lower() in {'nan', 'nat', 'none'}:
                return ''
            return text

        self.beginResetModel()
        self._headers = [str(h) for h in headers] if headers else []
        normalized = []
        for row in data:
            if isinstance(row, (list, tuple)):
                normalized.append([_display_value(c) for c in row])
            elif isinstance(row, dict):
                normalized.append([_display_value(v) for v in row.values()])
            else:
                normalized.append([_display_value(row)])
        self._data = normalized
        self.endResetModel()


class TableBackend(QObject):
    tableRowSelected = Signal(list)

    def __init__(self):
        QObject.__init__(self)
        return
    @Slot(int, list)
    def tableRowSelectedNotify(self, currentRow, selectedRows):
        self.checkedRows = selectedRows
        if currentRow in self.checkedRows:
            self.checkedRows.remove(currentRow)
            self.tableRowSelected.emit(self.checkedRows)
        else:
            self.checkedRows.append(currentRow)
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
    # Expose native QAbstractTableModel for QML TableView
    engine.rootContext().setContextProperty("tableModel", main.tableModel)


    #Load QML File
    engine.load(os.fspath(Path(__file__).resolve().parent / "qml/main.qml"))
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())
