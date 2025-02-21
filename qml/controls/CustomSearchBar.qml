import QtQuick 2.15
import  "../controls"
import QtQuick.Controls 2.15
import QtQuick.Dialogs 1.3
import QtQuick.Controls 1.4 as OldControls
Rectangle {
    id: containerBox
    //    height: 38
    // height: 100
    color: "#f5f8fa"
    implicitHeight: vscale(38)
    radius: 8
    border.color: "#dee6ec"
    width: searchmode!="default"?hscale(920):hscale(277)
    property string placeholderText: searchmode!="default"?"File Path" :"Search"
    property string searchmode: "default"
    property string searchBarText: ""
    property string fileDialogText: ""
    property string textVal: searchmode==="default"?searchBarText:fileDialogText
    // searchbymode can be 'off' 'bychqno' 'bychqamt' 'bydate'
    property string searchbyMode: "bychqno"
    property bool calendarButPressed: true
    property date startDateCalendar : undefined
    property date endDateCalendar: undefined
    
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
    TextInput {
        id: searchInput
        color: "#324254"
        //        text: qsTr("Search")
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        font.family: "PT Sans Caption"
        font.pixelSize: tscale(16)
        verticalAlignment: Text.AlignVCenter
        clip: true
        anchors.topMargin: 0
        anchors.bottomMargin: 0
        anchors.leftMargin: hscale(15)
        anchors.rightMargin: hscale(15)
        text: containerBox.textVal
        property string changed_date:  ""
        property string previous_date: ""
        onTextChanged: if (searchmode==="default") {
                           searchBarText = searchInput.text
                           if (searchbyMode == "bydate" && previous_date!=searchBarText){
                               // changed_date = Date.fromLocaleString(Qt.locale(), "2018-10-25", "yyyy-mm-dd")
                               changed_date = Date.fromLocaleString(Qt.locale(), searchBarText, "dd/mm/yyyy")
                               if (!changed_date){ return }
                               console.log("Changing calendar to "+ changed_date )
                               previous_date = searchBarText
                               calendar.selectedDate = Date.fromLocaleString(Qt.locale(), searchBarText, "dd/MM/yyyy")
                           }
                       }
                       else {
                           fileDialogText = searchInput.text
                       }

        Text {
            id: placeholder
            text: containerBox.placeholderText
            anchors.fill: parent
            color: "#c4c4c4"
            visible: !searchInput.text
            verticalAlignment: Text.AlignVCenter
            clip: true
            font.family: "PT Sans Caption"
            font.pixelSize: tscale(16)
        }
        CustomSubTitleButton {
            id:browseBut
            // width: 174
            width: hscale(74)
            height: vscale(parent.height)-vscale(6)
            // anchors.topMargin: vscale(4)
            // anchors.bottomMargin: vscale(4)
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: hscale(18)
            visible: containerBox.searchmode!="default"?true:false
            fontSize: tscale(8)
            // visible: true
            text: "Browse"
            onClicked: fileDialog.open()
        }
        Button {
            id: calendarBut
            width: hscale(30)
            height: vscale(30)
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: 0
            visible: (searchmode==="default" && searchbyMode == "bydate")?true:false

            onPressedChanged: {
                if(calendarBut.down) {
                    calendarButPressed = calendarButPressed?false:true
                }
                console.log("calendarButPressed: " + calendarButPressed)
            }

            QtObject {
                id: internal
                property var dynamicColor: if(calendarButPressed){
                                               return "#c4c4c4"
                                           } else {
                                               calendarBut.hovered ? "#c4c4c4" : "#f5f8fa"
                                           }
            }
            background: Rectangle{
                color: internal.dynamicColor
                anchors.fill: parent
                radius: 5

                Image{
                    id:calendarImg
                    source: "../../images/svg_images/calendar-on.svg"
                    anchors.fill: parent
                    anchors.margins: 3
                }
            }
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
    CustomCalendar {
        id: calendar
        anchors.top: searchInput.bottom
        anchors.topMargin: vscale(4)
        anchors.rightMargin: 0
        anchors.left: searchInput.left
        anchors.right: parent.right
        visible: (searchmode==="default" && searchbyMode == "bydate" && calendarButPressed)?true:false
        minimumDate : startDateCalendar
        maximumDate : endDateCalendar
        scaleFactorWidth: window.scaleFactorWidth
        scaleFactorHeight: window.scaleFactorHeight

        onSelectedDateChanged: {
            if(searchbyMode == "bydate"){
                containerBox.searchBarText = Qt.formatDate(selectedDate,"dd/MM/yyyy")
            }
            const day = selectedDate.getDate();
            const month = selectedDate.getMonth() + 1;
            const year = selectedDate.getFullYear();
            console.log(day,month,year)
        }
    }
}









/*##^##
Designer {
    D{i:0;formeditorZoom:10}
}
##^##*/
