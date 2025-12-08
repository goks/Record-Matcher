# Record Matcher - Core Features List

**Version:** 2.0  
**Last Updated:** December 8, 2025  
**Status:** Production

---

## Overview
Record Matcher is a bank statement reconciliation and party finder application built with Python and PySide2. It matches bank transactions with cheque reports from Tally/Infi systems and generates reconciliation reports.

---

## Core Features

### 1. Bank Statement Processing
**Status:** ✓ Active  
**Priority:** Critical  
**Dependencies:** Excel libraries (xlrd/openpyxl), pandas

#### Capabilities:
- **HDFC Bank Statement Import**
  - File: `core.py` → `HDFCBankChequeStatement` class
  - Supports .xls and .xlsx formats
  - Auto-detects statement start row
  - Extracts: Date, Narration, Cheque No., Debit, Credit, Balance
  
- **ICICI Bank Statement Import**
  - File: `core.py` → `ICICIBankChequeStatement` class
  - Supports .xls and .xlsx formats
  - Processes narration for cheque number extraction
  - Date format conversion (handles multiple formats)
  - Extracts: Date, Transaction ID, Cheque No., Debit, Credit, Balance

#### Validation:
- File path validation
- Excel format verification
- Data integrity checks
- Date format validation

#### Testing:
- Test files: Valid .xls/.xlsx bank statements required
- Validation functions in `test_suite.py`

---

### 2. Cheque Report Management
**Status:** ✓ Active  
**Priority:** Critical  
**Dependencies:** Excel libraries, Firebase

#### Capabilities:
- **Infi Cheque Statement Import**
  - File: `core.py` → `InfiChequeStatement` class
  - Supports receipt vouchers from Tally/Infi exports
  - Stores: Trans Date, Chq Date, Bank Name, Ledger Name, Chq No, Amount, Narration
  
- **Cheque Report Collection**
  - File: `core.py` → `ChequeReportCollection` class
  - Organizes reports by company and year
  - Persistent storage using pickle
  - Upload/download from Firebase
  - Delete functionality

#### Storage:
- Local: `%APPDATA%\Record Matcher\ChequeReportCollection.fil`
- Cloud: Firebase Realtime Database

---

### 3. Transaction Matching Engine
**Status:** ✓ Active  
**Priority:** Critical  
**Dependencies:** dateutil, pandas

#### Capabilities:
- **Cheque Number Matching**
  - Standardizes cheque numbers to 16 digits
  - Matches bank transactions with cheque reports
  - Handles multiple matches (double matches)
  - Cross-financial-year matching (current + previous year)
  
- **Amount Verification**
  - Matches debit amounts between bank and cheque reports
  - Validates transaction consistency
  
- **Date Validation**
  - Ensures cheque date ≤ bank transaction date
  - Handles multiple date formats
  - Cross-validates transaction and cheque dates

#### Output:
- Matched transactions with party names
- Unmatched transactions flagged
- Double match indicators
- Files: Master table with all matching results

---

### 4. Data Persistence & Synchronization
**Status:** ✓ Active  
**Priority:** High  
**Dependencies:** Firebase Admin SDK, pickle

