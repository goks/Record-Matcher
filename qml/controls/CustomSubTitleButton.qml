import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

Button {
    id: customBtn
    property color textColor: "#003366"
    property color textColorHighLight: "#ffffff"
    property color bgColor: "#F5F8FA"
    property color bgColorHighlight: "#003366"
    property bool selected: false
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
    property int fontSize: tscale(10)
    enabled: true

    // implicitWidth: hscale(69)
    implicitHeight: vscale(38)
    width: implicitWidth
    leftPadding: hscale(18)
    rightPadding: hscale(18)
    contentItem: Text {
            id: buttonLabel
            color: selected?textColorHighLight:textColor
            text: customBtn.text
//            text: qsTr("By Date12342168")
            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            lineHeightMode: Text.FixedHeight
            fontSizeMode: Text.HorizontalFit
            font.family: "PT Sans Caption"
            font.pointSize: customBtn.fontSize
        }
    background: Rectangle {
        id: container
        radius: 8
        color: selected?bgColorHighlight:bgColor
        border.color: textColor
        antialiasing: true
    }
    onClicked: {
            selected = selected?false:true
    }
}



/*##^##
Designer {
    D{i:0;formeditorZoom:3}
}
##^##*/
