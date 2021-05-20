import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

Button {
    id: menuBtn
    property url btnIconSource: "../../images/svg_images/menu.svg"
    property color bgcolorDefault: "#ffffff"
    property color bgcolorMouseOver: "#e5e5e5"
    property color bgcolorPressed: "#c4c4c4"

    QtObject {
        id: internal

        property var dynamicColor: if(menuBtn.down){
                                        menuBtn.down ? bgcolorPressed : bgcolorDefault
                                   } else {
                                       menuBtn.hovered ? bgcolorMouseOver : bgcolorDefault
                                   }
    }

    implicitWidth: 49
    implicitHeight: 43
    background: Rectangle {
        color: internal.dynamicColor


    Image {
        id: menu
        x: 0
        y: 0
        visible: true
        source: btnIconSource
        fillMode: Image.PreserveAspectFit
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        sourceSize.width: parent.width
        sourceSize.height: parent.height
    }

}}



/*##^##
Designer {
    D{i:0;formeditorZoom:4}
}
##^##*/
