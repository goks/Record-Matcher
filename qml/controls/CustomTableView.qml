import QtQuick 2.15
import QtQuick.Controls 1.4
import QtQuick.Controls 2.15 as C
Rectangle {
    width: 596
    height: 607
    color: "#f2f6f9"
    border.color: "#f2f6f9"
    radius: 8

    property color textColor: "#324254"
//    property color textColorHighlight: "#324254"
    property color textColorHighlight: "#931313"
     property color textColorSelected: "#97a1ad"
    property color rowBgColor:"#ffffff"
    property color rowBgColorHighlight: "#d4e6ed"
    property color rowBgColorSelected: "#324254"

    TableView {
        id: tableView
        anchors.fill: parent
        anchors.rightMargin: 2
        anchors.leftMargin: 2
        anchors.bottomMargin: 2
        anchors.topMargin: 2
        highlightOnFocus: true
        frameVisible: false
        //backgroundVisible : false
        clip: true
        headerVisible: true

        headerDelegate: Rectangle {
            id: headerRowBox
            implicitHeight: 51
            color:"#f2f6f9"
            Text {
                id: headerRowText
                color: textColor
                text: styleData.value
                font.styleName: "Bold"
                font.family: "PT Sans Caption"
                font.pointSize: 10
                verticalAlignment: Text.AlignVCenter
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.rightMargin: 0
                anchors.leftMargin: 19
                anchors.bottomMargin: 0
                anchors.topMargin: 0
            }
        }

        Keys.onSpacePressed: {
            console.log("SpaceBar pressed at" + tableView.currentRow)
            tableBackend.tableRowSelectedNotify(tableView.currentRow)
              console.log(model.get(tableView.currentRow).data)
            //itemRowBox.selected2?false:true
                console.log(model.get(tableView.currentRow)["bank_date"])
                model.get(tableView.currentRow).selected2 = true
                event.accepted = true

            }
//        onModelChanged: {
//            tableView.__style.height= 101
//        }

        onClicked: {
            //            send all the data to cpp inorder to append to char array.
            var rows = [];
            for (var i = 0; i < tableModel.count; ++i) {
                var obj = JSON.stringify(tableModel.get(i));
                rows.push(obj)
            }
            //console.log('We have ' + rows.length + ' rows')
            //console.log(rows)
        }

        itemDelegate: Item {
            id: itemBox
            height: 101
            property bool selected: false
            function change_color(d, status) {
                selected = styleData.row===d?status:selected
            }
            property color dynamicTextColor: {
               // selected = model.get(tableView.mapRowToSource(styleData.row))
                //console.log(selected)
                if (selected) { console.log('selected_text true for item');return textColorSelected }
                console.log("'selected_text false for item': ")
                //styleData.textColor = styleData.selected?textColorHighlight:textColor
                //console.log(styleData.textColor)
                return styleData.selected?textColorHighlight:textColor

            }
            Text {
                color: dynamicTextColor
                elide: styleData.elideMode
                anchors.fill: parent
                text: styleData.value
                //height: 51
                height: implicitHeight            }
        }
        rowDelegate: Rectangle {
            id: itemRowBox
            implicitHeight: 101
            height: 101
            color: dynamicRowColor
            anchors.fill: parent
            focus: true

            Component.onCompleted: {
                    print(childrenRect)
                itemRowBox.height = 101
                    print(childrenRect)

            }
            property bool selected: false

            function change_color(d, status) {
                selected = styleData.row===d?status:selected
            }
            property color dynamicRowColor: {
                if (selected) { return rowBgColorSelected }
                styleData.selected?rowBgColorHighlight:rowBgColor
            }
            property color dynamicTextColor: {
                if (selected) { console.log('selected_text true for row');return textColorSelected }
                console.log("'selected_text false for row': ")
                return styleData.selected?textColorHighlight:textColor

            }
//            MouseArea {
//                        id: cellMouseArea
//                        anchors.fill: parent
//                        onClicked: {
//                        }
//            }
            Connections {
                                target: tableBackend
                                function onTableRowSelected(currentRow, status){
                                    console.log('Calling functions: ',currentRow, status)
                                    itemRowBox.change_color(currentRow, status)
                                    itemRowBox.children.color = "#eeeeee"
                                    console.log('height',tableView.__currentRowItem.height)
                                    tableView.__currentRowItem.height = 90

                                }
                            }

            Text {
                id: itemRowText
//                text: styleData.value
                // anchors.left: parent.left
                // anchors.right: parent.right
                // anchors.top: parent.top
                // anchors.bottom: parent.bottom
                font.styleName: "Regular"
                font.family: "PT Sans Caption"
                font.pointSize: 10
                verticalAlignment: Text.AlignVCenter
                anchors.rightMargin: 0
                anchors.leftMargin: 21
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                //color: "#931313"
                color: dynamicTextColor

            }


        }
        TableViewColumn {
            role: "row"
            title: "Row"
            width: 100
        }
        TableViewColumn {
            role: "bank_date"
            title: "Bank Date"
            width: 200
        }
        TableViewColumn {
            role: "bank_narration"
            title: "Bank Narration"
            width: 200
        }
        TableViewColumn {
            role: "chq_no"
            title: "Cheque Number"
            width: 200
        }
        TableViewColumn {
            role: "party_name"
            title: "Party Name"
            width: 200
        }
        TableViewColumn {
            role: "infi_date"
            title: "Infi Date"
            width: 200
        }
        TableViewColumn {
            role: "credit"
            title: "Credit"
            width: 200
        }
        TableViewColumn {
            role: "debit"
            title: "Debit"
            width: 200
        }
        TableViewColumn {
            role: "closing_balance"
            title: "Closing Balance"
            width: 200
        }

        model:
            ListModel {
            id: tableModel
            ListElement {
                row: "A Masterpiece"
                bank_date: "Gabriel"
            }
            ListElement {
                row: "Brilliance"
                bank_date: "Jens"
            }
            ListElement {
                row: "Outstanding"
                bank_date: "Frederik"
            }
        }

    }
}

/*##^##
Designer {
    D{i:0;formeditorZoom:1.1;height:1000;width:1000}
}
##^##*/
