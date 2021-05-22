import QtQuick 2.15
import  "../controls"

ListView {
    id: listView
    height: 50
    spacing: 6
    layoutDirection: Qt.LeftToRight
    topMargin: 0
    boundsBehavior: Flickable.DragAndOvershootBounds
    highlightFollowsCurrentItem: false
     //highlight: Rectangle { color: "lightsteelblue"; radius: 5 }

    property color textcolorDefault: "#6a84a0"
    property color listItemSelected: "#EAF0F6"
    property color listItemUnselected: "#00000000"
    property color listItemHovered: "#ffffff"
    
    model: ListModel {
        ListElement {
            name: "HDFC"
            selected: false
        }

        ListElement {
            name: "ICICI"
            selected: true
        }

    }
    // highlight: Component {
    //     Rectangle {
    //             width: listView.width
    //             height: 27
    //             //anchors.horizontalCenter: parent.horizontalCenter
    //             radius: 5
    //             color: "#8f9193"
    //             y: listView.currentItem.y;
    //         }
    // }


    delegate: Item {
        // x: 5
        width: listView.width
        height: 27
        Row {
            id: row1
            Rectangle {
                id: rectangle
                width: listView.width -4
                height: 40
                color: selected?listItemSelected:listItemUnselected
                anchors.left: parent.left
                anchors.leftMargin: 4
                CustomBorder {
                    visible: selected ? true : false
                    commonBorder: false
                    lBorderwidth: 4
                    borderColor: "#33475b"
                }
            Text {
                id: listText
                text: name
                width: parent.width
                height: parent.height
                anchors.leftMargin: 29
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                verticalAlignment: Text.AlignVCenter
                font.family: "PT Sans Caption"
                font.pointSize: 10
                font.bold: false
                 color: textcolorDefault
            }
            }
        }
    }
}


/*##^##
Designer {
    D{i:0;formeditorZoom:6}
}
##^##*/
