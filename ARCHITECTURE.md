# Record Matcher - Architecture Documentation

**Version:** 2.0  
**Last Updated:** December 19, 2025  
**Maintainer:** Development Team

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Diagram](#component-diagram)
4. [Data Flow](#data-flow)
5. [Key Components](#key-components)
6. [Threading Model](#threading-model)
7. [State Management](#state-management)
8. [Data Persistence](#data-persistence)
9. [Error Handling Strategy](#error-handling-strategy)
10. [Integration Points](#integration-points)

---

## System Overview

### Purpose
Record Matcher is a desktop application for bank statement reconciliation and party finder functionality. It automates the process of matching bank statement entries with accounting system (InfiBooks) cheque entries, reducing manual reconciliation effort.

### Technology Stack
- **Language:** Python 3.9+
- **UI Framework:** PySide2 (Qt for Python) + QML
- **Data Processing:** pandas, numpy
- **Excel I/O:** xlrd, xlwt, openpyxl
- **Database:** Firebase Realtime Database
- **Threading:** concurrent.futures.ThreadPoolExecutor
- **Logging:** Python logging module

### Deployment
- Packaged as Windows executable (.exe)
- Uses auto-py-to-exe for bundling
- Includes virtual environment (RecordMatcher_env)

---

## Architecture Patterns

### 1. Model-View-Controller (MVC) Variant
```
┌─────────────────────────────────────────────────────────────┐
│                         VIEW LAYER                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              QML User Interface                       │  │
│  │  - main.qml (main application window)                │  │
│  │  - controls/*.qml (reusable UI components)           │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↕ Signals/Slots                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           CONTROLLER LAYER                            │  │
│  │  MainWindow (main.py)                                 │  │
│  │  - Handles UI events                                  │  │
│  │  - Coordinates operations                             │  │
│  │  - Manages threading                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↕                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MODEL/BUSINESS LOGIC LAYER               │  │
│  │  core.py                                              │  │
│  │  - TableOperations                                    │  │
│  │  - InfiChequeStatement                                │  │
│  │  - HDFCBankChequeStatement                            │  │
│  │  - ICICIBankChequeStatement                           │  │
│  │  - Validator                                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Singleton Pattern
- **JsonDataLoader**: Ensures single instance with cached data
- **Firebase**: Single connection instance shared across operations

### 3. Repository Pattern
- **TableOperations**: Abstracts data access (Excel, pickle, Firebase)
- **FirebaseControls**: Dedicated Firebase interaction layer

### 4. Observer Pattern
- **Qt Signals**: UI updates propagate through signal emissions
- **Property Bindings**: QML binds to Python properties

---

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        Record Matcher                             │
│                                                                   │
│  ┌────────────────┐         ┌──────────────────────────────┐    │
│  │   QML UI       │◄───────►│      MainWindow              │    │
│  │                │ Signals │  (Controller)                │    │
│  │  - Tables      │  Slots  │  - State Management          │    │
│  │  - Forms       │         │  - Thread Pool               │    │
│  │  - Dialogs     │         │  - Event Handling            │    │
│  └────────────────┘         └──────────────┬───────────────┘    │
│                                             │                     │
│                                             │ uses                │
│                            ┌────────────────▼──────────────┐     │
│                            │   TableOperations             │     │
│                            │   (Business Logic)            │     │
│                            │   - Cheque Matching           │     │
│                            │   - Table Management          │     │
│                            │   - Export/Import             │     │
│                            └─┬────────────┬────────────────┘     │
│                              │            │                      │
│                 ┌────────────▼──┐   ┌─────▼──────────────┐      │
│                 │ InfiCheque    │   │ BankChequeStatement│      │
│                 │ Statement     │   │ - HDFC             │      │
│                 │               │   │ - ICICI            │      │
│                 └───────────────┘   └────────────────────┘      │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                 Data Layer                                  │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │  Excel   │  │  Pickle  │  │ Firebase │  │   JSON   │  │ │
│  │  │  Files   │  │  Files   │  │ Database │  │  Config  │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. File Upload Flow
```
User selects file (QML)
       ↓
MainWindow.uploadFile() receives file URL
       ↓
Validation (company, year, bank selected?)
       ↓
Submit to ThreadPool
       ↓
MainWindow.threadedUploadFile() (background thread)
       ↓
Parse Excel file (HDFCBankChequeStatement or InfiChequeStatement)
       ↓
Save to collection (pickle or Firebase)
       ↓
Emit success signal → UI updates
```

### 2. Table Population Flow
```
User clicks populate (QML)
       ↓
MainWindow.populate_table()
       ↓
Read current selections (company, year, bank, month) [with lock]
       ↓
Submit to ThreadPool
       ↓
MainWindow.threadedPopulate_table() (background thread)
       ↓
Load InfiChequeStatement from Firebase
       ↓
Load bank statements for month
       ↓
Perform cheque matching algorithm
       ↓
Create TableSnapshot with results
       ↓
Update UI data [with lock] → QML updates table view
```

### 3. Cheque Matching Algorithm
```
For each bank statement entry:
    ↓
    Extract: cheque_number, debit_amount, transaction_date
    ↓
    InfiChequeStatement.findMatchByChequeNumber()
    ↓
    For each Infi entry:
        ↓
        Pad cheque numbers to 16 digits (leading zeros)
        ↓
        Compare: cheque_number, amount, date
        ↓
        If all match → Add to match_list
    ↓
    Create table row with match status
    ↓
Return complete reconciliation table
```

### 4. Export Flow
```
User clicks export (QML)
       ↓
MainWindow.exportFile() receives destination path
       ↓
Validate snapshot exists [with lock]
       ↓
Submit to ThreadPool
       ↓
TableOperations.export_to_excel()
       ↓
Create Excel workbook with xlwt
       ↓
Write headers and data rows
       ↓
Apply formatting (colors, borders)
       ↓
Save file → Emit success signal
```

---

## Key Components

### MainWindow (main.py)
**Responsibility:** Application controller and UI bridge

**Key Methods:**
- `uploadFile()`: Handle file uploads (cheque/bank statements)
- `populate_table()`: Trigger reconciliation process
- `search()`: Filter table data
- `exportFile()`: Export results to Excel
- `downloadfromDb()` / `uploadtoDb()`: Firebase sync operations

**State:**
- Current selections: `current_company`, `current_year`, `current_bank`, `current_month`
- Data: `tableSnapshot`, `_tableData`, `masterDisplayTableData`
- UI state: `chequeReportActivated`, `tallyExportBoxActivated`

**Threading:**
- ThreadPoolExecutor with 4 workers
- Exception wrapper for error handling
- Graceful shutdown mechanism

### TableOperations (core.py)
**Responsibility:** Core business logic and data operations

**Key Methods:**
- `add_snapshot_to_table()`: Process and add bank statement
- `save_snapshot_to_table()`: Persist table snapshot
- `export_to_excel()`: Generate Excel export
- `search()`: Search/filter table data
- `validateIntermediateDaybook()`: Validate daybook parameters
- `generateIntermediateDaybook()`: Create daybook Excel

**Data Structures:**
- Table format: List of lists (rows × columns)
- Snapshot: Pickled TableSnapshot objects
- Collections: Organized by company/year/bank/month

### InfiChequeStatement (core.py)
**Responsibility:** Parse and manage InfiBooks cheque data

**Key Methods:**
- `setPath()`: Load Excel file
- `grab_data()`: Extract transaction entries
- `findMatchByChequeNumber()`: Match with bank statement
- `compare_date()`: Date comparison logic

**Data Format:**
```python
entry = [
    transDate,      # Transaction date
    transNo,        # Transaction number
    book,           # Book reference
    code,           # Account code
    ledgerName,     # Ledger account name
    chqNo,          # Cheque number
    chqDate,        # Cheque date
    voucher,        # Voucher type
    narration,      # Description
    debit,          # Debit amount
    credit          # Credit amount
]
```

### HDFCBankChequeStatement / ICICIBankChequeStatement (core.py)
**Responsibility:** Parse bank-specific Excel statement formats

**Key Methods:**
- `setPath()`: Load statement file
- `find_start_row()`: Locate data start (bank-specific header detection)
- `grab_data()`: Extract transactions
- `release_resources()`: Clean up Excel resources

**HDFC Format:**
- Columns: Date, Narration, Cheque Number, Value Date, Debit, Credit, Balance
- Header row: "Date" with optional asterisk separator

**ICICI Format:**
- Columns: Transaction Date, Value Date, Description, Cheque Number, Debit, Credit, Balance
- Header detection: Looks for specific column names

### Validator (core.py)
**Responsibility:** Centralized validation logic

**Static Methods:**
- `validate_path()`: Excel file path validation
- `validate_date()`: Date format validation
- `validate_chqno()`: Cheque number validation
- `validate_amount()`: Amount validation
- `validateSavefile()`: Save file validation

### FirebaseControls (core.py)
**Responsibility:** Firebase database operations

**Key Methods:**
- `upload_data_to_firebase_db()`: Save data to Firebase
- `download_data_from_firebase_db()`: Retrieve data from Firebase
- Connection management and error handling

---

## Threading Model

### Thread Pool Architecture
```
MainWindow
    │
    ├─ _thread_pool (ThreadPoolExecutor, 4 workers)
    │   │
    │   ├─ File Upload Worker
    │   ├─ File Export Worker
    │   ├─ Table Population Worker
    │   └─ Firebase Sync Worker
    │
    ├─ _active_futures (WeakSet) - Track running tasks
    └─ _is_shutting_down (bool) - Shutdown flag
```

### Thread Safety Mechanisms

**Locks:**
- `_state_lock`: Protects user selections (month, year, bank, company)
- `_snapshot_lock`: Protects tableSnapshot and masterDisplayTableData
- `_data_lock`: Protects UI display data (_tableData, balances)
- `_shutdown_lock`: Protects shutdown flag

**Pattern:**
```python
# Read state safely
with self._state_lock:
    month = self.current_month
    year = self.current_year

# Perform long operation (outside lock)
result = process_data(month, year)

# Update UI data safely
with self._data_lock:
    self._tableData = result
    self.table_data_changed.emit()
```

### Exception Handling in Threads
All thread workers are wrapped with `_thread_exception_wrapper()`:
- Catches all exceptions
- Logs error with stack trace
- Emits signal to notify UI
- Re-raises for ThreadPoolExecutor tracking

### Graceful Shutdown
```python
def _cleanup_threads():
    1. Set _is_shutting_down flag
    2. Wait for active futures (timeout: 5 seconds)
    3. Force shutdown thread pool
    4. Save snapshot before exit
```

---

## State Management

### Application State
Managed by MainWindow instance variables:

**Selection State:**
- `current_company`: Selected company name
- `current_year`: Selected financial year
- `current_bank`: Selected bank (HDFC/ICICI)
- `current_month`: Selected month

**Data State:**
- `tableSnapshot`: Current TableSnapshot object
- `masterDisplayTableData`: Full table data
- `_tableData`: Filtered/displayed table data
- `infiChequeStatement`: Loaded cheque statement

**UI State:**
- `chequeReportActivated`: Cheque report mode flag
- `tallyExportBoxActivated`: Tally export mode flag
- `searchModeOffFirsttime`: Search initialization flag

### State Transitions
```
Initial → Load Menu Data (from data.json)
       ↓
User Selects Company + Year
       ↓
User Uploads Cheque Report
       ↓
chequeReportActivated = True
       ↓
User Selects Bank + Month
       ↓
User Uploads Bank Statement
       ↓
User Clicks Populate
       ↓
Table Populated (tableSnapshot created)
       ↓
User Can: Search, Export, Delete, Sync to Firebase
```

### Property Bindings (QML ↔ Python)
```python
# Python
@Property(str, notify=companyData_changed)
def companyData(self):
    return self._companyData

# QML
Text { text: backend.companyData }
```

---

## Data Persistence

### Storage Layers

**1. Pickle Files (Local Cache)**
- Location: User's AppData directory
- Format: Python pickle (binary)
- Contents:
  - Table snapshots
  - Cheque reports
  - Processed collections

**Structure:**
```
AppData/Record Matcher/
├── Collections/
│   ├── company_name/
│   │   ├── year/
│   │   │   ├── bank_name/
│   │   │   │   ├── month_name.pkl (TableSnapshot)
│   │   │   │   └── ...
│   │   │   └── cheque_report.pkl (InfiChequeStatement)
│   │   └── ...
│   └── ...
```

**2. Firebase Realtime Database (Cloud)**
- Structure:
```json
{
  "collections": {
    "company_name": {
      "year": {
        "bank_name": {
          "month": {
            "master_table": [...],
            "selected_rows": [...],
            "last_edited_time": "..."
          }
        },
        "cheque_report": {
          "entry_list": [...],
          "year": "...",
          "company": "..."
        }
      }
    }
  }
}
```

**3. Excel Files (Import/Export)**
- Bank statements (input)
- Cheque reports (input)
- Reconciliation results (output)
- Daybooks (output)
- Tally XML (output)

**4. JSON Configuration**
- `data.json`: Application configuration
  - Companies list
  - Banks list
  - Years list
  - Months list
  - Admin password

### Data Flow Between Layers
```
Excel Import → InMemory Objects → Pickle Cache → Firebase Cloud
                                       ↓
                                    QML UI Display
```

---

## Error Handling Strategy

### Exception Hierarchy
```
Exception (Python base)
    │
    ├── ValidationError
    │   └── User input validation failures
    │
    ├── FileOperationError
    │   └── File I/O errors
    │
    ├── SnapshotError
    │   └── Snapshot save/load failures
    │
    └── DatabaseError
        └── Firebase operation failures
```

### Logging Levels
- **DEBUG**: Detailed operation flow, state changes
- **INFO**: Major operations, success messages
- **WARNING**: Non-critical issues, validation failures
- **ERROR**: Failures requiring attention, with stack traces

### Error Reporting
```
Error Occurs
    ↓
Log error (with stack trace)
    ↓
Emit signal to UI (error code)
    ↓
QML displays user-friendly message
    ↓
User can retry or cancel
```

### Validation Error Codes
```python
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
```

---

## Integration Points

### 1. QML ↔ Python (PySide2)
**Mechanism:** Signals and Slots

**Python → QML:**
```python
# Signal definition
validationError = Signal(int, arguments=['type'])

# Emit signal
self.validationError.emit(error_code)
```

**QML → Python:**
```qml
// Call Python slot
backend.uploadFile(fileUrl)

// Handle Python signal
Connections {
    target: backend
    onValidationError: {
        // Show error message
    }
}
```

### 2. Firebase Integration
**Authentication:** Service account JSON
**Operations:** Async with retry logic
**Data Format:** JSON serialization

### 3. Excel Integration
**Libraries:**
- xlrd: Reading .xls and .xlsx files
- xlwt: Writing .xls files
- openpyxl: Alternative for .xlsx (future migration)

**Resource Management:**
```python
try:
    workbook = xlrd.open_workbook(path)
    # ... process data
finally:
    workbook.release_resources()  # Prevent memory leaks
```

### 4. File System
**Paths:** Using pathlib.Path for cross-platform compatibility
**Temp Files:** `./temp/` directory for intermediate files
**Config:** `data.json` for application configuration

---

## Performance Considerations

### Optimization Strategies

**1. Caching**
- JsonDataLoader: Singleton with file modification time check
- Avoid repeated data.json reads

**2. Threading**
- Long operations run in background threads
- UI remains responsive during processing

**3. Memory Management**
- Excel resources released after use
- Weak references for futures tracking
- Explicit cleanup on shutdown

**4. Data Processing**
- pandas for efficient table operations
- Vectorized operations where possible
- Chunking for large datasets (planned)

### Known Limitations
- Single-threaded matching algorithm (sequential)
- Full table loaded into memory (no pagination)
- Pickle files can grow large
- No database indexing for searches

---

## Future Architecture Improvements

### Planned Enhancements
1. **Migration to SQLite**
   - Replace pickle with SQLite database
   - Indexed searches
   - Better concurrent access

2. **Async Firebase Operations**
   - Non-blocking database calls
   - Connection pooling
   - Batch operations

3. **Modular Architecture**
   - Split TableOperations into focused classes
   - Service layer separation
   - Repository pattern for data access

4. **Improved State Management**
   - Centralized state manager
   - Immutable state objects
   - State validation

5. **Testing Infrastructure**
   - Unit tests with pytest
   - Integration tests
   - UI automation tests

---

## Glossary

**Terms:**
- **Infi/InfiBooks**: Accounting software used by clients
- **Cheque Report**: List of issued cheques from accounting system
- **Bank Statement**: Transaction list from bank
- **Reconciliation**: Matching cheque report with bank statement
- **Snapshot**: Saved state of reconciliation table
- **Collection**: Group of related snapshots (by company/year/bank/month)
- **Daybook**: Accounting ledger showing all transactions
- **Tally**: Popular accounting software (export target)
- **Voucher**: Accounting transaction entry

---

## Modern Architecture Layer (December 9, 2025)

### Overview
A comprehensive architectural improvement was implemented following modern software engineering best practices. This new layer sits alongside the existing architecture, providing a migration path while maintaining backward compatibility.

### New Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Presentation Layer (UI)                    │
│              main.py, QML Components                     │
│  • MainWindow: UI controller & event dispatcher         │
│  • TableBackend: Table operations UI binding            │
│  • Signals/Slots: Qt communication mechanism            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Service Layer                           │
│                   services.py                            │
│  • StateManagementService: State & validation           │
│  • FileOperationService: File I/O operations            │
│  • TablePopulationService: Data loading                 │
│  • SearchService: Search & filtering                    │
│  • SyncService: Firebase coordination                   │
│  • ChequeReportService: Cheque logic                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Domain/Core Layer                           │
│             core.py, models.py                           │
│  • TableOperations: Facade for backward compat          │
│  • Data Models: Type-safe dataclasses                   │
│  • Business Entities: TableSnapshot, etc.               │
│  • Domain Logic: Matching algorithms                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               Data Access Layer                          │
│                repositories.py                           │
│  • ISnapshotRepository: Abstract interface              │
│  • IChequeReportRepository: Abstract interface          │
│  • IConfigRepository: Abstract interface                │
│  • Concrete implementations: Pickle, JSON               │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns Implemented

#### 1. Repository Pattern
**Purpose:** Abstract data persistence behind clean interfaces

**Structure:**
- Abstract base classes (`ISnapshotRepository`, `IChequeReportRepository`, `IConfigRepository`)
- Concrete implementations (`PickleSnapshotRepository`, `PickleChequeReportRepository`, `JsonConfigRepository`)
- Dependency injection for flexibility

**Benefits:**
- Business logic decoupled from storage mechanism
- Easy to mock for testing
- Can swap pickle → database without changing business logic
- Centralized data access

#### 2. Service Layer Pattern
**Purpose:** Encapsulate business logic in reusable services

**Services:**
1. **StateManagementService** - Application state and validation
2. **FileOperationService** - File upload/export operations
3. **TablePopulationService** - Data loading and UI preparation
4. **SearchService** - Search and filtering
5. **SyncService** - Firebase synchronization
6. **ChequeReportService** - Cheque report management

**Benefits:**
- Single Responsibility Principle
- Testable in isolation
- Reusable across different UIs
- Clear API boundaries

#### 3. Data Transfer Objects (DTOs)
**Purpose:** Type-safe, immutable data structures

**Key Models:**
- `BankStatementEntry` (frozen): Bank transaction with validation
- `ChequeReportEntry` (frozen): Cheque entry immutable data
- `TableSnapshotData`: Complete snapshot state
- `ApplicationState`: Current app state with validation methods
- `UIDisplayData`: Aggregated display data
- `ValidationResult`: Standardized validation responses
- `SearchResult`: Typed search results

**Benefits:**
- Type safety catches errors at development time
- IDE autocomplete support
- Self-documenting code
- Prevents accidental mutations

#### 4. Facade Pattern
**Purpose:** Maintain backward compatibility during refactoring

**Implementation:**
- `TableOperations` acts as facade over new services
- Delegates to specialized services
- Maintains original interface
- Allows gradual migration

### Thread Safety Architecture

All new components implement comprehensive thread safety:

**Mechanisms:**
1. **Locks:** Each service has `_lock` protecting shared state
2. **Lock Context Managers:** Proper acquisition/release with `with`
3. **Immutable Data:** Frozen dataclasses prevent mutation
4. **Copy-on-Read:** State services return copies

**Example:**
```python
class StateManagementService:
    def __init__(self):
        self.state = ApplicationState()
        self._state_lock = threading.Lock()
    
    def get_state(self) -> ApplicationState:
        with self._state_lock:
            return ApplicationState(...)  # Return copy
```

### Error Handling Strategy

Consistent error handling across all layers:

**Validation Layer:**
- `ValidationResult` objects with success/failure factory methods
- Enum-based error codes (`ValidationErrorType`)
- Human-readable messages

**Repository Layer:**
- Return tuples: `(success: bool, error_code: int)`
- Standard error codes: 0=success, -1=serialization, -2=file, -3=other
- Health check methods

**Service Layer:**
- Comprehensive try/except with logging
- Convert exceptions to user-friendly codes
- Return typed results
- Stack traces for debugging

### Logging Architecture

Comprehensive logging throughout:

**Configuration:**
```python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('record_matcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
```

**Levels:**
- DEBUG: Detailed debugging info
- INFO: General informational messages
- WARNING: Non-critical issues
- ERROR: Errors with stack traces

### Testing Strategy

The new architecture enables comprehensive testing:

**Unit Testing:**
- Services testable in isolation
- Mock repositories for data layer
- Typed contracts verify interfaces

**Integration Testing:**
- Test workflows across layers
- Use real repositories with test data
- Verify end-to-end functionality

**Example:**
```python
def test_upload_workflow():
    # Arrange
    state_service = StateManagementService()
    file_service = FileOperationService(mock_table_ops)
    state_service.update_all_required_fields()
    
    # Act
    validation = state_service.validate_for_upload()
    success, code = file_service.process_upload(path, False)
    
    # Assert
    assert validation.is_valid
    assert success
```

### Migration Path

**Phase 1: Infrastructure (COMPLETED)**
- ✅ Created models.py with 14 dataclass models
- ✅ Created repositories.py with abstract interfaces
- ✅ Created services.py with 6 service classes
- ✅ All backward compatible with existing code

**Phase 2: Integration (IN PROGRESS)**
- ⏳ Update MainWindow to use services
- ⏳ Replace dictionaries with data models
- ⏳ Remove business logic from UI layer

**Phase 3: Optimization (FUTURE)**
- Add caching layer
- Implement database repository
- Add async operations
- Performance profiling

### Benefits Summary

1. **Type Safety:** Dataclasses catch errors at development time
2. **Separation of Concerns:** Clear layer boundaries
3. **Testability:** Each component testable in isolation
4. **Maintainability:** Single responsibility per class
5. **Flexibility:** Easy to swap implementations
6. **Documentation:** Self-documenting with types
7. **Modern Practices:** Industry-standard patterns

### Files Added

| File | Purpose | Lines | Key Classes |
|------|---------|-------|-------------|
| models.py | Data models | ~550 | 14 dataclasses, 2 enums |
| repositories.py | Data access | ~750 | 4 interfaces, 3 implementations |
| services.py | Business logic | ~850 | 6 service classes |
| ARCHITECTURE.md | Documentation | This file | - |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | Dec 9, 2025 | Added service layer, repository pattern, data models |
| 2.0 | Dec 2025 | Threading improvements, logging, validation, documentation |
| 1.0 | - | Initial release |

---

## Contact & Support

For architectural questions or suggestions, contact the development team.

**Documentation maintained by:** Custom Documentation Agent  
**Last architectural review:** December 9, 2025
