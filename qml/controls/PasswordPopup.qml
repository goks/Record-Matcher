import QtQuick 2.0
import QtQuick.Controls 2.15


Popup {
    id: popup
    parent: Overlay.overlay
    x: Math.round((parent.width - popupBckgroundBox.width) / 2)
    y: Math.round((parent.height - popupBckgroundBox.height) / 2)
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape
    property string password: "1234"
    property bool matchStatus: false
    property string passwordFieldText: ""
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

    background: Rectangle {
        id: popupBckgroundBox
        width: 560
        height: 100
        radius: 5
        anchors.left: parent.left
        anchors.leftMargin: 0
        color: "white"
        Text {
            id: passwordPromptText
            height: 52
            color: "#003366"
            //                color: "#000000"
            text: "Enter password: "
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            font.pixelSize: tscale(20)
            verticalAlignment: Text.AlignVCenter
            anchors.leftMargin: hscale(10)
            font.family: "PT Sans Caption"
        }
        TextField {
            id: passwordField
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: passwordPromptText.right
            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.leftMargin: 10
            font.pixelSize: tscale(20)
            font.family: "PT Sans Caption"
            echoMode: TextInput.Password
            color: "#003366"
            text: passwordFieldText
            Keys.onReturnPressed:  {
                console.log("Password Checking 1")
                if(passwordField.text === popup.password){
                    popup.matchStatus = true
                    popup.close()
                }
            }
            Keys.onEnterPressed: {
                console.log("Password Checking 2")
                if(passwordField.text === popup.password){
                    popup.matchStatus = true
                    popup.close()
                }
            }

        }

    }

}
/*##^##
Designer {
    D{i:0;autoSize:true;formeditorZoom:1.1;height:480;width:640}
}
##^##*/
