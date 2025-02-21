import QtQuick 2.15
import QtGraphicalEffects 1.15


Rectangle {
    id: main_box
    width:1177
//    height: 425

    signal createMasterXMLBtnClicked
    signal downloadMasterXMLBtnClicked
    property color textColor: "#324254"
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

    Rectangle {
        id: master_import_box
        width: hscale(1300)
        height: vscale(360)
        radius: 8
        border.color: "#c4c4c4"
        Text {
                visible:true
                id: header1
                text: "Master import"
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                //        font.pixelSize: 34
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.WordWrap
                anchors.topMargin: vscale(30)
                anchors.rightMargin: hscale(50)
                anchors.leftMargin: hscale(40)
                color: textColor
                font.family: "PT Sans Caption"
        //        font.pointSize: tscale(22)
                font.pointSize: tscale(22)
            }
        Text {
                visible:true
                id: bodyText1
                text: "- Administration>Data Export Import>Data Export/Import(XML)>Export Data>Masters. \n- Check on Account, All.\n- Uncheck on all else.\n- Change the file name extension to .xml."
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: header1.bottom
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.WordWrap
                anchors.topMargin: vscale(23)
                anchors.rightMargin: hscale(50)
                anchors.leftMargin: hscale(40)
                color: textColor
                font.family: "PT Sans Caption"
        //        font.pointSize: tscale(22)
                font.pointSize: tscale(12)
            }
        CustomSearchBar {
                                    id: textInput
                                     width: hscale(836)
                                     searchmode: "fileimport"
                                    //                            height: 38
                                    anchors.left: parent.left
                                    anchors.top: bodyText1.bottom
                                    anchors.leftMargin: hscale(34)
                                    //                            anchors.bottom: parent.bottom
                                    //                            anchors.bottomMargin: 0
                                    anchors.topMargin: vscale(23)
                                    searchbyMode: "off"
                                    startDateCalendar: backend.startDateCalendar
                                    endDateCalendar: backend.endDateCalendar
                                    scaleFactorWidth: main_box.scaleFactorWidth
                                    scaleFactorHeight: main_box.scaleFactorHeight
                                    onSearchBarTextChanged: backend.search(textInput.searchBarText, textInput.searchbyMode)
                                    // onSearchbyModeChanged: backend.search(textInput.searchBarText, textInput.searchbyMode)
                                }
        CustomSubTitleButton {
            id:getMasterXMLBut
            width: hscale(140)
            height: vscale(30)
            anchors.top: textInput.bottom
            anchors.topMargin: vscale(15)
            anchors.left: textInput.right
            anchors.leftMargin: hscale(20)
            fontSize: tscale(8)
            // visible: true
            text: "Get Master XML"
            onClicked: main_box.createMasterXMLBtnClicked()
        }          
        DownloadButton {
            id:masterXMLDlBut
            width: hscale(30)
            height: vscale(30)
            anchors.top: textInput.bottom
            anchors.topMargin: vscale(15)
            anchors.left: getMasterXMLBut.right
            anchors.leftMargin: hscale(20)
            onClicked: main_box.downloadMasterXMLBtnClicked()
        }                            

    }




}



/*##^##
Designer {
    D{i:0;formeditorZoom:0.9}
}
##^##*/
