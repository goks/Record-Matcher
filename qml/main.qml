import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import  "../qml/controls"
import QtGraphicalEffects 1.15



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
                visible: true
                anchors.fill: parent
                Label {
                    id: logoText
                    width: 411
                    visible: true
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
                    layer.enabled: true
                    layer.effect: DropShadow {
                        id: dropShadow
                               visible: false
                               color: "#40000000"
                               verticalOffset: 4
                               radius: 4
                               anchors.fill: parent
                               cached: false
                               fast: false
                               spread: 0
                               horizontalOffset: 0
                               samples: 0
                           }
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
                border.color: "#00000000"
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

                PropertyAnimation{
                    id: leftMenuAnimation
                    target: leftmenuBox
                    property: "width"
                    to: 4
                    duration: 1000
                    easing.type: Easing.InOutQuint

                }


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
                    onClicked: leftMenuAnimation.running = true
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
                    anchors.topMargin: 15
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: companyText
                        height: 23
                        color: "#2e3f51"
                        text: qsTr("Company")
                        font.family: "PT Sans Caption"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: 18
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.Bold
                        minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: 33
                    }

                    LeftPanelCustomList {
                        id: companyList
                        height: 61
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: companyText.bottom
                        anchors.bottom: parent.bottom
//                        boundsBehavior: Flickable.DragAndOvershootBounds
                        anchors.bottomMargin: 0
                        anchors.topMargin: 8
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex:1
                        model: ListModel {
                            ListElement {
                                name: "Gokul Agencies"
                            }

                            ListElement {
                                name: "Universal Enterprises"
                            }
                        }
                    }
                }

                Rectangle {
                    id: bankBox
                    height: 97
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: companyBox.bottom
                    anchors.topMargin: 15
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: bankText
                        height: 23
                        color: "#2e3f51"
                        text: qsTr("Bank")
                        font.family: "PT Sans Caption"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: 18
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.Bold
                        minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: 33
                    }

                    LeftPanelCustomList {
                        id: bankList
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: bankText.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                        anchors.topMargin: 8
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex:0
                        model: ListModel {
                            ListElement {
                                name: "HDFC"
                            }

                            ListElement {
                                name: "ICICI"
                            }
                        }
                    }
                }
                 Rectangle {
                    id: yearBox
                    height: 180
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: bankBox.bottom
                    anchors.topMargin: 15
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: yearText
                        height: 23
                        color: "#2e3f51"
                        text: qsTr("Year")
                        font.family: "PT Sans Caption"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: 18
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.Bold
                        minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: 33
                    }

                    LeftPanelCustomList {
                        id: yearList
                        height: 170
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: yearText.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 17
                        anchors.topMargin: 8
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex:2
                        model: ListModel {
                            ListElement { name: "2019" }
                            ListElement { name: "2020" }
                            ListElement { name: "2021" }
                            ListElement { name: "2022" }
                            ListElement { name: "2023" }
                        }
                    }
                }
                 Rectangle {
                    id: monthBox
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: yearBox.bottom
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 0
                    anchors.topMargin: 15
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: monthText
                        height: 23
                        color: "#2e3f51"
                        text: qsTr("Month")
                        font.family: "PT Sans Caption"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: 18
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.Bold
                        minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: 33
                    }

                    LeftPanelCustomList {
                        id: monthList
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: monthText.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                        anchors.topMargin: 8
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex:2
                        model: ListModel {
                            ListElement { name: "April" }
                            ListElement { name: "May" }
                            ListElement { name: "June" }
                            ListElement { name: "July" }
                            ListElement { name: "August" }
                            ListElement { name: "September" }
                            ListElement { name: "October" }
                            ListElement { name: "November" }
                            ListElement { name: "December" }
                            ListElement { name: "January" }
                            ListElement { name: "February" }
                            ListElement { name: "March" }
                        }
                    }
                }
            }

            Rectangle {
                id: contentPages
                color: "#ffffff"
                anchors.left: leftmenuBox.right
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.leftMargin: 5
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.rightMargin: 0

                Rectangle {
                    id: bodyHeaderBox
                    height: 141
                    color: "#ffffff"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0
                    anchors.topMargin: 0

                    Rectangle {
                        id: bodyTitleContainer
                        height: 45
                        color: "#ffffff"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        anchors.topMargin: 18

                        Label {
                            id: monthYearLabel
                            text: qsTr("January 2021")
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            verticalAlignment: Text.AlignVCenter
                            anchors.leftMargin: 35
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            font.family: "PT Sans Caption"
                            color: "#324254"
                            font.pixelSize: 26
                            font.weight: Font.Bold
                        }
                        Label {
                            id: companyLabel
                            text: qsTr("Gokul Agencies")
                            anchors.left: monthYearLabel.right
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            verticalAlignment: Text.AlignVCenter
                            anchors.leftMargin: 45
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            font.family: "PT Sans Caption"
                            color: "#324254"
                            font.pixelSize: 26
//                            font.weight: Font.Bold
                        }
                        Label {
                            id: bankLabel
                            text: qsTr("HDFC")
                            anchors.left: companyLabel.right
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            verticalAlignment: Text.AlignVCenter
                            anchors.leftMargin: 45
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            font.family: "PT Sans Caption"
                            color: "#324254"
                            font.pixelSize: 26
//                            font.weight: Font.Bold
                        }
                    }
                }
            }
        }

        Rectangle {
            id: footerBox
            height: 110
            color: "#003366"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
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

    }


}









/*##^##
Designer {
    D{i:0;formeditorZoom:0.9}D{i:58}D{i:57}D{i:56}
}
##^##*/
