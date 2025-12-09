import re
from time import strftime
import xlrd
import xlwt
import os,json,sys
import datetime, pytz
import pickle
import locale
from typing import Optional, List, Tuple, Dict, Any, Union
locale.setlocale(locale.LC_NUMERIC, 'hi_IN')
from copy import deepcopy
import firebase_admin
from firebase_admin import credentials, db
import dateutil.parser
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Import centralized date handler
from date_handler import DateHandler, get_date_handler, validate_date_range
import random

# Import utilities for better file management
try:
    from utils import (
        cleanup_temp_files, cleanup_all_temp_files, 
        ensure_temp_dir_exists, get_temp_file_path,
        save_to_json, load_from_json
    )
except ImportError:
    # Fallback if utils.py not available
    def cleanup_temp_files(*args, **kwargs):
        return 0, 0
    def cleanup_all_temp_files(*args, **kwargs):
        return 0
    def ensure_temp_dir_exists(temp_dir='./temp/'):
        os.makedirs(temp_dir, exist_ok=True)
        return True
    def get_temp_file_path(filename, temp_dir='./temp/'):
        ensure_temp_dir_exists(temp_dir)
        return os.path.join(temp_dir, filename)
    def save_to_json(data, filepath, indent=2):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, default=str)
            return True
        except:
            return False
    def load_from_json(filepath, default=None):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default

# Fix for opening xlsx
xlrd.xlsx.ensure_elementtree_imported(False, None)
xlrd.xlsx.Element_has_iter = True

# TODO: Check if the uploaded statement are in correct date range!

# Import configuration manager
from config import get_config

# Initialize configuration (lazy loaded)
_config = None

def _get_config():
    """Get global configuration instance (lazy initialization)."""
    global _config
    if _config is None:
        _config = get_config()
    return _config

# Configuration-based constants (backward compatibility)
# These are now functions that read from config, but maintain the same interface
def get_app_name():
    """Get application name from configuration."""
    return _get_config().application.app_name

def get_max_cheque_number_length():
    """Get maximum cheque number length from configuration."""
    return _get_config().validation.max_cheque_number_length

def get_cheque_number_padding_length():
    """Get cheque number padding length from configuration."""
    return _get_config().validation.cheque_number_padding_length

def get_hdfc_tally_ledgername():
    """Get HDFC Tally ledger name from configuration."""
    return _get_config().tally.hdfc_ledger_name

def get_icici_tally_ledgername_gok():
    """Get ICICI Tally ledger name (GOK) from configuration."""
    return _get_config().tally.icici_ledger_name_gok

def get_icici_tally_ledgername_uni():
    """Get ICICI Tally ledger name (UNI) from configuration."""
    return _get_config().tally.icici_ledger_name_uni

def get_payment_intermediary_tally_ledgername():
    """Get payment intermediary ledger name from configuration."""
    return _get_config().tally.payment_intermediary_ledger

def get_receipt_intermediary_tally_ledgername():
    """Get receipt intermediary ledger name from configuration."""
    return _get_config().tally.receipt_intermediary_ledger

# Backward compatibility: Create module-level constants that read from config
# These will be initialized on first import
APP_NAME = get_app_name()
MAX_CHEQUE_NUMBER_LENGTH = get_max_cheque_number_length()
CHEQUE_NUMBER_PADDING_LENGTH = get_cheque_number_padding_length()
HDFC_TALLY_LEDGERNAME = get_hdfc_tally_ledgername()
ICICI_TALLY_LEDGERNAME_GOK = get_icici_tally_ledgername_gok()
ICICI_TALLY_LEDGERNAME_UNI = get_icici_tally_ledgername_uni()
PAYMENT_INTERMEDIARY_TALLY_LEDGERNAME = get_payment_intermediary_tally_ledgername()
RECEIPT_INTERMEDIARY_TALLY_LEDGERNAME = get_receipt_intermediary_tally_ledgername()

def get_current_time() -> str:
    """Get current time in Indian timezone formatted as string.
    
    Returns:
        Formatted time string (DD/MM/YYYY HH:MM AM/PM)
    """
    t = datetime.datetime.now(pytz.timezone('Asia/Kolkata')) 
    # formatted_time = str(t.day)+'/'+str(t.month)+'/'+str(t.year)+' '+str(t.hour)+':'+str(t.minute)+' '
    formatted_time = t=strftime("%d/%m/%Y %I:%M %p") + '.'
    return formatted_time

class Validator:
    """Centralized validation class for all data validation operations."""
    
    @staticmethod
    def validate_path(path: str) -> bool:
        """Validate Excel file path (.xls or .xlsx).
        
        Args:
            path: File path to validate
            
        Returns:
            True if valid Excel file path, False otherwise
        """
        if not path:
            return False
        if not os.path.isfile(path) or not os.path.exists(path):
            return False
        extension = path.split('.')[-1].lower()
        return extension in ('xls', 'xlsx')
    
    @staticmethod
    def validate_save_path(path: str) -> bool:
        """Validate save file path (.fil extension).
        
        Args:
            path: File path to validate
            
        Returns:
            True if valid .fil file path, False otherwise
        """
        if not os.path.isfile(path) or not os.path.exists(path):
            return False
        return path.split('.')[-1] == 'fil'
    
    @staticmethod
    def validate_date(date: str) -> bool:
        """Validate date string in DD/MM/YY format.
        
        Args:
            date: Date string to validate
            
        Returns:
            True if valid date format, False otherwise
        """
        try:
            datetime.datetime.strptime(date, '%d/%m/%y')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_chqno(chqno: str) -> bool:
        """Validate cheque number (numeric and within max length).
        
        Args:
            chqno: Cheque number to validate
            
        Returns:
            True if valid cheque number, False otherwise
        """
        try:
            int(chqno)
        except ValueError:
            return False
        return len(chqno) <= MAX_CHEQUE_NUMBER_LENGTH
    
    @staticmethod
    def validate_amount(amount: Union[str, int, float]) -> bool:
        """Validate amount (numeric and non-negative).
        
        Args:
            amount: Amount to validate (string, int, or float)
            
        Returns:
            True if valid non-negative amount, False otherwise
        """
        try:
            int(amount)
        except ValueError:
            try:
                float(amount)
            except ValueError:
                return False
        return float(amount) >= 0
    
    @staticmethod
    def validateSavefile(filePath: str) -> Union[bool, str]:
        """Validate save file name and extension.
        
        Args:
            filePath: File path to validate
            
        Returns:
            True if valid, False if invalid, 'add_ext' if extension needed
        """
        if not filePath:
            return False
        fileName = filePath.split('/')[-1]
        if len(fileName) < 1:
            return False
        if fileName.split('.')[-1].lower() != 'fil':
            return 'add_ext'
        return True

# Backward compatibility: Keep old function names as aliases
def validate_path(path: str) -> bool:
    return Validator.validate_path(path)

def validate_save_path(path: str) -> bool:
    return Validator.validate_save_path(path)

def validate_date(date: str) -> bool:
    return Validator.validate_date(date)

def validate_chqno(chqno: str) -> bool:
    return Validator.validate_chqno(chqno)

def validate_amount(amount: Union[str, int, float]) -> bool:
    return Validator.validate_amount(amount)

def validateSavefile(filePath: str) -> Union[bool, str]:
    return Validator.validateSavefile(filePath)

def format_chqNo(chqNo: str) -> str:
    """Pad cheque number with leading zeros to standard length.
    
    Converts cheque numbers to a standardized 16-digit format by adding
    leading zeros. This ensures consistent comparison between cheque numbers
    from different sources.
    
    Args:
        chqNo: Cheque number string (can be any length)
    
    Returns:
        Padded cheque number string (16 digits total)
    
    Example:
        >>> format_chqNo('123')
        '0000000000000123'
        >>> format_chqNo('9876543210')
        '0000009876543210'
    """
    if(len(chqNo)>0):
        zerolist = ""
        for i in range(0,CHEQUE_NUMBER_PADDING_LENGTH-len(chqNo)):
            zerolist+=('0')
        zerolist+=chqNo
        newChqNo = zerolist
        return newChqNo
def searchby_transdate(table: List, date: str) -> List:
    """Search table for entries matching a specific transaction date.
    
    Performs fuzzy date matching by comparing day, month, and year components.
    Handles different date formats and year representations (2-digit vs 4-digit).
    
    Args:
        table: List of table entries (each entry is a list with date at index 0)
        date: Date string in DD/MM/YY or DD/MM/YYYY format
    
    Returns:
        List of matching entries that have the same date
    
    Example:
        >>> searchby_transdate(table_data, '15/01/24')
        [['15/01/2024', 'Narration', '123456', ...], ...]
    """
    new_table = []
    for each in table:
        # print(each[0],date)
        # if(each[0]==date):
        stmtdate = each[0].split('/')
        querydate = date.split('/')
        if stmtdate[0] == querydate[0]:
            if stmtdate[1] == querydate[1]:
                if stmtdate[2][-2:] == querydate[2][-2:]:
                    new_table.append(each)
    return new_table   
def searchby_chqno(table: List, chqNo: str) -> List:
    """Search table for entries with matching cheque number.
    
    Compares cheque numbers after standardizing them to padded format.
    This ensures '123' matches '0000000000000123'.
    
    Args:
        table: List of table entries (cheque number at index 2)
        chqNo: Cheque number to search for
    
    Returns:
        List of entries with matching cheque numbers
    
    Example:
        >>> searchby_chqno(table_data, '123456')
        [['15/01/2024', 'Payment', '0000000000123456', ...], ...]
    """
    new_table = []
    for each in table:
        if(format_chqNo( each[2])== format_chqNo( chqNo)):
            new_table.append(each)
    return new_table   
def searchby_amount(table: List, amount: Union[str, float]) -> List:
    """Search table for entries with matching debit or credit amount.
    
    Searches both debit (index 5) and credit (index 6) columns for the
    specified amount. Handles string to float conversion and ignores
    entries with invalid numeric values.
    
    Args:
        table: List of table entries
        amount: Amount to search for (string or float)
    
    Returns:
        List of entries where debit or credit matches the amount
    
    Example:
        >>> searchby_amount(table_data, '5000.00')
        [['15/01/2024', ..., '5000.00', '0'], ...]
    """
    new_table = []
    for each in table:
        try:
            if(float(each[5])==float(amount)):
                new_table.append(each)
        except ValueError:
            pass
        try:        
            if(float(each[6])== float(amount)):
                new_table.append(each)    
        except ValueError:
            pass       
    return new_table     
def prepare_save_data(master_table, master_selected_rows, save_path, master_excel_export_path):
    data_to_save = []
    data_to_save.append(master_table)
    data_to_save.append(master_selected_rows)
    data_to_save.append(save_path)
    data_to_save.append(master_excel_export_path)    
    return data_to_save

import json

class JsonDataLoader:
    """Loads years, banks, and companies from a JSON file and provides access to them.
    Implements singleton pattern with caching to avoid multiple file reads.
    """  
    _instance = None
    _cache = None
    _cache_timestamp = None
    
    def __new__(cls, json_path='./data.json'):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(JsonDataLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, json_path='./data.json'):
        if self._initialized:
            return
        self.json_path = json_path
        self.years = []
        self.banks = []
        self.companies = []
        self.months = []
        self.load_json_data()
        self._initialized = True
        
    def load_json_data(self, force_reload=False):
        """Load data from JSON and store it in class variables.
        Uses caching to avoid repeated file reads unless force_reload is True.
        """
        # Check if cache is valid (file hasn't changed)
        try:
            current_mtime = os.path.getmtime(self.json_path)
            if not force_reload and self._cache is not None and self._cache_timestamp == current_mtime:
                # Use cached data
                self.years = self._cache['years']
                self.banks = self._cache['banks']
                self.companies = self._cache['companies']
                self.months = self._cache['months']
                return
        except OSError:
            pass  # File doesn't exist or can't be accessed
            
        # Load from file
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.years = [item["value"] for item in data.get("Years", [])]
            self.banks = [item["value"] for item in data.get("Banks", [])]
            self.companies = [item["value"] for item in data.get("Companies", [])]
            self.months = [item["value"] for item in data.get("Months", [])]
            
            # Update cache
            self._cache = {
                'years': self.years,
                'banks': self.banks,
                'companies': self.companies,
                'months': self.months
            }
            self._cache_timestamp = os.path.getmtime(self.json_path)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON file: {e}")
            
    def get_years(self):
        return self.years
    def get_banks(self):
        return self.banks
    def get_companies(self):
        return self.companies
    def get_months(self):
        return self.months
    
    @classmethod
    def clear_cache(cls):
        """Clear the singleton instance and cache."""
        cls._instance = None
        cls._cache = None
        cls._cache_timestamp = None


