import QtQuick 2.15
import QtGraphicalEffects 1.15


Rectangle {
    id: rectangle
    width: hscale(800)
    height: singleText?vscale(200):vscale(425)
    // property color textColor: "#003366"
    property color textColor: "#324254"
    radius: 8
    border.color: "#c4c4c4"
    property bool singleText: false
    property string text1 : "No cheque report found in program."
    property string text2 : "Instructions to upload:"
    property string text3 : "1. Choose appropriate financial year in INfi.
2. Download cheque report of the entire financial year by pressing Ctrl+K.
3. Browse and select the path of the report and upload by clicking on the button."
    property string text4 : "Choose company, bank, year, month."

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

    Text {
        visible: singleText?false:true
        id: text1
        height: vscale(67)
        text: rectangle.text1
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        //        font.pixelSize: 34
        verticalAlignment: Text.AlignVCenter
        anchors.topMargin: vscale(76)
        anchors.rightMargin: hscale(50)
        anchors.leftMargin: hscale(50)
        color: textColor
        font.family: "PT Sans Caption"
        font.pointSize: tscale(22)
    }

    Text {
        visible: singleText?false:true
        id: text2
        y: vscale(181)
        height: vscale(51)
        text: rectangle.text2
        anchors.left: parent.left
        anchors.right: parent.right
        verticalAlignment: Text.AlignVCenter
        font.underline: true
        anchors.rightMargin: hscale(50)
        anchors.leftMargin: hscale(50)
        color: textColor
        font.family: "PT Sans Caption"
        //        font.pointSize: 20
        font.pointSize: tscale(18)
    }

    Text {
        visible: singleText?false:true
        id: text3
        height: vscale(96)
        text: rectangle.text3
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: text2.bottom
        wrapMode: Text.WordWrap
        anchors.topMargin: vscale(-2)
        anchors.rightMargin: hscale(50)
        anchors.leftMargin: hscale(50)
        color: textColor
        font.family: "PT Sans Caption"
        font.pointSize: tscale(12)

    }
    Text {
        visible: singleText?true:false
        id: text4
        height: vscale(65)
        text: rectangle.text4
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        //        font.pixelSize: 34
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        color: textColor
        font.family: "PT Sans Caption"
        font.pointSize: tscale(22)
    }
}


