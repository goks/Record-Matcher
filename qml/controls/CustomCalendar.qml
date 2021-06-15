import QtQuick 2.12
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.1

Calendar {
    property var startDate: undefined
    property var stopDate: undefined

    style: CalendarStyle {
        gridVisible: false
        dayDelegate: Rectangle {
            width: 53
            height: 39
            gradient: Gradient {
                GradientStop {
                    position: 0.00
                    color: styleData.selected ? "#111" : (styleData.visibleMonth && styleData.valid ? "#444" : "#666");
                }
                GradientStop {
                    position: 1.00
                    color: styleData.selected ? "#444" : (styleData.visibleMonth && styleData.valid ? "#111" : "#666");
                }
                GradientStop {
                    position: 1.00
                    color: styleData.selected ? "#777" : (styleData.visibleMonth && styleData.valid ? "#111" : "#666");
                }
            }

            Label {
                text: styleData.date.getDate()
                anchors.centerIn: parent
                color: styleData.valid ? "white" : "grey"
                font.family: "PT Sans Caption"
                font.pointSize: 6
            }

            Rectangle {
                width: parent.width
                height: 1
                color: "#e4e4e4"
                anchors.bottom: parent.bottom
            }

            Rectangle {
                width: 1
                height: parent.height
                color: "#e4e4e4"
                anchors.right: parent.right
            }
        }
    }
}    
/*##^##
Designer {
    D{i:0;formeditorZoom:1.75}
}
##^##*/
