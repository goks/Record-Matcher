"""
Excel Compatibility Layer for openpyxl Migration

This module provides compatibility wrappers to ease migration from xlrd/xlwt to openpyxl.
It maintains similar APIs while using modern openpyxl under the hood.

Migration Path:
- xlrd (deprecated for .xlsx) → openpyxl for reading
- xlwt (deprecated, .xls only) → openpyxl for writing

Author: Custom Documentation Agent
Date: December 9, 2025
"""

import logging
from typing import Any, Optional, Union, List
from pathlib import Path
import datetime

import openpyxl
from openpyxl.workbook import Workbook as OpenpyxlWorkbook
from openpyxl.worksheet.worksheet import Worksheet as OpenpyxlWorksheet
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
try:
    import xlrd  # Optional: used only for legacy .xls reads
except Exception:
    xlrd = None

logger = logging.getLogger(__name__)


class ExcelWorkbookReader:
    """
    Compatibility wrapper for reading Excel files using openpyxl.
    
    Provides xlrd-like API for reading .xlsx files.
    
    Example:
        >>> wb = ExcelWorkbookReader("data.xlsx")
        >>> sheet = wb.sheet_by_index(0)
        >>> value = sheet.cell(0, 0).value
    """
    
    def __init__(self, filename: Union[str, Path], data_only: bool = True):
        """
        Open Excel workbook for reading.
        
        Args:
            filename: Path to Excel file (.xlsx)
            data_only: If True, read cell values instead of formulas
        """
        self.filename = str(filename)
        self.workbook = openpyxl.load_workbook(
            self.filename,
            data_only=data_only,
            read_only=False  # Allow modifications if needed
        )
        self.worksheets = list(self.workbook.worksheets)
        logger.debug(f"Opened workbook: {self.filename} with {len(self.worksheets)} sheets")
    
    def sheet_by_index(self, index: int) -> 'ExcelWorksheetReader':
        """Get worksheet by index (0-based)."""
        if index < 0 or index >= len(self.worksheets):
            raise IndexError(f"Sheet index {index} out of range (0-{len(self.worksheets)-1})")
        return ExcelWorksheetReader(self.worksheets[index])
    
    def sheet_by_name(self, name: str) -> 'ExcelWorksheetReader':
        """Get worksheet by name."""
        if name not in self.workbook.sheetnames:
            raise ValueError(f"Sheet '{name}' not found. Available: {self.workbook.sheetnames}")
        return ExcelWorksheetReader(self.workbook[name])
    
    @property
    def sheet_names(self) -> List[str]:
        """Get list of sheet names."""
        return self.workbook.sheetnames
    
    @property
    def nsheets(self) -> int:
        """Get number of sheets."""
        return len(self.worksheets)
    
    def release_resources(self):
        """Release workbook resources (close file)."""
        if hasattr(self, 'workbook') and self.workbook:
            self.workbook.close()
            logger.debug(f"Released resources for: {self.filename}")
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.release_resources()
        return False


class ExcelWorkbookReaderXls:
    """
    Compatibility wrapper for reading legacy .xls files using xlrd.
    """

    def __init__(self, filename: Union[str, Path]):
        if xlrd is None:
            raise ImportError("xlrd is required for .xls support but is not installed.")
        self.filename = str(filename)
        self.workbook = xlrd.open_workbook(self.filename, formatting_info=False)
        self.worksheets = [self.workbook.sheet_by_index(i) for i in range(self.workbook.nsheets)]
        self._datemode = self.workbook.datemode
        logger.debug(f"Opened legacy workbook: {self.filename} with {len(self.worksheets)} sheets")

    def sheet_by_index(self, index: int) -> 'ExcelWorksheetReaderXls':
        if index < 0 or index >= len(self.worksheets):
            raise IndexError(f"Sheet index {index} out of range (0-{len(self.worksheets)-1})")
        return ExcelWorksheetReaderXls(self.worksheets[index], self._datemode)

    def sheet_by_name(self, name: str) -> 'ExcelWorksheetReaderXls':
        try:
            sheet = self.workbook.sheet_by_name(name)
        except Exception:
            raise ValueError(f"Sheet '{name}' not found.")
        return ExcelWorksheetReaderXls(sheet, self._datemode)

    @property
    def sheet_names(self) -> List[str]:
        return self.workbook.sheet_names()

    @property
    def nsheets(self) -> int:
        return self.workbook.nsheets

    def release_resources(self):
        # xlrd workbook doesn't need explicit close.
        self.workbook = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release_resources()
        return False


