import QtQuick 2.0

/**
  * adapted from StackOverflow:
  * http://stackoverflow.com/questions/26879266/make-toast-in-android-by-qml
  * @brief Manager that creates Toasts dynamically
  */
/**
  * adapted from gist:
  * https://gist.github.com/jonmcclung/bae669101d17b103e94790341301c129
  */
ListView {
    /**
      * Public
      */

    /**
      * @brief Shows a Toast
      *
      * @param {string} text Text to show
      * @param {real} duration Duration to show in milliseconds, defaults to 3000
      */
    function show(text, duration) {
        model.insert(0, {text: text, duration: duration});
    }

    /**
      * Private
      */

    id: root

    z: Infinity
    spacing: vscale(5)
    width: hscale(650)
    anchors.left: parent.left
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    anchors.topMargin: 0
    anchors.leftMargin: 0
    anchors.bottomMargin: vscale(10)
    verticalLayoutDirection: ListView.BottomToTop
    interactive: false

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

    displaced: Transition {
        NumberAnimation {
            properties: "y"
            easing.type: Easing.InOutQuad
        }
    }
    
    delegate: Toast {
        scaleFactorHeight: root.scaleFactorHeight
        scaleFactorWidth: root.scaleFactorWidth

        Component.onCompleted: {
            if (typeof duration === "undefined") {
                show(text);
            }
            else {
                show(text, duration);
            }
        }
    }

    model: ListModel {id: model}
}
