import QtQuick 2.15
import QtQuick.Controls 1.5
import QtQuick.Controls 2.15 as C
Rectangle {
    width: 596
    height: 607
    color: "#f2f6f9"
    border.color: "#f2f6f9"
    radius: 8

    property color textColor: "#324254"
    property color textColorHighlight: "#324254"
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


//        Keys.spacePressed: {
//                        console.log('HEMLAN')

//        }
        Keys.onPressed: {
            console.log("Key pressed at" + tableView.currentRow)
            if(event.Key === Qt.Key_Space){
                console.log("Bar")
                event.accepted = true
            }
            }
        rowDelegate: Rectangle {
            id: itemRowBox
            height: 51
            color: dynamicRowColor
            anchors.fill: parent
            focus: true
            property bool selected: false
            property color dynamicRowColor: {
                if (selected) { return rowBgColorHighlight }
                styleData.selected?rowBgColorHighlight:rowBgColor
            }
            property color dynamicTextColor: {
                if (selected) { return textColorSelected }
                styleData.selected?textColorHighlight:textColor
            }
//            MouseArea {
//                        id: cellMouseArea
//                        anchors.fill: parent
//                        onClicked: {
//                        }
//            }

            Text {
                id: itemRowText
                color: !styleData.selected?textColor:textColorHighlight
//                text: styleData.value
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                font.styleName: "Regular"
                font.family: "PT Sans Caption"
                font.pointSize: 10
                verticalAlignment: Text.AlignVCenter
                anchors.rightMargin: 0
                anchors.leftMargin: 21
                anchors.bottomMargin: 0
                anchors.topMargin: 0
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
            id: libraryModel
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
    D{i:0;height:1000;width:1000}
}
##^##*/
