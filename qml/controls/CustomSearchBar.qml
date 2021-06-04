import QtQuick 2.15
import  "../controls"
import QtQuick.Controls 2.15
import QtQuick.Dialogs 1.3
Rectangle {
    id: containerBox
    height: 38
    color: "#f5f8fa"
    radius: 8
    border.color: "#dee6ec"
    width: searchmode!="default"?920:277
    property string placeholderText: searchmode!="default"?"File Path" :"Search"
    property string searchmode: "default"
    property string searchBarText: ""
    property string fileDialogText: ""
    property string textVal: searchmode==="default"?searchBarText:fileDialogText

    TextInput {
        id: searchInput
        color: "#324254"
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
        text: textVal
        onTextChanged: if (searchmode==="default") {
            searchBarText = searchInput.text
            } 
        else {
            fileDialogText = searchInput.text
            }

        Text {
            id: text1
            text: containerBox.placeholderText
            anchors.fill: parent
            color: "#c4c4c4"
            visible: !searchInput.text
            verticalAlignment: Text.AlignVCenter
            clip: true
            font.family: "PT Sans Caption"
            font.pixelSize: 16
        }
        CustomSubTitleButton {
            id:browseBut
            // width: 174
            width: 74
            height: 30
            fontSize: 10
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: 18
            visible: containerBox.searchmode!="default"?true:false
            // visible: true
            text: "Browse"
            onClicked: fileDialog.open()                
        }

        FileDialog {
            id: fileDialog
            nameFilters: ["Excel Files (*.xls *.xlsx)"]
            title: "Choose the file to import "
            folder: shortcuts.desktop
            onAccepted: {
                console.log("You chose: " + fileDialog.fileUrl)
                fileDialogText = fileDialog.fileUrl
                browseBut.selected = false
            }
            onRejected: {
                console.log("Canceled")
                browseBut.selected = false
            }
        }
    }
}






