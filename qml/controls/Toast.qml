import QtQuick 2.0
import QtGraphicalEffects 1.15
import QtQuick.Controls 2.15

/**
 * adapted from StackOverflow:
 * http://stackoverflow.com/questions/26879266/make-toast-in-android-by-qml
 */
/**
 * adapted from Gist:
 * https://gist.github.com/jonmcclung/bae669101d17b103e94790341301c129
 */

/**
  * @brief An Android-like timed message text in a box that self-destroys when finished if desired
  */
Rectangle {

    /**
      * Public
      */

    /**
      * @brief Shows this Toast
      *
      * @param {string} text Text to show
      * @param {real} duration Duration to show in milliseconds, defaults to 3000
      */
    function show(text, status, duration ) {
        switch(status){
        case "info":
            status_color = "#68A5D8";
            main_message.text = "Info";
            image.source = "../../images/svg_images/status_info_icon.svg"
            break;
        case "success":
            status_color = "#60C67A";
            main_message.text = "Success";
            image.source = "../../images/svg_images/status_success_icon.svg"
            break;
        case "warning":
            status_color = "#F5A648";
            main_message.text = "Warning";
            image.source = "../../images/svg_images/status_warning_icon.svg"
            break;
        case "error":
            status_color = "#F48D62";
            main_message.text = "Error";
            image.source = "../../images/svg_images/status_error_icon.svg"
            break;
        }
        submessage.text = text;

        if (typeof duration !== "undefined") { // checks if parameter was passed
            time = Math.max(duration, 2 * fadeTime);
        }
        else {
            time = defaultTime;
        }
        animation.start();
    }

    property bool selfDestroying: false  // whether this Toast will self-destroy when it is finished

    /**
      * Private
      */

    id: root

    readonly property real defaultTime: 3000
    property real time: defaultTime
    readonly property real fadeTime: 300

    property real margin: 10

    property color status_color:"#60c67a"

    anchors {
        left: parent.left
        right: parent.right
        margins: margin
    }

    //    height: message.height + margin
    width: 650
    height: 103
    //    radius: margin

    opacity: 0
    color: "#ffffff"

    Rectangle {
        id: status_color_box
        width: 4
        color: status_color
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.leftMargin: 0
        anchors.bottomMargin: 0
        anchors.topMargin: 0
    }
    Rectangle {
        id: iconBox
        width: 46
        color: "#ffffff"
        anchors.left: status_color_box.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 0
        anchors.topMargin: 0
        anchors.leftMargin: 0

        Image {
            id: image
            y: 35
            width: 40
            height: 40
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.right: parent.right
            source: "../../images/svg_images/status_success_icon.svg"
            anchors.rightMargin: 0
            anchors.leftMargin: 12
            fillMode: Image.PreserveAspectFit
        }
    }
    Text {
        id: main_message
        height: 22
        color: "black"
        text: 'Success'
        anchors.left: iconBox.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 20
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter
        anchors.topMargin: 14
        anchors.rightMargin: 36
        font.family: "PT Sans Caption"
        font.pixelSize: 20
        font.weight: Font.Bold
    }
    Text {
        id: submessage
        color: "#9c9c9c"
        text: "Cheque report of Gokul Agencies for the financial year of 2018-2019 successfully saved."
        anchors.left: iconBox.right
        anchors.right: parent.right
        anchors.top: main_message.bottom
        anchors.bottom: parent.bottom
        anchors.leftMargin: 20
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter
        wrapMode: Text.WordWrap
        anchors.bottomMargin: 16
        font.styleName: "Regular"
        anchors.topMargin: 6
        anchors.rightMargin: 36
        font.family: "PT Sans Caption"
        font.pixelSize: 16
        font.weight: Font.Normal
    }
    QtObject {
            id: internal

            property var dynamicColor: if(close_btn.down){
                                           close_btn.down ? "grey" : "transparent"
                                       } else {
                                           close_btn.hovered ? "grey" : "transparent"
                                       }
        }
    Button{
        id: close_btn
        width: 18
        height: 18
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: 14
        anchors.rightMargin: 18
        background: Rectangle {
            color: internal.dynamicColor
        }

        Image {
            id: close_btn_img
            anchors.fill: parent
            source: "../../images/svg_images/status_download_btn.svg"
            fillMode: Image.PreserveAspectFit

        }
        onClicked: root.visible = false
    }
    DropShadow {
        anchors.fill: root
        source: root
        fast: true
        samples: 0
        cached: true
        horizontalOffset: 2
        verticalOffset: 3
        radius: 4
        spread: 0
        color: "#40000000"
    }


    SequentialAnimation on opacity {
        id: animation
        running: false


        NumberAnimation {
            to: .9
            duration: fadeTime
        }

        PauseAnimation {
            duration: time - 2 * fadeTime
        }

        NumberAnimation {
            to: 0
            duration: fadeTime
        }

        onRunningChanged: {
            if (!running && selfDestroying) {
                root.destroy();
            }
        }
    }
}

/*##^##
Designer {
    D{i:0;formeditorZoom:2}D{i:2}D{i:5}
}
##^##*/
