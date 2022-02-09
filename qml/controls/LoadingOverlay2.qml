import QtQuick 2.0
import QtQuick.Controls 2.15
import QtQuick.Dialogs 1.3
import  "../controls"

Rectangle{
    id: loadingOverlay
    color: "#ddffffff"
    anchors.fill: parent
    property real progressBarValue: 0.0
    property string text1: "123"
    property string text2: "456"
    property string daybookFileURL: ""
    property string fromDate: ""
    property string toDate: ""
    property string company: "gokul"
    signal createIntermediateDaybookButtonClicked
    signal createTallyVoucherXMlButtonClicked
    property bool status: true
    property var tallyXMLVoucherOptions: [true,true,true,true,true]
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
    MouseArea {
        z:3
        anchors.fill: parent
        onClicked: {
        }
    }
    MenuButton {
        z:4
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: hscale(82)
        anchors.topMargin: vscale(60)
        btnIconSource: "../../images/svg_images/close_button.svg"
        scaleFactorHeight: scaleFactorHeight
        scaleFactorWidth: scaleFactorWidth
        onClicked: {
            loadingOverlay.visible = false
        }
    }

    Rectangle {
        z:4
        id: container
        anchors.fill: parent
        anchors.margins: 100
        color: "#00000000"
        
        Text {
            // text: "Loading ChequeReports"
            id: h1
            text: "Prepare intermediate daybook file "
            anchors.top: parent.top
            font.pixelSize: tscale(30)
            anchors.topMargin: 0
            font.family: appFont4.name
        }
        Rectangle {
            id: fileImportContainerBox
            //    height: 38
            height: vscale(50)
            color: "#f5f8fa"
            implicitHeight: vscale(38)
            radius: 8
            border.color: "#dee6ec"
            anchors.top: h1.bottom
            anchors.topMargin: vscale(20)
            width: hscale(1000)

            TextInput {
                id: searchInput
                color: "#324254"
                //        text: qsTr("Search")
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                font.family: appFont4.name
                font.pixelSize: tscale(16)
                verticalAlignment: Text.AlignVCenter
                clip: true
                anchors.topMargin: 0
                anchors.bottomMargin: 0
                anchors.leftMargin: hscale(15)
                anchors.rightMargin: hscale(15)
                text: daybookFileURL
                onTextChanged: daybookFileURL = searchInput.text

                Text {
                    id: placeholder
                    text: "Daybook from start of financial year, from Accounts>Reports>Daybook-Export"
                    anchors.fill: parent
                    color: "#c4c4c4"
                    visible: !searchInput.text
                    verticalAlignment: Text.AlignVCenter
                    clip: true
                    font.family: appFont4.name
                    font.pixelSize: tscale(16)
                }
                CustomSubTitleButton {
                    id:browseBut
                    // width: 174
                    width: hscale(74)
                    height: vscale(25)
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: hscale(18)
                    visible: true
                    font.pixelSize: tscale(10)
                    text: "Browse"
                    onClicked: fileDialog.open()
                }
                FileDialog {
                    id: fileDialog
                    nameFilters: ["Excel Files (*.xls *.xlsx)"]
                    title: "Choose the Daybook file to import "
                    folder: shortcuts.desktop
                    onAccepted: {
                        console.log("You chose: " + fileDialog.fileUrl)
                        daybookFileURL = fileDialog.fileUrl
                        browseBut.selected = false
                    }
                    onRejected: {
                        console.log("Canceled")
                        browseBut.selected = false
                    }
                }
            }
        }
        Rectangle{
            id: companySelectionContainer
            anchors.left: parent.left
            anchors.top: fileImportContainerBox.bottom
            anchors.leftMargin: 0
            anchors.topMargin: vscale(25)
            height: vscale(50)

            Text{
                id: h3
                text: "for the company "
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.leftMargin: 0
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                font.pixelSize: tscale(30)
                font.family: appFont4.name
            }
            RadioButton {
                id: gokulRadio
                checked: true
                text: qsTr("Gokul Agencies")
                anchors.left: h3.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.leftMargin: hscale(10)
                font.pixelSize: tscale(30)
                font.family: appFont4.name
                onClicked: if(checked)
                               loadingOverlay.company="gokul"
            }
            RadioButton {
                id: universalRadio
                text: qsTr("Universal Enterprises")
                anchors.left: gokulRadio.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.leftMargin: hscale(10)
                font.pixelSize: tscale(30)
                font.family: appFont4.name
                onClicked: if(checked)
                               loadingOverlay.company="universal"
            }
        }
        Text {
            // text: "Loading ChequeReports"
            id: h2
            text: "for the date range"
            anchors.top: companySelectionContainer.bottom
            font.pixelSize: tscale(30)
            anchors.topMargin: vscale(25)
            font.family: appFont4.name
        }
        Rectangle {
            id: fromtoContainer
            anchors.left: parent.left
            anchors.top: h2.bottom
            anchors.leftMargin: 0
            anchors.topMargin: vscale(15)
            height: vscale(50)

            Text {
                // text: "Loading ChequeReports"
                id: fromText
                text: "from"
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                font.pixelSize: tscale(25)
                verticalAlignment: Text.AlignVCenter
                anchors.leftMargin: 0
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                font.family: appFont4.name
            }
            DateSelectorInput {
                id: fromDateSelector
                anchors.left: fromText.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 0
                anchors.leftMargin: hscale(15)
                anchors.topMargin: 0
                placeHolderText: "from Date"
                dateVal: loadingOverlay.fromDate
                onDateValChanged: loadingOverlay.fromDate = fromDateSelector.dateVal
                scaleFactorWidth: loadingOverlay.scaleFactorWidth
                scaleFactorHeight: loadingOverlay.scaleFactorHeight
            }
            Text {
                // text: "Loading ChequeReports"
                id: toText
                text: "to"
                anchors.left: fromDateSelector.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                font.pixelSize: tscale(25)
                verticalAlignment: Text.AlignVCenter
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.leftMargin: hscale(10)
                font.family: appFont4.name
            }
            DateSelectorInput {
                id: toDateSelector
                anchors.left: toText.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 0
                anchors.leftMargin: hscale(10)
                anchors.topMargin: 0
                placeHolderText: "to Date"
                dateVal: loadingOverlay.toDate
                onDateValChanged: loadingOverlay.toDate = toDateSelector.dateVal
                scaleFactorWidth: loadingOverlay.scaleFactorWidth
                scaleFactorHeight: loadingOverlay.scaleFactorHeight
            }
            Text {
                // text: "Loading ChequeReports"
                id: periodText
                text: "."
                anchors.left: toDateSelector.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                font.pixelSize: tscale(25)
                verticalAlignment: Text.AlignVCenter
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.leftMargin: hscale(10)
                font.family: appFont4.name
            }
            CustomSubTitleButton {
                id: createIntermediateDaybookButton
                anchors.left: periodText.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.leftMargin: hscale(10)
                text: "Create intermediate Daybook"
                onClicked: loadingOverlay.createIntermediateDaybookButtonClicked()
            }

        }
        Text {
            // text: "Loading ChequeReports"
            id: intermediaryDaybookText
            text: "Creating intermediary daybook"
            anchors.top: fromtoContainer.bottom
            font.pixelSize: tscale(30)
            anchors.topMargin: vscale(25)
            font.family: appFont4.name
        }
        ProgressBar {
            id: intermediaryDaybookProgressBar
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: intermediaryDaybookText.bottom
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            anchors.topMargin: vscale(25)
            to: 1.0
            value: loadingOverlay.progressBarValue
        }

        Text {
            // text: "Loading ChequeReports"
            id: intermediaryDaybookText1
            text: loadingOverlay.text1
            anchors.top: intermediaryDaybookProgressBar.bottom
            font.pixelSize: tscale(20)
            anchors.topMargin: vscale(5)
            font.family: appFont4.name
        }
        Text {
            // text: "processing Jun 2020 gokul"
            id: intermediaryDaybookText2
            text: loadingOverlay.text2
            anchors.top: intermediaryDaybookText1.bottom
            font.pixelSize: tscale(10)
            anchors.topMargin: vscale(5)
            font.family: appFont4.name
        }


        Rectangle {
            id: tallyXMLContainer
            color: "#00000000"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top:  intermediaryDaybookText2.bottom
            anchors.bottom: parent.bottom
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            anchors.bottomMargin: 0
            anchors.topMargin: 0
            z: 4
            
            Text {
                id: s2t1
                text: "Now, create Tally Voucher XML file with the options: "
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                font.pixelSize: tscale(30)
                anchors.leftMargin: 0
                anchors.rightMargin: 0
                anchors.topMargin: 10
                font.family: appFont4.name
            }
            Rectangle{
                id: checkBoxContainer
                height: 50
                // height: 20
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: s2t1.bottom
                anchors.rightMargin: 0
                anchors.leftMargin: 0
                anchors.topMargin: 5

                CheckBox {
                    id: c1
                    checked: loadingOverlay.tallyXMLVoucherOptions[0]
                    text: qsTr("Sales Invoices")
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 10
                    anchors.topMargin: 0
                    anchors.leftMargin: 0
                    onCheckedChanged: {
                        loadingOverlay.tallyXMLVoucherOptions[0] = checked
                    }

                }
                CheckBox {
                    id: c2
                    text: qsTr("Purchase Invoices")
                    checked: loadingOverlay.tallyXMLVoucherOptions[1]
                    anchors.left: c1.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 10
                    anchors.topMargin: 0
                    anchors.leftMargin: 0
                    onCheckedChanged: {
                        loadingOverlay.tallyXMLVoucherOptions[1] = checked
                    }
                }
                CheckBox {
                    id: c3
                    checked: loadingOverlay.tallyXMLVoucherOptions[2]
                    text: qsTr("Payment Vouchers")
                    anchors.left: c2.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 10
                    anchors.leftMargin: 0
                    anchors.topMargin: 0
                    onCheckedChanged: {
                        loadingOverlay.tallyXMLVoucherOptions[2] = checked
                    }
                }
                CheckBox {
                    id: c4
                    checked: loadingOverlay.tallyXMLVoucherOptions[3]
                    text: qsTr("Journal Entries")
                    anchors.left: c3.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 10
                    anchors.leftMargin: 0
                    anchors.topMargin: 0
                    onCheckedChanged: {
                        loadingOverlay.tallyXMLVoucherOptions[3] = checked
                    }
                }
                CheckBox {
                    id: c5
                    checked: loadingOverlay.tallyXMLVoucherOptions[4]
                    text: qsTr("Sales Return Invoices")
                    anchors.left: c4.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 10
                    anchors.leftMargin: 0
                    anchors.topMargin: 0
                    onCheckedChanged: {
                        loadingOverlay.tallyXMLVoucherOptions[4] = checked
                    }
                }
            }
            CustomSubTitleButton {
                id: createTallyVoucherXMlButton
                text: "Create Tally Voucher XML"
                anchors.left: parent.left
                anchors.top: checkBoxContainer.bottom
                anchors.leftMargin: 0
                anchors.topMargin: 0
                onClicked: loadingOverlay.createTallyVoucherXMlButtonClicked()
            }



        }

    }
}









/*##^##
Designer {
    D{i:0;autoSize:true;height:480;width:640}
}
##^##*/
