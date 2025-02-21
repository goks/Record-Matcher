import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls 1.6 as C
import QtGraphicalEffects 1.15
import QtQuick.Dialogs 1.3


import  "../qml/controls"

Window {
    id: window
    property int designWidth: 1562
    property int designHeight: 1080
    width: 1280
    height: 720
    //    minimumWidth: 1280
    //    minimumHeight: 720
    visible: true
    color: "#f4f6f8"
    title: qsTr("Record Matcher")
    // readonly property real refScreenWidth: 1562
    // readonly property real refScreenHeight: 1180
    readonly property real refScreenWidth: 1920
    readonly property real refScreenHeight: 1080

    readonly property real screenWidth: window.width
    readonly property real screenHeight: window.height

    property double scaleFactorHeight: (screenHeight / refScreenHeight)
    property double scaleFactorWidth: (screenWidth / refScreenWidth)

    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }

    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return Math.round((hscale(size) + vscale(size)) / 2)+2
    }
    //    onClosing: backend.beginWindowExitRoutine()
    FontLoader { id: appFont; name: "PT Sans Caption"; source: "../fonts/PTSansCaption-Regular.ttf" }
    FontLoader { id: appFont2; name: "Monoton"; source: "../fonts/Monoton-Regular.ttf" }
    FontLoader { id: appFont3; source: "../fonts/PTSansCaption-Bold.ttf" }
    FontLoader { id: appFont4; source: "../fonts/Sen-Regular.ttf" }
    property string chequeTimeData: ""
    Rectangle {
        z:0
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
        LoadingOverlay{
            id: fullScreenLoading
            visible: false
            z:15
            scaleFactorWidth: window.scaleFactorWidth
            scaleFactorHeight: window.scaleFactorHeight
            progressBarValue: backend.progressBarValue
            text1: backend.fullScreenLoadingInfo1
            text2: backend.fullScreenLoadingInfo2
        }
        LoadingOverlay2{
            id: fullScreenLoading2
            visible: false
            z:15
            scaleFactorWidth: window.scaleFactorWidth
            scaleFactorHeight: window.scaleFactorHeight
            progressBarValue: backend.progressBarValue
            text1: backend.fullScreenLoadingInfo1
            text2: backend.fullScreenLoadingInfo2
            fromDate: "01/06/2021"
            toDate: "30/06/2021"
            daybookFileURL: "C:\\Users\\Gokul\\Documents\\Cheque Reports\\Daybook 21.xlsx"
            company: "gokul"
            tallyXMLVoucherOptions: [true,true,true,true,true]
            onCreateIntermediateDaybookButtonClicked: {
               backend.createIntermediateDaybook(fullScreenLoading2.daybookFileURL, fullScreenLoading2.fromDate, fullScreenLoading2.toDate, fullScreenLoading2.company)
            }
            onCreateTallyVoucherXMlButtonClicked: {
                backend.createTallyXMLVoucher(fullScreenLoading2.tallyXMLVoucherOptions)
            }
            ToastManager {
                    id: toastOverlay2
                    leftMargin: hscale(100)
                    bottomMargin: vscale(100)
                    scaleFactorWidth: window.scaleFactorWidth
                    scaleFactorHeight: window.scaleFactorHeight
                }
        }
        CustomPopup{
            id: popup
            scaleFactorWidth: window.scaleFactorWidth
            scaleFactorHeight: window.scaleFactorHeight

        }
        PasswordPopup{
            id: passwordPopup
            scaleFactorWidth: window.scaleFactorWidth
            scaleFactorHeight: window.scaleFactorHeight
            passwordFieldText: ""
            password: backend.adminPassword
            matchStatus: false
            onClosed: {
                            if(passwordPopup.matchStatus === true){
                                        passwordPopup.matchStatus = false
                                        backend.uploadtoDb()
                                    }
                        }

        }
        Rectangle {
            id: headerBox
            color: "#ffffff"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            anchors.topMargin: 0
            implicitHeight: vscale(101)
            //            height: Math.min( parent.height*.12, implicitHeight)
            //            height: scaleFactorHeight*101
            height: vscale(101)
            //            transform: Scale { yScale: scaleFactorHeight; xScale: scaleFactorWidth;}
            Label {
                id: logoText
                width: hscale(411)
                visible: true
                color: "#003366"
                text: qsTr("Record Matcher")
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                font.pixelSize: tscale(36)
                font.family: "Monoton"
                verticalAlignment: Text.AlignVCenter
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.leftMargin: hscale(40)
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
                implicitWidth: hscale(460)
                //                width: Math.min(implicitWidth, parent.width*.30)
                width: hscale(460)
                color: "#ffffff"
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.horizontalCenterOffset: hscale(20)
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                implicitHeight: parent.implicitHeight


                TopBarButton {
                    id: export_button
                    // width: 133
                    text: qsTr("Export")
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    // font.pointSize: 16
                    leftPadding: 0
                    anchors.leftMargin: 0
                    anchors.bottomMargin: 0
                    anchors.topMargin: 0
                    scaleFactorWidth: window.scaleFactorWidth
                    scaleFactorHeight: window.scaleFactorHeight
                    onPressed: {
                        export_button.selected = export_button.selected?false:true
                        // console.log("scaleFactor: "+ window.scaleFactorHeight + " "+ headerBox.height+ " "+headerBox.implicitHeight)
                    }
                    onSelectedChanged: {
                        if (chequereport_button.selected){
                            chequereport_button.selected = false
                            backend.showChequeReportsSelection(chequereport_button.selected)
                        }
                        console.log("export_button.selected: " + export_button.selected)
                        if (export_button.selected == true){
                            popup.open();
                        }
                    }
                }
                TopBarButton {
                    id: chequereport_button
                    scaleFactorWidth: window.scaleFactorWidth
                    scaleFactorHeight: window.scaleFactorHeight
                    // width: 230
                    text: qsTr("Cheque Reports")
                    anchors.left: export_button.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
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
                    id: tallyexport_button
                    scaleFactorWidth: window.scaleFactorWidth
                    scaleFactorHeight: window.scaleFactorHeight
                    // width: 104
                    text: qsTr("Tally Export")
                    anchors.left: chequereport_button.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    leftPadding: 0
                    anchors.leftMargin: 1
                    anchors.bottomMargin: 0
                    anchors.topMargin: 0
                    // onPressed: backend.delete_table()
                    onPressed: {
                        tallyexport_button.selected = tallyexport_button.selected?false:true
                        backend.showTallyExportBox(tallyexport_button.selected)
                    }
                    onSelectedChanged: {
                        backend.setTallyExportBoxActivated(tallyexport_button.selected)
                    }
                }
                TopBarButton {
                    id: help_button
                    scaleFactorWidth: window.scaleFactorWidth
                    scaleFactorHeight: window.scaleFactorHeight
                    // width: 88
                    text: qsTr("Help")
                    anchors.left: tallyexport_button.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    leftPadding: 0
                    anchors.leftMargin: 1
                    anchors.bottomMargin: 0
                    anchors.topMargin: 0
                }
            }
            SettingsButton {
                id: settingsBtn
                width: tscale(43)
                height: width
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                z: 1
                anchors.rightMargin: hscale(99)
                scaleFactorWidth: window.scaleFactorWidth
                scaleFactorHeight: window.scaleFactorHeight
                btnIconSource: "../images/svg_images/settings_gear.svg"
                // onConvertSchemaClicked: backend.convertSchema()
                onDeleteButtonClicked: backend.delete_table()
                onDownloadFromDbClicked: backend.downloadfromDb()
                onUploadtoDbClicked:{
                                    passwordPopup.open()
                                    }
                onCreateTallyXMLFromDaybookClicked: backend.createTallyXMLFromDaybook()
            }
        }
        Rectangle {
            id: contentBox
            color: "#ffffff"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: headerBox.bottom
            anchors.bottom: footerBox.top
            anchors.rightMargin: 0
            anchors.leftMargin: 0
            anchors.bottomMargin: 4
            anchors.topMargin: vscale(5)

            Rectangle {
                id: leftmenuBox
                width: hscale(235)
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
                anchors.bottomMargin: vscale(5)
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
                            tallyexport_button.selected = false
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
                            bankBox.height = vscale(97)
                            bodySubtitleStatementModeContainer.visible = true
                            export_button.selected = false
                            tallyexport_button.selected = false
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
                    function onTallyExportButtonClicked(selected){
                        if(selected){
                            console.log("Pushing Tally Export Box")
                            monthBox.visible = false
                            bankBox.visible = false
                            yearBox.visible = false
                            bankLabel.visible = false
                            bankBox.height = 0
                            bodySubtitleStatementModeContainer.visible = false
                            export_button.selected = false
                            tallyexport_button.selected = true
                            help_button.selected = false
                            uploadBtn.visible = false
                            textInput.searchmode = "chqrpt"
                            textInput.fileDialogText = ""
                            bodySubtitleContainer.visible = false
                            bodySubtitleContainer.height = 0
                            bodyHeaderBox.height=0
                            stackView.push(tallyExportBoxComponent)
                            // else {
                            //     stackView.clear()
                            //     toast.show("No company or year selected", "warning")
                            // }
                        }
                        else{
                            console.log("popping Tally Export Box ")
                            monthBox.visible = true
                            yearBox.visible = true
                            bankBox.visible = true
                            bankLabel.visible = true
                            bankBox.height = vscale(97)
                            bodySubtitleStatementModeContainer.visible = true
                            export_button.selected = false
                            tallyexport_button.selected = false
                            help_button.selected = false
                            uploadBtn.visible = false
                            textInput.searchmode = "default"
                            textInput.fileDialogText = ""
                            bodySubtitleContainer.visible = true
                            bodySubtitleContainer.height = vscale(38)
                            bodyHeaderBox.height=vscale(126)
                            console.log(stackView.pop())

                        }
                    }
                    function onShowTallyExportPage(){
                        stackView.push(tallyExportBox)
                    }
                    function onShowTablePage(){
                        // console.log("Showing table")
                        monthBox.visible = true
                        bankBox.visible = true
                        bankBox.height = vscale(97)
                        bodySubtitleStatementModeContainer.visible = true
                        chequereport_button.selected = false
                        export_button.selected = false
                        tallyexport_button.selected = false
                        help_button.selected = false
                        textInput.searchmode = "default"
                        uploadBtn.visible = false
                        byDateBtn.selected = false
                        byChqAmtBtn.selected = false
                        byChqNoBtn.selected = false
                        stackView.push(tableComponent)
                    }
                    function onShowUploadBankStatementPage(){
                        // console.log("Showing upload Cheque Statement")
                        monthBox.visible = true
                        bankBox.visible = true
                        bankBox.height = vscale(97)
                        bodySubtitleStatementModeContainer.visible = false
                        chequereport_button.selected = false
                        export_button.selected = false
                        tallyexport_button.selected = false
                        help_button.selected = false
                        uploadBtn.visible = true
                        textInput.searchmode = "stmt"
                        stackView.push(uploadStatementComponent)
                    }
                    function onShowChooseOptionsPage(){
                        // console.log("Showing select options component")
                        monthBox.visible = true
                        bankBox.visible = true
                        bankBox.height = vscale(97)
                        bodySubtitleStatementModeContainer.visible = true
                        chequereport_button.selected = false
                        export_button.selected = false
                        tallyexport_button.selected = false
                        help_button.selected = false
                        textInput.searchmode = "default"
                        uploadBtn.visible = false
                        byDateBtn.selected = false
                        byChqAmtBtn.selected = false
                        byChqNoBtn.selected = false
                        stackView.push(selectOptionsComponent)

                    }
                    function onValidationError(type){
                        switch(type){
                        case 1: toast.show("Year or Company not selected." ,"warning");
                            break;
                        case 2: // popup.popupText = "Invalid cheque report file. Update fail";
                            // popup.open();
                            toast.show("Invalid cheque report file." ,"error");
                            break;
                        case 3: toast.show("Company or Bank or Year or Month not selected." ,"warning");
                            break;
                        case 4: toast.show("No table to export.", "error")        ;
                            break
                        case -1: toast.show("No Infi cheque report found for the financial year." ,"error");
                            break;
                        case -2: toast.show("Invalid file path." ,"error");
                            break;
                        case -3: toast.show("Invalid HDFC Bank statement file." ,"error");
                            break;
                        case -4: toast.show("Invalid ICICI Bank statement file." ,"error");
                            break;
                        case -5: toast.show("Permission error. Failed to write" ,"error");
                            break;
                        default:toast.show("Unknown error. Submit fail." ,"error");
                            break;
                        }

                        uploadBtn.selected = true
                        busyIndicator.visible = false

                    }

                    function onDayBookExportHandlingError(type, data){
                        switch(type){
                            case -1: toastOverlay2.show("Cannot import Daybook. Check file path/ file.", "error")
                                break;
                            case -2: toastOverlay2.show("Invalid from-date.", "warning")
                                break;
                            case -3: toastOverlay2.show("Invalid to-date.", "warning")
                                break;        
                            case -4: toastOverlay2.show("From-date is greater than or equal to to-date", "warning")
                                break;        
                            case -5: toastOverlay2.show("Interval is greater than 12 months", "warning")
                                break;        
                            case -6: toastOverlay2.show("Selected companies not in list", "error")
                                break;   
                            case -7: toastOverlay2.show("No bank statement for "+ data, "error")
                                break 
                            case -8: toastOverlay2.show("Error opening file. Try opening the file in excel and saving it.", "error")
                                break           
                            default: toastOverlay2.show("Unknown error. Could not start process." ,"error");
                            break;
                        }
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
                    function onStatementExportSuccess(){
                        popup.close()
                        toast.show("Bank statement export success.", "success");
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
                    function onFullScreenLoadingStart() {
                        fullScreenLoading.visible=true
                    }
                    function onFullScreenLoadingEnd() {
                        fullScreenLoading.visible=false
                    }
                    function onFullScreenLoading2Start() {
                        fullScreenLoading2.visible=true
                    }
                    function onFullScreenLoading2End() {
                        fullScreenLoading2.visible=false
                    }
                    function onShowMainScreenLoadingIndicator() {
                        mainScreenBusyIndicator.running = true
                    }
                    function onHideMainScreenLoadingIndicator() {
                        mainScreenBusyIndicator.running = false
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
                    from:vscale(101)
                    to: 0
                    duration: 1000
                    easing.type: Easing.InOutQuint
                }
                PropertyAnimation{
                    id: headerAnimationOpen
                    target: headerBox
                    property: "height"
                    from:0
                    to: vscale(101)
                    duration: 1000
                    easing.type: Easing.InOutQuint
                }
                PropertyAnimation{
                    id: bodyBoxAnimationClose
                    target: headerBox
                    property: "height"
                    from:0
                    to: vscale(101)
                    duration: 1000
                    easing.type: Easing.InOutQuint
                }
                PropertyAnimation{
                    id: leftMenuAnimationOpen
                    target: leftmenuBox
                    property: "width"
                    to: hscale(235)
                    duration: 1000
                    easing.type: Easing.InOutQuint
                }
                PropertyAnimation{
                    id: menuBtnCloseAnimation
                    target:burgerButton2
                    property: "width"
                    from: hscale(49)
                    to: 0
                    duration: 1000
                    easing.type: Easing.InOutQuint
                }
                PropertyAnimation{
                    id: menuBtnOpenAnimation
                    target:burgerButton2
                    property: "width"
                    from:0
                    to: hscale(49)
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
                    anchors.topMargin: vscale(22)
                    bottomPadding: 0
                    checkable: false
                    anchors.rightMargin: hscale(15)
                    anchors.leftMargin: hscale(171)
                    scaleFactorWidth: window.scaleFactorWidth
                    scaleFactorHeight: window.scaleFactorHeight
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
                    height: vscale(45)
                    text: qsTr("Options")
                    elide: Text.ElideRight
                    color: "#324254"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    font.family: appFont3.name
                    font.pixelSize: tscale(26)
                    font.weight: Font.Bold
                    verticalAlignment: Text.AlignVCenter
                    anchors.rightMargin: hscale(29)
                    anchors.leftMargin: hscale(33)
                    anchors.topMargin: vscale(18)
                }

                Rectangle {
                    id: companyBox
                    height: vscale(110)
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: optionsText.bottom
                    anchors.topMargin: vscale(26)
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: companyText
                        height: vscale(23)
                        color: "#2e3f51"
                        text: qsTr("Company")
                        elide: Text.ElideRight
                        font.family: appFont3.name
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: tscale(18)
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.Bold
                        // minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: hscale(33)
                        z:2
                    }

                    LeftPanelCustomList {
                        id: companyList
                        // height: vscale(61)
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: companyText.bottom
                        anchors.bottom: parent.bottom
                        // boundsBehavior: Flickable.DragAndOvershootBounds
                        anchors.bottomMargin: 0
                        anchors.topMargin: vscale(8)
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex:1
                        selected: ''
                        scaleFactorWidth: window.scaleFactorWidth
                        scaleFactorHeight: window.scaleFactorHeight
                        data: backend.companyDict
                        z:1
                        onSelectedChanged: {
                            backend.companyChanged(selected, selectedName)
                        }
                    }
                }

                Rectangle {
                    id: bankBox
                    // height: vscale(97)
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: companyBox.bottom
                    anchors.topMargin: vscale(20)
                    // anchors.topMargin: vscale(10)
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: bankText
                        height: vscale(23)
                        color: "#2e3f51"
                        text: qsTr("Bank")
                        elide: Text.ElideRight
                        font.family: appFont3.name
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: tscale(18)
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.Bold
                        // minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: hscale(33)
                        z:2
                    }

                    LeftPanelCustomList {
                        id: bankList
                        // height: vscale(61)
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: bankText.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                        anchors.topMargin: vscale(8)
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex:0
                        scaleFactorWidth: window.scaleFactorWidth
                        scaleFactorHeight: window.scaleFactorHeight
                        selected: ''
                        data: backend.bankDict
                        z:1
                        onSelectedChanged: {
                            backend.bankChanged(selected, selectedName)
                        }
                    }
                }
                Rectangle {
                    id: yearBox
                    height: vscale(190)
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: bankBox.bottom
                    // anchors.topMargin: vscale(15)
                    anchors.topMargin: vscale(26)
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0
                    
                    Text {
                        id: yearText
                        height: vscale(23)
                        color: "#2e3f51"
                        text: qsTr("Year")
                        elide: Text.ElideRight
                        font.family: appFont3.name
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: tscale(18)
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.Bold
                        // minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: hscale(33)
                        z:1
                    }

                    LeftPanelCustomList {
                        id: yearList
                        // height: vscale(170)
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: yearText.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: vscale(24)
                        anchors.topMargin: vscale(8)
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex:2
                        scaleFactorWidth: window.scaleFactorWidth
                        scaleFactorHeight: window.scaleFactorHeight
                        z:2
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
                    anchors.topMargin: vscale(20)
                    // anchors.topMargin: vscale(10)
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: monthText
                        height: vscale(23)
                        color: "#2e3f51"
                        text: qsTr("Month")
                        elide: Text.ElideRight
                        font.family: appFont3.name
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: tscale(18)
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.Bold
                        // minimumPointSize: 18
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: hscale(33)
                        z:2
                    }

                    LeftPanelCustomList {
                        id: monthList
                        visible: true
                        scaleFactorWidth: window.scaleFactorWidth
                        scaleFactorHeight: window.scaleFactorHeight
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: monthText.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                        anchors.topMargin: vscale(8)
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        //                        currentIndex:2
                        z:1
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
                anchors.leftMargin: hscale(5)
                anchors.bottomMargin: 0
                anchors.topMargin: 0
                anchors.rightMargin: 0

                ToastManager {
                    id: toast
                    scaleFactorWidth: window.scaleFactorWidth
                    scaleFactorHeight: window.scaleFactorHeight
                }
                BusyIndicator{
                    id: mainScreenBusyIndicator
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    running: true
                    z:12
                }

                Rectangle {
                    id: bodyHeaderBox
                    height: vscale(126)
                    color: "#ffffff"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    z: 2
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0
                    anchors.topMargin: 0

                    Rectangle {
                        id: bodyTitleContainer
                        height: vscale(45)
                        color: "#ffffff"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        anchors.topMargin: vscale(18)

                        MenuButton {
                            id: burgerButton2
                            width: 0
                            visible: true
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.leftMargin: hscale(15)
                            anchors.topMargin: vscale(4)
                            scaleFactorWidth: window.scaleFactorWidth
                            scaleFactorHeight: window.scaleFactorHeight
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
                            anchors.leftMargin: hscale(35)
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            font.family: appFont3.name
                            color: "#324254"
                            font.pixelSize: tscale(26)
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
                            anchors.leftMargin: hscale(45)
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            font.family: "PT Sans Caption"
                            color: "#324254"
                            font.pixelSize: tscale(26)
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
                            anchors.leftMargin: hscale(45)
                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            font.family: "PT Sans Caption"
                            color: "#324254"
                            font.pixelSize: tscale(26)
                            //                            font.weight: Font.Bold
                        }
                    }

                    Rectangle {
                        id: bodySubtitleContainer
                        height: vscale(38)
                        color: "#ffffff"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: bodyTitleContainer.bottom
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        anchors.topMargin: vscale(25)

                        CustomSearchBar {
                            id: textInput
                            // width: 277
                            //                            height: 38
                            anchors.left: parent.left
                            anchors.top: parent.top
                            //                            anchors.bottom: parent.bottom
                            anchors.leftMargin: hscale(42)
                            //                            anchors.bottomMargin: 0
                            anchors.topMargin: 0
                            searchbyMode: "off"
                            startDateCalendar: backend.startDateCalendar
                            endDateCalendar: backend.endDateCalendar
                            scaleFactorWidth: window.scaleFactorWidth
                            scaleFactorHeight: window.scaleFactorHeight
                            onSearchBarTextChanged: backend.search(textInput.searchBarText, textInput.searchbyMode)
                            onSearchbyModeChanged: backend.search(textInput.searchBarText, textInput.searchbyMode)
                        }
                        //                         CustomDatePicker2{
                        //                             visible: true
                        //                             anchors.right: textInput.right
                        //                             anchors.top: textInput.bottom
                        //                                 anchors.rightMargin: 0
                        //                                 anchors.topMargin: 4
                        // //                                z: 100
                        //                         }
                        
                        CustomSubTitleButton {
                            id: uploadBtn
                            width: hscale(177)
                            anchors.left: textInput.right
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            anchors.leftMargin: hscale(23)
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
                            //                        anchors.bottom: parent.bottom
                            anchors.leftMargin: hscale(23)
                            //                        anchors.bottomMargin: 0
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
                                //                                width: hscale(90)
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.leftMargin: hscale(23)
                                anchors.bottomMargin: 0
                                anchors.topMargin: 0
                                text: qsTr("By Date")
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                                onClicked: if(byDateBtn.selected){
                                               textInput.searchbyMode = "bydate"
                                               byChqNoBtn.selected = false
                                               byChqAmtBtn.selected = false
                                           }
                                           else { textInput.searchbyMode = "off" }
                            }
                            CustomSubTitleButton {
                                id: byChqAmtBtn
                                // width: hscale(177)
                                anchors.left: byDateBtn.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.leftMargin: hscale(23)
                                anchors.bottomMargin: 0
                                anchors.topMargin: 0
                                text: qsTr("By Cheque Amount")
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                                onClicked: if(byChqAmtBtn.selected){
                                               textInput.searchbyMode = "bychqamt"
                                               byChqNoBtn.selected = false
                                               byDateBtn.selected = false
                                           }
                                           else { textInput.searchbyMode = "off" }
                            }
                            CustomSubTitleButton {
                                id: byChqNoBtn
                                // width: hscale(177)
                                anchors.left: byChqAmtBtn.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.leftMargin: hscale(23)
                                anchors.bottomMargin: 0
                                anchors.topMargin: 0
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                                text: qsTr("By Cheque Number")
                                //selected: true
                                onClicked: if(byChqNoBtn.selected){
                                               textInput.searchbyMode = "bychqno"
                                               byChqAmtBtn.selected = false
                                               byDateBtn.selected = false
                                           }
                                           else { textInput.searchbyMode = "off" }
                            }
                            CustomSubTitleButton {
                                id: debitIndicator
                                //                                width: hscale(120)
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.rightMargin: hscale(69)
                                anchors.bottomMargin: 0
                                anchors.topMargin: 0
                                text: backend.debitBal
                                enabled: false
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                            CustomSubTitleButton {
                                id: creditIndicator
                                //                                width: hscale(120)
                                anchors.right: debitIndicator.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                anchors.rightMargin: hscale(23)
                                anchors.bottomMargin: 0
                                anchors.topMargin: 0
                                text: backend.creditBal
                                enabled: false
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                        }

                    }
                }
                Rectangle {
                    id: bodyBodyBox
                    width: hscale(200)
                    height: vscale(200)
                    //                    visible: false
                    color: "#ffffff"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: bodyHeaderBox.bottom
                    anchors.bottom: parent.bottom
                    anchors.rightMargin: hscale(29)
                    anchors.leftMargin: hscale(29)
                    anchors.bottomMargin: vscale(29)
                    anchors.topMargin: vscale(29)
                    StackView {
                        id: stackView
                        anchors.fill: parent
                        initialItem: selectOptionsComponent
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                        z:0
                    }
                    Component {
                        id: tableComponent
                        CustomTableView2{
                            tableData: backend.tableData
                            anchors.fill: parent
                            columns: backend.header
                            selectedRows : backend.selectedRows
                            scaleFactorWidth: window.scaleFactorWidth
                            scaleFactorHeight: window.scaleFactorHeight
                            onSelectedRowsChanged: backend.selectedRowsChanged(selectedRows)
                        }
                    }
                    Component {
                        id: uploadStatementComponent
                        UploadChequeStatementPage {
                            anchors.top: parent.top
                            anchors.topMargin: vscale(59)
                            scaleFactorWidth: window.scaleFactorWidth
                            scaleFactorHeight: window.scaleFactorHeight
                        }
                    }
                    Component {
                        id: chequeReportFoundComponent
                        ChequeReportFoundPage {
                            timeData: window.chequeTimeData
                            anchors.top: parent.top
                            anchors.topMargin: vscale(59)
                            scaleFactorWidth: window.scaleFactorWidth
                            scaleFactorHeight: window.scaleFactorHeight
                        }
                    }
                    Component {
                        id: chequeReportNotFoundComponent
                        ChequeReportNotFoundPage {
                            anchors.top: parent.top
                            anchors.topMargin: vscale(59)
                            scaleFactorWidth: window.scaleFactorWidth
                            scaleFactorHeight: window.scaleFactorHeight
                        }
                    }
                    Component {
                        id: tallyExportBoxComponent
                        TallyExportBoxPage {
                            anchors.top: parent.top
                            anchors.topMargin: vscale(59)
                            scaleFactorWidth: window.scaleFactorWidth
                            scaleFactorHeight: window.scaleFactorHeight
                           
                            onCreateMasterXMLBtnClicked: {
                            // backend.createIntermediateDaybook(fullScreenLoading2.daybookFileURL, fullScreenLoading2.fromDate, fullScreenLoading2.toDate, fullScreenLoading2.company)
                            }
                            onDownloadMasterXMLBtnClicked: {
                            }
                        }
                    }
                    Component {
                        id: selectOptionsComponent
                        OptionsNotSelectedPage {
                            anchors.top: parent.top
                            anchors.topMargin: vscale(59)
                            scaleFactorWidth: window.scaleFactorWidth
                            scaleFactorHeight: window.scaleFactorHeight
                        }
                    }
                }
            }
        }

        Rectangle {
            id: footerBox
            //            height: 110
            implicitHeight: vscale(101)
            //            height: Math.min( parent.height*.12, implicitHeight)
            height: vscale(101)
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
                font.pixelSize: tscale(26)
                horizontalAlignment: Text.AlignHCenter
                //                verticalAlignment: Text.AlignVCenter
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
                font.pixelSize: tscale(14)
                verticalAlignment: Text.AlignVCenter
                anchors.bottomMargin: vscale(13)
                anchors.leftMargin: hscale(214)
            }
        }

    }


}











/*##^##
Designer {
    D{i:0;formeditorZoom:0.5}D{i:36}
}
##^##*/
