import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

Button {
    id: menuBtn
    property url btnIconSource: "../../images/svg_images/download_btn.svg"
    property color bgcolorDefault: "#F5F8FA"
    property color bgcolorMouseOver: "#e5e5e5"
    property color bgcolorPressed: "#003366"

    property color bgColor: "#F5F8FA"
    property color bgColorHighlight: "#003366"

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

    QtObject {
        id: internal

        property var dynamicColor: if(menuBtn.down){
                                       menuBtn.down ? bgcolorPressed : bgcolorDefault
                                   } else {
                                       menuBtn.hovered ? bgcolorMouseOver : bgcolorDefault
                                   }
    }

    implicitWidth: hscale(49)
    implicitHeight: vscale(43)
    background: Rectangle {
        color: internal.dynamicColor
        radius: 8
//        color: selected?bgColorHighlight:bgColor
        border.color: textColor
        antialiasing: true


        Image {
            id: menu
            visible: true
            anchors.fill: parent
            source: btnIconSource
            anchors.rightMargin: hscale(2)
            anchors.leftMargin: hscale(2)
            anchors.bottomMargin: vscale(2)
            anchors.topMargin: vscale(2)
            fillMode: Image.PreserveAspectCrop

        }

    }
}



/*##^##
Designer {
    D{i:0;formeditorZoom:8}
}
##^##*/
