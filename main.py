# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QObject, Slot, Signal

import pandas as pd
from models import DataFrameModel


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
checkedRows = []

class MainWindow(QObject):
    def __init__(self):
        QObject.__init__(self)
    
    chequeReportsButtonClicked = Signal()

    @Slot()
    def showChequeReportsSelection(self):
        print("OBTAINED")
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
    
    tableRowSelected = Signal(list)

    @Slot(int)
    def tableRowSelectedNotify(self, currentRow):
        print("currentRow " , currentRow)
        print('Before: ',checkedRows)

        if currentRow in checkedRows:
            checkedRows.remove(currentRow)
            print('After: ',checkedRows)
            self.tableRowSelected.emit(checkedRows)
        else:
            checkedRows.append(currentRow)
            print('After: ',checkedRows)
            self.tableRowSelected.emit(checkedRows)

if __name__ == "__main__":

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    #Get Context
    main = MainWindow()
    engine.rootContext().setContextProperty("backend", main)

    tableBackend = TableBackend()
    engine.rootContext().setContextProperty("tableBackend", tableBackend)

    csv_path = os.path.join(CURRENT_DIR, "test.csv")
    df = pd.read_csv(csv_path)
    model = DataFrameModel(df)
    engine.rootContext().setContextProperty("table_model", model)

    #Load QML File
    engine.load(os.fspath(Path(__file__).resolve().parent / "qml/main.qml"))

    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec_())
