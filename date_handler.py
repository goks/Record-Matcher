"""
Centralized date handling utilities for Record Matcher application.

This module provides a unified DateHandler class that standardizes all date operations
across the application, including parsing, formatting, validation, and timezone handling.

Key Features:
- Parse dates once and cache results
- Consistent timezone handling (Asia/Kolkata for Indian banking)
- Date range validation
- Multiple format support with smart fallback
- Thread-safe operations
- Pandas integration for vectorized operations

Author: Custom Documentation Agent
Date: December 9, 2025
"""

import datetime
from typing import Union, Optional, Tuple, List
import logging
from functools import lru_cache
import threading

import pandas as pd
import dateutil.parser
import pytz

logger = logging.getLogger(__name__)


class DateValidationError(ValueError):
    """Raised when date validation fails."""
    pass


class DateRangeError(ValueError):
    """Raised when date range validation fails."""
    pass


class DateHandler:
    """
    Centralized date handling utility with timezone support and validation.
    
    This class provides:
    - Consistent date parsing across multiple formats
    - Timezone-aware datetime objects (Asia/Kolkata timezone for Indian banking)
    - Date range validation
    - Caching for frequently parsed dates
    - Thread-safe operations
    - Pandas DataFrame integration
    
    All dates are internally stored as timezone-aware datetime objects and can be
    formatted to various output formats as needed.
    
    Attributes:
        DEFAULT_TIMEZONE: Default timezone for Indian banking operations (Asia/Kolkata)
        SUPPORTED_INPUT_FORMATS: List of supported input date format strings
        DEFAULT_OUTPUT_FORMAT: Standard output format (%d/%m/%Y)
        TALLY_OUTPUT_FORMAT: Format for Tally export (%d-%b-%Y)
    """
    
    # Default timezone for Indian banking operations
    DEFAULT_TIMEZONE = pytz.timezone("Asia/Kolkata")
    
    # Supported input formats (most common first for performance)
    SUPPORTED_INPUT_FORMATS = [
        "%d/%m/%Y",      # 31/12/2025 (most common)
        "%d/%m/%y",      # 31/12/25
        "%d-%m-%Y",      # 31-12-2025
        "%d-%b-%Y",      # 31-Dec-2025 (Tally format)
        "%Y/%m/%d",      # 2025/12/31 (Firebase format)
        "%Y-%m-%d",      # 2025-12-31 (ISO format)
    ]
    
    # Output formats
    DEFAULT_OUTPUT_FORMAT = "%d/%m/%Y"
    TALLY_OUTPUT_FORMAT = "%d-%b-%Y"
    FIREBASE_OUTPUT_FORMAT = "%Y/%m/%d"
    ISO_OUTPUT_FORMAT = "%Y-%m-%d"
    DISPLAY_FORMAT_WITH_TIME = "%d/%m/%Y %I:%M %p"
    
    def __init__(self, timezone: Optional[pytz.tzinfo.BaseTzInfo] = None):
        """
        Initialize DateHandler with optional custom timezone.
        
        Args:
            timezone: Optional pytz timezone object. Defaults to Asia/Kolkata.
        """
        self.timezone = timezone or self.DEFAULT_TIMEZONE
        self._cache_lock = threading.Lock()
        logger.info(f"DateHandler initialized with timezone: {self.timezone}")
    
    @lru_cache(maxsize=1024)
    def parse(
        self, 
        date_str: str, 
        dayfirst: bool = True,
        strict: bool = False
    ) -> datetime.datetime:
        """
        Parse date string to timezone-aware datetime object with caching.
        
        Attempts to parse using supported formats in order. If all fail and strict=False,
        falls back to dateutil.parser for flexible parsing.
        
        Args:
            date_str: Date string to parse
            dayfirst: Whether to interpret ambiguous dates as day-first (default True)
            strict: If True, only use defined formats. If False, use dateutil fallback.
        
        Returns:
            Timezone-aware datetime object
            
        Raises:
            DateValidationError: If date cannot be parsed
            
        Example:
            >>> handler = DateHandler()
            >>> dt = handler.parse("31/12/2025")
            >>> print(dt)
            2025-12-31 00:00:00+05:30
        """
        if not date_str or not isinstance(date_str, str):
            raise DateValidationError(f"Invalid date string: {date_str}")
        
        date_str = date_str.strip()
        
        # Try each supported format
        for fmt in self.SUPPORTED_INPUT_FORMATS:
            try:
                naive_dt = datetime.datetime.strptime(date_str, fmt)
                # Make timezone-aware
                return naive_dt.replace(tzinfo=self.timezone)
            except ValueError:
                continue
        
        # Fallback to flexible parsing if not strict
        if not strict:
            try:
                naive_dt = dateutil.parser.parse(date_str, dayfirst=dayfirst)
                # Make timezone-aware
                return naive_dt.replace(tzinfo=self.timezone)
            except (ValueError, TypeError) as e:
                raise DateValidationError(
                    f"Unable to parse date '{date_str}': {e}"
                )
        
        raise DateValidationError(
            f"Date '{date_str}' does not match any supported format: "
            f"{', '.join(self.SUPPORTED_INPUT_FORMATS)}"
        )
    
    def parse_to_naive(self, date_str: str, dayfirst: bool = True) -> datetime.datetime:
        """
        Parse date string to naive (non-timezone-aware) datetime.
        
        Useful for compatibility with legacy code that expects naive datetime objects.
        
        Args:
            date_str: Date string to parse
            dayfirst: Whether to interpret ambiguous dates as day-first
            
        Returns:
            Naive datetime object (no timezone)
        """
        aware_dt = self.parse(date_str, dayfirst=dayfirst)
        return aware_dt.replace(tzinfo=None)
    
    def format(
        self, 
        dt: datetime.datetime, 
        format_str: Optional[str] = None
    ) -> str:
        """
        Format datetime object to string.
        
        Args:
            dt: Datetime object to format
            format_str: Optional format string. Defaults to DEFAULT_OUTPUT_FORMAT.
            
        Returns:
            Formatted date string
            
        Example:
            >>> handler = DateHandler()
            >>> dt = datetime.datetime(2025, 12, 31)
            >>> handler.format(dt)
            '31/12/2025'
            >>> handler.format(dt, handler.TALLY_OUTPUT_FORMAT)
            '31-Dec-2025'
        """
        if format_str is None:
            format_str = self.DEFAULT_OUTPUT_FORMAT
        
        return dt.strftime(format_str)
    
    def now(self) -> datetime.datetime:
        """
        Get current datetime in configured timezone.
        
        Returns:
            Current timezone-aware datetime
        """
        return datetime.datetime.now(tz=self.timezone)
    
    def now_formatted(self, format_str: Optional[str] = None) -> str:
        """
        Get current datetime as formatted string.
        
        Args:
            format_str: Optional format string. Defaults to DEFAULT_OUTPUT_FORMAT.
            
        Returns:
            Current datetime as formatted string
        """
        return self.format(self.now(), format_str)
    
    def validate_date(self, date_str: str, strict: bool = False) -> bool:
        """
        Validate if string is a parseable date.
        
        Args:
            date_str: Date string to validate
            strict: If True, only accept defined formats
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.parse(date_str, strict=strict)
            return True
        except DateValidationError:
            return False
    
    def validate_date_range(
        self, 
        start_date: Union[str, datetime.datetime],
        end_date: Union[str, datetime.datetime],
        max_months: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Validate date range (start <= end, optional max duration).
        
        Args:
            start_date: Start date (string or datetime)
            end_date: End date (string or datetime)
            max_months: Optional maximum allowed months between dates
            
        Returns:
            Tuple of (is_valid, error_message)
            
        Example:
            >>> handler = DateHandler()
            >>> valid, msg = handler.validate_date_range("01/01/2025", "31/12/2025")
            >>> print(valid)
            True
            >>> valid, msg = handler.validate_date_range("31/12/2025", "01/01/2025")
            >>> print(msg)
            'Start date must be before or equal to end date'
        """
        try:
            # Parse dates if strings
            if isinstance(start_date, str):
                start_dt = self.parse(start_date)
            else:
                start_dt = start_date
            
            if isinstance(end_date, str):
                end_dt = self.parse(end_date)
            else:
                end_dt = end_date
            
            # Check start <= end
            if start_dt > end_dt:
                return False, "Start date must be before or equal to end date"
            
            # Check max duration if specified
            if max_months is not None:
                months_diff = (
                    (end_dt.year - start_dt.year) * 12 + 
                    (end_dt.month - start_dt.month)
                )
                if months_diff > max_months:
                    return False, (
                        f"Date range exceeds maximum of {max_months} months "
                        f"(actual: {months_diff} months)"
                    )
            
            return True, ""
            
        except DateValidationError as e:
            return False, str(e)
    
    def convert_to_datetime(
        self, 
        date_input: Union[str, datetime.datetime, pd.Timestamp],
        dayfirst: bool = True
    ) -> datetime.datetime:
        """
        Convert various date types to timezone-aware datetime.
        
        Handles strings, datetime objects, and pandas Timestamps.
        
        Args:
            date_input: Date in various formats
            dayfirst: Whether to interpret ambiguous dates as day-first
            
        Returns:
            Timezone-aware datetime object
        """
        if isinstance(date_input, str):
            return self.parse(date_input, dayfirst=dayfirst)
        elif isinstance(date_input, pd.Timestamp):
            dt = date_input.to_pydatetime()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=self.timezone)
            return dt
        elif isinstance(date_input, datetime.datetime):
            if date_input.tzinfo is None:
                return date_input.replace(tzinfo=self.timezone)
            return date_input
        else:
            raise DateValidationError(
                f"Unsupported date type: {type(date_input)}"
            )
    
    def parse_dataframe_dates(
        self,
        df: pd.DataFrame,
        column: str,
        formats: Optional[List[str]] = None,
        errors: str = 'coerce'
    ) -> pd.DataFrame:
        """
        Parse date column in pandas DataFrame with smart fallback.
        
        Uses vectorized pandas operations for performance. Tries primary format first,
        then falls back to secondary formats for failed rows.
        
        Args:
            df: Pandas DataFrame
            column: Column name containing dates
            formats: Optional list of formats to try (uses SUPPORTED_INPUT_FORMATS if None)
            errors: How to handle parse errors ('coerce', 'raise', 'ignore')
            
        Returns:
            DataFrame with parsed datetime column
            
        Example:
            >>> handler = DateHandler()
            >>> df = pd.DataFrame({'date': ['31/12/2025', '01-01-2025']})
            >>> df = handler.parse_dataframe_dates(df, 'date')
            >>> print(df['date'].dtype)
            datetime64[ns]
        """
        if formats is None:
            formats = self.SUPPORTED_INPUT_FORMATS
        
        # Try primary format first (fastest)
        primary_format = formats[0]
        df[column] = pd.to_datetime(
            df[column], 
            format=primary_format, 
            errors='coerce'
        )
        
        # Try secondary formats for NaT values
        mask = df[column].isna()
        if mask.any() and len(formats) > 1:
            for fmt in formats[1:]:
                still_na = df[column].isna()
                if not still_na.any():
                    break
                
                df.loc[still_na, column] = pd.to_datetime(
                    df.loc[still_na, column],
                    format=fmt,
                    errors='coerce'
                )
        
        # Handle remaining errors based on errors parameter
        if errors == 'raise':
            if df[column].isna().any():
                failed_values = df.loc[df[column].isna(), column].unique()
                raise DateValidationError(
                    f"Failed to parse dates: {failed_values[:5]}"
                )
        elif errors == 'ignore':
            # Keep original values where parsing failed
            pass
        # 'coerce' keeps NaT values (already done)
        
        logger.debug(
            f"Parsed {len(df)} dates in column '{column}', "
            f"{df[column].isna().sum()} failed"
        )
        
        return df
    
    def format_dataframe_dates(
        self,
        df: pd.DataFrame,
        column: str,
        format_str: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Format datetime column in pandas DataFrame to string.
        
        Args:
            df: Pandas DataFrame
            column: Column name containing datetimes
            format_str: Optional format string (uses DEFAULT_OUTPUT_FORMAT if None)
            
        Returns:
            DataFrame with formatted string column
        """
        if format_str is None:
            format_str = self.DEFAULT_OUTPUT_FORMAT
        
        df[column] = df[column].dt.strftime(format_str)
        return df
    
    def get_month_range(
        self,
        year: int,
        month: int
    ) -> Tuple[datetime.datetime, datetime.datetime]:
        """
        Get start and end datetime for a given month.
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            
        Returns:
            Tuple of (start_of_month, end_of_month) as timezone-aware datetimes
            
        Example:
            >>> handler = DateHandler()
            >>> start, end = handler.get_month_range(2025, 12)
            >>> print(start)
            2025-12-01 00:00:00+05:30
            >>> print(end)
            2025-12-31 23:59:59+05:30
        """
        from dateutil.relativedelta import relativedelta
        
        start = datetime.datetime(year, month, 1, tzinfo=self.timezone)
        end = start + relativedelta(months=1) - datetime.timedelta(seconds=1)
        
        return start, end
    
    def clear_cache(self) -> None:
        """
        Clear the date parsing cache.
        
        Useful when memory is constrained or cache may be stale.
        """
        with self._cache_lock:
            self.parse.cache_clear()
            logger.debug("Date parsing cache cleared")
    
    def get_cache_info(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache hits, misses, size, and maxsize
        """
        info = self.parse.cache_info()
        return {
            'hits': info.hits,
            'misses': info.misses,
            'maxsize': info.maxsize,
            'currsize': info.currsize
        }


# Global singleton instance for application-wide use
_global_handler: Optional[DateHandler] = None
_global_handler_lock = threading.Lock()


def get_date_handler() -> DateHandler:
    """
    Get global DateHandler singleton instance.
    
    Returns:
        Shared DateHandler instance
        
    Example:
        >>> handler = get_date_handler()
        >>> dt = handler.parse("31/12/2025")
    """
    global _global_handler
    
    if _global_handler is None:
        with _global_handler_lock:
            if _global_handler is None:
                _global_handler = DateHandler()
    
    return _global_handler


# Convenience functions using global handler
def parse_date(date_str: str, dayfirst: bool = True) -> datetime.datetime:
    """Parse date string using global handler."""
    return get_date_handler().parse(date_str, dayfirst=dayfirst)


def format_date(dt: datetime.datetime, format_str: Optional[str] = None) -> str:
    """Format datetime using global handler."""
    return get_date_handler().format(dt, format_str)


def validate_date(date_str: str) -> bool:
    """Validate date string using global handler."""
    return get_date_handler().validate_date(date_str)


def validate_date_range(
    start_date: Union[str, datetime.datetime],
    end_date: Union[str, datetime.datetime],
    max_months: Optional[int] = None
) -> Tuple[bool, str]:
    """Validate date range using global handler."""
    return get_date_handler().validate_date_range(start_date, end_date, max_months)


if __name__ == "__main__":
    # Example usage and testing
    handler = DateHandler()
    
    print("=== DateHandler Example Usage ===\n")
    
    # Parsing various formats
    print("1. Parsing various date formats:")
    test_dates = [
        "31/12/2025",
        "31/12/25",
        "31-12-2025",
        "31-Dec-2025",
        "2025/12/31",
    ]
    for date_str in test_dates:
        dt = handler.parse(date_str)
        print(f"   '{date_str}' -> {dt}")
    
    # Date validation
    print("\n2. Date validation:")
    print(f"   '31/12/2025' valid: {handler.validate_date('31/12/2025')}")
    print(f"   'invalid-date' valid: {handler.validate_date('invalid-date')}")
    
    # Date range validation
    print("\n3. Date range validation:")
    valid, msg = handler.validate_date_range("01/01/2025", "31/12/2025")
    print(f"   01/01/2025 to 31/12/2025: {valid}")
    
    valid, msg = handler.validate_date_range("31/12/2025", "01/01/2025")
    print(f"   31/12/2025 to 01/01/2025: {valid} - {msg}")
    
    valid, msg = handler.validate_date_range("01/01/2025", "01/02/2026", max_months=12)
    print(f"   01/01/2025 to 01/02/2026 (max 12 months): {valid} - {msg}")
    
    # Formatting
    print("\n4. Date formatting:")
    dt = handler.parse("31/12/2025")
    print(f"   Default: {handler.format(dt)}")
    print(f"   Tally: {handler.format(dt, handler.TALLY_OUTPUT_FORMAT)}")
    print(f"   ISO: {handler.format(dt, handler.ISO_OUTPUT_FORMAT)}")
    
    # Current datetime
    print("\n5. Current datetime:")
    print(f"   Now: {handler.now()}")
    print(f"   Formatted: {handler.now_formatted()}")
    
    # Cache info
    print("\n6. Cache statistics:")
    print(f"   {handler.get_cache_info()}")
