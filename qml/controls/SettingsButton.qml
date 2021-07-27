import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

Button {
    id: menuBtn
    signal convertSchemaClicked
    signal downloadFromDbClicked
    signal uploadtoDbClicked
    signal createTallyXMLFromDaybookClicked
    property url btnIconSource: "../../images/svg_images/menu.svg"
    property color bgcolorDefault: "#ffffff"
    property color bgcolorMouseOver: "#e5e5e5"
    property color bgcolorPressed: "#c4c4c4"
    property color textcolorDefault: "#6a84a0"
    onClicked: menu.open()
    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1
    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return (Math.round((hscale(size) + vscale(size)) / 2)+2)
    }
    QtObject {
        id: internal

        property var dynamicColor: if(menuBtn.down){
                                       menuBtn.down ? bgcolorPressed : bgcolorDefault
                                   } else {
                                       menuBtn.hovered ? bgcolorMouseOver : bgcolorDefault
                                   }
    }
    implicitWidth: hscale(43)
    implicitHeight: vscale(43)
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
//        x: parent.x-100
        background: Item {
            implicitWidth: menuControl4.implicitWidth
            implicitHeight: vscale(40)
            Rectangle {
                anchors.fill: parent
                anchors.margins: 1
                color: "#F5F8FA"
                border.color: "#003366"
                // radius: 8
            }
        }
        MenuItem {
            id: menuControl2
            background:  Item {
                implicitWidth: hscale(280)
                implicitHeight: vscale(40)
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    // radius: 8
                    color: menuControl2.hovered ? "#003366" : "transparent"
                }
            }
            contentItem: Text {
                text: menuControl2.text
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                // horizontalAlignment: Text.AlignHCenter
                anchors.topMargin: vscale(4)
                anchors.bottomMargin: vscale(4)
                anchors.rightMargin: hscale(4)
                anchors.leftMargin: hscale(4)
                padding: 10
                minimumPixelSize: 14
                font.pixelSize: tscale(18)
                font.family: appFont4.name
                color: menuControl2.hovered ? "#ffffff" : "#003366"
            }
            text: "Download from web database"
            onTriggered: menuBtn.downloadFromDbClicked()
        }
        MenuItem {
            id: menuControl3
            background:  Item {
                implicitWidth: hscale(280)
                implicitHeight: vscale(40)
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    // radius: 8
                    color: menuControl3.hovered ? "#003366" : "transparent"
                }
            }
            contentItem: Text {
                text: menuControl3.text
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                // horizontalAlignment: Text.AlignHCenter
                anchors.topMargin: vscale(4)
                anchors.bottomMargin: vscale(4)
                anchors.rightMargin: hscale(4)
                anchors.leftMargin: hscale(4)
                padding: 10
                minimumPixelSize: 14
                font.pixelSize: tscale(18)
                font.family: appFont4.name
                color: menuControl3.hovered ? "#ffffff" : "#003366"
            }
            text: "Upload to web database"
            onTriggered: menuBtn.uploadtoDbClicked()
        }
        MenuItem {
            id: menuControl4
            background:  Item {
                implicitWidth: hscale(280)
                implicitHeight: vscale(40)

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    // radius: 8
                    color: menuControl4.hovered ? "#003366" : "transparent"
                }
            }
            contentItem: Text {
                text: menuControl4.text
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                // horizontalAlignment: Text.AlignHCenter
                anchors.topMargin: vscale(4)
                anchors.bottomMargin: vscale(4)
                anchors.rightMargin: hscale(4)
                anchors.leftMargin: hscale(4)
                padding: 10
                minimumPixelSize: 14
                font.pixelSize: tscale(18)
                font.family: appFont4.name
                color: menuControl4.hovered ? "#ffffff" : "#003366"
            }
            text: "Create Tally XML from Infi Daybook"
            onTriggered: menuBtn.createTallyXMLFromDaybookClicked()
        }
        MenuItem {
            id: menuControl
            background:  Item {
                implicitWidth: hscale(280)
                implicitHeight: vscale(40)

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 1
                    // radius: 8
                    color: menuControl.hovered ? "#003366" : "transparent"
                }
            }
            contentItem: Text {
                text: menuControl.text
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                // horizontalAlignment: Text.AlignHCenter
                anchors.topMargin: vscale(4)
                anchors.bottomMargin: vscale(4)
                anchors.rightMargin: hscale(4)
                anchors.leftMargin: hscale(4)
                padding: 10
                minimumPixelSize: 14
                font.pixelSize: tscale(18)
                font.family: appFont4.name
                color: menuControl.hovered ? "#ffffff" : "#003366"
            }
            text: "Convert old schema to new"
            onTriggered: menuBtn.convertSchemaClicked()
            // signal downloadFromDbClicked()
        }


    }
}





/*##^##
Designer {
    D{i:0;formeditorZoom:1.66}
}
##^##*/
