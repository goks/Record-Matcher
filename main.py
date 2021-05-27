# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys
import json

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QObject, Slot, Signal

# import pandas as pd
# from models import DataFrameModel


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QObject):
    def __init__(self):
        QObject.__init__(self)

    
    chequeReportsButtonClicked = Signal()

    @Slot()
    def showChequeReportsSelection(self):
        self.chequeReportsButtonClicked.emit()
    @Slot(str)
    def companyChanged(self, companyname):
        print(companyname)
    @Slot(str)
    def bankChanged(self, bankname):
        print(bankname)
    @Slot(str)
    def yearChanged(self, year):
        print(year)        

class TableBackend(QObject):


    def __init__(self):
        QObject.__init__(self)
        self.checkedRows = []
        json_path = os.path.join(CURRENT_DIR, "data.json")
        with open(json_path) as f:
            data = json.load(f)
        self. tableRowSelected = Signal(list)

    @Slot()
    def get_months(self):
        
    

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