#### Capabilities:
- **Local Storage**
  - File: `core.py` → `TableSnapshotCollection` class
  - Pickle-based persistence
  - Stores: Bank statements, cheque reports, snapshots
  - Location: `%APPDATA%\Record Matcher\`
  
- **Firebase Sync**
  - File: `core.py` → `FirebaseControls` class
  - Upload/Download snapshots
  - Upload/Download cheque reports
  - Upload/Download configuration (data.json)
  - Real-time database synchronization
  
- **Snapshot Management**
  - File: `core.py` → `TableSnapshot` class
  - Saves state by: Company, Bank, Month, Year
  - Tracks selected rows
  - Stores export paths
  - Maintains creation and edit timestamps

#### Storage Locations:
- Snapshots: `tableSnapshotCollection.filv2`
- Cheque Reports: `ChequeReportCollection.fil`
- Firebase: `/tableSnapshot/`, `/chequeReport/`, `/leftMenu/`

---

### 5. Search & Filtering
**Status:** ✓ Active  
**Priority:** Medium  
**Dependencies:** pandas, dateutil

#### Capabilities:
- **Search by Cheque Number**
  - Partial and exact match
  - Case-insensitive
  - Formatted number search
  
- **Search by Date**
  - Transaction date search
  - Multiple date format support
  - Day/Month/Year matching
  
- **Search by Amount**
  - Credit amount search
  - Debit amount search
  - Exact amount matching

#### Files:
- `core.py` → `TableOperations.search()` method
- `main.py` → `MainWindow.search()` method

---

### 6. Excel Export & Reporting
**Status:** ✓ Active  
**Priority:** High  
**Dependencies:** xlwt, openpyxl

#### Capabilities:
- **Multi-Sheet Export**
  - Sheet 1: Complete statement with selections highlighted
  - Sheet 2: Selected rows only
  - Sheet 3: Unselected rows only
  - Sheet 4: Matched CHQ Receipts (HDFC)
  - Sheet 5: Unmatched CHQ Receipts (HDFC)
  
- **Formatting**
  - Color-coded selected rows (light green)
  - Proper column headers
  - Formatted amounts with locale
  - Auto-open after export

#### Output:
- Excel .xls files
- User-selected location
- Default filename: `123.xls`

---

### 7. Intermediate Daybook Generation
**Status:** ✓ Active  
**Priority:** Medium  
**Dependencies:** pandas, dateutil.relativedelta

#### Capabilities:
- **Consolidated Reports**
  - File: `core.py` → `IntermediateDaybook` class
  - Combines multiple months of data
  - Separates: Receipt vouchers (with/without cheques), Payment vouchers
  - Date range validation (max 12 months)
  
- **Voucher Types**
  - Receipt with cheques: Bank deposits with party info
  - Receipt without cheques: Direct deposits
  - Payment vouchers: Bank withdrawals
  
- **Processing**
  - Files: `ConsolidatedReceiptVouchers`, `ConsolidatedPaymentVouchers`
  - Filters by date range
  - Generates Tally-compatible format
  - Assigns unique voucher IDs

#### Output:
- Excel daybook with voucher entries
- Tally import-ready format
- Temp files for debugging: `./temp/*.xlsx`

---

### 8. User Interface (QML/Qt)
**Status:** ✓ Active  
**Priority:** High  
**Dependencies:** PySide2, QML

#### Capabilities:
- **Left Panel Menu**
  - Company selection
  - Bank selection (HDFC/ICICI)
  - Year selection
  - Month selection
  - Cheque report mode
  - Tally export mode
  
- **Main Table Display**
  - Dynamic data binding
  - Row selection
  - Search functionality
  - Balance display (Credit/Debit)
  - Date range display
  
- **Pages/Views**
  - Table view page
  - Upload statement page
  - Choose options page
  - Cheque report page
  - Tally export page
  
- **Notifications**
  - Success toasts
  - Error dialogs
  - Validation messages
  - Progress indicators (full screen loading)

#### Files:
- `main.py` → `MainWindow` class
- `qml/main.qml` → Main UI
- `qml/controls/*.qml` → UI components

---

### 9. Configuration Management
**Status:** ✓ Active  
**Priority:** High  
**Dependencies:** JSON

#### Capabilities:
- **data.json Configuration**
  - File: `data.json`
  - Stores: Years, Banks, Companies, Months, Admin Password
  - Loaded at startup
  - Synced with Firebase
  - Dynamically updates UI
  
- **JsonDataLoader**
  - File: `core.py` → `JsonDataLoader` class
  - Parses configuration
  - Provides dropdown values
  - Validates selections

#### Configuration Structure:
```json
{
  "Years": [{"name": "2024", "value": "2024"}],
  "Banks": [{"name": "HDFC", "value": "hdfc"}],
  "Companies": [{"name": "Gokul", "value": "gokul"}],
  "Months": [{"name": "January", "value": "january"}],
  "AdminPassword": "password"
}
```

---

### 10. Validation System
**Status:** ✓ Active  
**Priority:** High  
**Dependencies:** datetime, re

#### Functions:
- **File Validation**
  - `validate_path()`: Checks file existence and extension (.xls/.xlsx)
  - `validate_save_path()`: Validates .fil extension
  
- **Data Validation**
  - `validate_date()`: Validates dd/mm/yy format
  - `validate_chqno()`: Checks numeric, max 15 digits
  - `validate_amount()`: Checks numeric, non-negative
  
- **Input Sanitization**
  - File URL processing
  - Path normalization
  - Extension verification

#### Files:
- `core.py` → validation functions
- `test_suite.py` → validation tests

---

### 11. Threading & Background Operations
**Status:** ✓ Active (with issues - see suggestions.md)  
**Priority:** High  
**Dependencies:** threading

#### Capabilities:
- **Async Operations**
  - File uploads (bank statements, cheque reports)
  - File exports
  - Firebase sync (upload/download)
  - Table population
  
- **Progress Callbacks**
  - Real-time progress updates
  - Full-screen loading indicators
  - Status messages
  - Progress bar values

#### Current Implementation:
- Uses daemon threads (needs improvement)
- No thread pool (needs improvement)
- No thread safety locks (needs improvement)

#### Files:
- `main.py` → Various `threaded*()` methods

---

### 12. Financial Year Handling
**Status:** ✓ Active  
**Priority:** Medium

#### Capabilities:
- **Year Calculation**
  - Automatic financial year detection
  - Handles Apr-Mar fiscal year
  - Previous year cheque matching
  
- **Cross-Year Matching**
  - Matches with current year cheque report
  - Falls back to previous year if no match
  - Handles year-end transactions

---

## Feature Dependencies Matrix

| Feature | Depends On | Used By |
|---------|------------|---------|
| Bank Statement Processing | Excel libraries | Transaction Matching |
| Cheque Report Management | Excel libraries, Firebase | Transaction Matching |
| Transaction Matching | Bank Statements, Cheque Reports | Excel Export, UI Display |
| Data Persistence | Pickle, Firebase | All features |
| Search & Filtering | Loaded data | UI Display |
| Excel Export | Matched data | User reporting |
| Daybook Generation | Multiple snapshots | Tally integration |
| UI | All backend features | User interaction |
| Configuration | JSON | All features |
| Validation | - | All input operations |
| Threading | - | Long operations |
| Financial Year | Configuration | Cheque matching |

---

## Known Limitations & Issues
(See `suggestions.md` for detailed optimization recommendations)

1. **Performance**
   - Large Excel files load slowly
   - No pagination in UI
   - Inefficient pandas operations

2. **Security**
   - Hardcoded credentials in source
   - Pickle usage (security risk)
   - No input sanitization

3. **Reliability**
   - Daemon threads can cause data loss
   - No error recovery mechanisms
   - Excel resources not always released

4. **Code Quality**
   - Bare except clauses
   - Missing documentation
   - Deprecated library usage (xlrd/xlwt)

---

## Testing Coverage

### Unit Tests
- `test_suite.py` covers:
  - Validation functions ✓
  - JSON data loading ✓
  - TableSnapshot operations ✓
  - Edge cases ✓
  - Integration scenarios ✓

### Quality Checks
- `quality_check.py` validates:
  - Import issues
  - Error handling
  - Security vulnerabilities
  - Code style
  - Resource management
  - Threading issues
  - Pandas usage

### Manual Testing Required
- Bank statement upload
- Cheque report upload
- Transaction matching accuracy
- Excel export formatting
- Firebase sync
- UI interactions
- Multi-user scenarios

---

## Critical Files

| File | Purpose | Risk Level |
|------|---------|------------|
| `core.py` | All business logic | **CRITICAL** |
| `main.py` | UI controller | **HIGH** |
| `data.json` | Configuration | **HIGH** |
| `qml/main.qml` | Main UI | **MEDIUM** |
| Service account JSON | Firebase auth | **CRITICAL** |

---

## Feature Change Protocol

**Before modifying any feature:**
1. Check this document for dependencies
2. Review affected features
3. Plan testing strategy
4. Document breaking changes
5. Update this document if needed

**After modifying any feature:**
1. Run quality checks: `python quality_check.py`
2. Run unit tests: `python test_suite.py`
3. Test affected features manually
4. Update CHANGELOG.md
5. Update this document if feature changed

---

**Note:** This document should be updated whenever:
- New features are added
- Existing features are modified
- Features are deprecated
- Dependencies change
- Known issues are discovered or resolved
