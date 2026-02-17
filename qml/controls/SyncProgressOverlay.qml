import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

Rectangle {
    id: syncOverlay

    property int currentItem: 0
    property int totalItems: 0
    property string currentItemName: ""
    property string statusMessage: ""
    property string operationType: "sync"  // "upload" or "download"
    property bool isVisible: false
    property bool canCancel: true
    property real scaleFactorWidth: 1
    property real scaleFactorHeight: 1

    signal cancelRequested()
    signal completed()

    property int elapsedSeconds: 0
    property string elapsedTimeText: "0:00"

    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return Math.round((hscale(size) + vscale(size)) / 2) + 2
    }

    function formatElapsed(seconds) {
        var mins = Math.floor(seconds / 60)
        var secs = seconds % 60
        return mins + ":" + (secs < 10 ? "0" : "") + secs
    }

    function show(operation) {
        operationType = operation || "sync"
        currentItem = 0
        totalItems = 0
        currentItemName = ""
        statusMessage = "preparing"
        elapsedSeconds = 0
        elapsedTimeText = "0:00"
        isVisible = true
        elapsedTimer.restart()
    }

    function hide() {
        isVisible = false
        elapsedTimer.stop()
    }

    function updateProgress(current, total, itemName, status) {
        currentItem = current
        totalItems = total
        currentItemName = itemName
        statusMessage = status

        if (status === "completed" || status === "error") {
            // Some backend stages emit intermediate "completed" status
            // (for a sub-step). Stop timer only for final sync completion.
            var label = (itemName || "").toString().toLowerCase()
            var isFinal = label.indexOf("upload complete") !== -1
                       || label.indexOf("download complete") !== -1
                       || label.indexOf("sync completed") !== -1
                       || label.indexOf("failed") !== -1
                       || label.indexOf("error") !== -1
                       || label.indexOf("cancelled") !== -1
            if (isFinal) {
                elapsedTimer.stop()
            }
        }
    }

    function getProgressPercent() {
        if (statusMessage === "completed" || statusMessage === "error") return 1.0
        if (totalItems <= 0) return 0.12
        return Math.min(currentItem / totalItems, 1.0)
    }

    Timer {
        id: elapsedTimer
        interval: 1000
        repeat: true
        running: false
        onTriggered: {
            elapsedSeconds = elapsedSeconds + 1
            elapsedTimeText = formatElapsed(elapsedSeconds)
        }
    }

    anchors.fill: parent
    color: "transparent"
    visible: isVisible
    z: 1000

    Rectangle {
        id: panel
        width: Math.min(hscale(460), parent.width - hscale(24))
        height: contentColumn.implicitHeight + vscale(28)
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: hscale(16)
        anchors.topMargin: vscale(112)
        radius: hscale(10)
        color: "#ffffff"
        border.color: "#dbe2ea"
        border.width: 1

        layer.enabled: true
        layer.smooth: true

        ColumnLayout {
            id: contentColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: hscale(14)
            spacing: vscale(8)

            RowLayout {
                Layout.fillWidth: true
                spacing: hscale(8)

                Rectangle {
                    width: hscale(28)
                    height: hscale(28)
                    radius: hscale(14)
                    color: operationType === "upload" ? "#dbeafe" : "#dcfce7"

                    Text {
                        anchors.centerIn: parent
                        text: operationType === "upload" ? "UP" : "DN"
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(9)
                        font.weight: Font.Bold
                        color: operationType === "upload" ? "#2563eb" : "#16a34a"
                    }
                }

                Column {
                    Layout.fillWidth: true
                    spacing: vscale(2)

                    Text {
                        text: operationType === "upload" ? "Uploading to Firebase" : "Downloading from Firebase"
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(13)
                        font.weight: Font.DemiBold
                        color: "#1e293b"
                    }
                    Text {
                        text: "Elapsed " + elapsedTimeText
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(10)
                        color: "#64748b"
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: currentItemName || "Preparing..."
                font.family: "PT Sans Caption"
                font.pixelSize: tscale(11)
                color: "#475569"
                elide: Text.ElideRight
            }

            Rectangle {
                Layout.fillWidth: true
                height: vscale(12)
                radius: vscale(6)
                color: "#e2e8f0"

                Rectangle {
                    width: parent.width * getProgressPercent()
                    height: parent.height
                    radius: parent.radius
                    color: statusMessage === "error" ? "#ef4444"
                          : (statusMessage === "completed" ? "#22c55e" : "#3b82f6")

                    Behavior on width {
                        NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: totalItems > 0 ? (currentItem + " / " + totalItems) : "Starting..."
                    font.family: "PT Sans Caption"
                    font.pixelSize: tscale(10)
                    color: "#334155"
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: Math.round(getProgressPercent() * 100) + "%"
                    font.family: "PT Sans Caption"
                    font.pixelSize: tscale(10)
                    font.weight: Font.DemiBold
                    color: statusMessage === "error" ? "#dc2626"
                          : (statusMessage === "completed" ? "#16a34a" : "#2563eb")
                }
            }

            Text {
                Layout.fillWidth: true
                text: {
                    if (statusMessage === "completed") return "Sync completed successfully"
                    if (statusMessage === "error") return "Sync failed"
                    if (statusMessage === "uploading") return "Uploading data..."
                    if (statusMessage === "downloading") return "Downloading data..."
                    if (statusMessage === "loading") return "Loading local data..."
                    if (statusMessage === "saving") return "Saving local data..."
                    return "Processing..."
                }
                font.family: "PT Sans Caption"
                font.pixelSize: tscale(10)
                color: statusMessage === "error" ? "#dc2626"
                      : (statusMessage === "completed" ? "#16a34a" : "#64748b")
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: hscale(8)
                Layout.topMargin: vscale(2)

                Item { Layout.fillWidth: true }

                Button {
                    visible: canCancel && statusMessage !== "completed" && statusMessage !== "error"
                    text: "Cancel"
                    onClicked: {
                        syncOverlay.cancelRequested()
                        syncOverlay.hide()
                    }
                }

                Button {
                    visible: statusMessage === "completed" || statusMessage === "error"
                    text: statusMessage === "completed" ? "Done" : "Close"
                    onClicked: {
                        syncOverlay.completed()
                        syncOverlay.hide()
                    }
                }
            }
        }
    }
}
