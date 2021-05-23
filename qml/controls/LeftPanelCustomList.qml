import QtQuick 2.15
import  "../controls"

ListView {
    id: listView
    height: 50
    spacing: 3
    layoutDirection: Qt.LeftToRight
    topMargin: 0
    currentIndex: 0

    property color textcolorDefault: "#6a84a0"
    property color listItemSelected: "#EAF0F6"
    property color listItemUnselected: "#00000000"
    property color listItemHovered: "#EAF0F6"
    property color customBorderColor: "#33475b"
    
    model: ListModel {
        ListElement {
            name: "HDFC"
        }

        ListElement {
            name: "ICICI"
        }

    }
   //highlight: listView.currentItem.rectangle.color = listItemSelected
   //focus: true
   onCurrentItemChanged:{
                             console.log(model.get(listView.currentIndex).name + ' selected')
                        }

    delegate: Item {
        id: delegateItem
        width: listView.width
        height: 27

            Rectangle {
                id: rectangle
                width: listView.width -4
                height: 26
                color: delegateItem.ListView.isCurrentItem ? listItemSelected : listItemUnselected
                //color: listItemSelected
                anchors.left: parent.left
                anchors.leftMargin: 4
                CustomBorder {
                    visible: delegateItem.ListView.isCurrentItem ? true : false
                    commonBorder: false
                    lBorderwidth: 4
                    borderColor: customBorderColor
                }
                Rectangle {
                    id: hoverRectangle
                    width: parent.width
                    height: parent.height
                    color: listItemUnselected
                    z:-1
                }

                MouseArea {
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: {
                                        listView.currentIndex = index
                                    }
                                    onEntered: {
                                        hoverRectangle.color = listItemHovered
                                    }
                                    onExited: {
                                        hoverRectangle.color = listItemUnselected
                                    }

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



/*##^##
Designer {
    D{i:0;formeditorZoom:1.5}
}
##^##*/
