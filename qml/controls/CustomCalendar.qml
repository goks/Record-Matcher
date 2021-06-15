import QtQuick 2.12
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.1

Calendar {
    // property var startDate: undefined
    // property var stopDate: undefined
    width: 277
    height: 255

    style: CalendarStyle {
               readonly property var eventColours: ["lightblue", "darkorange", "purple"]
               gridColor: "transparent"
               gridVisible: false

               background: Rectangle{
                   id:backgroundRect
                   radius: 5
                   anchors.fill: parent
                   color: "white"
                   anchors.margins: -1

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
                       color: "#c2c2c2"
                   }
                   Rectangle{
                       id: bottomGrid
                       anchors.bottom: parent.bottom
                       anchors.bottomMargin: 0
                       height:1
                       width: parent.width
                       color: "#c2c2c2"
                   }

                   Label {
                       id: dayDelegateText
                       text: styleData.date.getDate()
                       anchors.verticalCenter: parent.verticalCenter
                       font.family: "PT Sans Caption"
                       font.pixelSize: 14
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
