import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtGraphicalEffects 1.15
import QtQuick.Dialogs 1.3


import  "../qml/controls"

Window {
    id: window
    width: 1562
    height: 1180
    visible: true
    color: "#f4f6f8"
    title: qsTr("Record Matcher")
    //FontLoader { id: appFont; name: "PT Sans Caption"; source: "fonts/PTSansCaption-Regular.ttf" }
    property string chequeTimeData: ""
    Rectangle {
        id:backgroundBox
        color: "#f4f6f8"
        anchors.fill: parent

        // Timer {
        //     interval: 3000
        //     repeat: true
        //     running: true
        //     property int i: 0
        //     onTriggered: {
        //         toast.show("This important message has been shown " + (++i) + " times.",'success');
        //     }
        // }
        Popup {
        id: popup
        parent: Overlay.overlay
        x: Math.round((parent.width - messageBox.width) / 2)
        y: Math.round((parent.height - messageBox.height) / 2)
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnReleaseOutside
        property string popupText : ""
        // enter: Transition {
        //     NumberAnimation { property: "opacity"; from: 0.0; to: 1.0 }
        // }
        // exit: Transition {
        //     NumberAnimation { property: "opacity"; from: 1.0; to: 0.0 }
        // }
        background: Rectangle {
            id: popupBckgroundBox
            width: messageBox.width
            height: messageBox.height
            color: "transparent"
        }
            MessageBox{
                id: messageBox
                singleText:true
                text4: popup.popupText
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
                font.family: "Monoton"
                verticalAlignment: Text.AlignVCenter
                font.strikeout: false
                font.underline: false
                font.italic: false
                font.bold: false
                font.pointSize: 28
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
                FileDialog {
                    id: exportFileDialog
                    nameFilters: ["Excel Files (*.xls *.xlsx)"]
                    title: "Choose the location of file to export "
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
                    onPressed: {
                        chequereport_button.selected = chequereport_button.selected?false:true
                        backend.showChequeReportsSelection(chequereport_button.selected)
                    }
                    onSelectedChanged: {
                        backend.setChequeReportActivated(chequereport_button.selected)
                    }
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
                    onPressed: backend.delete_table()
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
            SettingsButton {
                id: settingsBtn
                width: 43
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                z: 1
                anchors.topMargin: 29
                anchors.bottomMargin: 29
                anchors.rightMargin: 99
                btnIconSource: "../images/svg_images/settings_gear.svg"
                onConvertSchemaClicked: backend.convertSchema()

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
                    id: customBorder
                    commonBorder : false
                    rBorderwidth : 2
                    borderColor: "#e3e5e7"
                }
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                z: 2
                anchors.bottomMargin: 5
                anchors.topMargin: 0
                anchors.leftMargin: 0

                Connections {
                    target: backend
                    function onChequeReportsButtonClicked(selected, status, time){
                        if(selected){
                            console.log("Pushing Cheque Report " + selected + "status" + status)
                            monthBox.visible = false
                            bankBox.visible = false
                            bankBox.height = 0
                            bankLabel.visible = false
                            bodySubtitleStatementModeContainer.visible = false
                            export_button.selected = false
                            delete_button.selected = false
                            help_button.selected = false
                            uploadBtn.visible = true
                            textInput.searchmode = "chqrpt"
                            textInput.fileDialogText = ""
                            if(status===1) {
                                window.chequeTimeData = time
                                stackView.push(chequeReportFoundComponent)
                            }
                            else if(status===0) stackView.push(chequeReportNotFoundComponent)
                            else {
                                stackView.clear()
                                toast.show("No company or year selected", "warning")
                            }
                        }
                        else{
                            console.log("popping Cheque Report ")
                            monthBox.visible = true
                            bankBox.visible = true
                            bankLabel.visible = true
                            bankBox.height = 97
                            bodySubtitleStatementModeContainer.visible = true
                            export_button.selected = false
                            delete_button.selected = false
                            help_button.selected = false
                            uploadBtn.visible = false
                            textInput.searchmode = "default"
                            textInput.fileDialogText = ""
                            console.log(stackView.pop())
                        }
                    }
                    function onShowChequeReportPage(status, time){
                        if(status===1) {
                            window.chequeTimeData = time
                            stackView.push(chequeReportFoundComponent)
                        }
                        else if(status===0) stackView.push(chequeReportNotFoundComponent)
                        else stackView.clear()
                    }
                    function onShowTablePage(){
                        console.log("Showing table")
                        monthBox.visible = true
                        bankBox.visible = true
                        bankBox.height = 97
                        bodySubtitleStatementModeContainer.visible = true
                        chequereport_button.selected = false
                        export_button.selected = false
                        delete_button.selected = false
                        help_button.selected = false
                        textInput.searchmode = "default"
                        uploadBtn.visible = false
                        stackView.push(tableComponent)
                    }
                    function onShowUploadBankStatementPage(){
                        console.log("Showing upload Cheque Statement")
                        monthBox.visible = true
                        bankBox.visible = true
                        bankBox.height = 97
                        bodySubtitleStatementModeContainer.visible = false
                        chequereport_button.selected = false
                        export_button.selected = false
                        delete_button.selected = false
                        help_button.selected = false
                        uploadBtn.visible = true
                        textInput.searchmode = "stmt"
                        stackView.push(uploadStatementComponent)
                    }
                    function onShowChooseOptionsPage(){
                        console.log("Showing select options component")
                        monthBox.visible = true
                        bankBox.visible = true
                        bankBox.height = 97
                        bodySubtitleStatementModeContainer.visible = true
                        chequereport_button.selected = false
                        export_button.selected = false
                        delete_button.selected = false
                        help_button.selected = false
                        textInput.searchmode = "default"
                        uploadBtn.visible = false
                        stackView.push(selectOptionsComponent)
                    }
                    function onValidationError(type){
                        switch(type){
                            case 1: toast.show("Year or Company not selected." ,"error");
                                    break;
                            case 2: // popup.popupText = "Invalid cheque report file. Update fail";
                                    // popup.open();
                                    toast.show("Invalid cheque report file." ,"error");
                                    break;
                            case 3: toast.show("Company or Bank or Year or Month not selected." ,"error");
                                    break;
                            case -1: toast.show("No Infi cheque report found for the financial year." ,"error");
                                    break;
                            // case -2: toast.show("Invalid file path." ,"error");
                            //         break;
                            case -3: toast.show("Invalid HDFC Bank statement file." ,"error");
                                    break;
                            case -4: toast.show("Invalid ICICI Bank statement file." ,"error");
                                    break;
                            default:toast.show("Unknown error. Submit fail." ,"error");
                                    break;
                        }

                        uploadBtn.selected = true
                        busyIndicator.visible = false

                    }
                    function onCheckReportUploadSuccess(){
                        // popup.popupText = "Cheque report file save success"
                        // popup.open()
                        toast.show("Cheque report file save success.", "success");
                        backend.showChequeReportsSelection(chequereport_button.selected)
                        uploadBtn.selected = true
                        busyIndicator.visible = false

                    }
                    function onBankStatementUploadSuccess(){
                        toast.show("Bank statement file save success.", "success");
                        backend.call_populate_table()
                        uploadBtn.selected = true;
                        busyIndicator.visible = false;
                    }
                    function onSnapshotDeleteSuccess() {
                        toast.show("Deleted table successfully.", "success");
                    }
                    function onSnapshotDeleteFail() {
                        toast.show("Table deletion failed.", "error");
                    }
                     function onChequeReportDeleteSuccess() {
                        toast.show("Deleted cheque report successfully.", "success");
                    }
                    function onChequeReportDeleteFail() {
                        toast.show("Cheque report deletion failed.", "error");
                    }
                }

                PropertyAnimation{
                    id: leftMenuAnimationClose
                    target: leftmenuBox
                    property: "width"
                    to: 4
                    duration: 1000
                    easing.type: Easing.InOutQuint

                }
                PropertyAnimation{
                    id: headerAnimationClose
                    target: headerBox
                    property: "height"
                    from:101
                    to: 0
                    duration: 1000
                    easing.type: Easing.InOutQuint
                }
                PropertyAnimation{
                    id: headerAnimationOpen
                    target: headerBox
                    property: "height"
                    from:0
                    to: 101
                    duration: 1000
                    easing.type: Easing.InOutQuint
                }
                PropertyAnimation{
                    id: bodyBoxAnimationClose
                    target: headerBox
                    property: "height"
                    from:0
                    to: 101
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
                        headerAnimationClose.running = true
                        //                        if (menuBtnOpacityAnimation.complete()){
                        //                            burgerButton.visible = false
                        //                        }

                    }
                }

                Text {
                    id: optionsText
                    height: 45
                    text: qsTr("Options")
                    elide: Text.ElideRight
                    color: "#324254"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    font.family: "PT Sans Caption"
                    font.pixelSize: 26
                    font.weight: Font.Bold
                    verticalAlignment: Text.AlignVCenter
                    anchors.rightMargin: 29
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
                        elide: Text.ElideRight
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
                        //                                                boundsBehavior: Flickable.DragAndOvershootBounds
                        anchors.bottomMargin: 0
                        anchors.topMargin: 8
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex:1
                        selected: ''
                        data: backend.companyDict
                        onSelectedChanged: {
                            backend.companyChanged(selected, selectedName)
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
                        elide: Text.ElideRight
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
                        selected: ''
                        onSelectedChanged: {
                            backend.bankChanged(selected, selectedName)
                        }
                        data: backend.bankDict
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
                        elide: Text.ElideRight
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
                        onSelectedChanged: {
                            backend.yearChanged(selected)
                        }
                        data: backend.yearDict
                    }
                }
                Rectangle {
                    id: monthBox
                    visible: true
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
                        elide: Text.ElideRight
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
                        visible: true
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: monthText.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                        anchors.topMargin: 8
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        //                        currentIndex:2
                        onSelectedChanged: {
                            backend.monthChanged(selected, selectedName)
                        }
                        data: backend.monthDict
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

                ToastManager {
                    id: toast
                }

                Rectangle {
                    id: bodyHeaderBox
                    height: 126
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
                            onClicked: {
                                menuBtnCloseAnimation.running = true
                                leftMenuAnimationOpen.running = true
                                menuBtnOpacityAnimation2.running = true
                                headerAnimationOpen.running = true
                            }
                        }
                        Label {
                            id: monthYearLabel
                            // text: qsTr("January 2021")
                            text: backend.monthYearData
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
                            // text: qsTr("Gokul Agencies")
                            text: backend.companyData
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
                            // text: qsTr("HDFC")
                            text: backend.bankData
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
                            // width: 277
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            anchors.leftMargin: 42
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            property string searchbyMode: "bychqno"
                            onSearchBarTextChanged: backend.search(textInput.searchBarText, textInput.searchbyMode)
                            onSearchbyModeChanged: backend.search(textInput.searchBarText, textInput.searchbyMode)
                        }
                        CustomSubTitleButton {
                            id: uploadBtn
                            width: 177
                            anchors.left: textInput.right
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            anchors.leftMargin: 23
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            text: qsTr("Import")
                            selected: true
                            visible: false
                            onClicked : {
                                            uploadBtn.selected = false
                                            busyIndicator.visible = true
                                            if (textInput.fileDialogText == ""){
                                                toast.show("No file selected to import", "error")
                                                uploadBtn.selected = true
                                                busyIndicator.visible = false
                                            return
                                            }
                                            backend.uploadFile(textInput.fileDialogText)
                                        }
                        }
                        BusyIndicator {
                        id: busyIndicator
                        anchors.left: uploadBtn.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        anchors.leftMargin: 23
                        anchors.bottomMargin: 0
                        anchors.topMargin: 0
                        visible: false
                        anchors.verticalCenter: parent.verticalCenter
                        // z: -1
                    }
                        Rectangle {
                            id: bodySubtitleStatementModeContainer
                            anchors.left: textInput.right
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            anchors.rightMargin: 0
                            anchors.leftMargin: 0
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0

                            CustomSubTitleButton {
                                id: byDateBtn
                                width: 90
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.leftMargin: 23
                                anchors.bottomMargin: 0
                                anchors.topMargin: 0
                                text: qsTr("By Date")
                                onSelectedChanged: if(byDateBtn.selected){
                                    textInput.searchbyMode = "bydate"
                                    byChqNoBtn.selected = false
                                    byChqAmtBtn.selected = false
                                }
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
                                onSelectedChanged: if(byChqAmtBtn.selected){
                                    textInput.searchbyMode = "bychqamt"
                                    byChqNoBtn.selected = false
                                    byDateBtn.selected = false
                                }
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
                                onSelectedChanged: if(byChqNoBtn.selected){
                                    textInput.searchbyMode = "bychqno"
                                    byChqAmtBtn.selected = false
                                    byDateBtn.selected = false
                                } 
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
                                text: backend.debitBal
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
                                text: backend.creditBal
                                enabled: false
                            }
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
                    //                    z:-1
                    StackView {
                        id: stackView
                        anchors.fill: parent
                        initialItem: selectOptionsComponent
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                    }
                    Component {
                        id: tableComponent
                        CustomTableView2{
                            tableData: backend.tableData
                            anchors.fill: parent
                            columns: backend.header
                            selectedRows : backend.selectedRows
                            onSelectedRowsChanged: backend.selectedRowsChanged(selectedRows)
                        }
                    }
                    Component {
                        id: uploadStatementComponent
                        UploadChequeStatementPage {
                            anchors.top: parent.top
                            anchors.topMargin: 59
                        }
                    }
                    Component {
                        id: chequeReportFoundComponent
                        ChequeReportFoundPage {
                            timeData: window.chequeTimeData
                            anchors.top: parent.top
                            anchors.topMargin: 59
                        }
                    }
                    Component {
                        id: chequeReportNotFoundComponent
                        ChequeReportNotFoundPage {
                            anchors.top: parent.top
                            anchors.topMargin: 59
                        }
                    }
                    Component {
                        id: selectOptionsComponent
                        OptionsNotSelectedPage {
                            anchors.top: parent.top
                            anchors.topMargin: 59
                        }
                    }

                    BusyIndicator {
                        id: busyIndicator2
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                        z: -1
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
                font.family: "Monoton"
                text: qsTr("Record Matcher")
                anchors.verticalCenter: parent.verticalCenter
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
    D{i:0;formeditorZoom:0.75}
}
##^##*/
