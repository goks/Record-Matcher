# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys
import json

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QObject, SIGNAL, Slot, Signal, Property

import core as C
from core import TableSnapshot, InfiChequeStatement

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QObject):
    def __init__(self):
        QObject.__init__(self)
        json_path = os.path.join(CURRENT_DIR, "data.json")
        with open(json_path) as f:
            data = json.load(f)
        self.hdfcBankChequeStatement = C.HDFCBankChequeStatement()
        self.iciciBankChequeStatement = C.ICICIBankChequeStatement() 
        self.tableOperations = C.TableOperations()  
        self.tableSnapshot = None
        self._monthDict = data['Months']    
        self._yearDict = data['Years']    
        self._bankDict = data['Banks'] 
        self._companyDict = data['Companies']  
        self._monthYearData = ''
        self._companyData = ''
        self._bankData = ''
        self._tableData =  [] 
        self._header = ['Bank Date', 'Bank Narration', 'Chq No','Party Name' ,'Infi Date','Credit', 'Debit', 'Closing Balance' ]
        self._selectedRows = [1,2,3]
        self.current_month = ''
        self.current_bank = ''
        self.current_year = ''
        self.current_company = ''
        self.chequeReportActivated  = False
        return   

    chequeReportsButtonClicked = Signal(bool,int,str, arguments=['selected','status','time'])
    showTablePage = Signal()
    showUploadBankStatementPage = Signal()
    showChooseOptionsPage = Signal()
    validationError = Signal(int, arguments=['type'])
    checkReportUploadSuccess = Signal()
    showChequeReportPage = Signal(int,str, arguments=['status','time'])
    bankStatementUploadSuccess = Signal()

    def save_snapshot(self):
        if(self.tableSnapshot):  
            print("saving selected rows",self.selectedRows)
            self.tableSnapshot.set_master_selected_rows(self._selectedRows)    
            self.tableOperations.save_snapshot_to_table(self.tableSnapshot)    
    @Slot(str)
    def uploadFile(self, fileUrl):
        if '' in [self.current_company, self.current_year]:
            self.validationError.emit(1)
            return   
        if not self.chequeReportActivated and '' in [self.current_bank, self.current_company, self.current_year, self.current_month]:
            self.validationError.emit(3)
            return        
        fileUrl = fileUrl.split('///')[1]
        # print('fileUrl', fileUrl, os.path.isfile(fileUrl) )
        if self.chequeReportActivated:
            if not self.tableOperations.save_chequeReport_to_collection(fileUrl):
                self.validationError.emit(2) 
            else: self.checkReportUploadSuccess.emit()               
            return                
        success, status_code = self.tableOperations.add_snapshot_to_table(fileUrl)    
        if not success:
            self.validationError.emit(status_code)
        else: self.bankStatementUploadSuccess.emit()
        return

    def populate_table(self):
        print(self.current_bank, self.current_company, self.current_month, self.current_year)
        if '' in [self.current_bank, self.current_company, self.current_month, self.current_year]:
            self.showChooseOptionsPage.emit()
            return -1
        self.save_snapshot()
        print('POPULATING TABLE')
        self.tableSnapshot = self.tableOperations.get_table_from_collection(self.current_month, self.current_year, self.current_bank, self.current_company)    
        if not self.tableSnapshot:
            self.showUploadBankStatementPage.emit()
            print("No tablesnapshot saved")
            return 0
        print("Snapshot found")    
        self._tableData = self.tableSnapshot.get_master_table()
        self.table_data_changed.emit()
        self._selectedRows = self.tableSnapshot.get_master_selected_rows()
        self.selectedRows_changed.emit()
        self.showTablePage.emit()
        return 1
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

    @Slot()
    def convertSchema(self):
        print('Converting Old to New Schema') 
        self.tableOperations.convert_old_schema_to_new_schema()  
    @Slot(bool)
    def showChequeReportsSelection(self, selected):
        status, data = self.populateChequeReports()
        self.chequeReportsButtonClicked.emit(selected, status, data )

    @Slot(str, str)
    def companyChanged(self, companyname, screenName):
        self.current_company = companyname
        self._companyData = screenName
        self.companyData_changed.emit()
        if self.chequeReportActivated:
            status, data = self.populateChequeReports()
            self.showChequeReportPage.emit(status, data )
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

    companyDict = Property('QVariantList', get_companyDict, notify=companyDict_changed)
    bankDict = Property('QVariantList', get_bankDict, notify=bankDict_changed)
    yearDict = Property('QVariantList', get_yearDict, notify=yearDict_changed)
    monthDict = Property('QVariantList', get_monthDict, notify=monthDict_changed)
    tableData = Property('QVariantList', get_table_data, notify=table_data_changed)
    header = Property('QVariantList', get_header, notify=header_changed)
    monthYearData = Property(str, get_monthYearData, notify=monthYearData_changed)
    companyData = Property(str, get_companyData, notify=companyData_changed)
    bankData = Property(str, get_bankData, notify=bankData_changed)
    selectedRows = Property('QVariantList', get_selectedRows, notify=selectedRows_changed)
    


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
