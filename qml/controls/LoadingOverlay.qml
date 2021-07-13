import QtQuick 2.0
import QtQuick.Controls 2.15

Rectangle{
    id: loadingOverlay
    color: "#ddffffff"
    anchors.fill: parent
    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1
    property real progressBarValue: 0.0
    property string text1: ""
    property string text2: ""
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
        id: rectangle
        anchors.fill: parent
        anchors.margins: 100
        color: "#00000000"
        Text {
            text: "Loading ChequeReports"
            anchors.verticalCenter: parent.verticalCenter
            font.pixelSize: tscale(40)
            anchors.verticalCenterOffset: -100
            font.family: appFont4.name
        }
        Text {
            text: "processing Jun 2020 gokul"
            anchors.verticalCenter: parent.verticalCenter
            font.pixelSize: tscale(20)
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
