import QtQuick 2.12
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0

Calendar {
    // property var startDate: undefined
    // property var stopDate: undefined
    // width: hscale(277)
    // height: vscale(255)
    width: hscale(300)
    height: vscale(300)
    // weekNumbersVisible: true
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

    style: CalendarStyle {
               readonly property var eventColours: ["lightblue", "darkorange", "purple"]
               gridColor: "transparent"
               gridVisible: false

               background: Rectangle{
                   id:backgroundRect
                   radius: 8
                   anchors.fill: parent
                   color: "white"
                   anchors.margins: -1

               }
            //    weekNumberDelegate:     Rectangle{
            //            id: leftGrid
            //            anchors.fill: parent
            //            color: "#ddd"
            //             implicitWidth: 10
            //             // not working
            //        }
               dayOfWeekDelegate: Rectangle {
                    color: gridVisible ?"#fcfcfc" : "transparent"
                    implicitHeight: vscale(30)
                    Label {
                        text: control.locale.dayName(styleData.dayOfWeek, control.dayOfWeekFormat)
                        font.capitalization: Font.AllUppercase
                        anchors.centerIn: parent
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(14)
                        color:"#6a84a0"
                    }
                     Rectangle {
                        anchors.bottom: parent.bottom
                        height: 1
                        width: parent.width
                        color: "#ddd"
                    }
                }
                navigationBar: Rectangle {
                    height: vscale(35)
                    color: "#f9f9f9"

                    Rectangle {
                        color: Qt.rgba(1,1,1,0.6)
                        height: 1
                        width: parent.width
                    }

                    Rectangle {
                        anchors.bottom: parent.bottom
                        height: 1
                        width: parent.width
                        color: "#ddd"
                    }

                    HoverButton {
                        id: previousMonth
                        width: parent.height
                        height: width
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        source: "../../images/svg_images/left-arrow.svg"
                        onClicked: control.showPreviousMonth()
                    }
                    Label {
                        id: dateText
                        text: styleData.title
                        elide: Text.ElideRight
                        horizontalAlignment: Text.AlignHCenter
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: previousMonth.right
                        anchors.leftMargin: 2
                        anchors.right: nextMonth.left
                        anchors.rightMargin: 2
                        font.family: appFont3.name
                        font.pixelSize: tscale(18)
                        font.weight: Font.Bold
                        color:"#2E3F51"
                    }
                    HoverButton {
                        id: nextMonth
                        width: parent.height
                        height: width
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: parent.right
                        source: "../../images/svg_images/right-arrow.svg"
                        onClicked: control.showNextMonth()
                    }
                    } 
               dayDelegate: Rectangle {
                   id: item1
                   z:0
                   readonly property color sameMonthDateTextColor: "#003366"
                   readonly property color selectedDateColor: "#003366"
                   readonly property color selectedDateTextColor: "white"
                   readonly property color differentMonthDateTextColor: "#bbb"
                   readonly property color invalidDatecolor: "#dddddd"

                   Rectangle {
                       id: selectionRect
                       anchors.fill: parent
                       border.color: "transparent"
                       color: styleData.date !== undefined && styleData.selected ? selectedDateColor : "transparent"
                       anchors.margins: styleData.selected ? -1 : 0
                   }
                   Rectangle{
                       id: rightGrid
                       anchors.right: parent.right
                       anchors.rightMargin: 0
                       width:1
                       height: parent.height
                       color: "#ddd"
                   }
                //    Rectangle{
                //        id: leftGrid
                //        anchors.left: parent.left
                //        anchors.leftMargin: 0
                //        width:1
                //        height: parent.height
                //        color: "#ddd"
                //    }
                   Rectangle{
                       id: bottomGrid
                       anchors.bottom: parent.bottom
                       anchors.bottomMargin: 0
                       height:1
                       width: parent.width
                    //    color: "#c2c2c2"
                       color: "#ddd"
                   }

                   Label {
                       id: dayDelegateText
                       text: styleData.date.getDate()
                       anchors.verticalCenter: parent.verticalCenter
                       font.family: "PT Sans Caption"
                       font.pixelSize: tscale(14)
                       horizontalAlignment: Text.AlignHCenter
                       verticalAlignment: Text.AlignVCenter
                       anchors.horizontalCenter: parent.horizontalCenter
                       color: {
                           var color = invalidDatecolor;
                           if (styleData.valid) {
                               // Date is within the valid range.
                               color = styleData.visibleMonth ? sameMonthDateTextColor : differentMonthDateTextColor;
                               if (styleData.selected) {
                                   color = selectedDateTextColor;
                               }
                           }
                           color;
                       }
                   }
               }
           }


















//        CalendarStyle {
//        gridVisible: false
////        background: Rectangle {
////            radius: 5
////        }

//        dayDelegate: Rectangle {
//            width: 53
//            height: 39
//            // gradient: Gradient {
//            //     GradientStop {
//            //         position: 0.00
//            //         color: styleData.selected ? "#111" : (styleData.visibleMonth && styleData.valid ? "#444" : "#666");
//            //     }
//            //     GradientStop {
//            //         position: 1.00
//            //         color: styleData.selected ? "#444" : (styleData.visibleMonth && styleData.valid ? "#111" : "#666");
//            //     }
//            //     GradientStop {
//            //         position: 1.00
//            //         color: styleData.selected ? "#777" : (styleData.visibleMonth && styleData.valid ? "#111" : "#666");
//            //     }
//            // }

//            Label {
//                text: styleData.date.getDate()
//                anchors.centerIn: parent
//                color: styleData.valid ? "white" : "blue"
//                font.family: "PT Sans Caption"
//                font.pointSize: 6
//            }

//            Rectangle {
//                width: parent.width
//                height: 1
//                color: "#e4e4e4"
//                anchors.bottom: parent.bottom
//            }

//            Rectangle {
//                width: 1
//                height: parent.height
//                color: "#e4e4e4"
//                anchors.right: parent.right
//            }
//        }
//    }
}
/*##^##
Designer {
    D{i:0;formeditorZoom:2}
}
##^##*/
