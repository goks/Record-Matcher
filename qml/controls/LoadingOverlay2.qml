import QtQuick 2.0
import QtQuick.Controls 2.15
import QtQuick.Dialogs 1.3
import  "../controls"

Rectangle{
    id: loadingOverlay
    color: "#ddffffff"
    anchors.fill: parent
    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1
    property real progressBarValue: 0.0
    property string text1: "123"
    property string text2: "456"
    property string daybookFileURL: ""
    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return (Math.round((hscale(size) + vscale(size)) / 2)+2)
    }
    MouseArea{
        z:3
        anchors.fill: parent
        onClicked: {

        }
    }
    Rectangle {
        z:4
        id: rectangle
        anchors.fill: parent
        anchors.margins: 100
        color: "#00000000"

        Text {
            // text: "Loading ChequeReports"
            id: h1
            text: "Select Daybook file from start of financial year. ( from Daybook-export )."
            font.pixelSize: tscale(30)
            font.family: appFont4.name
        }
        Rectangle {
            id: fileImportContainerBox
            //    height: 38
            // height: 100
            color: "#f5f8fa"
            implicitHeight: vscale(38)
            radius: 8
            border.color: "#dee6ec"
            anchors.top: h1.bottom
            anchors.topMargin: vscale(20)
            width: hscale(1000)

            TextInput {
                id: searchInput
                color: "#324254"
                //        text: qsTr("Search")
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                font.family: appFont4.name
                font.pixelSize: tscale(16)
                verticalAlignment: Text.AlignVCenter
                clip: true
                anchors.topMargin: 0
                anchors.bottomMargin: 0
                anchors.leftMargin: hscale(15)
                anchors.rightMargin: hscale(15)
                text: daybookFileURL
                onTextChanged: daybookFileURL = searchInput.text

                Text {
                    id: placeholder
                    text: "Infi Daybook location"
                    anchors.fill: parent
                    color: "#c4c4c4"
                    visible: !searchInput.text
                    verticalAlignment: Text.AlignVCenter
                    clip: true
                    font.family: appFont4.name
                    font.pixelSize: tscale(16)
                }
                CustomSubTitleButton {
                    id:browseBut
                    // width: 174
                    width: hscale(74)
                    height: vscale(25)
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: hscale(18)
                    visible: true
                    font.pixelSize: tscale(10)
                    text: "Browse"
                    onClicked: fileDialog.open()
                }
                FileDialog {
                    id: fileDialog
                    nameFilters: ["Excel Files (*.xls *.xlsx)"]
                    title: "Choose the Daybook file to import "
                    folder: shortcuts.desktop
                    onAccepted: {
                        console.log("You chose: " + fileDialog.fileUrl)
                        daybookFileURL = fileDialog.fileUrl
                        browseBut.selected = false
                    }
                    onRejected: {
                        console.log("Canceled")
                        browseBut.selected = false
                    }
                }
            }
        }
        Text {
            // text: "Loading ChequeReports"
            id: h2
            text: "Select date range"
            anchors.top: fileImportContainerBox.bottom
            font.pixelSize: tscale(30)
            anchors.topMargin: vscale(25)
            font.family: appFont4.name
        }
        Text {
            // text: "Loading ChequeReports"
            text: loadingOverlay.text1
            anchors.verticalCenter: parent.verticalCenter
            font.pixelSize: 40
            anchors.verticalCenterOffset: -100
            font.family: appFont4.name
        }
        Text {
            // text: "processing Jun 2020 gokul"
            text: loadingOverlay.text2
            anchors.verticalCenter: parent.verticalCenter
            font.pixelSize: 20
            anchors.verticalCenterOffset: -50
            font.family: appFont4.name
        }

        ProgressBar{
            anchors.fill: parent
            //            indeterminate: true
            to:1.0
            value: loadingOverlay.progressBarValue
        }
    }
}







/*##^##
Designer {
    D{i:0;autoSize:true;formeditorZoom:0.66;height:480;width:640}
}
##^##*/
