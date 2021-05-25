import QtQuick 2.12
import QtQuick.Controls 2.4
//import Qt.labs.qmlmodels 1.0

Rectangle {

    height: 607
    width: 1000
    color: "#f2f6f9"
    border.color: "#f2f6f9"
    radius: 8
    anchors.fill: parent

    property color textColor: "#324254"
    property color textColorHighlight: "#324254"
    property color textColorSelected: "#97a1ad"
    property color rowBgColor: "#ffffff"
    property color rowBgColorHighlight: "#d4e6ed"
    property color rowBgColorSelected: "#324254"

    TableView {
        id: tableView
        rowHeightProvider: function (column) { return 764; }
        columnWidthProvider: function (column) { return 1264; }
        implicitHeight: parent.height
        implicitWidth: parent.width
         anchors.fill: parent
        anchors.rightMargin: 2
        anchors.leftMargin: 2
        anchors.bottomMargin: 2
        anchors.topMargin: 2
        //backgroundVisible : false
        clip: true
//        model:  TableModel {
//            TableModelColumn { display: "name" }
//            TableModelColumn { display: "color" }

//            rows: [
//                {
//                    "name": "cat",
//                    "color": "black"
//                },
//                {
//                    "name": "dog",
//                    "color": "brown"
//                },
//                {
//                    "name": "bird",
//                    "color": "white"
//                }
//            ]
//        }
        delegate: Item {
                    Text {
                        text: display
                        anchors.fill: parent
                        anchors.margins: 10

                        color: '#aaaaaa'
                        font.pixelSize: 15
                        verticalAlignment: Text.AlignVCenter
                    }
                }
                Rectangle { // mask the headers
                    z: 3
                    color: "#00000000"
                    y: tableView.contentY
                    x: tableView.contentX
                    width: tableView.leftMargin
                    height: tableView.topMargin
                }

                Row {
                    id: columnsHeader
                    height: 51
//                    y: tableView.contentY
                    z: 2
                    Repeater {
                        model: tableView.columns > 0 ? tableView.columns : 1
                        Label {
                            width: tableView.columnWidthProvider(modelData)
                            height: 35
                            text: "Column" + modelData
                            color: textColor
                            padding: 10
                            verticalAlignment: Text.AlignVCenter
                            font.styleName: "Bold"
                            font.family: "PT Sans Caption"
                            font.pointSize: 10
                            background: Rectangle { color: "#f2f6f9" }
                        }
                    }
                }
                Column {
                    id: rowsHeader
                    height: 51
                    //x: tableView.contentX
                    z: 2
                    Repeater {
                        model: tableView.rows > 0 ? tableView.rows : 1
                        Label {
                            width: 180
                            height: tableView.rowHeightProvider(modelData)
                            text: "Row" + modelData
                            color: textColor
                            padding: 10
                            verticalAlignment: Text.AlignVCenter
                            font.styleName: "Bold"
                            font.family: "PT Sans Caption"
                            font.pointSize: 10
                            background: Rectangle { color: "#f2f6f9" }
                        }
                    }
                }

                ScrollIndicator.horizontal: ScrollIndicator { }
                ScrollIndicator.vertical: ScrollIndicator { }
            }
}

/*##^##
Designer {
    D{i:0;formeditorZoom:0.25}D{i:9}
}
##^##*/

