import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Controls 1.4 as OldControls

Rectangle {
    id: root
    width: childrenRect.width
    height: childrenRect.height
    clip: true
    z: 100
    property bool expanded: false
    property bool enabled: true

    property alias selectedDate: cal.selectedDate

    MouseArea {
        height: expanded ? txt.height + cal.height : txt.height
        width: expanded ? Math.max(txt.width, cal.width) : txt.width
        hoverEnabled: true
        enabled: root.enabled
        onHoveredChanged: {
            expanded =  root.enabled && containsMouse
        }

        TextField {
            id: txt
            enabled: root.enabled
            text: cal.selectedDate
            inputMask: "0000-00-00"
            z:100
        }

        OldControls.Calendar {
            id: cal
            anchors.top: txt.bottom
            anchors.left: txt.left
            visible: true
            z:100
        }
    }
}