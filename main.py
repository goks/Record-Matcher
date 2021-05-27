# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys
import json

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QObject, Slot, Signal, Property

import core as C
from core import TableSnapshot

# import pandas as pd
# from models import DataFrameModel

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
        # self.tableSnapshot = C.TableSnapshot() 
        self._monthDict = data['Months']    
        self._yearDict = data['Years']    
        self._bankDict = data['Banks'] 
        self._companyDict = data['Companies']  
        self._monthYearData = ''
        self._companyData = ''
        self._bankData = ''
        self._tableData =  [
        { "name": "Melbourne", "country": "Australia", "subcountry": "Victoria", "latitude": -37.9716929, "longitude": 144.7729583 },
        { "name": "London", "country": "United Kingdom", "subcountry": "England", "latitude": 51.5287718, "longitude": -0.2416804 },
        { "name": "Paris", "country": "France", "subcountry": "Île-de-France", "latitude": 48.8589507, "longitude": 2.2770205 },
        { "name": "New York City", "country": "United States", "subcountry": "New York", "latitude": 40.6976637, "longitude": -74.1197639 },
        { "name": "Tokyo", "country": "Japan", "subcountry": "Tokyo", "latitude": 35.6735408 , "longitude": 139.5703047 }
    ] 
        self._header = ['Bank Date', 'Bank Narration', 'Chq No','Party Name' ,'Infi Date','Credit', 'Debit', 'Closing Balance' ]
        self.current_month = ''
        self.current_bank = ''
        self.current_year = ''
        self.current_company = ''
        return   

    chequeReportsButtonClicked = Signal()

    def populate_table(self):
        print(self.current_bank, self.current_company, self.current_month, self.current_year)
        if '' in [self.current_bank, self.current_company, self.current_month, self.current_year]:
            return -1
        print('POPULATING TABLE')
        self.tableSnapshot = self.tableOperations.get_table(self.current_month, self.current_year, self.current_bank, self.current_company)    
        if not self.tableSnapshot:
            print("No tablesnapshot saved")
            return 0
        else:
            print("Snapshot found")    
        self._tableData = self.tableSnapshot.get_master_table()
        self.table_data_changed.emit()
        return 1

    @Slot()
    def convertSchema(self):
        print('Converting Old to New Schema') 
        self.tableOperations.convert_old_schema_to_new_schema()  
    @Slot()
    def showChequeReportsSelection(self):
        self.chequeReportsButtonClicked.emit()
    @Slot(str, str)
    def companyChanged(self, companyname, screenNane):
        self.current_company = companyname
        self._companyData = screenNane
        self.companyData_changed.emit()
        self.populate_table()
    @Slot(str, str)
    def bankChanged(self, bankname, screenNane):
        self.current_bank = bankname
        self._bankData = screenNane
        self.bankData_changed.emit()
        self.populate_table()
    @Slot(str)
    def yearChanged(self, year):
        self.current_year = year
        self.update_monthYearData()
        self.populate_table()
    @Slot(str, str)
    def monthChanged(self, month, screenNane):
        self.current_month = month 
        self.update_monthYearData()
        self.populate_table()
    def update_monthYearData(self):
        self._monthYearData = self.current_month.capitalize() +' ' + self.current_year
        self.monthYearData_changed.emit()

    
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

    companyDict = Property('QVariantList', get_companyDict, notify=companyDict_changed)
    bankDict = Property('QVariantList', get_bankDict, notify=bankDict_changed)
    yearDict = Property('QVariantList', get_yearDict, notify=yearDict_changed)
    monthDict = Property('QVariantList', get_monthDict, notify=monthDict_changed)
    tableData = Property('QVariantList', get_table_data, notify=table_data_changed)
    header = Property('QVariantList', get_header, notify=header_changed)
    monthYearData = Property(str, get_monthYearData, notify=monthYearData_changed)
    companyData = Property(str, get_companyData, notify=companyData_changed)
    bankData = Property(str, get_bankData, notify=bankData_changed)


class TableBackend(QObject):
    tableRowSelected = Signal(list)

    def __init__(self):
        QObject.__init__(self)
        self.checkedRows = []
        return
    @Slot(int)
    def tableRowSelectedNotify(self, currentRow):
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