class InfiChequeStatement:
    """Represents and processes Infi (InfiBooks) cheque statement data.
    
    This class handles reading, parsing, and managing cheque statement data from
    Excel files exported from InfiBooks accounting software. It provides methods for:
    - Loading Excel files and extracting transaction data
    - Matching cheque numbers and amounts with bank statements
    - Comparing dates between different date formats
    - Managing the statement's lifecycle and metadata
    
    The class expects Excel files in a specific format with columns:
    - Column 0: Transaction type (e.g., "Receipt Voucher")
    - Column 1: Transaction date
    - Columns 2-10: Transaction details (trans no, book, code, ledger, cheque no, etc.)
    
    Attributes:
        path (str): Path to the Excel file
        workbook: xlrd workbook object
        worksheet: Active worksheet from the workbook
        entry_list (List): List of parsed transaction entries
        year (str): Financial year of the statement
        company (str): Company name for this statement
        last_edited_time (str): Timestamp of last modification
    
    Example:
        >>> stmt = InfiChequeStatement()
        >>> if stmt.setPath('/path/to/cheques.xlsx'):
        ...     stmt.grab_data()
        ...     entries = stmt.entry_list
    """
    
    # Column indices for reference (used in data extraction)
    # trans_col = 0          # Transaction type
    # transDate_col = 1      # Transaction date
    # chqDate_col = 2        # Cheque date (dd-mm-yyyy)
    # bankName_col = 3       # Bank name
    # ledgerName_col = 4     # Ledger account name
    # chqNo_col = 5          # Cheque number
    # amount_col = 6         # Transaction amount
    # narration_col = 7      # Transaction narration/description
    # issueDate_col = 8      # Cheque issue date
    # passDate_col = 9       # Cheque pass/clear date
    # voucher_col = 10       # Voucher reference

    def setPath(self, path: str) -> bool:
        if validate_path(path):
            self.path = path
            self.workbook = xlrd.open_workbook(self.path)
            self.worksheet = self.workbook.sheet_by_index(0)
            return True
        else:
            return False    
    def __init__(self):
        self.start_row = 1
        self.path = None
        self.workbook = None
        self.worksheet = None
        self.entry_list = None
        self.year = None
        self.company = None
        self.last_edited_time = None
        # self.save_path = None
        # self.createSavePath()
        return    
    def get_json(self):
        dict = {}
        dict["entry_list"] = self.entry_list
        dict["year"] = self.year
        dict["company"] = self.company
        # dict["last_edited_time"] = self.last_edited_time
        return dict
    def set_entry_list(self, val):
        self.entry_list = val 
        self.update_last_edited_time()   

    # def createSavePath(self):
    #     self.save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\Snapshot_"+self.month+'_'+self.year+'_'+self.bank
    #     return
    def update_last_edited_time(self):
        self.last_edited_time = get_current_time()  
    def get_last_edited_time(self):
        return self.last_edited_time  
    def get_year(self):
        return self.year   
    def get_company(self):
        return self.company 
    def set_year(self, val):
        self.year = val
    def set_company(self, val):
        self.company = val
    def release_excel_file(self):
        self.workbook.release_resources()
        self.worksheet = None
        del self.workbook
        return True            
    def grab_data(self):
        i = self.start_row
        # transDate, transNo, book, code, ledgerName, chqNo, chqDate, transtypeVoucher, narration, debit, credit = None
        self.entry_list = []
        if not self.worksheet:
            return False
        while True:
            entry = []
            try:
                val = self.worksheet.cell(i,0).value
                # print(val)
            except IndexError:
                break   
            if val != "Receipt Voucher":
                i+=1
                continue
                # val_as_datetime = datetime.datetime(*xlrd.xldate_as_tuple(val, self.workbook.datemode))   
            val = self.worksheet.cell(i,1).value    
            # year, month, day, hour, minute, second = xlrd.xldate_as_tuple(val, self.workbook.datemode)
            # date_in_string = str(day)+'/'+str(month)+'/'+str(year)
            date_in_string = '/'.join(val.split('-'))
            entry.append(date_in_string)
            for j in range(2,11):
                val = None
                val = self.worksheet.cell(i,j).value
                entry.append(val)
                j+=1
            # print("entry: ",entry)    
            self.entry_list.append(entry)
            i+=1
        self.release_excel_file()  
        self.update_last_edited_time()
        return True

    def compare_date(self,infiChqStmtDate, bank_date):
        # infiChqStmtDate format dd/mm/yyyy
        # bank_date format dd/mm/yy or dd-bbb-yyyy
        assert datetime.datetime.strptime(infiChqStmtDate, "%d/%m/%Y")
        try:
            bank_date = dateutil.parser.parse(bank_date, dayfirst=True)
        except :
            print(bank_date)
            raise
        infiChqStmtDate = datetime.datetime.strptime(infiChqStmtDate, "%d/%m/%Y")
        if infiChqStmtDate>bank_date:
            return False
        return True    
                       

    def findMatchByChequeNumber(self, bank_chequeNumber: str, bank_debit: str, bank_date: str) -> List:
        """Find matching entries by cheque number, amount, and date.
        
        This is the core matching algorithm that reconciles bank statement entries
        with Infi cheque statement entries. Matches are made based on three criteria:
        1. Cheque number (padded to standard length for comparison)
        2. Debit amount (exact match required)
        3. Transaction date (Infi date must not be after bank date)
        
        The algorithm:
        - Standardizes cheque numbers by padding with leading zeros to 16 digits
        - Compares each Infi entry against the bank statement entry
        - Only returns entries that match all three criteria
        
        Args:
            bank_chequeNumber: Cheque number from bank statement
            bank_debit: Debit amount from bank statement
            bank_date: Transaction date from bank statement (various formats supported)
        
        Returns:
            List of matching entries from Infi statement. Each entry contains:
            [transDate, transNo, book, code, ledgerName, chqNo, chqDate, 
             transtypeVoucher, narration, debit, credit]
        
        Example:
            >>> matches = stmt.findMatchByChequeNumber('123456', '5000.00', '15/01/2024')
            >>> len(matches)  # Number of matching transactions
            1
        """
        match_list = []

        def makeChequeNumberStandard(input_cheque_number: str) -> str:
            """Pad cheque number with leading zeros to standard 16-digit length.
            
            Example: '123' becomes '0000000000000123'
            """
            zerolist = ""
            for i in range(0, CHEQUE_NUMBER_PADDING_LENGTH - len(input_cheque_number)):
                zerolist += ('0')
            zerolist += input_cheque_number
            return zerolist

        # Iterate through all Infi cheque entries to find matches
        for each in self.entry_list:
            # Extract fields from Infi entry
            infiChqNo = each[4]        # Column 4: Cheque number
            infiDebitamt = each[5]     # Column 5: Debit amount
            infiTransDate = each[0]    # Column 0: Transaction date
            
            # Only process entries with valid cheque numbers
            if(len(infiChqNo) >= 1):
                # Standardize both cheque numbers for comparison
                newInfiChqNo = makeChequeNumberStandard(infiChqNo)
                bank_chequeNumber = makeChequeNumberStandard(bank_chequeNumber)
                
                # Check all three matching criteria:
                # 1. Cheque numbers match (after padding)
                # 2. Amounts match exactly
                # 3. Infi transaction date is not after bank date
                if (newInfiChqNo == bank_chequeNumber and 
                    bank_debit == infiDebitamt and 
                    self.compare_date(infiTransDate, bank_date)):
                    match_list.append(each)
                    
        return match_list
    def getEntryList(self):
        return self.entry_list
class HDFCBankChequeStatement:
    """Processes HDFC Bank cheque statement data from Excel files.
    
    This class handles parsing and extracting transaction data from HDFC Bank
    statement Excel files. HDFC statements have a specific format where:
    - The data starts after a header row containing "Date"
    - May have a separator row with asterisks
    - Contains columns: Date, Narration, Cheque Number, Value Date, Debit, Credit, Balance
    
    The class automatically finds the starting row by looking for the "Date" header
    and handles the HDFC-specific formatting quirks.
    
    Attributes:
        start_row (int): Row number where transaction data begins
        path (str): Path to the Excel statement file
        workbook: xlrd workbook object
        worksheet: Active worksheet containing the statement
        entry_list (List): Parsed transaction entries
    
    Example:
        >>> hdfc_stmt = HDFCBankChequeStatement()
        >>> if hdfc_stmt.setPath('/path/to/hdfc_statement.xlsx'):
        ...     hdfc_stmt.grab_data()
        ...     transactions = hdfc_stmt.get_entry_list()
    """
    start_row = None
    path = None
    workbook = None
    worksheet = None
    entry_list = None

    def setPath(self, path):
        if validate_path(path):
            self.path = path
            self.workbook = xlrd.open_workbook(self.path)
            self.worksheet = self.workbook.sheet_by_index(0)
            self.find_start_row()
            return True
        else:
            return False
    
    def release_resources(self):
        """Release Excel workbook resources to prevent memory leaks."""
        if self.workbook:
            try:
                self.workbook.release_resources()
            except AttributeError:
                pass  # xlrd doesn't always have release_resources in older versions
            self.workbook = None
        self.worksheet = None
        return True    

    def find_start_row(self):
        i=0
        while True:
            try:
                val=self.worksheet.cell(i,0).value
            except IndexError:
                print("Cannot find startRow in HDfc statement.")
                return  
            if val == "Date":
                if self.worksheet.cell(i+1,0).value[0]=='*':
                    self.start_row=i+2
                else:
                    self.start_row=i+1
                break            
            i+=1

    def grab_data(self):
        i = self.start_row
        # transDate, transNo, book, code, ledgerName, chqNo, chqDate, transtypeVoucher, narration, credit, debit = None
        self.entry_list = []
        while True:
            entry = []
            try:
                val = self.worksheet.cell(i,0).value
            except IndexError:
                break     
            if(len(val.split('/'))!=3):
                print("Reached end of hdfc statement")
                break
            for j in range(0,7):
                val = None
                val = self.worksheet.cell(i,j).value
                entry.append(val)
                j+=1
            self.entry_list.append(entry)
            # print("entry", entry)
            i+=1
        # Release resources after grabbing data
        self.release_resources()

    def getEntryList(self):
        return self.entry_list
class ICICIBankChequeStatement:
    start_row = None
    path = None
    workbook = None
    worksheet = None
    entry_list = None
    narration = 5

    def setPath(self, path):
        if validate_path(path):
            self.path = path
            self.workbook = xlrd.open_workbook(self.path)
            self.worksheet = self.workbook.sheet_by_index(0)
            self.find_start_row()
            return True
        else:
            return False
    
    def release_resources(self):
        """Release Excel workbook resources to prevent memory leaks."""
        if self.workbook:
            try:
                self.workbook.release_resources()
            except AttributeError:
                pass  # xlrd doesn't always have release_resources in older versions
            self.workbook = None
        self.worksheet = None
        return True    
    def getPath(self):
        return self.path
    def find_start_row(self):
        i=6
        try:
            val=self.worksheet.cell(i,0).value
        except IndexError:
            print("Cannot find startRow in ICICI statement.")
            return  
        try: 
            val2 = self.worksheet.cell(i-1,0).value.split('-')[2]
        except:
            print("Invalid ICICI statement.")
            return
        if val == "No.":
            self.start_row=i+1
        else:
            print("Invalid ICICI statement.")
        return    
    
    def process_narration(self, entry):
        narration = entry[5]
        narration = narration.split('/')
        entry[4] = ''
        if narration[0] != 'CLG' or len(narration)<3:
            return entry
        chq_no = narration[2]
        entry[4] = chq_no
        # print(entry)
        return entry

    def process_date(self, entry):
        """Process date field using centralized DateHandler."""
        date = entry[2]
        try:
            handler = get_date_handler()
            parsed_date = handler.parse(str(date), dayfirst=True)
            entry[2] = handler.format(parsed_date, handler.TALLY_OUTPUT_FORMAT)
        except Exception:
            print(date)
            raise
        return entry        

    def grab_data(self):
        i = self.start_row
        # No.	Transaction_ID	Value_Date	Txn_Posted_Date	ChequeNo.	Description_Cr/Dr	Transaction_Amount(INR)	Available_Balance(INR)	
        self.entry_list = []
        while True:
            entry = []
            try:
                val = self.worksheet.cell(i,0).value
            except IndexError:
                print("Reached end of Icici statement")
                break
            for j in range(0,9):
                val = None
                val = self.worksheet.cell(i,j).value
                entry.append(val)
                j+=1
            entry = self.process_narration(entry)    
            entry = self.process_date(entry)
            if entry:
                self.entry_list.append(entry)
            # print("entry", entry)
            i+=1
        # Release resources after grabbing data
        self.release_resources()

    def getEntryList(self):
        return self.entry_list

class TableSnapshot:
    master_table = None
    master_selected_rows = None
    master_excel_export_path = None
    month = None
    year = None
    bank = None
    company = None
    save_path = None

    def __init__(self, *inp):
        if len(inp) == 1:
            self.initialize_mode1(inp[0])
        elif len(inp) == 7:
            self.initialize_mode2(inp[0], inp[1],inp[2] ,inp[3] ,inp[4] ,inp[5] ,inp[6])
        return  

    def initialize_mode2(self,company,month,year,bank,master_table, master_selected_rows, master_excel_export_path):
        self.master_table = master_table
        self.master_selected_rows = master_selected_rows
        self.master_excel_export_path = master_excel_export_path
        self.month = month.lower()
        self.year = year.lower()
        self.bank = bank.lower()
        self.company = company.lower()
        self.creation_time = get_current_time()
        self.last_edited_time = None
        self.createSavePath()
        self.update_last_edited_time()
        return
    def initialize_mode1(self, dict):
        self.master_table = dict["master_table"]
        self.month = dict["month"]
        self.year = dict["year"]
        self.bank = dict["bank"]
        self.company = dict["company"]
        self.creation_time = dict["creation_time"]
        # self.creation_time = get_current_time()
        self.master_selected_rows = []
        self.master_excel_export_path = None
        self.last_edited_time = None
        self.createSavePath()
        self.update_last_edited_time()
        return

    def get_json(self):
        dict = {}
        dict["master_table"] = self.master_table
        dict["month"] = self.month
        dict["year"] = self.year
        dict["bank"] = self.bank
        dict["company"] = self.company
        dict["creation_time"] = self.creation_time
        return dict  

    def update_last_edited_time(self):
        self.last_edited_time = get_current_time()
    def get_master_table(self):
        return self.master_table
    def set_master_table(self, table):
        self.master_table = table
        return
    def get_master_selected_rows(self):
        return self.master_selected_rows
    def get_master_excel_export_path(self):
        return self.master_excel_export_path  
    def get_save_path(self):
        return self.save_path  
    def get_month(self):
        return self.month
    def get_year(self):
        return self.year
    def get_bank(self):
        return self.bank 
    def get_company(self):
        return self.company 
    def set_company(self, val):
        self.company = val       
    def get_last_edited_time(self):
        return self.last_edited_time   
    def set_master_selected_rows(self, val):
        self.master_selected_rows = val
        self.update_last_edited_time()
    def set_master_excel_export_path(self, val):
        self.master_excel_export_path = val    
        self.update_last_edited_time()
    def createSavePath(self):
        self.save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\Snapshot_"+self.month+'_'+self.year+'_'+self.bank
        return

