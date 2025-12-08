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

from PySide2.QtGui import QGuiApplication, QIcon
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QBitArray, QObject, SIGNAL, Slot, Signal, Property, QDate

import core as C
from core import TableOperations, TableSnapshot, InfiChequeStatement

from core import TableSnapshotCollection

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.hdfcBankChequeStatement = C.HDFCBankChequeStatement()
        self.iciciBankChequeStatement = C.ICICIBankChequeStatement() 
        self.tableOperations = C.TableOperations()  
        self.tableSnapshot = None
        self.masterDisplayTableData = list()
        self.populate_left_menu(True)
        self._monthYearData = ''
        self._companyData = ''
        self._bankData = ''
        self._tableData =  list()
        self._creditBal = 'Credit Bal' 
        self._debitBal = 'Debit Bal' 
        self._header = self.tableOperations.get_header()
        self._selectedRows = [1,2,3]
        self._endDateCalendar =  QDate(2020,6,5)
        self._startDateCalendar = QDate(2016,1,1)
        self._progressBarValue = 0.0
        self._fullScreenLoadingInfo1 = ''
        self._fullScreenLoadingInfo2 = ''
        self.current_month = ''
        self.current_bank = ''
        self.current_year = ''
        self.current_company = ''
        self.chequeReportActivated  = False
        self.searchModeOffFirsttime = False
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
        return   
    def _thread_exception_wrapper(self, func, operation_name):
        """Wrapper to handle exceptions in threaded operations."""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                import traceback
                error_msg = f"{type(e).__name__}: {str(e)}"
                stack_trace = traceback.format_exc()
                print(f"[THREAD ERROR] {operation_name} failed:")
                print(stack_trace)
                # Emit signal to notify UI of error
                self.threadExceptionOccurred.emit(operation_name, error_msg)
                raise  # Re-raise to ensure thread pool tracks the failure
        return wrapper
    
    def populate_left_menu(self, first_time=False):
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
    
    def save_snapshot(self):
        """Save current snapshot with lock protection."""
        with self._snapshot_lock:
            snapshot = self.tableSnapshot
            selected_rows = self._selectedRows.copy() if self._selectedRows else []
        
        if snapshot:
            print(f"[SAVE] Saving snapshot with {len(selected_rows)} selected rows")
            snapshot.set_master_selected_rows(selected_rows)
            self.tableOperations.save_snapshot_to_table(snapshot)
        else:
            print("[SAVE] No snapshot to save")   

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
    def uploadFile(self, fileUrl):
        with self._state_lock:
            if '' in [self.current_company, self.current_year]:
                self.validationError.emit(1)
                return   
            if not self.chequeReportActivated and '' in [self.current_bank, self.current_month]:
                self.validationError.emit(3)
                return
        fileUrl = fileUrl.split('///')[1]
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.threadedUploadFile, "File Upload")
            future = self._thread_pool.submit(wrapped_func, fileUrl)
            self._active_futures.add(future)
        return
    def threadedUploadFile(self, fileUrl):
        """Thread worker for file upload with lock protection."""
        with self._state_lock:
            cheque_activated = self.chequeReportActivated
        
        if cheque_activated:
            if not self.tableOperations.save_chequeReport_to_collection(fileUrl):
                self.validationError.emit(2) 
            else: 
                self.checkReportUploadSuccess.emit()               
            return
        
        # Add snapshot to table (may modify shared state)
        success, status_code = self.tableOperations.add_snapshot_to_table(fileUrl)
        if not success:
            print(f"[ERROR] File upload failed with status code: {status_code}")
            self.validationError.emit(status_code)
        else:
            self.bankStatementUploadSuccess.emit()
        return
    @Slot(str)
    def exportFile(self, fileURL):
        with self._snapshot_lock:
            if not self.tableSnapshot:
                self.validationError.emit(4)
                return
            # Create a reference to current snapshot
            snapshot = self.tableSnapshot
        
        try:     
            fileURL = fileURL.split('///')[1]
        except:
            pass
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.threadedExportFile, "File Export")
            future = self._thread_pool.submit(wrapped_func, fileURL, snapshot)
            self._active_futures.add(future)
        return    
    def threadedExportFile(self, fileURL, snapshot):
        """Thread worker for file export with lock protection."""
        status, status_code = self.tableOperations.export_to_excel(fileURL, snapshot)
        if not status:
            print(f"[ERROR] File export failed with status code: {status_code}")
            self.validationError.emit(status_code)
        else:
            self.statementExportSuccess.emit()
        return  

    @Slot(str, str, str, str)
    def createIntermediateDaybook(self, daybookURL, fromDate, toDate, company):
        print(daybookURL, fromDate, toDate,company, "Validating intermediate daybook ")
        status, code = self.tableOperations.validateIntermediateDaybook(daybookURL, fromDate, toDate, company)
        print(status, code)
        if not status:
            self.dayBookExportHandlingError.emit(code, '')            
            return
        status, code, data = self.tableOperations.generateIntermediateDaybook()    
        if not status:
            self.dayBookExportHandlingError.emit(code, data)

    @Slot(list)
    def createTallyXMLVoucher(self, propertyArray):
        print("CREATE TALLY XML DAYBOOK", propertyArray)        

    def populate_table(self):
        self.showMainScreenLoadingIndicator.emit()
        with self._state_lock:
            current_state = (self.current_bank, self.current_company, self.current_month, self.current_year)
            print("Current state:", current_state)
            if '' in current_state:
                self.showChooseOptionsPage.emit()
                self.hideMainScreenLoadingIndicator.emit()
                return -1
            self.searchModeOffFirsttime = False
        
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.threadedPopulate_table, "Table Population")
            future = self._thread_pool.submit(wrapped_func)
            self._active_futures.add(future)
        return 1
    
    def threadedPopulate_table(self):
        """Thread worker for table population with lock protection."""
        self.save_snapshot()
        print('[THREAD] Populating table...')
        
        # Get current state safely
        with self._state_lock:
            month = self.current_month
            year = self.current_year
            bank = self.current_bank
            company = self.current_company
        
        # Load data from collection (may take time, no lock needed)
        tableSnapshot, masterDisplayTableData, credit_bal, debit_bal, start_date, end_date = \
            self.tableOperations.get_table_from_collection(month, year, bank, company)
        
        if not tableSnapshot:
            self.showUploadBankStatementPage.emit()
            print("[THREAD] No tablesnapshot saved")
            self.hideMainScreenLoadingIndicator.emit()
            return 0
        
        print("[THREAD] Snapshot found, updating state...")
        
        # Update shared state with lock
        with self._snapshot_lock:
            self.tableSnapshot = tableSnapshot
            self.masterDisplayTableData = masterDisplayTableData
        
        with self._data_lock:
            self._tableData = masterDisplayTableData
            self._creditBal = credit_bal
            self._debitBal = debit_bal
        
        # Emit signals to update UI
        self.table_data_changed.emit()
        self.creditBal_changed.emit()
        self.debitBal_changed.emit()
        
        print(f"[THREAD] Date range: {start_date} to {end_date}")
        self._startDateCalendar = QDate(int(start_date.split('/')[0]), int(start_date.split('/')[1]), int(start_date.split('/')[2]))
        self.startDateCalendar_changed.emit()
        self._endDateCalendar = QDate(int(end_date.split('/')[0]), int(end_date.split('/')[1]), int(end_date.split('/')[2]))
        self.endDateCalendar_changed.emit()
        
        with self._snapshot_lock:
            self._selectedRows = tableSnapshot.get_master_selected_rows()
        self.selectedRows_changed.emit()
        
        self.showTablePage.emit()
        self.hideMainScreenLoadingIndicator.emit()
        print('[THREAD] Table population complete')
        return 1

    def callBackFunction_for_Updating_fullScreenLoading(self, text1, text2, prograssbarVal):
        self._fullScreenLoadingInfo1 = text1
        self._fullScreenLoadingInfo2 = text2
        self._progressBarValue = prograssbarVal
        self.fullScreenLoadingInfo1_changed.emit()
        self.fullScreenLoadingInfo2_changed.emit()
        self.progressBarValue_changed.emit()
        return

    def populateChequeReports(self):    
        if '' in [self.current_company,self.current_year]:
            return -1, ''
        self.save_snapshot()
        print('POPULATING ChequeReport')
        self.infiChequeStatement = self.tableOperations.get_chequeReport_from_collection( self.current_year, self.current_company)    
        if not self.infiChequeStatement:
            print("No ChequeReport found")
            return 0, ''
        time = self.infiChequeStatement.get_last_edited_time() 
        print("ChequeReport found", time)    
        return 1, time
    @Slot(str, str)    
    def search(self, searchQuery, searchMode):
        print("Searching for ", searchQuery, " mode: ", searchMode)
        if not self.tableSnapshot:
            return
        if searchMode == "off" and self.searchModeOffFirsttime:
            self.populate_table()
            return
        self.searchModeOffFirsttime=False
        self._tableData = self.tableOperations.search(self.tableSnapshot.get_master_table(), searchQuery, searchMode)
        self.table_data_changed.emit()
        return 
    # @Slot()
    # def convertSchema(self):
    #     print('Converting Old to New Schema') 
    #     self.tableOperations.convert_old_schema_to_new_schema()  
    @Slot(bool)
    def showChequeReportsSelection(self, selected):
        status, data = self.populateChequeReports()
        self.chequeReportsButtonClicked.emit(selected, status, data )
    @Slot(bool)
    def showTallyExportBox(self, selected):
        # status, data = self.populateChequeReports()
        # self.chequeReportsButtonClicked.emit(selected, status, data )  
        self.tallyExportButtonClicked.emit(selected)
        pass
    
    def _cleanup_threads(self):
        """Properly shutdown all managed threads."""
        with self._shutdown_lock:
            if self._is_shutting_down:
                return
            self._is_shutting_down = True
        
        print("Shutting down thread pool...")
        
        # Wait for active futures to complete (with timeout)
        active_count = len(self._active_futures)
        if active_count > 0:
            print(f"Waiting for {active_count} active tasks to complete...")
            # Give threads reasonable time to finish
            import time
            max_wait = 10.0  # seconds
            start_time = time.time()
            
            while len(self._active_futures) > 0 and (time.time() - start_time) < max_wait:
                time.sleep(0.1)
            
            remaining = len(self._active_futures)
            if remaining > 0:
                print(f"Warning: {remaining} tasks did not complete within timeout")
        
        # Shutdown thread pool gracefully
        self._thread_pool.shutdown(wait=True, cancel_futures=False)
        print("Thread pool shutdown complete")
    
    @Slot()
    def beginWindowExitRoutine(self):
        """Enhanced exit routine with proper thread cleanup."""
        print("Beginning exit routine...")
        self.save_snapshot()
        self._cleanup_threads()
    @Slot()
    def downloadfromDb(self):
        self.fullScreenLoadingStart.emit()
        # Submit to thread pool with exception handling
        if not self._is_shutting_down:
            wrapped_func = self._thread_exception_wrapper(self.downloadfromDbThreaded, "Firebase Download")
            future = self._thread_pool.submit(wrapped_func)
            self._active_futures.add(future)
    
    def downloadfromDbThreaded(self):
        """Thread worker for Firebase download with exception handling."""
        print('[THREAD] Starting Firebase download...')
        self.tableOperations.get_data_from_firebase_db(self.callBackFunction_for_Updating_fullScreenLoading)
        print('[THREAD] Firebase download complete')
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
    
    def uploadtoDbThreaded(self):
        """Thread worker for Firebase upload with exception handling."""
        print('[THREAD] Starting Firebase upload...')
        self.tableOperations.upload_data_to_firebase_db(self.callBackFunction_for_Updating_fullScreenLoading)
        print('[THREAD] Firebase upload complete')
        self.fullScreenLoadingEnd.emit()
        return
    @Slot()
    def createTallyXMLFromDaybook(self):
        self.fullScreenLoading2Start.emit()
        print("Create TALLY XML here")


    @Slot(str, str)
    def companyChanged(self, companyname, screenName):
        with self._state_lock:
            self.current_company = companyname
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
        with self._state_lock:
            self.current_bank = bankname
            self._bankData = screenName
        self.bankData_changed.emit()
        self.populate_table()
    @Slot(str)
    def yearChanged(self, year):
        with self._state_lock:
            self.current_year = year
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
        with self._state_lock:
            self.current_month = month
        self.update_monthYearData()
        self.populate_table()
    def update_monthYearData(self):
        with self._state_lock:
            cheque_activated = self.chequeReportActivated
            current_year = self.current_year
            current_month = self.current_month
        
        if cheque_activated:
            if current_year:
                self._monthYearData = current_year + ' - ' + str(int(current_year)+1)
            else:
                self._monthYearData = ''
        else:
            self._monthYearData = current_month.capitalize() + ' ' + current_year
        
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
        # self.update_monthYearData()
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
        return self._tableData 
    @Signal
    def creditBal_changed(self):
        print('creditBal_changed')
        return
    def get_creditBal(self):
        return self._creditBal
    @Signal
    def debitBal_changed(self):
        print('debitBal_changed')
        return
    def get_debitBal(self):
        return self._debitBal         
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
