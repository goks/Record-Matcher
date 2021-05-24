import QtQuick 2.15
import  "../controls"

Rectangle {
    id: containerBox
    height: 38
    color: "#f5f8fa"
    radius: 8
    border.color: "#dee6ec"
    width: 277

    TextInput {
        id: searchInput
        property string placeholderText: "Search"
        color: "#c4c4c4"
//        text: qsTr("Search")
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        font.family: "PT Sans Caption"
        font.pixelSize: 16
        verticalAlignment: Text.AlignVCenter
        clip: true
        anchors.topMargin: 0
        anchors.bottomMargin: 0
        anchors.leftMargin: 15
        anchors.rightMargin: 15

        Text {
            text: searchInput.placeholderText
            anchors.fill: parent
            color: "#c4c4c4"
            visible: !searchInput.text
            verticalAlignment: Text.AlignVCenter
            clip: true
            font.family: "PT Sans Caption"
            font.pixelSize: 16
        }
    }


}

/*##^##
Designer {
    D{i:0;formeditorZoom:6}
}
##^##*/