class ExcelWorksheetReaderXls:
    """xlrd-based worksheet reader with xlrd-like API."""

    def __init__(self, worksheet, datemode: int):
        self.worksheet = worksheet
        self._nrows = worksheet.nrows
        self._ncols = worksheet.ncols
        self._datemode = datemode

    def cell(self, rowx: int, colx: int) -> 'ExcelCellXls':
        raw_cell = self.worksheet.cell(rowx, colx)
        return ExcelCellXls(raw_cell, self._datemode)

    @property
    def nrows(self) -> int:
        return self._nrows

    @property
    def ncols(self) -> int:
        return self._ncols

    @property
    def name(self) -> str:
        return self.worksheet.name


class ExcelCellXls:
    """Cell wrapper for xlrd cells."""

    def __init__(self, cell, datemode: int):
        self._cell = cell
        self._datemode = datemode

    @property
    def value(self) -> Any:
        val = self._cell.value
        ctype = self._cell.ctype

        if ctype == 0 or val is None:
            return ''
        if ctype == 3 and xlrd is not None:
            # Convert Excel serial date to datetime for downstream date parsing.
            try:
                dt = xlrd.xldate_as_datetime(val, self._datemode)
                if isinstance(dt, datetime.datetime):
                    return dt.strftime("%d/%m/%Y")
            except Exception:
                return val
        return val

    @property
    def ctype(self) -> int:
        return self._cell.ctype


class ExcelWorksheetReader:
    """
    Compatibility wrapper for reading Excel worksheets.
    
    Provides xlrd-like API for accessing cells.
    """
    
    def __init__(self, worksheet: OpenpyxlWorksheet):
        """
        Initialize worksheet reader.
        
        Args:
            worksheet: openpyxl Worksheet object
        """
        self.worksheet = worksheet
        self._nrows = worksheet.max_row
        self._ncols = worksheet.max_column
    
    def cell(self, rowx: int, colx: int) -> 'ExcelCell':
        """
        Get cell at position (row, col) - 0-indexed.
        
        Args:
            rowx: Row index (0-based)
            colx: Column index (0-based)
            
        Returns:
            ExcelCell wrapper
        """
        # openpyxl uses 1-indexed, xlrd uses 0-indexed
        openpyxl_cell = self.worksheet.cell(row=rowx + 1, column=colx + 1)
        return ExcelCell(openpyxl_cell)
    
    @property
    def nrows(self) -> int:
        """Get number of rows."""
        return self._nrows
    
    @property
    def ncols(self) -> int:
        """Get number of columns."""
        return self._ncols
    
    @property
    def name(self) -> str:
        """Get worksheet name."""
        return self.worksheet.title


class ExcelCell:
    """
    Compatibility wrapper for Excel cells.
    
    Provides xlrd-like API for cell values.
    """
    
    def __init__(self, cell):
        """
        Initialize cell wrapper.
        
        Args:
            cell: openpyxl Cell object
        """
        self._cell = cell
    
    @property
    def value(self) -> Any:
        """Get cell value."""
        val = self._cell.value
        # Handle None values
        if val is None:
            return ''
        return val
    
    @property
    def ctype(self) -> int:
        """
        Get cell type (xlrd compatibility).
        
        Types:
            0: Empty
            1: Text
            2: Number
            3: Date
            4: Boolean
            5: Error
        """
        if self._cell.value is None:
            return 0  # Empty
        elif isinstance(self._cell.value, str):
            return 1  # Text
        elif isinstance(self._cell.value, (int, float)):
            return 2  # Number
        elif isinstance(self._cell.value, bool):
            return 4  # Boolean
        else:
            return 1  # Default to text


