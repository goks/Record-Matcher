import QtQuick 6.5
import QtQuick.Window
import QtQuick.Controls 6.5
// QtGraphicalEffects is deprecated in Qt 6 - effects disabled for now
// TODO: Migrate to Qt6.5.Effects or Qt Multimediate Effects
// import QtQuick.Effects
import QtQuick.Dialogs


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
    // Qt6: FontLoader 'name' property is now read-only, use 'source' only
    FontLoader { id: appFont; source: "../fonts/PTSansCaption-Regular.ttf" }
    FontLoader { id: appFont2; source: "../fonts/Monoton-Regular.ttf" }
    FontLoader { id: appFont3; source: "../fonts/PTSansCaption-Bold.ttf" }
    FontLoader { id: appFont4; source: "../fonts/Sen-Regular.ttf" }
    property string chequeTimeData: ""
    property string currentScreenKey: "selectOptions"
    property string previousScreenKey: "selectOptions"
    property string pendingSearchText: ""
    property string pendingSearchMode: "off"
    property string lastSearchText: "__INIT__"
    property string lastSearchMode: "__INIT__"

    function componentForScreen(screenKey) {
        switch (screenKey) {
        case "table": return tableComponent
        case "upload": return uploadStatementComponent
        case "chequeFound": return chequeReportFoundComponent
        case "chequeNotFound": return chequeReportNotFoundComponent
        case "tallyExport": return tallyExportBoxComponent
        case "settings": return settingsPageComponent
        default: return selectOptionsComponent
        }
    }

    function navigateTo(screenKey) {
        var component = componentForScreen(screenKey)
        if (!component) return
        if (currentScreenKey === screenKey && stackView.currentItem) return
        if (screenKey === "settings") {
            previousScreenKey = currentScreenKey
        }
        if (stackView.depth <= 0) {
            stackView.push(component)
        } else {
            stackView.replace(component)
        }
        currentScreenKey = screenKey
    }

    function closeSettingsPage() {
        navigateTo(previousScreenKey || "selectOptions")
    }

    Timer {
        id: searchDebounceTimer
        interval: 250
        repeat: false
        onTriggered: {
            if (!backend || window.currentScreenKey !== "table") {
                return
            }
            if (window.pendingSearchText === window.lastSearchText &&
                    window.pendingSearchMode === window.lastSearchMode) {
                return
            }
            window.lastSearchText = window.pendingSearchText
            window.lastSearchMode = window.pendingSearchMode
            backend.search(window.pendingSearchText, window.pendingSearchMode)
        }
    }

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
            progressBarValue: backend ? backend.progressBarValue : 0
            text1: backend ? backend.fullScreenLoadingInfo1 : ""
            text2: backend ? backend.fullScreenLoadingInfo2 : ""
        }
        LoadingOverlay2{
            id: fullScreenLoading2
            visible: false
            z:15
            scaleFactorWidth: window.scaleFactorWidth
            scaleFactorHeight: window.scaleFactorHeight
            progressBarValue: backend ? backend.progressBarValue : 0
            text1: backend ? backend.fullScreenLoadingInfo1 : ""
            text2: backend ? backend.fullScreenLoadingInfo2 : ""
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
        
        // Firebase sync progress overlay
        SyncProgressOverlay {
            id: syncProgressOverlay
            scaleFactorWidth: window.scaleFactorWidth
            scaleFactorHeight: window.scaleFactorHeight
            
            onCancelRequested: {
                backend.cancelSync()
            }
            onCompleted: {
                // Optionally refresh data after sync
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
            password: backend ? backend.adminPassword : ""
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
                // TODO Qt6: DropShadow moved to different module
                // layer.enabled: true
                // layer.effect: // TODO Qt6: DropShadow disabled
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
                    text: qsTr("Reconcile")
                    anchors.left: tallyexport_button.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    leftPadding: 0
                    anchors.leftMargin: 1
                    anchors.bottomMargin: 0
                    anchors.topMargin: 0
                    enabled: !(mainScreenBusyIndicator.running || busyIndicator.visible || fullScreenLoading.visible || fullScreenLoading2.visible || syncProgressOverlay.visible)
                    onPressed: {
                        if (!help_button.enabled) return
                        if (backend) backend.runReconciliation()
                    }
                }
            }
            SettingsButton {
                id: settingsBtn
                width: tscale(48)
                height: width
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                z: 10
                anchors.rightMargin: hscale(20)
                scaleFactorWidth: window.scaleFactorWidth
                scaleFactorHeight: window.scaleFactorHeight
                btnIconSource: Qt.resolvedUrl("../images/svg_images/settings_gear.svg")
                // onConvertSchemaClicked: backend.convertSchema()
                onDeleteButtonClicked: backend.delete_table()
                onDownloadFromDbClicked: backend.downloadfromDb()
                onUploadtoDbClicked:{
                                    passwordPopup.open()
                                    }
                onCreateTallyXMLFromDaybookClicked: backend.createTallyXMLFromDaybook()
                onOpenSettingsClicked: backend.openSettingsPage()
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
                                navigateTo("chequeFound")
                            }
                            else if(status===0) navigateTo("chequeNotFound")
                            else {
                                navigateTo("selectOptions")
                                toast.show("No company or year selected", "warning")
                            }
                        }
                        else{
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
                            navigateTo("selectOptions")
                        }
                    }
                    function onShowChequeReportPage(status, time){
                        if(status===1) {
                            window.chequeTimeData = time
                            navigateTo("chequeFound")
                        }
                        else if(status===0) navigateTo("chequeNotFound")
                        else navigateTo("selectOptions")
                    }
                    function onTallyExportButtonClicked(selected){
                        if(selected){
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
                            navigateTo("tallyExport")
                            // else {
                            //     stackView.clear()
                            //     toast.show("No company or year selected", "warning")
                            // }
                        }
                        else{
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
                            bodySubtitleContainer.height = vscale(52)
                            bodyHeaderBox.height = bodyTitleContainer.height + bodySubtitleContainer.height + vscale(12) + vscale(8) + vscale(10)
                            navigateTo("selectOptions")

                        }
                    }
                    function onShowTallyExportPage(){
                        navigateTo("tallyExport")
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
                        // Ensure header and subtitle containers are visible when showing the table
                        bodySubtitleContainer.visible = true
                        bodySubtitleContainer.height = vscale(52)
                        bodyHeaderBox.height = bodyTitleContainer.height + bodySubtitleContainer.height + vscale(12) + vscale(8) + vscale(10)
                        navigateTo("table")
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
                        navigateTo("upload")
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
                        navigateTo("selectOptions")

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
                    function onErpBankMappingSaved(message) {
                        toast.show(message, "success")
                    }
                    function onErpBankMappingSaveFailed(error) {
                        toast.show("Failed to save ERP mapping: " + error, "error")
                    }
                    function onReconciliationSuccess(outputPath) {
                        toast.show(outputPath, "success")
                    }
                    function onReconciliationFailed(error) {
                        toast.show("Reconciliation failed: " + error, "error")
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
                        if (backend && backend.fullScreenLoadingInfo1 !== "") {
                            fullScreenLoading.visible = true
                        }
                    }
                    function onHideMainScreenLoadingIndicator() {
                        mainScreenBusyIndicator.running = false
                        fullScreenLoading.visible = false
                    }
                    
                    // Firebase sync handlers (new repository-based)
                    function onSyncProgressUpdated(current, total, itemName, status) {
                        syncProgressOverlay.updateProgress(current, total, itemName, status)
                    }
                    function onSyncCompleted(success, message) {
                        if (success) {
                            syncProgressOverlay.updateProgress(1, 1, message, "completed")
                            toast.show(message, "success")
                        } else {
                            syncProgressOverlay.updateProgress(1, 1, message, "error")
                            toast.show(message, "error")
                        }
                    }
                    function onShowSettingsPage() {
                        // Hide left panel elements for full-page settings view
                        bodySubtitleStatementModeContainer.visible = false
                        chequereport_button.selected = false
                        export_button.selected = false
                        tallyexport_button.selected = false
                        help_button.selected = false
                        uploadBtn.visible = false
                        navigateTo("settings")
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
                    height: vscale(32)
                    text: qsTr("Options")
                    elide: Text.ElideRight
                    color: "#324254"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    font.family: appFont3.name
                    font.pixelSize: tscale(20)
                    font.weight: Font.Bold
                    verticalAlignment: Text.AlignVCenter
                    anchors.rightMargin: hscale(20)
                    anchors.leftMargin: hscale(16)
                    anchors.topMargin: vscale(10)
                }

                Rectangle {
                    id: companyBox
                    height: vscale(120)
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: optionsText.bottom
                    anchors.topMargin: vscale(10)
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: companyText
                        height: vscale(22)
                        color: "#475569"
                        text: qsTr("Company")
                        elide: Text.ElideRight
                        font.family: appFont3.name
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: tscale(15)
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.DemiBold
                        textFormat: Text.PlainText
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: hscale(16)
                        z:2
                    }
                    
                    // Section divider
                    Rectangle {
                        id: companyDivider
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: companyText.bottom
                        anchors.leftMargin: hscale(16)
                        anchors.rightMargin: hscale(12)
                        anchors.topMargin: vscale(4)
                        height: 1
                        color: "#e2e8f0"
                    }

                    LeftPanelCustomList {
                        id: companyList
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: companyDivider.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                        anchors.topMargin: vscale(6)
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex: -1
                        selected: ''
                        scaleFactorWidth: window.scaleFactorWidth
                        scaleFactorHeight: window.scaleFactorHeight
                        data: backend ? backend.companyDict : []
                        z:1
                        onSelectedChanged: {
                            if (backend) backend.companyChanged(selected, selectedName)
                        }
                    }
                }

                Rectangle {
                    id: bankBox
                    height: vscale(85)
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: companyBox.bottom
                    anchors.topMargin: vscale(6)
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: bankText
                        height: vscale(22)
                        color: "#475569"
                        text: qsTr("Bank")
                        elide: Text.ElideRight
                        font.family: appFont3.name
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: tscale(15)
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.DemiBold
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: hscale(16)
                        z:2
                    }
                    
                    // Section divider
                    Rectangle {
                        id: bankDivider
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: bankText.bottom
                        anchors.leftMargin: hscale(16)
                        anchors.rightMargin: hscale(12)
                        anchors.topMargin: vscale(4)
                        height: 1
                        color: "#e2e8f0"
                    }

                    LeftPanelCustomList {
                        id: bankList
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: bankDivider.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 0
                        anchors.topMargin: vscale(6)
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex: -1
                        scaleFactorWidth: window.scaleFactorWidth
                        scaleFactorHeight: window.scaleFactorHeight
                        selected: ''
                        data: backend ? backend.bankDict : []
                        z:1
                        onSelectedChanged: {
                            if (backend) backend.bankChanged(selected, selectedName)
                        }
                    }
                }
                Rectangle {
                    id: yearBox
                    height: Math.min(vscale(220), yearList.contentHeight + vscale(30))
                    color: "#00000000"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: bankBox.bottom
                    anchors.topMargin: vscale(10)
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0
                    
                    Text {
                        id: yearText
                        height: vscale(22)
                        color: "#475569"
                        text: qsTr("Year")
                        elide: Text.ElideRight
                        font.family: appFont3.name
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: tscale(15)
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.DemiBold
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: hscale(16)
                        z:1
                    }
                    
                    // Section divider
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: yearText.bottom
                        anchors.leftMargin: hscale(16)
                        anchors.rightMargin: hscale(12)
                        anchors.topMargin: vscale(3)
                        height: 1
                        color: "#e2e8f0"
                    }

                    LeftPanelCustomList {
                        id: yearList
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: yearText.bottom
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: vscale(4)
                        anchors.topMargin: vscale(6)
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex: -1
                        scaleFactorWidth: window.scaleFactorWidth
                        scaleFactorHeight: window.scaleFactorHeight
                        z:2
                        onSelectedChanged: {
                            if (backend) backend.yearChanged(selected)
                        }
                        data: backend ? backend.yearDict : []
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
                    anchors.topMargin: vscale(10)
                    anchors.bottomMargin: vscale(8)
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0

                    Text {
                        id: monthText
                        height: vscale(22)
                        color: "#475569"
                        text: qsTr("Month")
                        elide: Text.ElideRight
                        font.family: appFont3.name
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        font.pixelSize: tscale(15)
                        verticalAlignment: Text.AlignBottom
                        font.weight: Font.DemiBold
                        anchors.topMargin: 0
                        anchors.rightMargin: 0
                        anchors.leftMargin: hscale(16)
                        z:2
                    }
                    
                    // Section divider
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: monthText.bottom
                        anchors.leftMargin: hscale(16)
                        anchors.rightMargin: hscale(12)
                        anchors.topMargin: vscale(3)
                        height: 1
                        color: "#e2e8f0"
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
                        anchors.topMargin: vscale(6)
                        anchors.rightMargin: 0
                        anchors.leftMargin: 0
                        currentIndex: -1
                        z:1
                        onSelectedChanged: {
                            if (backend) backend.monthChanged(selected, selectedName)
                        }
                        data: backend ? backend.monthDict : []
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
                    running: false
                    visible: running
                    width: hscale(40)
                    height: vscale(40)
                    palette.dark: "#003366"
                    palette.mid: "#003366"
                    palette.highlight: "#003366"
                    z:12
                    contentItem: Item {
                        implicitWidth: mainScreenBusyIndicator.width
                        implicitHeight: mainScreenBusyIndicator.height
                        RotationAnimator on rotation {
                            running: mainScreenBusyIndicator.running
                            loops: Animation.Infinite
                            duration: 900
                            from: 0
                            to: 360
                        }
                        Repeater {
                            model: 10
                            Item {
                                width: parent.width
                                height: parent.height
                                rotation: index * 36
                                transformOrigin: Item.Center
                                Rectangle {
                                    width: Math.max(2, hscale(4))
                                    height: Math.max(6, vscale(8))
                                    radius: width / 2
                                    color: "#003366"
                                    antialiasing: true
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    y: 2
                                    opacity: (index + 1) / 10
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    id: bodyHeaderBox
                    // Dynamic height based on content
                    height: bodyTitleContainer.height + bodySubtitleContainer.height + vscale(12) + vscale(8) + vscale(10)
                    color: "#ffffff"
                    clip: false
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    z: 10
                    anchors.rightMargin: 0
                    anchors.leftMargin: 0
                    anchors.topMargin: 0
                    
                    // Bottom border for visual separation
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: "#e2e8f0"
                        z: 3
                    }

                    Rectangle {
                        id: bodyTitleContainer
                        readonly property bool hasTableData: backend && backend.tableData && backend.tableData.length > 0
                        height: vscale(44)
                        color: "#ffffff"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.rightMargin: hscale(20)
                        anchors.leftMargin: hscale(35)
                        anchors.topMargin: vscale(12)

                        MenuButton {
                            id: burgerButton2
                            width: 0
                            visible: true
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.leftMargin: 0
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
                        
                        // Month/Year chip - uniform style
                        Rectangle {
                            id: monthYearChip
                            width: Math.max(hscale(74), monthYearContent.width + hscale(16))
                            height: vscale(32)
                            radius: hscale(6)
                            color: "#eff6ff"
                            border.color: "#bfdbfe"
                            border.width: 1
                            visible: backend
                            anchors.left: burgerButton2.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: 0
                            
                            Row {
                                id: monthYearContent
                                anchors.centerIn: parent
                                spacing: hscale(6)
                                
                                Rectangle {
                                    width: hscale(20)
                                    height: hscale(20)
                                    radius: hscale(4)
                                    color: "#3b82f6"
                                    anchors.verticalCenter: parent.verticalCenter
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: "M"
                                        font.pixelSize: hscale(11)
                                        font.weight: Font.Bold
                                        color: "#ffffff"
                                    }
                                }
                                
                                Text {
                                    id: monthYearLabel
                                    text: backend ? backend.monthYearData : ""
                                    anchors.verticalCenter: parent.verticalCenter
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: tscale(13)
                                    font.weight: Font.DemiBold
                                    color: "#1e40af"
                                }
                            }
                        }
                        
                        // Company chip - uniform style
                        Rectangle {
                            id: companyChip
                            width: Math.max(hscale(74), companyChipContent.width + hscale(16))
                            height: vscale(32)
                            radius: hscale(6)
                            color: "#eff6ff"
                            border.color: "#bfdbfe"
                            border.width: 1
                            visible: backend
                            anchors.left: monthYearChip.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: hscale(10)
                            
                            Row {
                                id: companyChipContent
                                anchors.centerIn: parent
                                spacing: hscale(6)
                                
                                Rectangle {
                                    width: hscale(20)
                                    height: hscale(20)
                                    radius: hscale(4)
                                    color: "#3b82f6"
                                    anchors.verticalCenter: parent.verticalCenter
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: "C"
                                        font.pixelSize: hscale(11)
                                        font.weight: Font.Bold
                                        color: "#ffffff"
                                    }
                                }
                                
                                Text {
                                    id: companyChipLabel
                                    text: backend ? backend.companyData : ""
                                    anchors.verticalCenter: parent.verticalCenter
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: tscale(13)
                                    font.weight: Font.DemiBold
                                    color: "#1e40af"
                                }
                            }
                        }
                        
                        // Bank chip - uniform style
                        Rectangle {
                            id: bankChip
                            width: Math.max(hscale(74), bankChipContent.width + hscale(16))
                            height: vscale(32)
                            radius: hscale(6)
                            color: "#eff6ff"
                            border.color: "#bfdbfe"
                            border.width: 1
                            visible: backend
                            anchors.left: companyChip.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: hscale(10)
                            
                            Row {
                                id: bankChipContent
                                anchors.centerIn: parent
                                spacing: hscale(6)
                                
                                Rectangle {
                                    width: hscale(20)
                                    height: hscale(20)
                                    radius: hscale(4)
                                    color: "#3b82f6"
                                    anchors.verticalCenter: parent.verticalCenter
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: "B"
                                        font.pixelSize: hscale(11)
                                        font.weight: Font.Bold
                                        color: "#ffffff"
                                    }
                                }
                                
                                Text {
                                    id: bankChipLabel
                                    text: backend ? backend.bankData : ""
                                    anchors.verticalCenter: parent.verticalCenter
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: tscale(13)
                                    font.weight: Font.DemiBold
                                    color: "#1e40af"
                                }
                            }
                        }
                        
                        // Keep old labels hidden for compatibility
                        Label {
                            id: companyLabel
                            visible: false
                            text: backend ? backend.companyData : ""
                        }
                        Label {
                            id: bankLabel
                            visible: false
                            text: backend ? backend.bankData : ""
                        }
                    }

                    Rectangle {
                        id: bodySubtitleContainer
                        readonly property bool reconciliationInProgress: backend && backend.fullScreenLoadingInfo2 !== ""
                        height: reconciliationInProgress ? vscale(84) : vscale(52)
                        color: "#ffffff"
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: bodyTitleContainer.bottom
                        anchors.rightMargin: hscale(20)
                        anchors.leftMargin: hscale(35)
                        anchors.topMargin: vscale(8)
                        
                        // Search bar with rounded background
                        Rectangle {
                            id: searchContainer
                            width: hscale(240)
                            height: vscale(40)
                            radius: hscale(8)
                            color: "#f8fafc"
                            border.color: "#e2e8f0"
                            border.width: 1
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            
                            CustomSearchBar {
                                id: textInput
                                anchors.fill: parent
                                anchors.margins: 2
                                searchbyMode: "off"
                                startDateCalendar: backend ? backend.startDateCalendar : null
                                endDateCalendar: backend ? backend.endDateCalendar : null
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                                onSearchBarTextChanged: {
                                    window.pendingSearchText = textInput.searchBarText
                                    window.pendingSearchMode = textInput.searchbyMode
                                    searchDebounceTimer.restart()
                                }
                                onSearchbyModeChanged: {
                                    window.pendingSearchText = textInput.searchBarText
                                    window.pendingSearchMode = textInput.searchbyMode
                                    searchDebounceTimer.restart()
                                }
                            }
                        }
                        
                        // Filter buttons in the center
                        Row {
                            id: filterButtonsRow
                            anchors.left: searchContainer.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: hscale(20)
                            spacing: hscale(10)
                            visible: bodySubtitleStatementModeContainer.visible
                            
                            CustomSubTitleButton {
                                id: byDateBtn
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
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                                text: qsTr("By Cheque Number")
                                onClicked: if(byChqNoBtn.selected){
                                               textInput.searchbyMode = "bychqno"
                                               byChqAmtBtn.selected = false
                                               byDateBtn.selected = false
                                           }
                                           else { textInput.searchbyMode = "off" }
                            }
                        }
                        
                        // Upload button (hidden by default)
                        CustomSubTitleButton {
                            id: uploadBtn
                            width: hscale(100)
                            anchors.left: searchContainer.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: hscale(20)
                            text: qsTr("Import")
                            selected: true
                            visible: false
                            enabled: !(mainScreenBusyIndicator.running || busyIndicator.visible || syncProgressOverlay.visible)
                            opacity: enabled ? 1.0 : 0.6
                            onClicked : {
                                if (!uploadBtn.enabled) return
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
                        Rectangle {
                            id: busyIndicatorBg
                            anchors.left: uploadBtn.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: hscale(12)
                            width: hscale(34)
                            height: vscale(34)
                            radius: hscale(17)
                            color: "#dbeafe"
                            border.color: "#003366"
                            border.width: 1
                            visible: busyIndicator.visible
                        }
                        BusyIndicator {
                            id: busyIndicator
                            anchors.centerIn: busyIndicatorBg
                            width: hscale(22)
                            height: vscale(22)
                            visible: false
                            running: visible
                            palette.dark: "#003366"
                            palette.mid: "#003366"
                            palette.highlight: "#003366"

                            contentItem: Item {
                                implicitWidth: busyIndicator.width
                                implicitHeight: busyIndicator.height
                                RotationAnimator on rotation {
                                    running: busyIndicator.running
                                    loops: Animation.Infinite
                                    duration: 900
                                    from: 0
                                    to: 360
                                }

                                Repeater {
                                    model: 10
                                    Item {
                                        width: parent.width
                                        height: parent.height
                                        rotation: index * 36
                                        transformOrigin: Item.Center
                                        Rectangle {
                                            width: Math.max(2, hscale(3))
                                            height: Math.max(5, vscale(7))
                                            radius: width / 2
                                            color: "#003366"
                                            antialiasing: true
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            y: 1
                                            opacity: (index + 1) / 10
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Balance indicators on the right
                        Row {
                            id: balanceIndicatorsRow
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.rightMargin: 0
                            spacing: hscale(10)
                            
                            // Credit balance pill
                            Rectangle {
                                width: creditContent.width + hscale(20)
                                height: vscale(36)
                                radius: hscale(8)
                                color: "#ecfdf5"
                                border.color: "#a7f3d0"
                                border.width: 1
                                visible: backend && backend.tableData && backend.tableData.length > 0 && backend.creditBal !== ""
                                
                                Row {
                                    id: creditContent
                                    anchors.centerIn: parent
                                    spacing: hscale(6)
                                    
                                    Rectangle {
                                        width: hscale(8)
                                        height: hscale(8)
                                        radius: hscale(4)
                                        color: "#10b981"
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    
                                    Text {
                                        id: creditText
                                        text: backend ? backend.creditBal : ""
                                        anchors.verticalCenter: parent.verticalCenter
                                        font.family: "PT Sans Caption"
                                        font.pixelSize: tscale(13)
                                        font.weight: Font.DemiBold
                                        color: "#047857"
                                    }
                                }
                            }
                            
                            // Debit balance pill
                            Rectangle {
                                width: debitContent.width + hscale(20)
                                height: vscale(36)
                                radius: hscale(8)
                                color: "#fef2f2"
                                border.color: "#fecaca"
                                border.width: 1
                                visible: backend && backend.tableData && backend.tableData.length > 0 && backend.debitBal !== ""
                                
                                Row {
                                    id: debitContent
                                    anchors.centerIn: parent
                                    spacing: hscale(6)
                                    
                                    Rectangle {
                                        width: hscale(8)
                                        height: hscale(8)
                                        radius: hscale(4)
                                        color: "#ef4444"
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                    
                                    Text {
                                        id: debitText
                                        text: backend ? backend.debitBal : ""
                                        anchors.verticalCenter: parent.verticalCenter
                                        font.family: "PT Sans Caption"
                                        font.pixelSize: tscale(13)
                                        font.weight: Font.DemiBold
                                        color: "#dc2626"
                                    }
                                }
                            }
                        }
                        
                        // Hidden container for backward compatibility
                        Item {
                            id: bodySubtitleStatementModeContainer
                            visible: true
                            width: 0
                            height: 0
                            
                            // Legacy indicators (hidden, for compatibility)
                            CustomSubTitleButton {
                                id: debitIndicator
                                visible: false
                                text: backend ? backend.debitBal : ""
                                enabled: false
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                            CustomSubTitleButton {
                                id: creditIndicator
                                visible: false
                                text: backend ? backend.creditBal : ""
                                enabled: false
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                        }

                        Rectangle {
                            id: reconciliationProgressContainer
                            visible: bodySubtitleContainer.reconciliationInProgress
                            color: "#f8fafc"
                            border.color: "#dbeafe"
                            border.width: 1
                            radius: hscale(8)
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            anchors.leftMargin: 0
                            anchors.rightMargin: 0
                            anchors.bottomMargin: 0
                            height: vscale(30)

                            Row {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.leftMargin: hscale(10)
                                anchors.rightMargin: hscale(10)
                                spacing: hscale(10)

                                ProgressBar {
                                    id: reconciliationProgressBar
                                    value: backend ? backend.progressBarValue : 0
                                    from: 0
                                    to: 1
                                    width: Math.max(hscale(180), parent.width - hscale(320))
                                    height: vscale(14)
                                }

                                Text {
                                    width: hscale(300)
                                    text: backend ? (backend.fullScreenLoadingInfo2 + " (" + Math.round(backend.progressBarValue * 100) + "%)") : ""
                                    elide: Text.ElideRight
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: tscale(11)
                                    color: "#1e3a8a"
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }

                    }
                }
                Rectangle {
                    id: bodyBodyBox
                    // Allow anchors to control size so StackView and contents can expand
                    //                    visible: false
                    color: "#ffffff"
                    clip: true
                    z: 1
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
                        z:0
                    }
                    Component {
                        id: tableComponent
                        Item {
                            anchors.fill: parent
                            CustomTableView2{
                                id: customTable
                                tableData: backend ? backend.tableData : []
                                anchors.fill: parent
                                columns: backend ? backend.header : []
                                selectedRows: backend ? backend.selectedRows : []
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                        }
                    }
                    Component {
                        id: uploadStatementComponent
                        Item {
                            anchors.fill: parent
                            UploadChequeStatementPage {
                                anchors.fill: parent
                                anchors.topMargin: vscale(59)
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                        }
                    }
                    Component {
                        id: chequeReportFoundComponent
                        Item {
                            anchors.fill: parent
                            ChequeReportFoundPage {
                                timeData: window.chequeTimeData
                                anchors.fill: parent
                                anchors.topMargin: vscale(59)
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                        }
                    }
                    Component {
                        id: chequeReportNotFoundComponent
                        Item {
                            anchors.fill: parent
                            ChequeReportNotFoundPage {
                                anchors.fill: parent
                                anchors.topMargin: vscale(59)
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                        }
                    }
                    Component {
                        id: tallyExportBoxComponent
                        Item {
                            anchors.fill: parent
                            TallyExportBoxPage {
                                anchors.fill: parent
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
                    }
                    Component {
                        id: selectOptionsComponent
                        Item {
                            anchors.fill: parent
                            OptionsNotSelectedPage {
                                anchors.fill: parent
                                anchors.topMargin: vscale(59)
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                            }
                        }
                    }
                    
                    // Settings page component
                    Component {
                        id: settingsPageComponent
                        Item {
                            anchors.fill: parent
                            SettingsPage {
                                anchors.fill: parent
                                scaleFactorWidth: window.scaleFactorWidth
                                scaleFactorHeight: window.scaleFactorHeight
                                lastUploadTime: backend ? backend.lastSyncUpload : "Never"
                                lastDownloadTime: backend ? backend.lastSyncDownload : "Never"
                                isSyncing: backend ? backend.isSyncing : false
                                
                                // Migration properties
                                migrationStatus: backend ? backend.migrationStatus : "checking"
                                migrationProgressText: backend ? backend.migrationProgressText : ""
                                migrationCurrent: backend ? backend.migrationCurrent : 0
                                migrationTotal: backend ? backend.migrationTotal : 0
                                pickleSnapshotCount: backend ? backend.pickleSnapshotCount : 0
                                pickleChequeCount: backend ? backend.pickleChequeCount : 0
                                databasePath: backend ? backend.databasePath : ""
                                totalSnapshotCount: backend ? backend.totalSnapshotCount : 0
                                totalChequeReportCount: backend ? backend.totalChequeReportCount : 0
                                erpBankMapping: backend ? backend.erpBankMapping : []
                                erpBankOptions: backend ? backend.erpBankOptions : ({})
                                reconciliationOutputEnabled: backend ? backend.reconciliationOutputEnabled : true
                                
                                onUploadRequested: {
                                    syncProgressOverlay.show("upload")
                                    backend.syncUploadToFirebase()
                                }
                                onDownloadRequested: {
                                    syncProgressOverlay.show("download")
                                    backend.syncDownloadFromFirebase()
                                }
                                onMigrationRequested: {
                                    backend.startMigration()
                                }
                                onErpBankMappingUpdated: {
                                    backend.updateErpBankMapping(company, bank, bankCode)
                                }
                                onSaveErpBankMappingRequested: {
                                    backend.saveErpBankMapping()
                                }
                                onReconciliationOutputToggleRequested: {
                                    backend.setReconciliationOutputEnabled(enabled)
                                }
                                onCloseRequested: {
                                    closeSettingsPage()
                                }
                            }
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
                // TODO Qt6: DropShadow disabled (Qt 5 GraphicalEffects deprecated)
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





