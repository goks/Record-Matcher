import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

Button {
    id: menuBtn
    property url btnIconSource: "../../images/svg_images/menu.svg"
    property color bgcolorDefault: "#ffffff"
    property color bgcolorMouseOver: "#e5e5e5"
    property color bgcolorPressed: "#c4c4c4"
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


        Image {
            id: menu
            visible: true
            anchors.fill: parent
            source: btnIconSource
            fillMode: Image.PreserveAspectCrop
            sourceSize.width: parent.width
            sourceSize.height: parent.height
        }

    }
}



/*##^##
Designer {
    D{i:0;formeditorZoom:8}
}
##^##*/
