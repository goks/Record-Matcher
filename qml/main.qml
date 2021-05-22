import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import  "../qml/controls"



Window {
    id: window
    width: 1562
    height: 1180
    visible: true
    color: "#f4f6f8"
    title: qsTr("Record Matcher")
    //FontLoader { id: appFont; name: "PT Sans Caption"; source: "fonts/PTSansCaption-Regular.ttf" }
    Rectangle {
        id:backgroundBox
        color: "#f4f6f8"
        anchors.fill: parent

        Rectangle {
            id: footerBox
            color: "#003366"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: contentBox.bottom
            anchors.bottom: parent.bottom
            anchors.topMargin: 5
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            anchors.bottomMargin: 0

            Text {
                id: footerLogo
                x: 812
                y: 40
                color: "#ffffff"
                text: qsTr("Record Matcher")
                anchors.verticalCenter: parent.verticalCenter
                font.family: "Monoton"
                font.pixelSize: 26
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                id: copyright_text
                color: "#ffffff"
                font.family: "PT Sans Caption"
                text: qsTr("©Copyright 2021. All rights reserved.")
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                font.pixelSize: 14
                verticalAlignment: Text.AlignVCenter
                anchors.bottomMargin: 13
                anchors.leftMargin: 214
            }
        }

        Rectangle {
            id: headerBox
            height: 101
            color: "#ffffff"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            anchors.topMargin: 0
            Column {
                id: column
                anchors.fill: parent
                Label {
                    id: logoText
                    width: 411
                    color: "#003366"
                    //FontLoader { id: headerFont; name: "Monoton"; source: "fonts/Monoton-Regular.ttf" }
                    text: qsTr("Record Matcher")
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    verticalAlignment: Text.AlignVCenter
                    font.strikeout: false
                    font.underline: false
                    font.italic: false
                    font.bold: false
                    font.pointSize: 28
                    font.family: "Monoton"
                    anchors.bottomMargin: 0
                    anchors.topMargin: 0
                    anchors.leftMargin: 40
                }
                Rectangle {
                    id: headerMenuContainer
                    x: 576
                    width: 460
                    color: "#ffffff"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottomMargin: 0
                    anchors.topMargin: 0


                    TopBarButton {
                        id: export_button
                        width: 133
                        text: qsTr("Export")
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        // font.pointSize: 16
                        leftPadding: 0
                        anchors.leftMargin: 0
                        anchors.bottomMargin: 0
                        anchors.topMargin: 0
                    }
                    TopBarButton {
                        id: chequereport_button
                        width: 230
                        text: qsTr("Cheque Reports")
                        anchors.left: export_button.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        // font.pointSize: 16
                        leftPadding: 0
                        anchors.leftMargin: 1
                        anchors.bottomMargin: 0
                        anchors.topMargin: 0
                    }
                     TopBarButton {
                        id: delete_button
                        width: 104
                        text: qsTr("Delete")
                        anchors.left: chequereport_button.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        // font.pointSize: 16
                        leftPadding: 0
                        anchors.leftMargin: 1
                        anchors.bottomMargin: 0
                        anchors.topMargin: 0
                    }
                     TopBarButton {
                        id: help_button
                        width: 88
                        text: qsTr("Help")
                        anchors.left: delete_button.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        // font.pointSize: 16
                        leftPadding: 0
                        anchors.leftMargin: 1
                        anchors.bottomMargin: 0
                        anchors.topMargin: 0
                    }
                }
                MenuButton {
                    id: settingsBtn
                    width: 43
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: 99
                    btnIconSource: "../images/svg_images/settings_gear.svg"
                }



            }
        }
        Rectangle {
            id: contentBox
            color: "#ffffff"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: headerBox.bottom
            anchors.bottom: parent.bottom
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            anchors.bottomMargin: 115
            anchors.topMargin: 5

            Rectangle {
                id: leftmenuBox
                width: 235
                color: "#ffffff"
                border.color: "#00000000"
                //border.width: 4
                CustomBorder
                        {
                            commonBorder : false
                            rBorderwidth : 2
                            borderColor: "#e3e5e7"
                        }
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 5
                anchors.topMargin: 0
                anchors.leftMargin: 0

                MenuButton {
                    id: burgerButton
                    //                    width: 49
                    //                    height: 43
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    checkable: false
                    anchors.rightMargin: 15
                    anchors.topMargin: 18
                    anchors.leftMargin: 171
                }

                Text {
                    id: optionsText
                    width: 173
                    height: 45
                    text: qsTr("Options")
                    font.family: "PT Sans Caption"
                    color: "#324254"
                    anchors.left: parent.left
                    anchors.top: parent.top
                    font.pixelSize: 26
                    verticalAlignment: Text.AlignVCenter
                    font.weight: Font.Bold
                    anchors.topMargin: 18
                    anchors.leftMargin: 33
                }

                Rectangle {
                    id: companyBox
                    height: 97
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: optionsText.bottom
                    anchors.topMargin: 19
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: companyText
                        height: 40
                        color: "#2e3f51"
                        text: qsTr("Company")
                        font.family: "PT Sans Caption"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: 18
                        verticalAlignment: Text.AlignVCenter
                        font.weight: Font.Bold
                        minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: 33
                    }

                    LeftPanelCustomList {
                        id: listView
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: companyText.bottom
                        anchors.bottom: parent.bottom
                        boundsBehavior: Flickable.DragAndOvershootBounds
                        anchors.bottomMargin: 0
                        anchors.topMargin: -4
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                       model: ListModel {
                            ListElement {
                                name: "Gokul Agencies"
                                selected: false
                            }

                            ListElement {
                                name: "Universal Enterprises"
                                selected: true
                            }   
                        }
                    }
                }

            }

            Rectangle {
                id: contentPages
                color: "#ffffff"
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.leftMargin: 240
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.rightMargin: 0
            }
        }
    }


}







/*##^##
Designer {
    D{i:0;formeditorZoom:1.25}D{i:4}D{i:17}D{i:20}D{i:19}
}
##^##*/
