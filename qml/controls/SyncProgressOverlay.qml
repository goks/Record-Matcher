import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

/**
 * SyncProgressOverlay - Displays detailed progress for Firebase sync operations
 * 
 * Shows:
 * - Progress bar with current/total items
 * - Current item name being processed
 * - Status message (uploading, downloading, completed, error)
 * - Cancel button
 * - Elapsed time
 */
Rectangle {
    id: syncOverlay
    
    // Public properties
    property int currentItem: 0
    property int totalItems: 0
    property string currentItemName: ""
    property string statusMessage: ""
    property string operationType: "sync"  // "upload" or "download"
    property bool isVisible: false
    property bool canCancel: true
    property real scaleFactorWidth: 1
    property real scaleFactorHeight: 1
    
    // Signals
    signal cancelRequested()
    signal completed()
    
    // Internal state
    property real startTime: 0
    property string elapsedTimeText: "0:00"
    
    // Helper functions
    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return Math.round((hscale(size) + vscale(size)) / 2) + 2
    }
    
    // Show the overlay and reset state
    function show(operation) {
        operationType = operation || "sync"
        currentItem = 0
        totalItems = 0
        currentItemName = ""
        statusMessage = "Preparing..."
        startTime = Date.now()
        isVisible = true
        elapsedTimer.start()
    }
    
    // Hide the overlay
    function hide() {
        isVisible = false
        elapsedTimer.stop()
    }
    
    // Update progress
    function updateProgress(current, total, itemName, status) {
        currentItem = current
        totalItems = total
        currentItemName = itemName
        statusMessage = status
        
        if (status === "completed" || status === "error") {
            elapsedTimer.stop()
        }
    }
    
    // Calculate progress percentage
    function getProgressPercent() {
        if (totalItems <= 0) return 0
        return Math.min(currentItem / totalItems, 1.0)
    }
    
    // Timer to update elapsed time
    Timer {
        id: elapsedTimer
        interval: 1000
        repeat: true
        running: false
        onTriggered: {
            var elapsed = Math.floor((Date.now() - startTime) / 1000)
            var minutes = Math.floor(elapsed / 60)
            var seconds = elapsed % 60
            elapsedTimeText = minutes + ":" + (seconds < 10 ? "0" : "") + seconds
        }
    }
    
    // Full screen semi-transparent overlay
    anchors.fill: parent
    color: "#80000000"
    visible: isVisible
    z: 1000
    
    // Block mouse events from passing through
    MouseArea {
        anchors.fill: parent
        onClicked: {} // Absorb clicks
    }
    
    // Centered modal card
    Rectangle {
        id: modalCard
        width: Math.min(hscale(500), parent.width - hscale(40))
        height: contentColumn.height + vscale(48)
        anchors.centerIn: parent
        radius: hscale(12)
        color: "#ffffff"
        
        // Card shadow
        layer.enabled: true
        layer.effect: Item {
            Rectangle {
                anchors.fill: parent
                anchors.margins: -4
                radius: hscale(14)
                color: "#20000000"
            }
        }
        
        ColumnLayout {
            id: contentColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: hscale(24)
            spacing: vscale(16)
            
            // Header with icon and title
            RowLayout {
                Layout.fillWidth: true
                spacing: hscale(12)
                
                // Sync icon (animated)
                Rectangle {
                    width: hscale(40)
                    height: hscale(40)
                    radius: hscale(20)
                    color: operationType === "upload" ? "#dbeafe" : "#dcfce7"
                    
                    Text {
                        anchors.centerIn: parent
                        text: operationType === "upload" ? "⬆" : "⬇"
                        font.pixelSize: hscale(20)
                        color: operationType === "upload" ? "#2563eb" : "#16a34a"
                        
                        RotationAnimation on rotation {
                            running: statusMessage !== "completed" && statusMessage !== "error"
                            from: 0
                            to: operationType === "upload" ? -15 : 15
                            duration: 500
                            loops: Animation.Infinite
                            easing.type: Easing.InOutSine
                        }
                    }
                }
                
                Column {
                    Layout.fillWidth: true
                    spacing: vscale(2)
                    
                    Text {
                        text: operationType === "upload" ? "Uploading to Firebase" : "Downloading from Firebase"
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(16)
                        font.weight: Font.DemiBold
                        color: "#1e293b"
                    }
                    
                    Text {
                        text: "Elapsed: " + elapsedTimeText
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(11)
                        color: "#64748b"
                    }
                }
            }
            
            // Progress section
            Column {
                Layout.fillWidth: true
                spacing: vscale(8)
                
                // Progress text
                RowLayout {
                    width: parent.width
                    
                    Text {
                        text: currentItemName || "Preparing..."
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(12)
                        color: "#475569"
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                    
                    Text {
                        text: totalItems > 0 ? (currentItem + " / " + totalItems) : ""
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(12)
                        font.weight: Font.DemiBold
                        color: "#3b82f6"
                    }
                }
                
                // Progress bar
                Rectangle {
                    width: parent.width
                    height: vscale(8)
                    radius: vscale(4)
                    color: "#e2e8f0"
                    
                    Rectangle {
                        width: parent.width * getProgressPercent()
                        height: parent.height
                        radius: vscale(4)
                        color: statusMessage === "error" ? "#ef4444" : 
                               statusMessage === "completed" ? "#22c55e" : "#3b82f6"
                        
                        Behavior on width {
                            NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
                        }
                    }
                }
                
                // Status message
                Text {
                    text: {
                        switch(statusMessage) {
                            case "uploading": return "📤 Uploading..."
                            case "downloading": return "📥 Downloading..."
                            case "loading": return "📂 Loading data..."
                            case "saving": return "💾 Saving data..."
                            case "completed": return "✅ Sync completed successfully!"
                            case "error": return "❌ An error occurred"
                            default: return statusMessage || "Processing..."
                        }
                    }
                    font.family: "PT Sans Caption"
                    font.pixelSize: tscale(11)
                    color: statusMessage === "error" ? "#dc2626" : 
                           statusMessage === "completed" ? "#16a34a" : "#64748b"
                }
            }
            
            // Buttons
            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: vscale(8)
                spacing: hscale(12)
                
                Item { Layout.fillWidth: true }
                
                // Cancel button
                Rectangle {
                    width: hscale(100)
                    height: vscale(36)
                    radius: hscale(6)
                    color: cancelMouseArea.containsMouse ? "#f1f5f9" : "#ffffff"
                    border.color: "#e2e8f0"
                    border.width: 1
                    visible: canCancel && statusMessage !== "completed"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Cancel"
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(13)
                        color: "#475569"
                    }
                    
                    MouseArea {
                        id: cancelMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            syncOverlay.cancelRequested()
                            syncOverlay.hide()
                        }
                    }
                }
                
                // Close/Done button (shown when completed)
                Rectangle {
                    width: hscale(100)
                    height: vscale(36)
                    radius: hscale(6)
                    color: doneMouseArea.containsMouse ? "#2563eb" : "#3b82f6"
                    visible: statusMessage === "completed" || statusMessage === "error"
                    
                    Text {
                        anchors.centerIn: parent
                        text: statusMessage === "completed" ? "Done" : "Close"
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(13)
                        font.weight: Font.DemiBold
                        color: "#ffffff"
                    }
                    
                    MouseArea {
                        id: doneMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            syncOverlay.completed()
                            syncOverlay.hide()
                        }
                    }
                }
            }
        }
    }
}
