import QtQuick 2.0
import QtQuick.Controls 2.15
import QtCharts 2.2
import QtQuick.Dialogs 1.3

Popup {
    id: popup
    parent: Overlay.overlay
    x: Math.round((parent.width - popupBckgroundBox.width) / 2)
    y: Math.round((parent.height - popupBckgroundBox.height) / 2)
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape
    //                     | Popup.CloseOnReleaseOutside

    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1
    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return Math.round((hscale(size) + vscale(size)) / 2)+2
    }
    background: Rectangle {
        id: popupBckgroundBox
        width: 560
        height: 310
        radius: 5
        color: "white"

        Text {
            id: headerText
            height: 52
            color: "#003366"
            //                color: "#000000"
            text: "Export"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            font.pixelSize: 32
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            anchors.topMargin: 28
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            font.family: "PT Sans Caption"

        }

        Rectangle {
            id: divider1
            height: 1
            color: "#6a84a0"
            border.color: "#6a84a0"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: headerText.bottom
            anchors.topMargin: 22
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            radius: 8
        }
        Text {
            id: subHeaderText
            height: 21
            color: "#003366"
            //                color: "#000000"
            text: "Choose the location to export"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: divider1.bottom
            font.pixelSize: 16
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            anchors.leftMargin: 27
            anchors.topMargin: 27
            anchors.rightMargin: 0
            font.family: "PT Sans Caption"
        }
        Rectangle {
            id: searchBox
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: divider1.bottom
            anchors.topMargin: 66
            anchors.leftMargin: 27
            anchors.rightMargin: 27
            height: 24
            color: "#f5f8fa"
            radius: 8
            border.color: "#dee6ec"

            TextInput {
                id: searchInput
                color: "#324254"
                //        text: qsTr("Search")
                font.family: "PT Sans Caption"
                font.pixelSize: 16
                verticalAlignment: Text.AlignVCenter
                clip: true
                text: ""
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.topMargin: 0
                anchors.bottomMargin: 0
                anchors.leftMargin: 15
                anchors.rightMargin: 15
                // onTextChanged: {}
                Text {
                    anchors.fill: parent
                    id: placeholder
                    text: "File Path"
                    color: "#c4c4c4"
                    visible: !searchInput.text
                    verticalAlignment: Text.AlignVCenter
                    clip: true
                    font.family: "PT Sans Caption"
                    font.pixelSize: 14
                }
            }
        }
        CustomSubTitleButton {
            id:browseBut
            height: 25
            fontSize: 10
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: searchBox.bottom
            anchors.topMargin: 7
            anchors.leftMargin: 467
            anchors.rightMargin: 27
            visible: true
            // visible: true
            text: "Browse"
            onClicked: {
                browseBut.selected = true
                fileDialog.open()
            }
        }
        FileDialog {
            id: fileDialog
            selectFolder: true
            // nameFilters: ["Excel Files (*.xls *.xlsx)"]
            title: "Choose the folder to import "
            folder: shortcuts.documents
            onAccepted: {
                console.log("You chose: " + folder)
                searchInput.text = folder + '/123.xls'
                browseBut.selected = false
            }
            onRejected: {
                console.log("Canceled")
                browseBut.selected = false
            }
        }
        Rectangle {
            id: divider2
            height: 1
            color: "#EAF0F6"
            radius: 8
            border.color: "#EAF0F6"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: browseBut.bottom
            anchors.topMargin: 24
            anchors.rightMargin: 0
            anchors.leftMargin: 0
        }
        CustomSubTitleButton {
            id: cancelBut
            width: 102
            height: 33
            fontSize: 10
            anchors.right: parent.right
            anchors.top: divider2.bottom
            anchors.topMargin: 15
            anchors.rightMargin: 27
            visible: true
            // visible: true
            text: "Cancel"
            onClicked: popup.close()
        }
        CustomSubTitleButton {
            id: exportBut
            width: 102
            height: 33
            fontSize: 10
            anchors.right: cancelBut.left
            anchors.top: divider2.bottom
            anchors.topMargin: 15
            anchors.rightMargin: 27
            visible: true
            selected: true
            // visible: true
            text: "Export"
            onClicked : {
                exportBut.selected = false
                busyIndicator.visible = true
                if (searchInput.text === ""){
                    toast.show("No file selected to import", "error")
                    exportBut.selected = true
                    busyIndicator.visible = false
                    return
                }
                backend.exportFile(searchInput.text )
            }
        }
        BusyIndicator {
            id: busyIndicator
            anchors.right: exportBut.left
            anchors.top: divider2.bottom
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 15
            anchors.rightMargin: 15
            anchors.topMargin: 15
            visible: false
        }
    }
}





/*##^##
Designer {
    D{i:0;autoSize:true;formeditorZoom:1.1;height:480;width:640}
}
##^##*/