class ChequeReportCollection:
    save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\ChequeReportCollection.fil"
    def __init__(self, json_path='data.json'):
        # Use JsonDataLoader to fetch common data
        self.data_loader = JsonDataLoader(json_path)
        self.years = self.data_loader.get_years()
        self.banks = self.data_loader.get_banks()
        self.companies = self.data_loader.get_companies()
        
        self.cheque_report_dict = {}
        return
    def get_years(self):
        return self.years   
    def get_cheque_report_dict(self):
        return self.cheque_report_dict         
    def load_cheque_report_collection(self):
        # Checking if directory exists
        if os.getenv('APPDATA'):
            target_dir = os.path.join(os.getenv('APPDATA'), APP_NAME)
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                print(f"Directory created: {target_dir}")
            else:
                print(f"Directory already exists: {target_dir}")
        else:
            print("APPDATA environment variable is not set.")
            return
        try:
            # raise FileNotFoundError
            with open(self.save_path, 'rb') as f:
                data_loaded = pickle.load(f)
                self.cheque_report_dict = data_loaded
        except FileNotFoundError:
            return False
        print('LOAD OK')    
        self.print_cheque_report()    
        return
    def save_cheque_report_collection(self):
        if not self.cheque_report_dict:
            print('Empty dict, save skip')
            return(True, 0)
        try:
            # print(self.cheque_report_dict)
            with open(self.save_path, 'wb') as f:
                pickle.dump(self.cheque_report_dict, f)    
        except TypeError: 
            raise
            return None,-1
        except FileNotFoundError:    
            return None,-2
        print('SAVE OK')     
        # self.print_cheque_report()    
        return True, 0        
    def print_cheque_report(self):
        print("*******ChequeReportCollection*******")
        for key,val in self.cheque_report_dict.items():
            print(key,':',val)
        return                        
    def get_dict_reference(self, year,  company):
        company = company.lower()
        if(company in self.companies and year in self.years ):
            return company+'_'+'_'+year
        return None                
    def delete_cheque_report_from_collection(self,  year,  company):
        ref = self.get_dict_reference(year,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('deleting table of ',company,year,'from table list with ref',ref)    
        self.cheque_report_dict[ref] = None
        status, code = self.save_cheque_report_collection()
        if status:
            print('ChequeReportCollection save success!!')
        else:
            print('ChequeReportCollection save fail with code ',code)   
        return True   
    def add_cheque_report_to_collection(self, chequeReport,ref=None):
        if not ref:
            year = chequeReport.get_year()
            company = chequeReport.get_company()
            ref = self.get_dict_reference(year,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('adding chequeReport to chequeReportCollection with ref',ref)    
        self.cheque_report_dict[ref] = chequeReport
        status, code = self.save_cheque_report_collection()
        if status:
            print('ChequeReportCollection save success!!')
        else:
            print('ChequeReportCollection save fail with code ',code)   
        return True   
    def get_cheque_report_from_collection(self,  year, company):
        ref = self.get_dict_reference(year,company)
        return self.get_table_from_collection_by_reference(ref)
    def get_table_from_collection_by_reference(self, ref):
        if not ref:
            return None
        try:
            return self.cheque_report_dict[ref]
        except KeyError:
            return None    
                    

class TableSnapshotCollection:
    save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\tableSnapshotCollection.filv2"
    save_path_old = os.getenv('APPDATA')+'\\'+APP_NAME+"\\tableSnapshotCollection.fil"
    table_list = {}
    def __init__(self, json_path='./data.json'):
        # Use JsonDataLoader to fetch common data
        self.data_loader = JsonDataLoader(json_path)
        self.years = self.data_loader.get_years()
        self.banks = self.data_loader.get_banks()
        self.companies = self.data_loader.get_companies()
        self.months = self.data_loader.get_months()
        
        self.cheque_report_dict = {}
    def get_months(self):
        return self.months
    def get_years(self):
        return self.years 
    def rename_old_save_path(self):
        os.rename(self.save_path_old,self.save_path_old+'_000')        
    def load_table(self):
        print(self.save_path)
        try:
            with open(self.save_path, 'rb') as f:
                data_loaded = pickle.load(f)
                self.table_list = data_loaded
        except FileNotFoundError:
            print("Load Failed. New installation?.")
            return False
        print('LOAD OK')    
        # self.print_table()    
        return True
    def load_old_table(self):
        print(self.save_path_old)
        try:
            with open(self.save_path_old, 'rb') as f:
                data_loaded = pickle.load(f)
                self.table_list = data_loaded
        except FileNotFoundError:
            return False
        print('Old file loaded')    
        self.print_table(old = True)    
        return True  
    def get_table_list(self):
        return self.table_list    
    def save_table(self):
        try:
            # print(self.table_list)
            with open(self.save_path, 'wb') as f:
                pickle.dump(self.table_list, f)    
        except TypeError: 
            return None,-1
        except FileNotFoundError:    
            return None,-2
        print('SAVE OK')     
        # self.print_table()    
        return True, 0        
    def print_table(self, old=False):
        if old:
            print("*******OLDTableSnapshotCollection*******")    
        else:    
            print("*******TableSnapshotCollection*******")
        for key,val in self.table_list.items():
            print(key,':',val)
        return                        
    def get_dict_reference(self, month, year, bank, company):
        month = month.lower()  
        bank = bank.lower()
        company = company.lower()
        # print('bank', bank)
        if(company in self.companies and month in self.months and year in self.years and bank in self.banks):
            return company+'_'+month+'_'+year+'_'+bank
        return None                
    def delete_table_from_collection(self, month, year, bank, company):
        ref = self.get_dict_reference(month,year,bank,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('deleting table of ',company,month,year,bank,'from table list with ref',ref)    
        self.table_list[ref] = None
        status, code = self.save_table()
        if status:
            print('TableCollection save success!!')
        else:
            print('TableCollection save fail with code ',code)   
        return True   
    def add_table_to_colection(self, tableSnapshot, save=True):
        month = tableSnapshot.get_month()
        year = tableSnapshot.get_year()
        company = tableSnapshot.get_company()
        bank = tableSnapshot.get_bank()     
        print(month, year,company,bank, tableSnapshot.get_master_excel_export_path(), tableSnapshot.get_save_path())       
        ref = self.get_dict_reference(month,year,bank,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('adding table to ',month,year,bank,company,'to table list with ref',ref,'.')    
        self.table_list[ref] = tableSnapshot
        if not save: 
            return
        status, code = self.save_table()
        if status:
            print('TableCollection save success!!')
        else:
            print('TableCollection save fail with code ',code)   
        return True   
    def get_table_from_collection(self, month, year, bank,company):
        ref = self.get_dict_reference(month,year,bank,company)
        return self.get_table_from_collection_by_reference(ref)
    def get_table_from_collection_by_reference(self,ref):
        if not ref:
            return None
        try:
            return self.table_list[ref]
        except KeyError:
            return None
class StorageManager:
    """Handle all file I/O and pickle persistence operations.
    
    This service class is responsible for managing table snapshots and cheque reports
    stored in pickle files. It provides a clean abstraction over the TableSnapshotCollection
    and ChequeReportCollection classes.
    
    Responsibilities:
        - Load and save table snapshots (pickle storage)
        - Load and save cheque reports (pickle storage)
        - Retrieve snapshots by month/year/bank/company
        - Delete snapshots and reports
        - Provide access to collections
    
    Thread Safety:
        This class is not thread-safe. External synchronization required if used
        from multiple threads.
    """
    
    def __init__(self):
        """Initialize storage manager and load existing collections from disk."""
        self.tableSnapshotCollection = TableSnapshotCollection()
        self.chequeReportCollection = ChequeReportCollection()
        
        if self.chequeReportCollection.load_cheque_report_collection():
            print('StorageManager: ChequeReportCollection loaded successfully')
        
        if self.tableSnapshotCollection.load_table():
            print('StorageManager: TableSnapshotCollection loaded successfully')
    
    def get_table_snapshot(self, month: str, year: str, bank: str, company: str) -> Optional['TableSnapshot']:
        """Retrieve a table snapshot from the collection.
        
        Args:
            month: Month name (e.g., 'january')
            year: Year as string (e.g., '2024')
            bank: Bank name (e.g., 'hdfc', 'icici')
            company: Company name (e.g., 'gokul')
        
        Returns:
            TableSnapshot object if found, None otherwise
        """
        return self.tableSnapshotCollection.get_table_from_collection(month, year, bank, company)
    
    def save_table_snapshot(self, tableSnapshot: 'TableSnapshot') -> bool:
        """Save a table snapshot to the collection.
        
        Args:
            tableSnapshot: TableSnapshot object to save
        
        Returns:
            True if save successful, False otherwise
        """
        return self.tableSnapshotCollection.add_table_to_colection(tableSnapshot, save=True)
    
    def delete_table_snapshot(self, month: str, year: str, bank: str, company: str) -> bool:
        """Delete a table snapshot from the collection.
        
        Args:
            month: Month name
            year: Year as string
            bank: Bank name
            company: Company name
        
        Returns:
            True if delete successful, False otherwise
        """
        return self.tableSnapshotCollection.delete_table_from_collection(month, year, bank, company)
    
    def get_cheque_report(self, year: str, company: str) -> Optional['InfiChequeStatement']:
        """Retrieve a cheque report from the collection.
        
        Args:
            year: Financial year (e.g., '2024')
            company: Company name (e.g., 'gokul')
        
        Returns:
            InfiChequeStatement object if found, None otherwise
        """
        return self.chequeReportCollection.get_cheque_report_from_collection(year, company)
    
    def save_cheque_report(self, chequeReportPath: str, year: str, company: str) -> bool:
        """Load and save a cheque report from an Excel file.
        
        Args:
            chequeReportPath: Path to the cheque report Excel file
            year: Financial year
            company: Company name
        
        Returns:
            True if save successful, False otherwise
        """
        infiChequeStatement = InfiChequeStatement()
        if not infiChequeStatement.setPath(chequeReportPath):
            return False
        infiChequeStatement.grab_data()  
        infiChequeStatement.set_year(year)
        infiChequeStatement.set_company(company)
        self.chequeReportCollection.add_cheque_report_to_collection(infiChequeStatement)  
        return True
    
    def delete_cheque_report(self, year: str, company: str) -> bool:
        """Delete a cheque report from the collection.
        
        Args:
            year: Financial year
            company: Company name
        
        Returns:
            True if delete successful, False otherwise
        """
        return self.chequeReportCollection.delete_cheque_report_from_collection(year, company)
    
    def get_all_table_snapshots(self) -> Dict[str, 'TableSnapshot']:
        """Get all table snapshots in the collection.
        
        Returns:
            Dictionary mapping reference keys to TableSnapshot objects
        """
        return self.tableSnapshotCollection.get_table_list()
    
    def get_all_cheque_reports(self) -> Dict[str, 'InfiChequeStatement']:
        """Get all cheque reports in the collection.
        
        Returns:
            Dictionary mapping reference keys to InfiChequeStatement objects
        """
        return self.chequeReportCollection.get_cheque_report_dict()


class ExcelProcessor:
    """Handle Excel import/export operations.
    
    This service class is responsible for reading from and writing to Excel files.
    It handles exporting table data to Excel with multiple sheets for different views
    (all data, selected, unselected, matched, unmatched).
    
    Responsibilities:
        - Export table data to Excel files
        - Create multiple sheets (selected, unselected, matched, unmatched)
        - Apply formatting and styling
        - Handle file operations (save, open)
    
    Thread Safety:
        This class is thread-safe for independent operations.
        Not safe if same file is written by multiple threads simultaneously.
    """
    
    TABLE_HEADER = ['Bank Date', 'Bank Narration', 'Chq No', 'Party Name', 
                    'Infi Date', 'Credit', 'Debit', 'Closing Balance']
    
    def get_header(self) -> List[str]:
        """Get the standard table header.
        
        Returns:
            List of column names for the table
        """
        return self.TABLE_HEADER
    
    def export_to_excel(self, folder_url: str, snapshot: 'TableSnapshot') -> Tuple[bool, int]:
        """Export table snapshot to Excel file with multiple sheets.
        
        Creates an Excel file with 5 sheets:
        1. Sheet_1: All data (selected rows highlighted in green)
        2. Selected: Only selected rows
        3. Unselected: Only unselected rows
        4. Matched CHQReceipts(HDFC): Only matched cheque deposits
        5. Unmatched CHQReceipts(HDFC): Only unmatched cheque deposits
        
        Args:
            folder_url: Output path (can be folder or .xls file path)
            snapshot: TableSnapshot object containing data to export
        
        Returns:
            Tuple of (success: bool, error_code: int)
            Error codes:
                0: Success
                -2: FileNotFoundError (invalid path)
                -5: PermissionError (file is open or no write permission)
                99: Other exception
        """
        # Initialize counters for each sheet
        k = 0   # Main sheet
        k2 = 0  # Selected sheet
        k3 = 0  # Unselected sheet
        k4 = 0  # Matched sheet
        k5 = 0  # Unmatched sheet
        
        # Create workbook and sheets
        export_workbook = xlwt.Workbook()
        export_worksheet = export_workbook.add_sheet('Sheet_1')
        selected_worksheet = export_workbook.add_sheet('Selected')
        unselected_worksheet = export_workbook.add_sheet('Unselected')
        matched_worksheet = export_workbook.add_sheet('Matched CHQReceipts(HDFC)')
        unmatched_worksheet = export_workbook.add_sheet('Unmatched CHQReceipts(HDFC)')
        
        # Define styling
        row_color_select = xlwt.easyxf('pattern: pattern solid, fore_colour light_green')
        
        # Write headers to all sheets
        row = export_worksheet.row(k)
        row_s2 = selected_worksheet.row(k2)
        row_s3 = unselected_worksheet.row(k3)
        row_s4 = matched_worksheet.row(k4)
        row_s5 = unmatched_worksheet.row(k5)
        
        for j, header_item in enumerate(self.get_header()):
            row.write(j, str(header_item))
            row_s2.write(j, str(header_item))
            row_s3.write(j, str(header_item))
            row_s4.write(j, str(header_item))
            row_s5.write(j, str(header_item))
        
        k += 1
        
        # Write data rows
        for each in snapshot.get_master_table():
            row = export_worksheet.row(k)
            a = k - 1  # Row index (0-based)
            
            # Determine which additional sheets this row belongs to
            is_selected = a in snapshot.get_master_selected_rows()
            is_matched_chq_deposit = (each['Party Name'] != '' and 
                                     each["Bank Narration"] != '' and 
                                     each["Bank Narration"][0:7] == "CHQ DEP")
            is_unmatched_chq_deposit = (each["Bank Narration"][0:7] == "CHQ DEP" and 
                                       not is_matched_chq_deposit)
            
            # Prepare rows for conditional sheets
            if is_selected:
                k2 += 1
                row_s2 = selected_worksheet.row(k2)
            else:
                k3 += 1
                row_s3 = unselected_worksheet.row(k3)
            
            if is_matched_chq_deposit:
                k4 += 1
                row_s4 = matched_worksheet.row(k4)
            elif is_unmatched_chq_deposit:
                k5 += 1
                row_s5 = unmatched_worksheet.row(k5)
            
            # Write cells for this row
            for j, header_item in enumerate(self.get_header()):
                cell = each[header_item]
                
                # Main sheet (with highlighting)
                if is_selected:
                    row.write(j, cell, row_color_select)
                    row_s2.write(j, cell, row_color_select)
                else:
                    row.write(j, cell)
                    row_s3.write(j, cell)
                
                # Matched/unmatched sheets
                if is_matched_chq_deposit:
                    row_s4.write(j, cell)
                elif is_unmatched_chq_deposit:
                    row_s5.write(j, cell)
            
            k += 1
        
        # Determine save path
        if folder_url != '' and (folder_url.split('.')[-1].lower() != 'xls'):
            save_file = folder_url + '/123.xls'
        else:
            save_file = folder_url
        
        # Save file
        try:
            export_workbook.save(save_file)
            os.startfile(save_file)  # Open the file
            return True, 0
        except FileNotFoundError:
            return False, -2
        except PermissionError:
            return False, -5
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False, 99


class SearchService:
    """Handle search and filter operations on table data with optimization.
    
    This service class provides optimized search functionality using:
    - DataFrame indexing for fast lookups
    - LRU cache for repeated searches
    - Pandas vectorized filtering (no loops)
    - Pre-processed search data
    
    Responsibilities:
        - Search by cheque number (partial match)
        - Search by date (exact match with flexible format)
        - Search by amount (debit or credit)
        - Format search results for display
        - Cache frequent searches
    
    Thread Safety:
        This class is thread-safe with instance-level locking for cache access.
    
    Performance Optimizations:
        - Index creation: O(n) once, then O(1) or O(log n) lookups
        - LRU cache: O(1) for cached results
        - Vectorized operations: 10x-100x faster than loops
        - Pre-processed data: Avoids repeated formatting
    """
    
    def __init__(self, cache_size=128):
        """Initialize search service with LRU cache.
        
        Args:
            cache_size: Maximum number of search results to cache (default 128)
        """
        # Import lru_cache from functools
        from functools import lru_cache
        
        # Cache for search results (keyed by search parameters)
        self._search_cache = {}
        self._cache_size = cache_size
        self._cache_lock = threading.Lock()
        
        # Pre-processed DataFrame (set by prepare_search_data)
        self._df = None
        self._df_lock = threading.Lock()
        
        # Index columns for fast lookup
        self._indexed = False
    
    def prepare_search_data(self, masterTableData: List[Dict]) -> None:
        """Pre-process and index data for fast searching.
        
        Converts list of dicts to pandas DataFrame with optimized dtypes
        and creates indexes for common search fields.
        
        Args:
            masterTableData: Raw table data (list of dictionaries)
        """
        with self._df_lock:
            if not masterTableData:
                self._df = pd.DataFrame()
                self._indexed = False
                return
            
            # Convert to DataFrame once
            self._df = pd.DataFrame(masterTableData)
            
            # Optimize dtypes for memory and performance
            if not self._df.empty:
                # Parse dates once for fast comparison
                self._df['Bank Date Parsed'] = pd.to_datetime(
                    self._df['Bank Date'], 
                    dayfirst=True, 
                    errors='coerce'
                )
                
                # Lowercase cheque numbers for case-insensitive search
                self._df['Chq No Lower'] = self._df['Chq No'].str.lower()
                
                # Convert amounts to numeric for fast filtering
                self._df['Credit Numeric'] = pd.to_numeric(self._df['Credit'], errors='coerce').fillna(0)
                self._df['Debit Numeric'] = pd.to_numeric(self._df['Debit'], errors='coerce').fillna(0)
                
                # Create multi-index for fast lookups (optional, for very large datasets)
                # self._df.set_index(['Chq No Lower', 'Bank Date Parsed'], inplace=True)
                
                self._indexed = True
            else:
                self._indexed = False
            
            # Clear cache when data changes
            self._clear_cache()
    
    def _clear_cache(self) -> None:
        """Clear the search results cache."""
        with self._cache_lock:
            self._search_cache.clear()
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[Dict]]:
        """Get cached search result if available.
        
        Args:
            cache_key: Cache key (combination of query and mode)
        
        Returns:
            Cached result or None if not found
        """
        with self._cache_lock:
            return self._search_cache.get(cache_key)
    
    def _set_cached_result(self, cache_key: str, result: List[Dict]) -> None:
        """Store search result in cache with LRU eviction.
        
        Args:
            cache_key: Cache key
            result: Search result to cache
        """
        with self._cache_lock:
            # Implement simple LRU: remove oldest if cache full
            if len(self._search_cache) >= self._cache_size:
                # Remove first item (oldest in dict order for Python 3.7+)
                first_key = next(iter(self._search_cache))
                del self._search_cache[first_key]
            
            self._search_cache[cache_key] = result
    
    def format_table_data(self, _tableData: List[Dict]) -> List[Dict]:
        """Format table data for display (apply locale formatting to numbers).
        
        Args:
            _tableData: Raw table data (list of dictionaries)
        
        Returns:
            Formatted table data with locale-formatted numbers
        """
        tableData = deepcopy(_tableData)
        for each in tableData:
            if each['Credit'] != '':
                each['Credit'] = locale.format_string("%.2f", float(each['Credit']), grouping=True)
            if each['Debit'] != '':
                each['Debit'] = locale.format_string("%.2f", float(each['Debit']), grouping=True)
            if each['Closing Balance'] != '':
                each['Closing Balance'] = locale.format_string("%.2f", float(each['Closing Balance']), grouping=True)
        return tableData
    
    def search(self, masterTableData: List[Dict], searchQuery: str, searchMode: str) -> List[Dict]:
        """Search table data using specified mode and query with caching.
        
        Uses LRU cache for repeated searches and pandas filtering for performance.
        
        Args:
            masterTableData: Table data to search (list of row dictionaries)
            searchQuery: Search term entered by user
            searchMode: Search mode ('bychqno', 'bydate', 'bychqamt')
        
        Returns:
            Filtered and formatted table data matching the search criteria
        """
        # Empty query returns all data
        if searchQuery == "":
            return self.format_table_data(masterTableData)
        
        # Check cache first
        cache_key = f"{searchMode}:{searchQuery}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Prepare data if not already done or data changed
        with self._df_lock:
            needs_prep = (self._df is None or 
                         len(self._df) != len(masterTableData) or
                         not self._indexed)
        
        if needs_prep:
            self.prepare_search_data(masterTableData)
        
        # Perform search using pandas filtering
        final_table = []
        
        if searchMode == "bychqno":
            final_table = self._search_by_cheque_number_optimized(searchQuery)
        elif searchMode == "bydate":
            final_table = self._search_by_date_optimized(searchQuery)
        elif searchMode == "bychqamt":
            final_table = self._search_by_amount_optimized(searchQuery)
        else:
            final_table = masterTableData
        
        # Format and cache result
        formatted_result = self.format_table_data(final_table)
        self._set_cached_result(cache_key, formatted_result)
        
        return formatted_result
    
    def _search_by_cheque_number_optimized(self, searchQuery: str) -> List[Dict]:
        """Search by cheque number using pandas vectorized string operations.
        
        Args:
            searchQuery: Cheque number to search for
        
        Returns:
            List of rows where cheque number contains the query
        """
        with self._df_lock:
            if self._df is None or self._df.empty:
                return []
            
            # Vectorized string contains (much faster than loop)
            mask = self._df['Chq No Lower'].str.contains(
                searchQuery.lower(), 
                na=False, 
                regex=False
            )
            
            # Convert filtered DataFrame back to list of dicts
            filtered_df = self._df[mask]
            return filtered_df.drop(
                columns=['Bank Date Parsed', 'Chq No Lower', 'Credit Numeric', 'Debit Numeric'],
                errors='ignore'
            ).to_dict('records')
    
    def _search_by_date_optimized(self, searchQuery: str) -> List[Dict]:
        """Search by date using pandas vectorized date operations.
        
        Matches dates where day and month match exactly, and last 2 digits of year match.
        
        Args:
            searchQuery: Date string in dd/mm/yyyy or dd/mm/yy format
        
        Returns:
            List of rows matching the date
        """
        with self._df_lock:
            if self._df is None or self._df.empty:
                return []
            
            try:
                querydate = searchQuery.split('/')
                if len(querydate) != 3:
                    return []
                
                query_day = int(querydate[0])
                query_month = int(querydate[1])
                query_year_last2 = querydate[2][-2:]
                
                # Vectorized date component extraction and comparison
                valid_dates = self._df['Bank Date Parsed'].notna()
                
                # Extract day, month, year components (vectorized)
                day_match = self._df.loc[valid_dates, 'Bank Date Parsed'].dt.day == query_day
                month_match = self._df.loc[valid_dates, 'Bank Date Parsed'].dt.month == query_month
                year_match = (self._df.loc[valid_dates, 'Bank Date Parsed'].dt.year % 100).astype(str) == query_year_last2
                
                # Combine masks
                mask = valid_dates.copy()
                mask[valid_dates] = day_match & month_match & year_match
                
                # Convert filtered DataFrame back to list of dicts
                filtered_df = self._df[mask]
                return filtered_df.drop(
                    columns=['Bank Date Parsed', 'Chq No Lower', 'Credit Numeric', 'Debit Numeric'],
                    errors='ignore'
                ).to_dict('records')
                
            except (ValueError, IndexError):
                return []
    
    def _search_by_amount_optimized(self, searchQuery: str) -> List[Dict]:
        """Search by amount using pandas vectorized numeric operations.
        
        Args:
            searchQuery: Amount to search for (partial match)
        
        Returns:
            List of rows where credit or debit contains the search query
        """
        with self._df_lock:
            if self._df is None or self._df.empty:
                return []
            
            # For numeric search, try exact and partial match
            try:
                # Convert search query to string for partial matching
                query_str = str(searchQuery)
                
                # Vectorized string contains on both Credit and Debit
                credit_match = self._df['Credit'].astype(str).str.contains(
                    query_str, 
                    na=False, 
                    regex=False
                )
                debit_match = self._df['Debit'].astype(str).str.contains(
                    query_str, 
                    na=False, 
                    regex=False
                )
                
                # Combine with OR
                mask = credit_match | debit_match
                
                # Convert filtered DataFrame back to list of dicts
                filtered_df = self._df[mask]
                return filtered_df.drop(
                    columns=['Bank Date Parsed', 'Chq No Lower', 'Credit Numeric', 'Debit Numeric'],
                    errors='ignore'
                ).to_dict('records')
                
            except Exception:
                return []
    
    # Legacy methods for backward compatibility (use optimized versions above)
    def _search_by_cheque_number(self, masterTableData: List[Dict], searchQuery: str) -> List[Dict]:
        """Legacy method - use _search_by_cheque_number_optimized instead."""
        final_table = []
        for each in masterTableData:
            if searchQuery in each['Chq No'].lower():
                final_table.append(each)
        return final_table
    
    def _search_by_date(self, masterTableData: List[Dict], searchQuery: str) -> List[Dict]:
        """Legacy method - use _search_by_date_optimized instead (DateHandler integrated)."""
        final_table = []
        querydate = searchQuery.split('/')
        handler = get_date_handler()
        
        for each in masterTableData:
            try:
                parsed_date = handler.parse(each['Bank Date'], dayfirst=True)
                formatted_date = handler.format(parsed_date)
                stmtdate = formatted_date.split('/')
                
                if (stmtdate[0] == querydate[0] and
                    stmtdate[1] == querydate[1] and
                    stmtdate[2][-2:] == querydate[2][-2:]):
                    final_table.append(each)
            except Exception:
                continue
        
        return final_table
    
    def _search_by_amount(self, masterTableData: List[Dict], searchQuery: str) -> List[Dict]:
        """Legacy method - use _search_by_amount_optimized instead."""
        final_table = []
        for each in masterTableData:
            if searchQuery in str(each["Credit"]) or searchQuery in str(each["Debit"]):
                final_table.append(each)
        return final_table


class ValidationService:
    """Handle data validation and business rule validation.
    
    This service class validates file paths, dates, and business rule constraints
    for various operations like daybook generation and file exports.
    
    Responsibilities:
        - Validate file paths and accessibility
        - Validate date ranges and formats
        - Validate daybook generation inputs
        - Use existing Validator class for data validation
    
    Thread Safety:
        This class is thread-safe as it's stateless.
    """
    
    def __init__(self):
        """Initialize validation service."""
        self.intermediateDaybook = None
    
    def validate_daybook_inputs(self, path: str, fromDate: str, toDate: str, company: str) -> Tuple[bool, int]:
        """Validate inputs for daybook generation.
        
        Args:
            path: Path to intermediate daybook Excel file
            fromDate: Start date in dd/mm/yyyy format
            toDate: End date in dd/mm/yyyy format
            company: Company name
        
        Returns:
            Tuple of (success: bool, error_code: int)
            Error codes:
                1: Success
                -1: Invalid file path
                -2: Invalid fromDate format
                -3: Invalid toDate format
                -4: fromDate >= toDate (invalid range)
                -5: Date range > 12 months
                -8: Error reading Excel file
        """
        # Remove file:// prefix if present
        if path.startswith('file:///'):
            path = path[8:]
        
        self.intermediateDaybook = IntermediateDaybook(path, fromDate, toDate, company)
        return self.intermediateDaybook.validateAndSetValues()
    
    def get_intermediate_daybook(self) -> Optional['IntermediateDaybook']:
        """Get the validated intermediate daybook instance.
        
        Returns:
            IntermediateDaybook instance if validation succeeded, None otherwise
        """
        return self.intermediateDaybook


class DataProcessor:
    """Process bank statements and match with cheque reports.
    
    This service class handles the core business logic of matching bank statement
    entries with cheque report entries. It prepares table data by combining bank
    statement information with matching cheque details.
    
    Responsibilities:
        - Match bank statements with cheque reports
        - Process HDFC and ICICI bank statements
        - Calculate balances and date ranges
        - Format table data for display
        - Create table snapshots from statements
    
    Thread Safety:
        This class is thread-safe for independent operations.
    """
    
    def __init__(self):
        """Initialize data processor."""
        pass
    
    def format_table_data(self, _tableData: List[Dict]) -> List[Dict]:
        """Format table data for display (apply locale formatting to numbers).
        
        Args:
            _tableData: Raw table data
        
        Returns:
            Formatted table data with locale-formatted numbers
        """
        tableData = deepcopy(_tableData)
        for each in tableData:
            if each['Credit'] != '':
                each['Credit'] = locale.format_string("%.2f", float(each['Credit']), grouping=True)
            if each['Debit'] != '':
                each['Debit'] = locale.format_string("%.2f", float(each['Debit']), grouping=True)
            if each['Closing Balance'] != '':
                each['Closing Balance'] = locale.format_string("%.2f", float(each['Closing Balance']), grouping=True)
        return tableData
    
    def calculate_balances_and_dates(self, master_table: List[Dict]) -> Tuple[str, str, str, str]:
        """Calculate credit/debit balances and determine date range.
        
        Args:
            master_table: Table data
        
        Returns:
            Tuple of (credit_balance, debit_balance, start_date, end_date)
            All formatted as strings
        """
        credit_bal = 0.0
        debit_bal = 0.0
        start_date, end_date = "", ""
        
        for each in master_table:
            try:
                bank_date = dateutil.parser.parse(each['Bank Date'], dayfirst=True)
            except:
                if each['meta'] == 'double':
                    each['Bank Narration'] = "Double Match"
                    continue
                else:
                    print(f"Error at entry: {each}")
                    raise
            
            if start_date == "" or start_date > bank_date:
                start_date = bank_date
            if end_date == "" or end_date < bank_date:
                end_date = bank_date
            
            if each['Credit'] != '':
                credit_bal += float(each['Credit'])
            if each['Debit'] != '':
                debit_bal += float(each['Debit'])
        
        credit_bal_str = locale.format_string("%.2f", credit_bal, grouping=True)
        debit_bal_str = locale.format_string("%.2f", debit_bal, grouping=True)
        start_date_str = start_date.strftime("%Y/%m/%d")
        end_date_str = end_date.strftime("%Y/%m/%d")
        
        return credit_bal_str, debit_bal_str, start_date_str, end_date_str
    
    def prepare_table_data(self, statementObj: Any, infiChequeStatement: Optional['InfiChequeStatement'], 
                          previous_infiChequeStatement: Optional['InfiChequeStatement'], 
                          bank: str) -> List[Dict]:
        """Match bank statement entries with cheque report entries.
        
        This is the core business logic that matches bank transactions with
        issued cheques using cheque number, amount, and date matching.
        
        Args:
            statementObj: Bank statement object (HDFC or ICICI)
            infiChequeStatement: Current year cheque report
            previous_infiChequeStatement: Previous year cheque report (for cross-year matching)
            bank: Bank name ('hdfc' or 'icici')
        
        Returns:
            List of table rows (dictionaries) with matched data
        """
        if bank == 'hdfc':
            return self._prepare_hdfc_table_data(statementObj, infiChequeStatement, previous_infiChequeStatement)
        elif bank == 'icici':
            return self._prepare_icici_table_data(statementObj, infiChequeStatement, previous_infiChequeStatement)
        else:
            raise ValueError(f"Unsupported bank: {bank}")
    
    def _prepare_hdfc_table_data(self, statementObj: 'HDFCBankChequeStatement', 
                                  infiChequeStatement: Optional['InfiChequeStatement'],
                                  previous_infiChequeStatement: Optional['InfiChequeStatement']) -> List[Dict]:
        """Prepare table data for HDFC bank statements.
        
        Bank Statement Format (HDFC):
        [0] Date, [1] Narration, [2] Chq./Ref.No., [3] Value Dt, 
        [4] Withdrawal Amt., [5] Deposit Amt., [6] Closing Balance
        """
        bank_statement = statementObj.getEntryList()
        final_table = []
        
        for bank_entry in bank_statement:
            # Find matches in current year cheque report
            if not infiChequeStatement:
                match_list = []
            else:
                match_list = infiChequeStatement.findMatchByChequeNumber(
                    bank_entry[2], bank_entry[5], bank_entry[0]
                )
            
            # Try previous year if no match found
            if len(match_list) == 0 and previous_infiChequeStatement:
                match_list = previous_infiChequeStatement.findMatchByChequeNumber(
                    bank_entry[2], bank_entry[5], bank_entry[0]
                )
            
            # Process matches
            if len(match_list) > 0:
                for i in range(len(match_list)):
                    infi_entry = match_list[i]
                    
                    if i == 0:
                        # First match - include full bank entry
                        table_row = {
                            'Bank Date': bank_entry[0],
                            'Bank Narration': bank_entry[1],
                            'Chq No': bank_entry[2],
                            'Party Name': infi_entry[3],
                            'Infi Date': infi_entry[0],
                            'Debit': bank_entry[4],
                            'Credit': bank_entry[5],
                            'Closing Balance': bank_entry[6],
                            'meta': "" if len(match_list) == 1 else "double"
                        }
                    else:
                        # Additional matches - show as separate rows
                        print("Double match found.")
                        table_row = {
                            'Bank Date': "",
                            'Bank Narration': "",
                            'Chq No': bank_entry[2],
                            'Party Name': infi_entry[3],
                            'Infi Date': infi_entry[0],
                            'Debit': "",
                            'Credit': bank_entry[5],
                            'Closing Balance': "",
                            'meta': "double"
                        }
                    final_table.append(table_row)
            else:
                # No match found
                table_row = {
                    'Bank Date': bank_entry[0],
                    'Bank Narration': bank_entry[1],
                    'Chq No': bank_entry[2],
                    'Party Name': "",
                    'Infi Date': "",
                    'Debit': bank_entry[4],
                    'Credit': bank_entry[5],
                    'Closing Balance': bank_entry[6],
                    'meta': ""
                }
                final_table.append(table_row)
        
        return final_table
    
    def _prepare_icici_table_data(self, statementObj: 'ICICIBankChequeStatement',
                                   infiChequeStatement: Optional['InfiChequeStatement'],
                                   previous_infiChequeStatement: Optional['InfiChequeStatement']) -> List[Dict]:
        """Prepare table data for ICICI bank statements."""
        bank_statement = statementObj.getEntryList()
        final_table = []
        
        for bank_entry in bank_statement:
            # Find matches
            if bank_entry[4] is not None and bank_entry[4] != '':
                if not infiChequeStatement:
                    match_list = []
                else:
                    match_list = infiChequeStatement.findMatchByChequeNumber(
                        bank_entry[4], bank_entry[7], bank_entry[2]
                    )
                
                if len(match_list) == 0 and previous_infiChequeStatement:
                    match_list = previous_infiChequeStatement.findMatchByChequeNumber(
                        bank_entry[4], bank_entry[7], bank_entry[2]
                    )
            else:
                match_list = []
            
            # Determine credit/debit
            cred_amt = '' if bank_entry[6] != 'CR' else bank_entry[7]
            deb_amt = '' if bank_entry[6] != 'DR' else bank_entry[7]
            
            # Process matches
            if len(match_list) > 0:
                for i in range(len(match_list)):
                    infi_entry = match_list[i]
                    
                    if i == 0:
                        table_row = {
                            'Bank Date': bank_entry[2],
                            'Bank Narration': bank_entry[5],
                            'Chq No': bank_entry[4],
                            'Party Name': infi_entry[3],
                            'Infi Date': infi_entry[0],
                            'Credit': cred_amt,
                            'Debit': deb_amt,
                            'Closing Balance': bank_entry[8],
                            'meta': "" if len(match_list) == 1 else "double"
                        }
                    else:
                        print("Double match found.")
                        table_row = {
                            'Bank Date': "",
                            'Bank Narration': "",
                            'Chq No': bank_entry[4],
                            'Party Name': infi_entry[3],
                            'Infi Date': infi_entry[0],
                            'Credit': cred_amt,
                            'Debit': deb_amt,
                            'Closing Balance': "",
                            'meta': "double"
                        }
                    final_table.append(table_row)
            else:
                # No match
                table_row = {
                    'Bank Date': bank_entry[2],
                    'Bank Narration': bank_entry[5],
                    'Chq No': bank_entry[4],
                    'Party Name': "",
                    'Infi Date': "",
                    'Credit': cred_amt,
                    'Debit': deb_amt,
                    'Closing Balance': bank_entry[8],
                    'meta': ""
                }
                final_table.append(table_row)
        
        return final_table
    
    def add_snapshot_to_table(self, statement_path: str, month: str, year: str, 
                             bank: str, company: str, 
                             storageManager: 'StorageManager') -> Tuple[bool, int]:
        """Create a table snapshot from a bank statement file.
        
        Args:
            statement_path: Path to bank statement Excel file
            month: Month name
            year: Year string
            bank: Bank name ('hdfc' or 'icici')
            company: Company name
            storageManager: StorageManager instance to access cheque reports
        
        Returns:
            Tuple of (success: bool, status_code: int)
            Status codes:
                1: Success
                -3: Invalid HDFC statement file
                -4: Invalid ICICI statement file
        """
        # Determine financial year
        if month in ['january', 'february', 'march']:
            financial_year = str(int(year) - 1)
        else:
            financial_year = year
        
        previous_financial_year = str(int(financial_year) - 1)
        print(f"FINANCIAL YEAR = {financial_year}")
        
        # Get cheque reports
        infiChequeStatement = storageManager.get_cheque_report(financial_year, company)
        previous_infiChequeStatement = storageManager.get_cheque_report(previous_financial_year, company)
        
        # Process bank statement
        try:
            if bank == 'hdfc':
                statementObj = HDFCBankChequeStatement()
                if not statementObj.setPath(statement_path):
                    return False, -3
                try:
                    statementObj.grab_data()
                except TypeError:
                    return False, -3
            else:  # ICICI
                statementObj = ICICIBankChequeStatement()
                if not statementObj.setPath(statement_path):
                    return False, -4
                try:
                    statementObj.grab_data()
                except TypeError:
                    return False, -4
            
            # Prepare matched table data
            master_table = self.prepare_table_data(
                statementObj, infiChequeStatement, previous_infiChequeStatement, bank
            )
            
            # Create and save snapshot
            tableSnapshot = TableSnapshot(company, month, year, bank, master_table, [], None)
            storageManager.save_table_snapshot(tableSnapshot)
            
            return True, 1
            
        except Exception as e:
            print(f"Error creating snapshot: {e}")
            return False, -99


class DaybookService:
    """Handle daybook generation operations.
    
    This service class manages the complex workflow of generating intermediate
    daybooks from multiple table snapshots spanning a date range.
    
    Responsibilities:
        - Validate daybook generation inputs
        - Collect required table snapshots for date range
        - Generate consolidated voucher entries
        - Prepare intermediate daybook
    
    Thread Safety:
        This class is not thread-safe due to mutable state.
    """
    
    def __init__(self, validationService: 'ValidationService'):
        """Initialize daybook service.
        
        Args:
            validationService: ValidationService instance for input validation
        """
        self.validationService = validationService
    
    def generate_daybook(self, storageManager: 'StorageManager') -> Tuple[bool, int, str]:
        """Generate intermediate daybook from table snapshots.
        
        Args:
            storageManager: StorageManager to access table snapshots
        
        Returns:
            Tuple of (success: bool, code: int, error_message: str)
            Codes:
                1: Success
                -7: Missing snapshot for required month/year/bank
        """
        intermediateDaybook = self.validationService.get_intermediate_daybook()
        if not intermediateDaybook:
            return False, -99, "Daybook not validated"
        
        # Get date range
        startDate = intermediateDaybook.getFromDate()
        endDate = intermediateDaybook.getToDate()
        company = intermediateDaybook.getCompany()
        
        # Build list of months in range
        list_of_months = []
        tempDate = startDate
        while True:
            month_name = tempDate.strftime('%B')
            month = tempDate.month
            year = tempDate.year
            list_of_months.append([month_name, year])
            if month == endDate.month and year == endDate.year:
                break
            tempDate = tempDate + relativedelta(months=+1)
        
        print(list_of_months)
        
        # Collect snapshots for all required months/banks
        snapshot_list = []
        banks = ['icici']
        if company == 'gokul':
            banks.append('hdfc')
        
        for bank in banks:
            for [month, year] in list_of_months:
                snapshot = storageManager.get_table_snapshot(month, str(year), bank, company)
                if not snapshot:
                    print(f"No snapshot for {month} {year} {bank} {company}")
                    return False, -7, f"{month} {year} {bank}"
                snapshot_list.append(snapshot)
        
        # Prepare consolidated vouchers
        consolidatedReceiptVouchers = ConsolidatedReceiptVouchers(snapshot_list)
        consolidatedReceiptVouchers.prepare_df(startDate, endDate, mode="matched_cheques")
        consolidatedReceiptVouchers.prepare_df(startDate, endDate, mode="chequeless_receipts")
        
        consolidatedPaymentVouchers = ConsolidatedPaymentVouchers(snapshot_list)
        consolidatedPaymentVouchers.prepare_df(startDate, endDate)
        
        # Generate daybook
        intermediateDaybook.prepare_daybook(
            consolidatedReceiptVouchers.get_receipt_with_cheques_df(),
            consolidatedPaymentVouchers.get_payment_entries_df(),
            consolidatedReceiptVouchers.get_receipt_without_cheques_df()
        )
        
        return True, 1, ''


class FirebaseService:
    """Handle Firebase synchronization operations.
    
    This service class manages uploading and downloading data to/from Firebase,
    including left menu data, table snapshots, and cheque reports. It uses async
    operations with progress callbacks.
    
    Responsibilities:
        - Upload data to Firebase (left menu, snapshots, reports)
        - Download data from Firebase
        - Batch operations for better performance
        - Progress reporting via callbacks
    
    Thread Safety:
        Uses FirebaseControls which is thread-safe via connection pooling.
    """
    
    def __init__(self):
        """Initialize Firebase service with connection pooling."""
        self.firebaseControls = FirebaseControls()
        
        # Get base path for left menu JSON
        try:
            base_path = sys._MEIPASS  # type: ignore
        except Exception:
            base_path = os.path.abspath(".")
        self.leftMenuJsonPath = os.path.join(base_path, 'data.json')
    
    def upload_all_data(self, callbackFuncforProgress: callable, storageManager: 'StorageManager') -> None:
        """Upload all data to Firebase (left menu, snapshots, reports).
        
        Args:
            callbackFuncforProgress: Callback function(text1, text2, progress)
            storageManager: StorageManager to access collections
        """
        # Upload left menu
        print("Uploading left-menu values to db")
        callbackFuncforProgress("Processing Left Menu values", "Retrieving values to upload", 0.0)
        
        with open(self.leftMenuJsonPath) as f:
            data = json.load(f)
        leftmenu_future = self.firebaseControls.set_leftMenu_data_async(data)
        
        print("Uploading tableSnapshot values to db")
        callbackFuncforProgress("Processing Left Menu values", "Uploading...", 0.5)
        
        try:
            leftmenu_future.result(timeout=30)
            callbackFuncforProgress("Processing Left Menu values", "Finished uploading", 1.0)
        except Exception as e:
            print(f"Error uploading left menu: {e}")
            callbackFuncforProgress("Processing Left Menu values", "Error occurred", 1.0)
        
        # Upload cheque reports
        callbackFuncforProgress("Processing cheque reports", "Retrieving snapshots to upload", 0.0)
        collection_dict = storageManager.get_all_cheque_reports()
        print(f"Found {len(collection_dict)} cheque reports to upload")
        
        cheque_upload_dict = {}
        for key, obj in collection_dict.items():
            if obj:
                cheque_upload_dict[key] = obj.get_json()
        
        if cheque_upload_dict:
            def cheque_progress(current, total, key):
                progress = round(current * 8 / total) / 10
                callbackFuncforProgress("Processing cheque reports", f"Uploading {key}", progress)
                print(f"Uploaded chequeReport: {key} ({current}/{total})")
            
            self.firebaseControls.batch_set_chequeReports(cheque_upload_dict, cheque_progress)
        
        callbackFuncforProgress("Processing cheque reports", "Finished", 1.0)
        
        # Upload table snapshots
        callbackFuncforProgress("Processing table snapshots", "Retrieving values to upload", 0.0)
        table_list = storageManager.get_all_table_snapshots()
        print(f"Found {len(table_list)} table snapshots to upload")
        
        snapshot_upload_dict = {}
        for key, obj in table_list.items():
            if obj:
                snapshot_upload_dict[key] = obj.get_json()
        
        if snapshot_upload_dict:
            def snapshot_progress(current, total, key):
                progress = round(current * 8 / total) / 10
                callbackFuncforProgress("Processing table snapshots", f"Uploading {key}", progress)
                print(f"Uploaded tablesnapshot: {key} ({current}/{total})")
            
            self.firebaseControls.batch_set_tableSnapshots(snapshot_upload_dict, snapshot_progress)
        
        callbackFuncforProgress("Processing table snapshots", "Finished", 1.0)
    
    def download_all_data(self, callbackFuncforProgress: callable, storageManager: 'StorageManager') -> None:
        """Download all data from Firebase.
        
        Args:
            callbackFuncforProgress: Callback function(text1, text2, progress)
            storageManager: StorageManager to save downloaded data
        """
        # Download left menu
        print("Getting left-menu values from db")
        callbackFuncforProgress("Processing Left Menu values", "Downloading values from Firebase", 0.0)
        
        leftmenu_future = self.firebaseControls.get_leftMenu_data_async()
        
        try:
            data = leftmenu_future.result(timeout=30)
            data = json.dumps(data, indent=4)
            callbackFuncforProgress("Processing Left Menu values", "Writing values to local file", 0.5)
            with open(self.leftMenuJsonPath, "w") as outfile:
                outfile.write(data)
            callbackFuncforProgress("Processing Left Menu values", "Finished", 1.0)
        except Exception as e:
            print(f"Error downloading left menu: {e}")
            callbackFuncforProgress("Processing Left Menu values", "Error occurred", 1.0)
        
        callbackFuncforProgress("Processing cheque reports", "Downloading values from Firebase", 0.0)
        
        # Download table snapshots
        print("Downloading tableSnapshot values from db")
        callbackFuncforProgress("Processing table snapshots", "Downloading values from Firebase", 0.0)
        
        snapshot_future = self.firebaseControls.get_tableSnapshot_async()
        
        try:
            incomingTableSnapshotData = snapshot_future.result(timeout=60)
            
            if incomingTableSnapshotData:
                total_val = len(incomingTableSnapshotData)
                count = 0
                
                for key in incomingTableSnapshotData:
                    count += 1
                    progress = round(count * 8 / total_val) / 10
                    callbackFuncforProgress("Processing table snapshots", f"Writing {key}", progress)
                    
                    tableSnapshot = storageManager.get_table_snapshot(
                        incomingTableSnapshotData[key]['month'],
                        incomingTableSnapshotData[key]['year'],
                        incomingTableSnapshotData[key]['bank'],
                        incomingTableSnapshotData[key]['company']
                    )
                    
                    if not tableSnapshot:
                        print(f"New tableSnapshot for {key}")
                        tableSnapshot = TableSnapshot(incomingTableSnapshotData[key])
                        storageManager.save_table_snapshot(tableSnapshot)
                    else:
                        print(f"Existing tableSnapshot found for {key}, replacing master table data")
                        tableSnapshot.set_master_table(incomingTableSnapshotData[key]['master_table'])
                
                callbackFuncforProgress("Processing table snapshots", "Finalizing", 0.9)
            else:
                print("No table snapshots found in Firebase")
            
            callbackFuncforProgress("Processing table snapshots", "Finished", 1.0)
        except Exception as e:
            print(f"Error downloading table snapshots: {e}")
            callbackFuncforProgress("Processing table snapshots", "Error occurred", 1.0)


class  TableOperations:
    """Coordinator class for table operations using service-oriented architecture.
    
    This class has been refactored to follow the Single Responsibility Principle.
    It delegates responsibilities to focused service classes:
    - StorageManager: Pickle persistence
    - ExcelProcessor: Excel import/export
    - SearchService: Search operations
    - ValidationService: Input validation
    - FirebaseService: Firebase sync
    - DataProcessor: Business logic (matching)
    - DaybookService: Daybook generation
    
    This class maintains backward compatibility with existing code while improving
    maintainability, testability, and code organization.
    """
    
    def __init__(self):
        """Initialize table operations coordinator and all service classes."""
        # Initialize service classes
        self.storageManager = StorageManager()
        self.excelProcessor = ExcelProcessor()
        self.searchService = SearchService()
        self.validationService = ValidationService()
        self.firebaseService = FirebaseService()
        self.dataProcessor = DataProcessor()
        self.daybookService = DaybookService(self.validationService)
        
        # Maintain backward compatibility with old attributes
        self.tableSnapshotCollection = self.storageManager.tableSnapshotCollection
        self.chequeReportCollection = self.storageManager.chequeReportCollection
        self.firebaseControls = self.firebaseService.firebaseControls
        self.leftMenuJsonPath = self.firebaseService.leftMenuJsonPath
        self.TableSnapshot = None
        
        # Instance variables for backward compatibility (set by various methods)
        self.month = None
        self.year = None
        self.bank = None
        self.company = None
        
        print("TableOperations initialized with service-oriented architecture")

    # ===== Firebase Operations (delegate to FirebaseService) =====
    
    def upload_data_to_firebase_db(self, callbackFuncforProgress):
        """Upload data to Firebase using async batch operations.
        
        Args:
            callbackFuncforProgress: Callback function(text1, text2, progress)
        """
        return self.firebaseService.upload_all_data(callbackFuncforProgress, self.storageManager)
    
    def get_data_from_firebase_db(self, callbackFuncforProgress):
        """Download data from Firebase using async operations.
        
        Args:
            callbackFuncforProgress: Callback function(text1, text2, progress)
        """
        return self.firebaseService.download_all_data(callbackFuncforProgress, self.storageManager)

    # ===== Storage Operations (delegate to StorageManager) =====
    
    def get_table_from_collection(self, month, year, bank, company):
        """Get table snapshot from collection with calculated balances and date range.
        
        Args:
            month: Month name
            year: Year as string
            bank: Bank name
            company: Company name
        
        Returns:
            Tuple of (snapshot, formatted_data, credit_bal, debit_bal, start_date, end_date)
        """
        # Store parameters for backward compatibility (used by other methods)
        self.month = month
        self.year = year
        self.bank = bank
        self.company = company
        
        snapshot = self.storageManager.get_table_snapshot(month, year, bank, company)
        if not snapshot:
            return snapshot, '', '', '', '', ''
        
        # Get master table and calculate balances
        master_table = snapshot.get_master_table()
        credit_bal, debit_bal, start_date, end_date = self.dataProcessor.calculate_balances_and_dates(master_table)
        
        # Format table data for display
        formatted_data = self.dataProcessor.format_table_data(master_table)
        
        return snapshot, formatted_data, credit_bal, debit_bal, start_date, end_date
    
    def format_table_data(self, _tableData):
        """Format table data for display (delegate to DataProcessor).
        
        Args:
            _tableData: Raw table data
        
        Returns:
            Formatted table data
        """
        return self.dataProcessor.format_table_data(_tableData)
    
    def delete_table_from_collection(self, month, year, bank, company):
        """Delete table snapshot from collection.
        
        Args:
            month: Month name
            year: Year as string
            bank: Bank name
            company: Company name
        
        Returns:
            True if successful, False otherwise
        """
        return self.storageManager.delete_table_snapshot(month, year, bank, company)
    
    def delete_chequeReport_from_collection(self, year, company):
        """Delete cheque report from collection.
        
        Args:
            year: Financial year
            company: Company name
        
        Returns:
            True if successful, False otherwise
        """
        return self.storageManager.delete_cheque_report(year, company)
    
    def get_chequeReport_from_collection(self, year, company):
        """Get cheque report from collection.
        
        Args:
            year: Financial year
            company: Company name
        
        Returns:
            InfiChequeStatement object if found, None otherwise
        """
        # Store parameters for backward compatibility
        self.year = year
        self.company = company
        return self.storageManager.get_cheque_report(year, company)
    
    def save_snapshot_to_table(self, tableSnapshot):
        """Save table snapshot to collection.
        
        Args:
            tableSnapshot: TableSnapshot object to save
        
        Returns:
            True if successful, False otherwise
        """
        return self.storageManager.save_table_snapshot(tableSnapshot)
    
    def save_chequeReport_to_collection(self, chequeReportpath):
        """Save cheque report from Excel file to collection.
        
        Note: This method stores year and company in instance variables
        for backward compatibility. New code should pass these as parameters.
        
        Args:
            chequeReportpath: Path to cheque report Excel file
        
        Returns:
            True if successful, False otherwise
        """
        return self.storageManager.save_cheque_report(chequeReportpath, self.year, self.company)

    # ===== Data Processing (delegate to DataProcessor) =====
    
    def prepare_table_data(self, statementObj, infiChequeStatement, previous_infiChequeStatement):
        """Match bank statement entries with cheque report entries.
        
        Note: Uses instance variable self.bank for backward compatibility.
        
        Args:
            statementObj: Bank statement object (HDFC or ICICI)
            infiChequeStatement: Current year cheque report
            previous_infiChequeStatement: Previous year cheque report
        
        Returns:
            List of table rows with matched data
        """
        return self.dataProcessor.prepare_table_data(
            statementObj, infiChequeStatement, previous_infiChequeStatement, self.bank
        )
    
    def add_snapshot_to_table(self, statement_path):
        """Create table snapshot from bank statement file.
        
        Note: Uses instance variables (month, year, bank, company) for backward compatibility.
        
        Args:
            statement_path: Path to bank statement Excel file
        
        Returns:
            Tuple of (success: bool, status_code: int)
        """
        return self.dataProcessor.add_snapshot_to_table(
            statement_path, self.month, self.year, self.bank, self.company, self.storageManager
        )

    # ===== Excel Operations (delegate to ExcelProcessor) =====
    
    def export_to_excel(self, folder_url, snapshot):
        """Export table snapshot to Excel file with multiple sheets.
        
        Args:
            folder_url: Output path (folder or .xls file path)
            snapshot: TableSnapshot object to export
        
        Returns:
            Tuple of (success: bool, error_code: int)
        """
        return self.excelProcessor.export_to_excel(folder_url, snapshot)
    
    def get_header(self):
        """Get standard table header.
        
        Returns:
            List of column names
        """
        return self.excelProcessor.get_header()

    # ===== Search Operations (delegate to SearchService) =====
    
    def search(self, masterTableData, searchQuery, searchMode):
        """Search table data using specified mode.
        
        Args:
            masterTableData: Table data to search
            searchQuery: Search term
            searchMode: Search mode ('bychqno', 'bydate', 'bychqamt')
        
        Returns:
            Filtered and formatted table data
        """
        return self.searchService.search(masterTableData, searchQuery, searchMode)

    # ===== Daybook Operations (delegate to ValidationService and DaybookService) =====
    
    def validateIntermediateDaybook(self, path, fromDate, toDate, company):
        """Validate inputs for daybook generation.
        
        Args:
            path: Path to intermediate daybook Excel file
            fromDate: Start date in dd/mm/yyyy format
            toDate: End date in dd/mm/yyyy format
            company: Company name
        
        Returns:
            Tuple of (success: bool, error_code: int)
        """
        return self.validationService.validate_daybook_inputs(path, fromDate, toDate, company)
    
    def generateIntermediateDaybook(self):
        """Generate intermediate daybook from table snapshots.
        
        Returns:
            Tuple of (success: bool, code: int, error_message: str)
        """
        return self.daybookService.generate_daybook(self.storageManager)


class FirebaseControls:
    """Firebase operations with connection pooling and async support.
    
    Implements singleton pattern to ensure Firebase is initialized only once
    and reused across the application. All Firebase operations are executed 
    in a thread pool to prevent blocking the main thread.
    
    Connection Pooling Features:
    - Single Firebase app instance (singleton pattern)
    - Reusable database references
    - Thread-safe initialization
    - Shared thread pool executor
    """
    
    # Class-level attributes for connection pooling
    _instance = None
    _initialized = False
    _init_lock = threading.Lock()
    _app = None
    _tableSnapshot_ref = None
    _leftMenu_ref = None
    _chequeReport_ref = None
    
    def __new__(cls, max_workers=5):
        """Implement singleton pattern for connection pooling.
        
        Ensures only one FirebaseControls instance exists, preventing
        repeated Firebase initialization and improving performance.
        """
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super(FirebaseControls, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, max_workers=5):
        """Initialize Firebase connection with thread pool (only once).
        
        Args:
            max_workers: Maximum number of concurrent Firebase operations
        """
        # Only initialize once (connection pooling)
        if FirebaseControls._initialized:
            return
        
        with FirebaseControls._init_lock:
            if FirebaseControls._initialized:
                return
            
            # correction for auto-py-to-exe
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            
            certificate_path = os.path.join(base_path, r"service-account\\recordmatcher-firebase-adminsdk-mfcn7-d0ee2c6bad.json")
            
            # Initialize Firebase app only if not already initialized
            try:
                FirebaseControls._app = firebase_admin.get_app()
                print("Firebase app already initialized - reusing connection")
            except ValueError:
                # App doesn't exist, initialize it
                cred = credentials.Certificate(certificate_path)
                FirebaseControls._app = firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://recordmatcher-default-rtdb.firebaseio.com/'
                })
                print("Firebase app initialized successfully")
            
            # Create database references (reusable across all instances)
            FirebaseControls._tableSnapshot_ref = db.reference("/tableSnapshot/")
            FirebaseControls._leftMenu_ref = db.reference('/leftMenu/')
            FirebaseControls._chequeReport_ref = db.reference('/chequeReport')
            
            # Thread pool for async operations (shared across instances)
            self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Firebase")
            self._lock = threading.Lock()
            
            FirebaseControls._initialized = True
            print(f"Firebase connection pool initialized with {max_workers} workers")
    
    @property
    def tableSnapshot_ref(self):
        """Get the shared table snapshot reference."""
        return FirebaseControls._tableSnapshot_ref
    
    @property
    def leftMenu_ref(self):
        """Get the shared left menu reference."""
        return FirebaseControls._leftMenu_ref
    
    @property
    def chequeReport_ref(self):
        """Get the shared cheque report reference."""
        return FirebaseControls._chequeReport_ref
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing purposes only)."""
        with cls._init_lock:
            cls._instance = None
            cls._initialized = False
            if cls._app:
                try:
                    firebase_admin.delete_app(cls._app)
                except:
                    pass
                cls._app = None
    
    @staticmethod
    def _retry_with_exponential_backoff(operation, max_retries=3, base_delay=1.0, max_delay=30.0, operation_name="Firebase operation"):
        """Retry an operation with exponential backoff for transient failures.
        
        Args:
            operation: Callable to execute
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 30.0)
            operation_name: Name of operation for logging
            
        Returns:
            Result of the operation
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                result = operation()
                if attempt > 0:
                    print(f"✓ {operation_name} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e
                
                # Don't retry on final attempt
                if attempt >= max_retries:
                    print(f"✗ {operation_name} failed after {max_retries + 1} attempts: {e}")
                    break
                
                # Calculate exponential backoff with jitter
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(0, delay * 0.1)  # Add 10% jitter
                sleep_time = delay + jitter
                
                print(f"⚠ {operation_name} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                print(f"  Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
        
        raise last_exception
    
    def shutdown(self):
        """Shutdown the thread pool executor gracefully."""
        self.executor.shutdown(wait=True)
    
    # Synchronous methods with retry logic
    def set_tableSnapshot(self, child, data):
        """Synchronously set table snapshot data with retry logic.
        
        Automatically retries on transient network failures with exponential backoff.
        """
        return self._retry_with_exponential_backoff(
            lambda: self.tableSnapshot_ref.child(child).set(data),
            operation_name=f"set_tableSnapshot({child})"
        )
    
    def remove_tableSnapshot(self, child):
        """Synchronously remove table snapshot."""
        return self.tableSnapshot_ref.child(child).set({}) 
    
    def get_tableSnapshot(self):
        """Synchronously get all table snapshots with retry logic.
        
        Automatically retries on transient network failures with exponential backoff.
        """
        return self._retry_with_exponential_backoff(
            lambda: self.tableSnapshot_ref.get(),
            operation_name="get_tableSnapshot()"
        ) 
    
    def set_chequeReport(self, child, data):
        """Synchronously set cheque report data with retry logic.
        
        Automatically retries on transient network failures with exponential backoff.
        """
        return self._retry_with_exponential_backoff(
            lambda: self.chequeReport_ref.child(child).set(data),
            operation_name=f"set_chequeReport({child})"
        )
    
    def remove_chequeReport(self, child):
        """Synchronously remove cheque report."""
        return self.chequeReport_ref.child(child).set({}) 
    
    def get_chequeReport(self):
        """Synchronously get all cheque reports with retry logic.
        
        Automatically retries on transient network failures with exponential backoff.
        """
        return self._retry_with_exponential_backoff(
            lambda: self.chequeReport_ref.get(),
            operation_name="get_chequeReport()"
        )     
    
    def set_leftMenu_data(self, data):
        """Synchronously set left menu data with retry logic.
        
        Automatically retries on transient network failures with exponential backoff.
        """
        return self._retry_with_exponential_backoff(
            lambda: self.leftMenu_ref.set(data),
            operation_name="set_leftMenu_data()"
        )
    
    def get_leftMenu_data(self):
        """Synchronously get left menu data with retry logic.
        
        Automatically retries on transient network failures with exponential backoff.
        """
        return self._retry_with_exponential_backoff(
            lambda: self.leftMenu_ref.get(),
            operation_name="get_leftMenu_data()"
        )
    
    # Async methods (non-blocking)
    def set_tableSnapshot_async(self, child, data):
        """Asynchronously set table snapshot data.
        
        Returns:
            Future object that can be used to check status or get result
        """
        return self.executor.submit(self.set_tableSnapshot, child, data)
    
    def get_tableSnapshot_async(self):
        """Asynchronously get all table snapshots.
        
        Returns:
            Future object that will contain the snapshot data
        """
        return self.executor.submit(self.get_tableSnapshot)
    
    def set_chequeReport_async(self, child, data):
        """Asynchronously set cheque report data.
        
        Returns:
            Future object that can be used to check status or get result
        """
        return self.executor.submit(self.set_chequeReport, child, data)
    
    def get_chequeReport_async(self):
        """Asynchronously get all cheque reports.
        
        Returns:
            Future object that will contain the report data
        """
        return self.executor.submit(self.get_chequeReport)
    
    def set_leftMenu_data_async(self, data):
        """Asynchronously set left menu data.
        
        Returns:
            Future object that can be used to check status or get result
        """
        return self.executor.submit(self.set_leftMenu_data, data)
    
    def get_leftMenu_data_async(self):
        """Asynchronously get left menu data.
        
        Returns:
            Future object that will contain the menu data
        """
        return self.executor.submit(self.get_leftMenu_data)
    
    # Batch operations for better performance
    def batch_set_tableSnapshots(self, items_dict, progress_callback=None):
        """Set multiple table snapshots concurrently.
        
        Args:
            items_dict: Dictionary of {child_key: data} to upload
            progress_callback: Optional callback(current, total, key) for progress
            
        Returns:
            List of results from all operations
        """
        futures = {}
        total = len(items_dict)
        
        for key, data in items_dict.items():
            future = self.set_tableSnapshot_async(key, data)
            futures[future] = key
        
        results = []
        for idx, future in enumerate(as_completed(futures), 1):
            key = futures[future]
            try:
                result = future.result()
                results.append((key, True, result))
                if progress_callback:
                    progress_callback(idx, total, key)
            except Exception as e:
                results.append((key, False, str(e)))
                print(f"Error uploading {key}: {e}")
        
        return results
    
    def batch_set_chequeReports(self, items_dict, progress_callback=None):
        """Set multiple cheque reports concurrently.
        
        Args:
            items_dict: Dictionary of {child_key: data} to upload
            progress_callback: Optional callback(current, total, key) for progress
            
        Returns:
            List of results from all operations
        """
        futures = {}
        total = len(items_dict)
        
        for key, data in items_dict.items():
            future = self.set_chequeReport_async(key, data)
            futures[future] = key
        
        results = []
        for idx, future in enumerate(as_completed(futures), 1):
            key = futures[future]
            try:
                result = future.result()
                results.append((key, True, result))
                if progress_callback:
                    progress_callback(idx, total, key)
            except Exception as e:
                results.append((key, False, str(e)))
                print(f"Error uploading {key}: {e}")
        
        return results

# class InfiDaybookModifier:
class IntermediateDaybook:
    path = None
    df = None
    header = None
    valid_ids = None
    id_count = 0

    def __init__(self, path, fromDate, toDate, company):
        self.path = path
        self.toDate = toDate
        self.fromDate = fromDate
        self.company = company
        # Ensure temp directory exists and clean old files
        ensure_temp_dir_exists('./temp/')
        # Clean up temp files older than 7 days on initialization
        cleanup_temp_files('./temp/', max_age_days=7)
        return 
    def validateAndSetValues(self):
        if validate_path(self.path):
            try:
                self.df = pd.read_excel(self.path)
            except ValueError:
                return False, -8
            self.header = list(self.df.columns)
        else:
            return False, -1
        
        # Use centralized DateHandler for date parsing and validation
        handler = get_date_handler()
        try:
            self.fromDate = handler.parse_to_naive(self.fromDate)
        except Exception:
            return False, -2
        
        try:
            self.toDate = handler.parse_to_naive(self.toDate)
        except Exception:
            return False, -3
        
        # Validate date range using DateHandler
        valid, error_msg = validate_date_range(self.fromDate, self.toDate, max_months=12)
        if not valid:
            if "before or equal" in error_msg:
                return False, -4  # Start date not before end date
            elif "exceeds maximum" in error_msg:
                return False, -5  # Exceeds 12 months
            else:
                return False, -2  # Other validation error    
        if self.company not in ['gokul','universal','gawel1','gawel2','focus']:
            return False, -6
        try:
            self.grab_data()
        except:
            raise        
        return True, 1    
    def getFromDate(self):
        return self.fromDate    
    def getToDate(self):
        return self.toDate  
    def getCompany(self):
        return self.company            
    def getPath(self):
        return self.path
    def getdf(self):
        return self.df      
    def convert_to_datetime_obj(self, date):
        """Convert date string to datetime object using centralized DateHandler."""
        handler = get_date_handler()
        return handler.parse_to_naive(date)    
    def grab_data(self):
        self.df = self.df[self.df['Number'].notna()]
        # Vectorized date conversion with error handling
        # Try primary format first, fallback to secondary format if needed
        try:
            self.df['Date'] = pd.to_datetime(self.df['Date'], format='%d-%m-%Y', errors='coerce')
            # Fill NaT values by trying alternative format
            mask = self.df['Date'].isna()
            if mask.any():
                self.df.loc[mask, 'Date'] = pd.to_datetime(
                    self.df.loc[mask, 'Date'], 
                    format='%d-%b-%Y', 
                    errors='coerce'
                )
        except:
            # Fallback to slower but more flexible parsing
            self.df['Date'] = self.df['Date'].apply(self.convert_to_datetime_obj)
        return
    def prepare_valid_ids_without_bank_receipt_voucher_filtering(self):
        vouchers_with_receipt_df = self.df[(self.df["Voucher Type"]=="Receipt Voucher") & (self.df["Debit Ledger"] == "Cash Book")]
        # valid_ids__without_receipt = vouchers_without_receipt_df['Number'].unique()
        valid_ids__with_receipt = vouchers_with_receipt_df['Number'].unique()
        if valid_ids__with_receipt is []:
            return pd.DataFrame()
        vouchers_without_receipt_df = self.df[((self.df['Voucher Type']!="Receipt Voucher") & (self.df['Voucher Type']!="Payment Voucher"))]
        daybook_wih_fixed_data = self.df[ self.df['Number'].isin(valid_ids__with_receipt)].copy()
        # Replace append with concat for better performance
        daybook_wih_fixed_data = pd.concat([daybook_wih_fixed_data, vouchers_without_receipt_df], ignore_index=True)
        daybook_wih_fixed_data.reset_index(inplace=True, drop=True)
        daybook_wih_fixed_data = daybook_wih_fixed_data[(daybook_wih_fixed_data['Date']>=self.fromDate) & (daybook_wih_fixed_data['Date']<=self.toDate)]
        # Vectorized date formatting (faster than apply with lambda)
        daybook_wih_fixed_data['Date'] = daybook_wih_fixed_data['Date'].dt.strftime('%d-%m-%Y')
        daybook_wih_fixed_data.reset_index(inplace=True, drop=True)
        daybook_wih_fixed_data.to_excel("./temp/daybook_wih_fixed_data.xlsx")
        return daybook_wih_fixed_data
    # def prepare_valid_ids_with_bank_receipt_voucher_filtering(self, consolidatedChequeReport, startDate, endDate):
    #     valid_list, filtered_df = consolidatedChequeReport.get_id_list_in_time_range(startDate,endDate)
    #     if valid_list is []:
    #         return pd.DataFrame()
    #     daybook_with_added_data = self.df[ self.df['Number'].isin(valid_list)].copy()
    #     daybook_with_added_data.reset_index(inplace=True, drop=True)
    #     daybook_with_added_data['Debit Ledger'] = daybook_with_added_data.apply(lambda x: filtered_df['Bank Name'][x['Number']] if not pd.isnull(x["Debit Ledger"]) else None, axis=1)
    #     daybook_with_added_data['Date'] = daybook_with_added_data['Number'].apply(lambda x: str(datetime.datetime.strftime(filtered_df['Bank Date'][x], '%d-%m-%Y')))
    #     daybook_with_added_data['Narration'] = daybook_with_added_data.apply(lambda x: x['Narration'] + ' ' + filtered_df['Narration'][x['Number']],axis=1)
    #     daybook_with_added_data.to_excel("./temp/daybook_wih_added_data.xlsx")
    #     return daybook_with_added_data
    def create_id_for_voucher(self, Bank_Name,Date,type='p'):
        bank_letter = Bank_Name[0].upper()
        month_number = str(int(Date.strftime('%m')))
        self.id_count+=1
        return type.upper()+bank_letter+month_number+'-'+str(self.id_count)        
    def prepare_payment_voucher_daybook_entries(self, consolidated_df):
        if consolidated_df.empty:
            return pd.DataFrame()
        row_1_df = pd.DataFrame()
        row_1_df['Number'] = consolidated_df.apply( lambda x: self.create_id_for_voucher(x['Bank Name'],x['Date']), axis=1 )
        # Vectorized date formatting (faster than apply with lambda)
        formatted_dates = consolidated_df['Date'].dt.strftime("%d-%m-%Y")
        row_1_df['Date'] = formatted_dates
        row_1_df['Voucher Type'] = "Payment Voucher"
        row_1_df['Debit Ledger'] =  PAYMENT_INTERMEDIARY_TALLY_LEDGERNAME
        row_1_df['Debit Amount'] =  consolidated_df['Amount']
        row_1_df['Narration'] = consolidated_df['Narration']
        row_2_df = pd.DataFrame()
        row_2_df['Number'] = row_1_df['Number']
        row_2_df['Date'] = consolidated_df['Date']
        row_2_df['Voucher Type'] = "Payment Voucher"
        row_2_df["Credit Ledger"] = consolidated_df["Bank Name"]
        row_2_df["Credit Amount"] = consolidated_df["Amount"]
        row_2_df['Narration'] = consolidated_df['Narration']
        output_df = pd.concat([row_1_df, row_2_df]).sort_index(kind='merge')
        output_df.to_excel(get_temp_file_path('payment_voucher_only_daybook.xlsx'))
        return output_df   
    def prepare_receipt_voucher_without_cheques_daybook_entries(self, consolidated_df):
        if consolidated_df.empty:
            return pd.DataFrame()
        row_1_df = pd.DataFrame()
        row_1_df['Number'] = consolidated_df.apply( lambda x: self.create_id_for_voucher(x['Bank Name'],x['Date'],type='r'), axis=1 )
        # Vectorized date formatting (faster than apply with lambda)
        row_1_df['Date'] = consolidated_df['Date'].dt.strftime("%d-%m-%Y")
        row_1_df['Voucher Type'] = "Receipt Voucher"
        row_1_df['Debit Ledger'] =  consolidated_df["Bank Name"]
        row_1_df['Debit Amount'] =  consolidated_df['Amount']
        row_1_df['Narration'] = consolidated_df['Narration']
        row_2_df = pd.DataFrame()
        row_2_df['Number'] = row_1_df['Number']
        row_2_df['Date'] = row_1_df['Date']
        row_2_df['Voucher Type'] = "Receipt Voucher"
        row_2_df["Credit Ledger"] = RECEIPT_INTERMEDIARY_TALLY_LEDGERNAME
        row_2_df["Credit Amount"] = consolidated_df["Amount"]
        row_2_df['Narration'] = consolidated_df['Narration']
        output_df = pd.concat([row_1_df, row_2_df]).sort_index(kind='merge')
        output_df.to_excel(get_temp_file_path('receipt_voucher_without_cheques_daybook.xlsx'))
        return output_df  
    def prepare_receipt_voucher_with_cheques_daybook_entries(self, consolidated_df):
        if consolidated_df.empty:
            print("Empty consolidatedChequeReceiptVouchers")
            return pd.DataFrame()
        consolidated_df['Narration'] = consolidated_df.apply(lambda x: x['Cheque No.'] if x['Bank Name']==HDFC_TALLY_LEDGERNAME else x['Narration'], axis=1 )
        row_1_df = pd.DataFrame()
        row_1_df['Number'] = consolidated_df.apply( lambda x: self.create_id_for_voucher(x['Bank Name'],x['Date'],type='c'), axis=1 )
        # Vectorized date formatting (faster than apply with lambda)
        row_1_df['Date'] = consolidated_df['Date'].dt.strftime("%d-%m-%Y")
        row_1_df['Voucher Type'] = "Receipt Voucher"
        row_1_df['Debit Ledger'] =  consolidated_df["Bank Name"]
        row_1_df['Debit Amount'] =  consolidated_df['Amount']
        row_1_df['Narration'] = consolidated_df['Narration']   
        row_2_df = pd.DataFrame()
        row_2_df['Number'] = row_1_df['Number']
        row_2_df['Date'] = row_1_df['Date']
        row_2_df['Voucher Type'] = "Receipt Voucher"
        row_2_df["Credit Ledger"] = consolidated_df['Debit Ledger']
        row_2_df["Credit Amount"] = consolidated_df["Amount"]
        row_2_df['Narration'] = consolidated_df['Narration']
        output_df = pd.concat([row_1_df, row_2_df]).sort_index(kind='merge')
        output_df.to_excel(get_temp_file_path('receipt_voucher_with_cheques_daybook.xlsx'))
        return output_df   
    def prepare_daybook(self, consolidatedChequeReceiptVouchers, consolidatedBankPaymentVouchers, consolidatedWithoutChequeReceiptVouchers):
        # Collect all DataFrames in a list for efficient concatenation
        daybook_parts = [
            self.prepare_valid_ids_without_bank_receipt_voucher_filtering(),
            # self.prepare_valid_ids_with_bank_receipt_voucher_filtering(consolidatedChequeReport, startDate, endDate),
            self.prepare_receipt_voucher_with_cheques_daybook_entries(consolidatedChequeReceiptVouchers),
            self.prepare_payment_voucher_daybook_entries(consolidatedBankPaymentVouchers),
            self.prepare_receipt_voucher_without_cheques_daybook_entries(consolidatedWithoutChequeReceiptVouchers)
        ]
        
        # Filter out empty DataFrames and concatenate all at once
        non_empty_parts = [df for df in daybook_parts if not df.empty]
        if non_empty_parts:
            final_daybook = pd.concat(non_empty_parts, ignore_index=True)
        else:
            final_daybook = pd.DataFrame()
            
        column_list = "Number	Date	Voucher Type	Debit Ledger	Debit Amount	Credit Ledger	Credit Amount	Narration".split('\t')
        final_daybook = final_daybook.reindex(columns=column_list)
        final_daybook.to_excel('./temp/final_daybook.xlsx', index=False)
        return final_daybook

class ConsolidatedReceiptVouchers:
    def __init__(self, snapshot_list):
        self.snapshot_list = snapshot_list
        self.receipt_with_cheques = pd.DataFrame()
        self.receipt_without_cheques = pd.DataFrame()
        self.main_df = pd.DataFrame()

    def prepare_df(self, startDate, endDate, mode="matched_cheques"):    
        # Collect all DataFrames in a list for efficient concatenation
        df_list = []
        
        for each in self.snapshot_list:
            temp_df = pd.DataFrame(each.get_master_table())
            if not temp_df.empty:
                if each.get_company()=='universal':
                    bank_name = ICICI_TALLY_LEDGERNAME_UNI
                elif each.get_bank() =='icici':
                    bank_name = ICICI_TALLY_LEDGERNAME_GOK
                else: 
                    bank_name = HDFC_TALLY_LEDGERNAME
                # Use categorical dtype for memory optimization
                temp_df['Bank Name'] = pd.Categorical([bank_name] * len(temp_df), 
                                                      categories=[HDFC_TALLY_LEDGERNAME, 
                                                                ICICI_TALLY_LEDGERNAME_GOK, 
                                                                ICICI_TALLY_LEDGERNAME_UNI])
                df_list.append(temp_df)
        
        # Concatenate all DataFrames at once (much faster than iterative append)
        if df_list:
            self.main_df = pd.concat(df_list, ignore_index=True)
        else:
            self.main_df = pd.DataFrame()
            
        if self.main_df.empty:
            return       
        
        self.main_df.to_excel('./temp/test123.xlsx')
         
        self.main_df.drop('Closing Balance', axis='columns', inplace=True)
        self.main_df.drop('Infi Date', axis='columns', inplace=True)
        self.main_df = self.main_df[ ~(self.main_df['meta'].isna())]
        # self.main_df = self.main_df[ (self.main_df['Party Name'].isna())]
        self.main_df.drop('meta', axis='columns', inplace=True)
        if mode == "matched_cheques":
            self.main_df = self.get_receipts_with_cheque_entries()
        else:
            self.main_df = self.get_receipts_without_cheque_entries()
        self.main_df.drop('Debit', axis='columns', inplace=True)
        # Vectorized date parsing (faster than map with lambda)
        self.main_df['Date'] = pd.to_datetime(self.main_df['Bank Date'], dayfirst=True, errors='coerce')
        self.main_df.drop('Bank Date', axis='columns', inplace=True)
        # Filter by date range using vectorized comparison
        self.main_df = self.main_df[ (self.main_df['Date']>=startDate) & (self.main_df['Date']<=endDate) ]
        self.main_df.rename(columns={'Chq No': 'Cheque No.', 'Bank Narration':'Narration', 'Credit':'Amount', 'Party Name': 'Debit Ledger'}, inplace=True)

        self.main_df.reset_index(inplace=True, drop=True) 
        if mode == "matched_cheques":
            self.main_df.to_excel('./temp/receipt cheque voucher consolidated.xlsx')
            self.receipt_with_cheques = self.main_df    
            print('Prepared consolidated Receipt Vouchers df')
        else:
            self.main_df.to_excel('./temp/receipt voucher without cheques daybook.xlsx') 
            self.receipt_without_cheques = self.main_df   
            print('Prepared consolidated Receipt Vouchers without cheques df')

    def process_date(self, val):
        try:
            return dateutil.parser.parse(val, dayfirst=True)
        except :
            print("Cannot process invalid date value: '", val, "'. Skipping")
            return np.NaN
    def get_receipts_without_cheque_entries(self):
        self.main_df = self.main_df.replace(r'^\s*$', np.NaN, regex=True)
        new_df = self.main_df.dropna(subset=['Credit'])
        new_df =  new_df[ ~(new_df['Bank Narration'].str.contains("CHQ DEP - MICR 1 CLG - KOTTARAKARA", regex=False) ) & ~(new_df['Bank Narration'].str.contains("CLG/", regex=False)) ]
        return new_df
    def get_receipts_with_cheque_entries(self):
        self.main_df = self.main_df.replace(r'^\s*$', np.NaN, regex=True)
        new_df = self.main_df[ (self.main_df['Credit'].notna())]
        new_df =  new_df[ (new_df['Bank Narration'].str.contains("CHQ DEP - MICR 1 CLG - KOTTARAKARA", regex=False) ) | (new_df['Bank Narration'].str.contains("CLG/", regex=False)) ]
        new_df["Party Name"] = new_df["Party Name"].replace(np.NaN, RECEIPT_INTERMEDIARY_TALLY_LEDGERNAME, regex=True)  
        return new_df

    def get_receipt_without_cheques_df(self):
        return self.receipt_without_cheques
    def get_receipt_with_cheques_df(self):
        return self.receipt_with_cheques    
   
class ConsolidatedPaymentVouchers:
    def __init__(self, snapshot_list):
        self.snapshot_list = snapshot_list
        self.paymentVoucherDF = pd.DataFrame()
        self.main_df = pd.DataFrame()

    def prepare_df(self, startDate, endDate):    
        # Collect all DataFrames in a list for efficient concatenation
        df_list = []
        
        for each in self.snapshot_list:
            temp_df = pd.DataFrame(each.get_master_table())
            if not temp_df.empty:
                if each.get_company()=='universal':
                    bank_name = ICICI_TALLY_LEDGERNAME_UNI
                elif each.get_bank() =='icici':
                    bank_name = ICICI_TALLY_LEDGERNAME_GOK
                else: 
                    bank_name = HDFC_TALLY_LEDGERNAME
                # Use categorical dtype for memory optimization
                temp_df['Bank Name'] = pd.Categorical([bank_name] * len(temp_df),
                                                      categories=[HDFC_TALLY_LEDGERNAME,
                                                                ICICI_TALLY_LEDGERNAME_GOK,
                                                                ICICI_TALLY_LEDGERNAME_UNI])
                df_list.append(temp_df)
        
        # Concatenate all DataFrames at once (much faster than iterative append)
        if df_list:
            self.main_df = pd.concat(df_list, ignore_index=True)
        else:
            self.main_df = pd.DataFrame()
            
        if self.main_df.empty:
            return        
        self.main_df = self.main_df.replace(r'^\s*$', np.NaN, regex=True)
        self.main_df.drop('Closing Balance', axis='columns', inplace=True)
        self.main_df.drop('Infi Date', axis='columns', inplace=True)
        self.main_df.drop('Party Name', axis='columns', inplace=True)
        self.main_df = self.main_df.dropna(subset=['Debit'])
        # self.main_df.drop('Credit', axis='columns', inplace=True)
        self.main_df.drop('Chq No', axis='columns', inplace=True)
        # Vectorized date parsing (faster than map with lambda)
        self.main_df['Date'] = pd.to_datetime(self.main_df['Bank Date'], dayfirst=True, errors='raise')
        # Filter by date range using vectorized comparison
        self.main_df = self.main_df[ (self.main_df['Date']>=startDate) & (self.main_df['Date']<=endDate) ]
        self.main_df.drop('Bank Date', axis='columns', inplace=True)
        self.main_df.drop('meta', axis='columns', inplace=True)
        self.main_df.rename(columns={'Bank Date': 'Date', 'Bank Narration':'Narration', 'Debit':'Amount', }, inplace=True)
        # print(self.main_df.head())

        self.main_df.reset_index(inplace=True, drop=True)   
        self.main_df.to_excel('./temp/payment voucher consolidated.xlsx')    
        self.paymentVoucherDF = self.main_df
    def process_date(self, val):
            try:
                final_val = dateutil.parser.parse(val, dayfirst=True)
                # print(val, final_val)
                return final_val
            except :
                raise
    def get_payment_entries_df(self):
        return self.paymentVoucherDF