class ExcelWorkbookWriter:
    """
    Compatibility wrapper for writing Excel files using openpyxl.
    
    Provides xlwt-like API for writing .xlsx files.
    
    Example:
        >>> wb = ExcelWorkbookWriter()
        >>> sheet = wb.add_sheet("Sheet1")
        >>> sheet.write(0, 0, "Hello")
        >>> wb.save("output.xlsx")
    """
    
    def __init__(self):
        """Initialize new Excel workbook for writing."""
        self.workbook = OpenpyxlWorkbook()
        # Remove default sheet
        if 'Sheet' in self.workbook.sheetnames:
            del self.workbook['Sheet']
        self.worksheets = {}
        logger.debug("Created new workbook for writing")
    
    def add_sheet(self, name: str, cell_overwrite_ok: bool = True) -> 'ExcelWorksheetWriter':
        """
        Add new worksheet.
        
        Args:
            name: Sheet name
            cell_overwrite_ok: Ignored (openpyxl always allows overwrite)
            
        Returns:
            ExcelWorksheetWriter wrapper
        """
        if name in self.worksheets:
            logger.warning(f"Sheet '{name}' already exists, returning existing sheet")
            return self.worksheets[name]
        
        worksheet = self.workbook.create_sheet(title=name)
        writer = ExcelWorksheetWriter(worksheet)
        self.worksheets[name] = writer
        logger.debug(f"Added sheet: {name}")
        return writer
    
    def save(self, filename: Union[str, Path]):
        """
        Save workbook to file.
        
        Args:
            filename: Output file path (.xlsx)
        """
        filename = str(filename)
        # Ensure .xlsx extension
        if not filename.lower().endswith('.xlsx'):
            logger.warning(f"File '{filename}' doesn't end with .xlsx, appending extension")
            filename += '.xlsx'
        
        self.workbook.save(filename)
        logger.info(f"Saved workbook to: {filename}")
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        # Workbook doesn't need explicit closing for writing
        return False


class ExcelWorksheetWriter:
    """
    Compatibility wrapper for writing to Excel worksheets.
    
    Provides xlwt-like API for writing cells.
    """
    
    def __init__(self, worksheet: OpenpyxlWorksheet):
        """
        Initialize worksheet writer.
        
        Args:
            worksheet: openpyxl Worksheet object
        """
        self.worksheet = worksheet
    
    def write(
        self, 
        rowx: int, 
        colx: int, 
        value: Any,
        style: Optional[Any] = None
    ):
        """
        Write value to cell at position (row, col) - 0-indexed.
        
        Args:
            rowx: Row index (0-based)
            colx: Column index (0-based)
            value: Value to write
            style: Optional cell style (xlwt.XFStyle or dict)
        """
        # openpyxl uses 1-indexed, xlwt uses 0-indexed
        cell = self.worksheet.cell(row=rowx + 1, column=colx + 1)
        cell.value = value
        
        # Apply basic styling if provided
        if style:
            self._apply_style(cell, style)
    
    def _apply_style(self, cell, style):
        """
        Apply cell styling (simplified).
        
        Args:
            cell: openpyxl Cell object
            style: Style specification (dict or xlwt.XFStyle)
        """
        # If style is a dict, apply directly
        if isinstance(style, dict):
            if 'font' in style:
                cell.font = Font(**style['font'])
            if 'alignment' in style:
                cell.alignment = Alignment(**style['alignment'])
            if 'fill' in style:
                cell.fill = PatternFill(**style['fill'])
        # Otherwise assume it's xlwt.XFStyle (ignore for now)
        # Full xlwt.XFStyle conversion can be added if needed
    
    def col(self, colx: int):
        """
        Get column wrapper (for width setting).
        
        Args:
            colx: Column index (0-based)
            
        Returns:
            Column wrapper
        """
        return ExcelColumnWriter(self.worksheet, colx)


