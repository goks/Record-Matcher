# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtCore import QObject, Slot, Signal



class MainWindow(QObject):
    def __init__(self):
        QObject.__init__(self)
    
    chequeReportsButtonClicked = Signal()

    @Slot()
    def showChequeReportsSelection(self):
        print("OBTAINED")
        self.chequeReportsButtonClicked.emit()

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    #Get Context
    main = MainWindow()
    engine.rootContext().setContextProperty("backend", main)

    #Load QML File
    engine.load(os.fspath(Path(__file__).resolve().parent / "qml/main.qml"))

    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec_())
