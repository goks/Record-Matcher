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


    implicitWidth: 49
    implicitHeight: 43
    text: qsTr("Help")
    contentItem: Text {
        id: buttonLabel
        color: internal.dynamicTextColor
        text: topBarButton.text
        anchors.fill: parent
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        anchors.topMargin: 10
        minimumPointSize: 18
        minimumPixelSize: 18
        fontSizeMode: Text.Fit
        font.family: "PT Sans Caption"
        font.pointSize: 18
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

        // Rectangle {
        //     id: rectangle
        //     visible: internal.dynamicVisibility
        //     color: "#33475b"
        //     anchors.left: parent.left
        //     anchors.right: parent.right
        //     anchors.top: parent.top
        //     anchors.bottom: parent.bottom
        //     anchors.rightMargin: 0
        //     anchors.leftMargin: 0
        //     anchors.bottomMargin: 39
        //     anchors.topMargin: 0
        // }
    }

    // onClicked: {
    //     selected = selected?false:true
    // }
}



/*##^##
Designer {
    D{i:0;formeditorZoom:4}
}
##^##*/
