import QtQuick 2.0
import QtQuick.Controls 2.15
import QtQuick.Dialogs 1.3
import  "../controls"

Rectangle {
    id: container
    //    height: 38
    // height: 100
    color: "#f5f8fa"
    implicitHeight: 38
    radius: 8
    border.color: "#dee6ec"
    width: hscale(250)
    height: vscale(38)

    property bool calendarButPressed: false
    property string placeHolderText: "from Date"
    property string dateVal: "01/04/2020"

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

    TextInput {
        id: textInput
        color: "#324254"
        //        text: qsTr("Search")
        font.family: appFont4.name
        font.pixelSize: tscale(16)
        verticalAlignment: Text.AlignVCenter
        anchors.margins: 4
        clip: true
        text: container.dateVal
        anchors.fill: parent
        property string changed_date:  ""
        property string previous_date: ""
        onTextChanged: {
            container.dateVal = textInput.text
            if (previous_date!=container.dateVal){
                // changed_date = Date.fromLocaleString(Qt.locale(), "2018-10-25", "yyyy-mm-dd")
                changed_date = Date.fromLocaleString(Qt.locale(), container.dateVal, "dd/mm/yyyy")
                if (!changed_date){ return }
                console.log("Changing calendar to "+ changed_date )
                previous_date = container.dateVal
                calendar.selectedDate = Date.fromLocaleString(Qt.locale(), container.dateVal, "dd/MM/yyyy")
            }
        }

        Text {
            id: placeholder
            text: container.placeHolderText
            anchors.fill: parent
            color: "#c4c4c4"
            visible: !textInput.text
            verticalAlignment: Text.AlignVCenter
            clip: true
            font.family: appFont4.name
            font.pixelSize: tscale(16)
        }
        Button {
            id: calendarBut
            width: hscale(30)
            height: vscale(30)
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: hscale(6)
            visible: true

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
    }

    CustomCalendar {
        id: calendar
        anchors.top: textInput.bottom
        anchors.topMargin: vscale(4)
        anchors.rightMargin: 0
        anchors.left: textInput.left
        anchors.right: parent.right
        visible: calendarButPressed?true:false
        minimumDate : startDateCalendar
        maximumDate : endDateCalendar
        scaleFactorWidth: window.scaleFactorWidth
        scaleFactorHeight: window.scaleFactorHeight

        onSelectedDateChanged: {
            container.dateVal = Qt.formatDate(selectedDate,"dd/MM/yyyy")
            const day = selectedDate.getDate();
            const month = selectedDate.getMonth() + 1;
            const year = selectedDate.getFullYear();
            console.log(day,month,year)
        }
    }
}
