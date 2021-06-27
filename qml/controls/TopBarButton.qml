import QtQuick 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15

import  "../controls"

Button {
    id: topBarButton
    property color bgcolorDefault: "#ffffff"
//    property color bgcolorMouseOver: "#e5e5e5"
    property color bgcolorMouseOver: "#ffffff"
    property color bgcolorPressed: "#c4c4c4"
    property color textcolorDefault: "#33475B"
    property color textcolorMouseOver: "#043769"
    property bool selected: false
    property real scaleFactor: 1
    QtObject {
        id: internal

        property var dynamicColor: if(topBarButton.down){
                                        topBarButton.down ? bgcolorPressed : bgcolorDefault
                                   } else {
                                       topBarButton.hovered ? bgcolorMouseOver : bgcolorDefault
                                   }
        property var dynamicVisibility: if(topBarButton.down){
                                        topBarButton.down ? true : false
                                   } else {
                                       topBarButton.hovered ? true : false
                                   }
        property var dynamicTextColor: if(topBarButton.down){
                                        topBarButton.down ? textcolorMouseOver : textcolorDefault
                                   } else {
                                       topBarButton.hovered ? textcolorMouseOver : textcolorDefault
                                   }                                                 
    }


//    implicitWidth: 55
//    implicitHeight: parent.width

    text: qsTr("SABUSA")
    contentItem:
        Text {
//        width: topBarButton.width
        id: buttonLabel
        color: internal.dynamicTextColor
        text: topBarButton.text
        anchors.fill: parent
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        anchors.topMargin: 10
//        fontSizeMode: Text.Fit
        font.family: "PT Sans Caption"
//        font.pointSize: 18
        font.pixelSize: scaleFactor*22
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
    background: Rectangle {
        color: internal.dynamicColor
        anchors.fill: parent
        anchors.topMargin: 4
        implicitWidth:  buttonLabel.paintedWidth + scaleFactor*50
        CustomBorder {
            visible: internal.dynamicVisibility
            commonBorder: false
            tBorderwidth: 4
//            commonBorderWidth: 20
            borderColor: "#33475b"
        }
        CustomBorder {
            visible: selected?true:false
            commonBorder: false
            tBorderwidth: 4
//            commonBorderWidth: 20
            borderColor: "#33475b"
        }
    }
}



/*##^##
Designer {
    D{i:0;formeditorZoom:1.5}
}
##^##*/
