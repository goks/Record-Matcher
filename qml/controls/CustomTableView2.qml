import QtQuick 2.8
import QtQuick.Controls 1.4
import QtQuick.Controls 2.1

Rectangle{
    property var columns: [
//        "name", "country", "subcountry", "latitude", "longitude"
    ]
    property var tableData: [
        // { name: "Melbourne", country: "Australia", subcountry: "Victoria", latitude: -37.9716929, longitude: 144.7729583 },
        // { name: "London", country: "United Kingdom", subcountry: "England", latitude: 51.5287718, longitude: -0.2416804 },
        // { name: "Paris", country: "France", subcountry: "Île-de-France", latitude: 48.8589507, longitude: 2.2770205 },
        // { name: "New York City", country: "United States", subcountry: "New York", latitude: 40.6976637, longitude: -74.1197639 },
        // { name: "Tokyo", country: "Japan", subcountry: "Tokyo", latitude: 35.6735408 , longitude: 139.5703047 }
    ];
    property var selectedRows: []
    id: tableBox
    width: parent.width
    height: vscale(607)
    color: "#f2f6f9"
    border.color: "#f2f6f9"
    radius: 8

    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1
    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return Math.round((hscale(size) + vscale(size)) / 2)
    }

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
        clip: true
        headerVisible: true

        model: tableData
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOn
        flickableItem.flickableDirection: Flickable.HorizontalAndVerticalFlick
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
                font.pointSize: tscale(10)
                verticalAlignment: Text.AlignVCenter
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.rightMargin: 0
                anchors.leftMargin: hscale(19)
                anchors.bottomMargin: 0
                anchors.topMargin: 0
            }
        }
        Keys.onSpacePressed: {
            console.log("SpaceBar pressed at " + tableView.currentRow)
            tableBackend.tableRowSelectedNotify(tableView.currentRow, tableBox.selectedRows)
            event.accepted = true

        }
        Connections {
            target: tableBackend
            function onTableRowSelected(selectedRowList){
                console.log('Setting row in qml ', selectedRowList)
                tableBox.selectedRows = selectedRowList
            }
        }

        rowDelegate: Rectangle {
            //color: styleData.selected ? "#0077CC" : styleData.row & 1 ? "white" : "#f5f5f5"
            height: vscale(51)
            id: itemRowBox
            color: dynamicRowColor
            focus: true
            property var selectedRows : tableBox.selectedRows

            property bool selected : false

            onSelectedRowsChanged: function() {
                selected = selectedRows.includes(styleData.row)?true:false
            }
            property color dynamicRowColor: selected?rowBgColorSelected:styleData.selected?rowBgColorHighlight:rowBgColor

        }
        itemDelegate:
            Text {
            id: itemText
            property var selectedRows : tableBox.selectedRows

            property bool selected : false

            onSelectedRowsChanged: function() {
                selected = selectedRows.includes(styleData.row)?true:false
            }
            property color dynamicTextColor: selected?textColorSelected:styleData.selected?textColorHighlight:textColor

            color: dynamicTextColor
            elide: styleData.elideMode
            anchors.fill: parent
            text: styleData.value
            font.styleName: "Regular"
            font.family: "PT Sans Caption"
            font.pointSize: tscale(10)
            verticalAlignment: Text.AlignVCenter
            anchors.rightMargin: 0
            anchors.leftMargin: hscale(21)
            anchors.bottomMargin: 0
            anchors.topMargin: 0
        }
    }

    Component {
        id: columnComponent
        TableViewColumn {
//            width: 100
        }
    }

    function toUpperCase(c) { return c.toUpperCase(); }
    function capitalize(str) { return str.replace(/^./, toUpperCase); }
    
    function addColumn(name) {
        tableView.addColumn(columnComponent.createObject(tableView, { role: name, title: capitalize(name) } ) );
    }

    Component.onCompleted: columns.forEach(addColumn)

}


/*##^##
Designer {
    D{i:0;formeditorZoom:1.75}
}
##^##*/
