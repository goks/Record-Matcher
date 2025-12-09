"""Data models for the Record Matcher application.

This module defines type-safe data models using Python dataclasses to replace
dictionary-based data structures throughout the application. These models provide:
- Type safety and IDE autocomplete support
- Validation and default values
- Immutability options for critical data
- Clear documentation of data structures
- Easy serialization/deserialization

Classes:
    BankStatementEntry: Represents a single bank statement transaction
    ChequeReportEntry: Represents a single cheque report entry from Infi
    TableSnapshotData: Immutable snapshot of table state
    SearchResult: Result of a search operation
    ValidationResult: Result of validation operations
    ExportConfig: Configuration for export operations
    DaybookConfig: Configuration for daybook generation
    FirebaseSyncProgress: Progress tracking for Firebase operations
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum


class BankType(Enum):
    """Supported bank types for statement processing."""
    HDFC = "hdfc"
    ICICI = "icici"
    
    @classmethod
    def from_string(cls, value: str) -> 'BankType':
        """Convert string to BankType enum.
        
        Args:
            value: Bank name string (case-insensitive)
            
        Returns:
            BankType enum value
            
        Raises:
            ValueError: If bank type is not supported
        """
        value_lower = value.lower()
        for bank in cls:
            if bank.value == value_lower:
                return bank
        raise ValueError(f"Unsupported bank type: {value}")


class ValidationErrorType(Enum):
    """Validation error types with codes matching existing system."""
    COMPANY_YEAR_MISSING = 1
    CHEQUE_REPORT_SAVE_FAILED = 2
    BANK_MONTH_MISSING = 3
    NO_SNAPSHOT_AVAILABLE = 4
    INVALID_FILE_FORMAT = 5
    FILE_NOT_FOUND = 6
    EXPORT_FAILED = 7
    DATA_VALIDATION_FAILED = 8


@dataclass(frozen=True)
class BankStatementEntry:
    """Represents a single transaction from a bank statement.
    
    Immutable data class representing one row from HDFC or ICICI bank statements.
    Contains all transaction details needed for reconciliation.
    
    Attributes:
        date: Transaction date (format: DD/MM/YYYY or parsed date string)
        narration: Transaction description/narration
        cheque_number: Cheque number (if applicable, empty string otherwise)
        value_date: Value date of transaction
        debit: Debit amount (empty string if credit transaction)
        credit: Credit amount (empty string if debit transaction)
        balance: Account balance after transaction
    """
    date: str
    narration: str
    cheque_number: str
    value_date: str
    debit: str
    credit: str
    balance: str
    
    def to_list(self) -> List[str]:
        """Convert to list format for backward compatibility.
        
        Returns:
            List containing all fields in order
        """
        return [
            self.date,
            self.narration,
            self.cheque_number,
            self.value_date,
            self.debit,
            self.credit,
            self.balance
        ]
    
    @classmethod
    def from_list(cls, data: List[str]) -> 'BankStatementEntry':
        """Create BankStatementEntry from list format.
        
        Args:
            data: List with 7 elements [date, narration, chq_no, value_date, debit, credit, balance]
            
        Returns:
            BankStatementEntry instance
            
        Raises:
            ValueError: If data list doesn't have exactly 7 elements
        """
        if len(data) != 7:
            raise ValueError(f"Expected 7 elements, got {len(data)}")
        return cls(
            date=data[0],
            narration=data[1],
            cheque_number=data[2],
            value_date=data[3],
            debit=data[4],
            credit=data[5],
            balance=data[6]
        )
    
    def is_debit_transaction(self) -> bool:
        """Check if this is a debit transaction."""
        return bool(self.debit and self.debit.strip())
    
    def is_credit_transaction(self) -> bool:
        """Check if this is a credit transaction."""
        return bool(self.credit and self.credit.strip())


@dataclass(frozen=True)
class ChequeReportEntry:
    """Represents a single entry from Infi cheque statement.
    
    Immutable data class for cheque report entries used in matching algorithm.
    
    Attributes:
        trans_date: Transaction date (format: DD/MM/YYYY)
        trans_no: Transaction number
        book: Book reference
        code: Account/ledger code
        ledger_name: Ledger/account name
        chq_no: Cheque number
        chq_date: Cheque date
        transtype_voucher: Transaction type and voucher info
        narration: Transaction narration/description
        debit: Debit amount
        credit: Credit amount
    """
    trans_date: str
    trans_no: str
    book: str
    code: str
    ledger_name: str
    chq_no: str
    chq_date: str
    transtype_voucher: str
    narration: str
    debit: str
    credit: str
    
    def to_list(self) -> List[str]:
        """Convert to list format for backward compatibility."""
        return [
            self.trans_date,
            self.trans_no,
            self.book,
            self.code,
            self.ledger_name,
            self.chq_no,
            self.chq_date,
            self.transtype_voucher,
            self.narration,
            self.debit,
            self.credit
        ]
    
    @classmethod
    def from_list(cls, data: List[str]) -> 'ChequeReportEntry':
        """Create ChequeReportEntry from list format.
        
        Args:
            data: List with 11 elements
            
        Returns:
            ChequeReportEntry instance
        """
        if len(data) != 11:
            raise ValueError(f"Expected 11 elements, got {len(data)}")
        return cls(
            trans_date=data[0],
            trans_no=data[1],
            book=data[2],
            code=data[3],
            ledger_name=data[4],
            chq_no=data[5],
            chq_date=data[6],
            transtype_voucher=data[7],
            narration=data[8],
            debit=data[9],
            credit=data[10]
        )


@dataclass
class TableSnapshotData:
    """Represents a snapshot of the reconciliation table state.
    
    Contains all data needed to save and restore a bank reconciliation session.
    
    Attributes:
        month: Month name (lowercase)
        year: Year as string
        bank: Bank name (lowercase)
        company: Company name (lowercase)
        master_table: List of all transaction entries (as lists for compatibility)
        master_selected_rows: List of row indices that are selected/matched
        master_excel_export_path: Path to exported Excel file (if any)
        creation_time: Timestamp when snapshot was created
        last_edited_time: Timestamp of last edit
    """
    month: str
    year: str
    bank: str
    company: str
    master_table: List[List[str]]
    master_selected_rows: List[int] = field(default_factory=list)
    master_excel_export_path: Optional[str] = None
    creation_time: Optional[str] = None
    last_edited_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'month': self.month,
            'year': self.year,
            'bank': self.bank,
            'company': self.company,
            'master_table': self.master_table,
            'master_selected_rows': self.master_selected_rows,
            'master_excel_export_path': self.master_excel_export_path,
            'creation_time': self.creation_time,
            'last_edited_time': self.last_edited_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableSnapshotData':
        """Create TableSnapshotData from dictionary."""
        return cls(
            month=data['month'],
            year=data['year'],
            bank=data['bank'],
            company=data['company'],
            master_table=data['master_table'],
            master_selected_rows=data.get('master_selected_rows', []),
            master_excel_export_path=data.get('master_excel_export_path'),
            creation_time=data.get('creation_time'),
            last_edited_time=data.get('last_edited_time')
        )
    
    def get_reference_key(self) -> str:
        """Get unique reference key for this snapshot."""
        return f"{self.company}_{self.month}_{self.year}_{self.bank}"


@dataclass
class SearchResult:
    """Result of a search operation on table data.
    
    Attributes:
        filtered_data: Table data matching search criteria
        credit_balance: Sum of credit amounts in filtered data
        debit_balance: Sum of debit amounts in filtered data
        row_count: Number of rows in filtered data
    """
    filtered_data: List[List[str]]
    credit_balance: str
    debit_balance: str
    row_count: int = field(init=False)
    
    def __post_init__(self):
        """Calculate row count after initialization."""
        self.row_count = len(self.filtered_data)


@dataclass
class ValidationResult:
    """Result of a validation operation.
    
    Attributes:
        is_valid: Whether validation passed
        error_code: Error code if validation failed (None if valid)
        error_message: Human-readable error message
        data: Additional data related to validation (optional)
    """
    is_valid: bool
    error_code: Optional[int] = None
    error_message: str = ""
    data: Any = None
    
    @classmethod
    def success(cls, data: Any = None) -> 'ValidationResult':
        """Create a successful validation result."""
        return cls(is_valid=True, data=data)
    
    @classmethod
    def failure(cls, error_code: int, error_message: str, data: Any = None) -> 'ValidationResult':
        """Create a failed validation result."""
        return cls(
            is_valid=False,
            error_code=error_code,
            error_message=error_message,
            data=data
        )


@dataclass
class ExportConfig:
    """Configuration for table export operations.
    
    Attributes:
        output_path: Destination file path for export
        include_all: Whether to include all rows
        include_selected: Whether to include selected rows sheet
        include_unselected: Whether to include unselected rows sheet
        include_matched: Whether to include matched rows sheet
        include_unmatched: Whether to include unmatched rows sheet
        sheet_names: Custom names for sheets (optional)
    """
    output_path: str
    include_all: bool = True
    include_selected: bool = True
    include_unselected: bool = True
    include_matched: bool = True
    include_unmatched: bool = True
    sheet_names: Optional[Dict[str, str]] = None
    
    def get_sheet_name(self, sheet_type: str, default: str) -> str:
        """Get sheet name for a given type, falling back to default."""
        if self.sheet_names and sheet_type in self.sheet_names:
            return self.sheet_names[sheet_type]
        return default


@dataclass
class DaybookConfig:
    """Configuration for daybook generation.
    
    Attributes:
        output_path: Destination file path for daybook
        from_date: Start date for daybook (format: DD/MM/YYYY)
        to_date: End date for daybook (format: DD/MM/YYYY)
        company: Company name for daybook
        include_voucher_details: Whether to include detailed voucher info
        tally_format: Whether to format for Tally import
    """
    output_path: str
    from_date: str
    to_date: str
    company: str
    include_voucher_details: bool = True
    tally_format: bool = False
    
    def validate_dates(self) -> ValidationResult:
        """Validate date format and range.
        
        Returns:
            ValidationResult indicating if dates are valid
        """
        from dateutil.parser import parse
        try:
            from_dt = parse(self.from_date, dayfirst=True)
            to_dt = parse(self.to_date, dayfirst=True)
            
            if from_dt > to_dt:
                return ValidationResult.failure(
                    error_code=8,
                    error_message="From date cannot be after to date"
                )
            
            return ValidationResult.success()
        except Exception as e:
            return ValidationResult.failure(
                error_code=8,
                error_message=f"Invalid date format: {str(e)}"
            )


@dataclass
class FirebaseSyncProgress:
    """Progress tracking for Firebase sync operations.
    
    Attributes:
        operation: Description of current operation
        stage: Current stage of the operation
        progress: Progress value (0.0 to 1.0)
        items_processed: Number of items processed
        total_items: Total number of items to process
        error: Error message if operation failed
    """
    operation: str
    stage: str
    progress: float
    items_processed: int = 0
    total_items: int = 0
    error: Optional[str] = None
    
    def is_complete(self) -> bool:
        """Check if operation is complete."""
        return self.progress >= 1.0
    
    def has_error(self) -> bool:
        """Check if operation has error."""
        return self.error is not None
    
    def get_percentage(self) -> int:
        """Get progress as percentage (0-100)."""
        return int(self.progress * 100)


@dataclass
class ApplicationState:
    """Represents the current state of the application UI.
    
    This model captures the current selections and mode of the application,
    providing a single source of truth for state management.
    
    Attributes:
        current_month: Selected month (lowercase)
        current_year: Selected year
        current_bank: Selected bank (lowercase)
        current_company: Selected company (lowercase)
        cheque_report_activated: Whether in cheque report mode
        tally_export_activated: Whether in Tally export mode
        search_mode_off_first_time: Flag for search initialization
    """
    current_month: str = ''
    current_year: str = ''
    current_bank: str = ''
    current_company: str = ''
    cheque_report_activated: bool = False
    tally_export_activated: bool = False
    search_mode_off_first_time: bool = False
    
    def is_ready_for_bank_statement(self) -> bool:
        """Check if all required selections are made for bank statement mode."""
        return all([
            self.current_month,
            self.current_year,
            self.current_bank,
            self.current_company
        ])
    
    def is_ready_for_cheque_report(self) -> bool:
        """Check if all required selections are made for cheque report mode."""
        return all([
            self.current_year,
            self.current_company
        ])
    
    def get_validation_error(self) -> Optional[ValidationErrorType]:
        """Get validation error for current state, if any.
        
        Returns:
            ValidationErrorType if state is invalid, None if valid
        """
        if not self.current_company or not self.current_year:
            return ValidationErrorType.COMPANY_YEAR_MISSING
        
        if not self.cheque_report_activated:
            if not self.current_bank or not self.current_month:
                return ValidationErrorType.BANK_MONTH_MISSING
        
        return None


@dataclass
class UIDisplayData:
    """Data prepared for UI display.
    
    Aggregates all the data that needs to be displayed in the UI,
    simplifying the interface between business logic and presentation layer.
    
    Attributes:
        table_data: List of rows to display in table
        credit_balance: Formatted credit balance string
        debit_balance: Formatted debit balance string
        header: Column headers for table
        selected_rows: List of selected row indices
        month_year_data: Formatted month/year display string
        company_data: Formatted company display string
        bank_data: Formatted bank display string
        start_date: Start date of data range
        end_date: End date of data range
    """
    table_data: List[List[str]] = field(default_factory=list)
    credit_balance: str = "Credit Bal"
    debit_balance: str = "Debit Bal"
    header: List[str] = field(default_factory=list)
    selected_rows: List[int] = field(default_factory=list)
    month_year_data: str = ""
    company_data: str = ""
    bank_data: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
