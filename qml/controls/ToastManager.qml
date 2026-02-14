import QtQuick 6.5

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
    function show(text, status, duration) {
        model.insert(0, {text: text, status: status, duration: duration});
    }

    /**
      * Private
      */

    id: root

    z: Infinity
    spacing: vscale(5)
    width: Math.min(hscale(920), parent ? parent.width - hscale(24) : hscale(920))
    anchors.left: parent.left
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    anchors.topMargin: 0
    anchors.leftMargin: hscale(12)
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
            if (typeof status === "undefined") {
                show(text);
            }
            else if (typeof duration === "undefined") {
                show(text, status);
            }
            else {
                show(text, status, duration);
            }
        }
    }

    model: ListModel {id: model}
}





