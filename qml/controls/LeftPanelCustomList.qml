import QtQuick 2.15
import  "../controls"

ListView {
    id: listView
    // height: vscale(10)
    property var data: [
        {"name": "HDFC", "value": "hdfc"},
        {"name": "ICICI", "value": "icici"}
    ];
    property string selected: ''
    property string selectedName: ''
    spacing: 3
    layoutDirection: Qt.LeftToRight
    topMargin: 0
    currentIndex: 0
    // property real scaleFactor : 1
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

    property color textcolorDefault: "#6a84a0"
    property color listItemSelected: "#EAF0F6"
    property color listItemUnselected: "#00000000"
    property color listItemHovered: "#EAF0F6"
    property color customBorderColor: "#33475b"
    
    model: ListModel{ id:model}
    onCurrentItemChanged:{
        selectedName = model.get(listView.currentIndex).name
        selected = model.get(listView.currentIndex).value
        console.log(model.get(listView.currentIndex).name + ' selected')
    }

    delegate: Item {
        id: delegateItem
        width: listView.width
        height: vscale(27)
        Rectangle {
            id: rectangle
            width: listView.width-4
            height: vscale(26)
            color: delegateItem.ListView.isCurrentItem ? listItemSelected : listItemUnselected
            //color: listItemSelected
            anchors.left: parent.left
            anchors.leftMargin: hscale(4)
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
                text: model.name
                elide: Text.ElideRight
                width: parent.width
                height: parent.height
                anchors.leftMargin: hscale(29)
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                verticalAlignment: Text.AlignVCenter
                minimumPixelSize: 14
                // font.family: "PT Sans Caption"
                font.family: appFont4.name
                font.pixelSize: tscale(16)
                font.bold: false
                color: textcolorDefault
            }
        }
    }
    function addColumn(val) {
        listView.addColumn(delegateItem.createObject(listView, { name: val } ) );
    }

    Component.onCompleted: function(){
        model.clear();
        for (var i in data) {
            model.append({name: data[i]['name'], value: data[i]['value']})
        }
    }
}




/*##^##
Designer {
    D{i:0;autoSize:true;height:480;width:640}
}
##^##*/
