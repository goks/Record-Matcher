import QtQuick 6.5
import QtQuick.Controls 6.5
// Qt6: QtGraphicalEffects removed - effects disabled

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
        //    width: topBarButton.width
        id: buttonLabel
        color: internal.dynamicTextColor
        text: topBarButton.text
        anchors.fill: parent
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        anchors.topMargin: vscale(10)
        //        fontSizeMode: Text.Fit
        font.family: "PT Sans Caption"
        //        font.pointSize: 18
        font.pixelSize: tscale(22)
        // TODO Qt6: DropShadow disabled (Qt 5 GraphicalEffects deprecated)
    }
    background: Rectangle {
        color: internal.dynamicColor
        anchors.fill: parent
        anchors.topMargin: vscale(4)
        implicitWidth:  buttonLabel.paintedWidth + hscale(50)
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