class ExcelColumnWriter:
    """Wrapper for column operations."""
    
    def __init__(self, worksheet: OpenpyxlWorksheet, colx: int):
        """
        Initialize column writer.
        
        Args:
            worksheet: openpyxl Worksheet object
            colx: Column index (0-based)
        """
        self.worksheet = worksheet
        self.colx = colx
        self.column_letter = get_column_letter(colx + 1)
    
    @property
    def width(self) -> float:
        """Get column width."""
        return self.worksheet.column_dimensions[self.column_letter].width
    
    @width.setter
    def width(self, value: float):
        """
        Set column width.
        
        Args:
            value: Width in Excel units (character width)
        """
        self.worksheet.column_dimensions[self.column_letter].width = value


# Convenience functions for backward compatibility
def open_workbook(filename: Union[str, Path], **kwargs) -> ExcelWorkbookReader:
    """
    Open Excel workbook for reading (xlrd compatibility).
    
    Args:
        filename: Path to Excel file
        **kwargs: Additional arguments (formatting_info, etc. ignored)
        
    Returns:
        ExcelWorkbookReader instance
    """
    file_path = str(filename)
    if file_path.lower().endswith(".xls") and not file_path.lower().endswith(".xlsx"):
        return ExcelWorkbookReaderXls(file_path)
    return ExcelWorkbookReader(file_path)


def create_workbook() -> ExcelWorkbookWriter:
    """
    Create new Excel workbook for writing (xlwt compatibility).
    
    Returns:
        ExcelWorkbookWriter instance
    """
    return ExcelWorkbookWriter()


# Migration helper
class XlrdXlwtDeprecationHelper:
    """
    Helper class to detect and warn about xlrd/xlwt usage.
    
    Use this during migration to identify code that needs updating.
    """
    
    @staticmethod
    def check_imports(file_path: str) -> List[str]:
        """
        Check Python file for xlrd/xlwt imports.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            List of lines with deprecated imports
        """
        warnings = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if 'import xlrd' in line or 'from xlrd' in line:
                        warnings.append(f"Line {i}: xlrd import (deprecated for .xlsx)")
                    if 'import xlwt' in line or 'from xlwt' in line:
                        warnings.append(f"Line {i}: xlwt import (deprecated, use openpyxl)")
        except Exception as e:
            logger.error(f"Error checking {file_path}: {e}")
        
        return warnings


if __name__ == "__main__":
    # Example usage and testing
    print("=== Excel Compatibility Layer Example ===\n")
    
    # Example 1: Reading Excel file
    print("1. Reading Excel file (xlrd-style API):")
    print("""
    wb = open_workbook("data.xlsx")
    sheet = wb.sheet_by_index(0)
    value = sheet.cell(0, 0).value
    wb.release_resources()
    """)
    
    # Example 2: Writing Excel file
    print("\n2. Writing Excel file (xlwt-style API):")
    print("""
    wb = create_workbook()
    sheet = wb.add_sheet("Sheet1")
    sheet.write(0, 0, "Hello")
    sheet.write(0, 1, "World")
    wb.save("output.xlsx")
    """)
    
    # Example 3: Context manager
    print("\n3. Using context manager:")
    print("""
    with open_workbook("data.xlsx") as wb:
        sheet = wb.sheet_by_index(0)
        for row in range(sheet.nrows):
            for col in range(sheet.ncols):
                print(sheet.cell(row, col).value)
    """)
    
    print("\n=== Migration Benefits ===")
    print("✅ Modern openpyxl under the hood")
    print("✅ .xlsx format support (xlrd deprecated for .xlsx)")
    print("✅ Both read and write in same library")
    print("✅ Better performance and memory usage")
    print("✅ Active maintenance and security updates")
    print("✅ Familiar API for easy migration")
