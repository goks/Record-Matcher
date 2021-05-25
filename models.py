import pandas as pd

from PySide2.QtCore import Property, QAbstractTableModel, QModelIndex, Qt, Slot


class DataFrameModel(QAbstractTableModel):
    DtypeRole = Qt.UserRole + 1000
    ValueRole = Qt.UserRole + 1001

    def __init__(self, df=pd.DataFrame(), parent=None):
        super(DataFrameModel, self).__init__(parent)
        self._dataframe = df

    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()

    def dataFrame(self):
        return self._dataframe

    dataFrame = Property(pd.DataFrame, fget=dataFrame, fset=setDataFrame)

    # @Slot(int, Qt.Orientation, result=str)
    # def headerData(
    #     self,
    #     section: int,
    #     orientation: Qt.Orientation,
    #     role: int = Qt.DisplayRole,
    # ):
    #     if role == Qt.DisplayRole:
    #         if orientation == Qt.Horizontal:
    #             return self._dataframe.columns[section]
    #         else:
    #             return str(self._dataframe.index[section])

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self._dataframe.columns.size

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (
            0 <= index.row() < self.rowCount()
            and 0 <= index.column() < self.columnCount()
        ):
            return
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt = self._dataframe[col].dtype

        val = self._dataframe.iloc[row][col]
        if role == Qt.DisplayRole:
            return str(val)
        elif role == DataFrameModel.ValueRole:
            return val
        if role == DataFrameModel.DtypeRole:
            return dt

    def roleNames(self):
        roles = {
            Qt.DisplayRole: b"display",
            DataFrameModel.DtypeRole: b"dtype",
            DataFrameModel.ValueRole: b"value",
        }
        return roles