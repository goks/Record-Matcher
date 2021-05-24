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
    enabled: true

    implicitWidth: 69
    implicitHeight: 38
    contentItem: Text {
            id: buttonLabel
            color: selected?textColorHighLight:textColor
            text: customBtn.text
//            text: qsTr("By Date12342168")
            anchors.fill: parent
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.family: "PT Sans Caption"
            font.pointSize: 12
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
