# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys
import json
import threading
import dateutil.parser

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
        return   
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
        if(self.tableSnapshot):  
            print("saving selected rows",self.selectedRows)
            self.tableSnapshot.set_master_selected_rows(self._selectedRows)    
            self.tableOperations.save_snapshot_to_table(self.tableSnapshot)   

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
        if '' in [self.current_company, self.current_year]:
            self.validationError.emit(1)
            return   
        if not self.chequeReportActivated and '' in [self.current_bank, self.current_month]:
            self.validationError.emit(3)
            return        
        fileUrl = fileUrl.split('///')[1]
        # print('fileUrl', fileUrl, os.path.isfile(fileUrl) )
        # self.threadedUploadFile(fileUrl)
        x = threading.Thread(target=self.threadedUploadFile, args=(fileUrl,), daemon=True)
        x.start()
        return
    def threadedUploadFile(self, fileUrl):    
        if self.chequeReportActivated:
            if not self.tableOperations.save_chequeReport_to_collection(fileUrl):
                self.validationError.emit(2) 
            else: self.checkReportUploadSuccess.emit()               
            return                
        success, status_code = self.tableOperations.add_snapshot_to_table(fileUrl)    
        if not success:
            print("ERROR", status_code)
            self.validationError.emit(status_code)
        else: self.bankStatementUploadSuccess.emit()
        return
    @Slot(str)
    def exportFile(self, fileURL):
        if not self.tableSnapshot:
            self.validationError.emit(4)
            return    
        try:     
            fileURL = fileURL.split('///')[1]
        except:
            pass
        # print('fileURL: ', fileURL, os.path.isdir(fileURL), os.path.isfile(fileURL) )
        x = threading.Thread(target=self.threadedExportFile, args=(fileURL,), daemon=True)
        x.start()
        return    
    def threadedExportFile(self, fileURL):    
        status, status_code = self.tableOperations.export_to_excel(fileURL, self.tableSnapshot)    
        if not status:
            self.validationError.emit(status_code)
        else: self.statementExportSuccess.emit()
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
        print(self.current_bank, self.current_company, self.current_month, self.current_year)
        if '' in [self.current_bank, self.current_company, self.current_month, self.current_year]:
            self.showChooseOptionsPage.emit()
            self.hideMainScreenLoadingIndicator.emit()
            return -1
        self.searchModeOffFirsttime=False
        x = threading.Thread(target=self.threadedPopulate_table, args=( ), daemon=True)
        x.start()
        return 1   
    def threadedPopulate_table(self):      
        self.save_snapshot()
        print('POPULATING TABLE')
        self.tableSnapshot, self.masterDisplayTableData, credit_bal, debit_bal, start_date,end_date = self.tableOperations.get_table_from_collection(self.current_month, self.current_year, self.current_bank, self.current_company)    
        if not self.tableSnapshot:
            self.showUploadBankStatementPage.emit()
            print("No tablesnapshot saved")
            self.hideMainScreenLoadingIndicator.emit()
            return 0
        print("Snapshot found")
        self._tableData = self.masterDisplayTableData
        self.table_data_changed.emit()
        self._creditBal = credit_bal
        self.creditBal_changed.emit()
        self._debitBal = debit_bal
        print(start_date, end_date)
        self.debitBal_changed.emit()
        self._startDateCalendar = QDate(int(start_date.split('/')[0]), int(start_date.split('/')[1]), int(start_date.split('/')[2]))
        self.startDateCalendar_changed.emit()
        self._endDateCalendar = QDate(int(end_date.split('/')[0]), int(end_date.split('/')[1]), int(end_date.split('/')[2]))
        self.endDateCalendar_changed.emit()        
        self._selectedRows = self.tableSnapshot.get_master_selected_rows()
        self.selectedRows_changed.emit()
        self.showTablePage.emit()
        self.hideMainScreenLoadingIndicator.emit()
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
    @Slot()
    def beginWindowExitRoutine(self):
        self.save_snapshot()
    @Slot()
    def downloadfromDb(self):
        self.fullScreenLoadingStart.emit()
        x = threading.Thread(target=self.downloadfromDbThreaded, args=(), daemon=True)
        x.start()
    def  downloadfromDbThreaded(self):
        self.tableOperations.get_data_from_firebase_db(self.callBackFunction_for_Updating_fullScreenLoading)
        self.fullScreenLoadingEnd.emit()
        return    
    @Slot()
    def uploadtoDb(self):
        self.fullScreenLoadingStart.emit()
        x = threading.Thread(target=self.uploadtoDbThreaded, args=(), daemon=True)
        x.start()
    def uploadtoDbThreaded(self):    
        self.tableOperations.upload_data_to_firebase_db(self.callBackFunction_for_Updating_fullScreenLoading)
        self.fullScreenLoadingEnd.emit()
        return
    @Slot()
    def createTallyXMLFromDaybook(self):
        self.fullScreenLoading2Start.emit()
        print("Create TALLY XML here")


    @Slot(str, str)
    def companyChanged(self, companyname, screenName):
        self.current_company = companyname
        self._companyData = screenName
        self.companyData_changed.emit()
        if self.chequeReportActivated:
            status, data = self.populateChequeReports()
            self.showChequeReportPage.emit(status, data )
            return
        elif self.tallyExportBoxActivated:
            self.showTallyExportBox.emit()
            return
        self.populate_table()
    @Slot(str, str)
    def bankChanged(self, bankname, screenName):
        self.current_bank = bankname
        self._bankData = screenName
        self.bankData_changed.emit()
        self.populate_table()
    @Slot(str)
    def yearChanged(self, year):
        self.current_year = year
        self.update_monthYearData()
        if self.chequeReportActivated:
            status, data = self.populateChequeReports()
            self.showChequeReportPage.emit(status, data )
            return
        elif self.tallyExportBoxActivated:
            self.showTallyExportBox.emit()
            return
        self.populate_table()
    @Slot(str, str)
    def monthChanged(self, month, screenNane):
        self.current_month = month 
        self.update_monthYearData()
        self.populate_table()
    def update_monthYearData(self):
        if self.chequeReportActivated: 
            if self.current_year:
                self._monthYearData = self.current_year + ' - ' +str(int(self.current_year)+1)
            else: self._monthYearData = ''    
        else: self._monthYearData = self.current_month.capitalize() +' ' + self.current_year
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
