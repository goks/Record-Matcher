import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

Button {
    id: menuBtn
    signal convertSchemaClicked
    property url btnIconSource: "../../images/svg_images/menu.svg"
    property color bgcolorDefault: "#ffffff"
    property color bgcolorMouseOver: "#e5e5e5"
    property color bgcolorPressed: "#c4c4c4"
    property color textcolorDefault: "#6a84a0"
    onClicked: menu.open()
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
            id: btnImg
            visible: true
            anchors.fill: parent
            source: btnIconSource
            fillMode: Image.PreserveAspectCrop
            sourceSize.width: parent.width
            sourceSize.height: parent.height
            layer.enabled: true
            layer.effect: DropShadow {
                id: dropShadow
                color: "#40000000"
                verticalOffset: 4
                radius: 4
                spread: 0
                horizontalOffset: 0
            }
        }

    }
    Menu {
        id: menu
        y: parent.height+4
        background: Item {
            implicitWidth: 200
            implicitHeight: 40

            Rectangle {
                anchors.fill: parent
                anchors.margins: 1
                color: "#F5F8FA"
                border.color: "#003366"
                radius: 8
            }
        }




        MenuItem {
            id: menuControl
            background:  Item {
                implicitWidth: 200
                implicitHeight: 40

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1

                    radius: 8
                    color: menuControl.hovered ? "#003366" : "transparent"
                }
            }
            contentItem: Text {
                id: name
                text: menuControl.text
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                anchors.topMargin: 4
                anchors.bottomMargin: 4
                anchors.rightMargin: 4
                anchors.leftMargin: 4
                padding: 10
                color: menuControl.hovered ? "#ffffff" : "#003366"
            }

            text: "Convert Old Schema to New"
            onTriggered: menuBtn.convertSchemaClicked()
        }

    }
}




