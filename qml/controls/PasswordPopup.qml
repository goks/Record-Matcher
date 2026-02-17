import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Popup {
    id: popup
    parent: Overlay.overlay
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape

    property bool matchStatus: false
    property string passwordFieldText: ""
    property string errorText: ""
    property bool revealPassword: false
    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1

    signal authenticated()

    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return Math.round((hscale(size) + vscale(size)) / 2) + 2
    }

    x: Math.round((parent.width - width) / 2)
    y: Math.round((parent.height - height) / 2)
    width: Math.min(hscale(520), parent ? (parent.width - hscale(28)) : hscale(520))
    height: vscale(250)

    background: Rectangle {
        radius: hscale(10)
        color: "#ffffff"
        border.color: "#d6dde6"
        border.width: 1
    }

    function tryAuthenticate() {
        if (backend && backend.verifyAdminPassword(passwordField.text)) {
            popup.matchStatus = true
            errorText = ""
            popup.close()
            popup.authenticated()
            return
        }
        popup.matchStatus = false
        errorText = "Incorrect password"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: hscale(16)
        spacing: vscale(10)

        Text {
            text: "Authentication Required"
            font.family: "PT Sans Caption"
            font.pixelSize: tscale(17)
            font.weight: Font.DemiBold
            color: "#0f172a"
        }

        Text {
            text: "Enter admin password to continue Firebase upload."
            font.family: "PT Sans Caption"
            font.pixelSize: tscale(11)
            color: "#64748b"
        }

        Rectangle {
            Layout.fillWidth: true
            height: vscale(46)
            radius: hscale(8)
            color: "#f8fafc"
            border.color: errorText !== "" ? "#ef4444" : "#cbd5e1"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: hscale(10)
                anchors.rightMargin: hscale(8)
                spacing: hscale(8)

                TextField {
                    id: passwordField
                    Layout.fillWidth: true
                    font.family: "PT Sans Caption"
                    font.pixelSize: tscale(13)
                    placeholderText: "Password"
                    color: "#0f172a"
                    text: passwordFieldText
                    echoMode: revealPassword ? TextInput.Normal : TextInput.Password
                    passwordCharacter: "*"
                    passwordMaskDelay: 0
                    inputMethodHints: Qt.ImhHiddenText | Qt.ImhNoPredictiveText | Qt.ImhSensitiveData
                    background: Rectangle { color: "transparent"; border.width: 0 }
                    onTextChanged: errorText = ""
                    Keys.onReturnPressed: popup.tryAuthenticate()
                    Keys.onEnterPressed: popup.tryAuthenticate()
                }

                Button {
                    text: revealPassword ? "Hide" : "Show"
                    font.family: "PT Sans Caption"
                    font.pixelSize: tscale(11)
                    onClicked: revealPassword = !revealPassword
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: errorText
            visible: errorText !== ""
            font.family: "PT Sans Caption"
            font.pixelSize: tscale(10)
            color: "#dc2626"
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: hscale(8)

            Item { Layout.fillWidth: true }

            Button {
                text: "Cancel"
                onClicked: {
                    popup.matchStatus = false
                    popup.close()
                }
            }

            Button {
                text: "Continue"
                onClicked: popup.tryAuthenticate()
            }
        }
    }

    onOpened: {
        errorText = ""
        revealPassword = false
        passwordField.text = ""
        passwordField.forceActiveFocus()
    }
}
