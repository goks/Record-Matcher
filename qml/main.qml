import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15


import  "../qml/controls"
import  "../qml/table"


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
                               color: "#40000000"
                               verticalOffset: 4
                               radius: 4
                               spread: 0
                               horizontalOffset: 0
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
                    id: leftMenuAnimationClose
                    target: leftmenuBox
                    property: "width"
                    to: 4
                    duration: 1000
                    easing.type: Easing.InOutQuint

                }
                PropertyAnimation{
                    id: leftMenuAnimationOpen
                    target: leftmenuBox
                    property: "width"
                    to: 235
                    duration: 1000
                    easing.type: Easing.InOutQuint

                }
                PropertyAnimation{
                    id: menuBtnCloseAnimation
                    target:burgerButton2
                    property: "width"
                    from:49
                    to: 0
                    duration: 1000
                    easing.type: Easing.InOutQuint

                }
                PropertyAnimation{
                    id: menuBtnOpenAnimation
                    target:burgerButton2
                    property: "width"
                    from:0
                    to: 49
                    duration: 1000
                    easing.type: Easing.InOutQuint

                }
                PropertyAnimation{
                    id: menuBtnOpacityAnimation
                    target:burgerButton
                    property: "opacity"
                    from:1
                    to: 0
                    duration: 1000
                    easing.type: Easing.InOutQuint

                }
                PropertyAnimation{
                    id: menuBtnOpacityAnimation2
                    target:burgerButton
                    property: "opacity"
                    from:0
                    to: 1
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
                    anchors.topMargin: 22
                    bottomPadding: 0
                    checkable: false
                    anchors.rightMargin: 15
                    anchors.leftMargin: 171
                    onClicked:{
                        menuBtnOpenAnimation .running = true
                        leftMenuAnimationClose.running = true
                        menuBtnOpacityAnimation.running = true
//                        if (menuBtnOpacityAnimation.complete()){
//                            burgerButton.visible = false
//                        }

                    }
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

                        MenuButton {
                            id: burgerButton2
                            width: 0
                            visible: true
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.leftMargin: 15
                            anchors.topMargin: 4
                            clip: false
                            //                            //                    width: 49
                            //                            //                    height: 43
//                            anchors.left: parent.left
//                            anchors.right: parent.right
//                            anchors.top: parent.top
//                            anchors.topMargin: 18
//                            checkable: false
//                            anchors.rightMargin: 15
//                            anchors.leftMargin: 171
                            onClicked: {
                                menuBtnCloseAnimation.running = true
                                leftMenuAnimationOpen.running = true
                                menuBtnOpacityAnimation2.running = true
                            }
                        }
                        Label {
                            id: monthYearLabel
                            text: qsTr("January 2021")
                            anchors.left: burgerButton2.right
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
                    Rectangle {
                        id: bodySubtitleContainer
                        height: 38
                        color: "#ffffff"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: bodyTitleContainer.bottom
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        anchors.topMargin: 25
                         CustomSearchBar {
                             id: textInput
                             width: 277
                             anchors.left: parent.left
                             anchors.top: parent.top
                             anchors.bottom: parent.bottom
                             anchors.leftMargin: 42
                             anchors.bottomMargin: 0
                             anchors.topMargin: 0
                         }
                         CustomSubTitleButton {
                             id: byDateBtn
                             width: 69
                             anchors.left: textInput.right
                             anchors.top: parent.top
                             anchors.bottom: parent.bottom
                             anchors.leftMargin: 23
                             anchors.bottomMargin: 0
                             anchors.topMargin: 0
                             text: qsTr("By Date")
                         }
                         CustomSubTitleButton {
                             id: byChqAmtBtn
                             width: 177
                             anchors.left: byDateBtn.right
                             anchors.top: parent.top
                             anchors.bottom: parent.bottom
                             anchors.leftMargin: 23
                             anchors.bottomMargin: 0
                             anchors.topMargin: 0
                             text: qsTr("By Cheque Amount")
                         }
                         CustomSubTitleButton {
                             id: byChqNoBtn
                             width: 177
                             anchors.left: byChqAmtBtn.right
                             anchors.top: parent.top
                             anchors.bottom: parent.bottom
                             anchors.leftMargin: 23
                             anchors.bottomMargin: 0
                             anchors.topMargin: 0
                             text: qsTr("By Cheque Number")
                             selected: true
                         }
                         CustomSubTitleButton {
                             id: debitIndicator
                             width: 120
                             anchors.right: parent.right
                             anchors.top: parent.top
                             anchors.bottom: parent.bottom
                             anchors.rightMargin: 69
                             anchors.bottomMargin: 0
                             anchors.topMargin: 0
                             text: qsTr("1234567890")
                             enabled: false
                         }
                         CustomSubTitleButton {
                             id: creditIndicator
                             width: 120
                             anchors.right: debitIndicator.left
                             anchors.top: parent.top
                             anchors.bottom: parent.bottom
                             anchors.rightMargin: 23
                             anchors.bottomMargin: 0
                             anchors.topMargin: 0
                             text: qsTr("1234567890")
                             enabled: false
                         }

                    }
                }
                Rectangle {
                    id: bodyBodyBox
                    width: 200
                    height: 200
                    color: "#ffffff"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: bodyHeaderBox.bottom
                    anchors.bottom: parent.bottom
                    anchors.rightMargin: 29
                    anchors.leftMargin: 29
                    anchors.bottomMargin: 29
                    anchors.topMargin: 29

                    BusyIndicator {
                        id: busyIndicator
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    CustomTableView{
                        anchors.fill: parent
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
                layer.enabled: true
                                   layer.effect: DropShadow {
                                                 id: dropShadow2
                                                  color: "#40000000"
                                                  verticalOffset: 4
                                                  radius: 4
                                                  spread: 0
                                                  horizontalOffset: 0
                                              }
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
    D{i:0;formeditorZoom:0.5}D{i:72}D{i:74}
}
##^##*/
