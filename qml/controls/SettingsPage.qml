import QtQuick 6.5
import QtQuick.Controls 6.5
import QtQuick.Layouts 6.5

/**
 * SettingsPage - Application settings panel with Firebase sync and migration controls
 * 
 * Features:
 * - Manual Upload to Firebase button
 * - Manual Download from Firebase button
 * - Last sync timestamps display
 * - Database migration from pickle to SQLite
 * - Storage information display
 */
Rectangle {
    id: settingsPage
    
    // Public properties - should be bound from main application
    property string lastUploadTime: "Never"
    property string lastDownloadTime: "Never"
    property bool syncEnabled: true
    property bool isSyncing: false
    property real scaleFactorWidth: 1
    property real scaleFactorHeight: 1
    
    // Migration properties
    property string migrationStatus: "checking"  // "checking", "pending", "in_progress", "completed"
    property string migrationProgressText: ""
    property int migrationCurrent: 0
    property int migrationTotal: 0
    property int pickleSnapshotCount: 0
    property int pickleChequeCount: 0
    property string databasePath: ""
    property int totalSnapshotCount: 0
    property int totalChequeReportCount: 0
    
    // Signals to trigger operations
    signal uploadRequested()
    signal downloadRequested()
    signal closeRequested()
    signal migrationRequested()
    
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
    
    // Format timestamp for display
    function formatTimestamp(timestamp) {
        if (!timestamp || timestamp === "" || timestamp === "Never") {
            return "Never"
        }
        try {
            var date = new Date(timestamp)
            return date.toLocaleDateString() + " " + date.toLocaleTimeString()
        } catch (e) {
            return timestamp
        }
    }
    
    color: "#f8fafc"
    
    // Main content scroll area
    ScrollView {
        anchors.fill: parent
        anchors.margins: hscale(24)
        clip: true
        
        ColumnLayout {
            width: settingsPage.width - hscale(48)
            spacing: vscale(24)
            
            // Header
            RowLayout {
                Layout.fillWidth: true
                spacing: hscale(12)
                
                // Back button
                Rectangle {
                    width: hscale(40)
                    height: hscale(40)
                    radius: hscale(8)
                    color: backMouseArea.containsMouse ? "#e2e8f0" : "transparent"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "←"
                        font.pixelSize: tscale(20)
                        color: "#475569"
                    }
                    
                    MouseArea {
                        id: backMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: settingsPage.closeRequested()
                    }
                }
                
                Text {
                    text: "Settings"
                    font.family: "PT Sans Caption"
                    font.pixelSize: tscale(24)
                    font.weight: Font.Bold
                    color: "#1e293b"
                }
                
                Item { Layout.fillWidth: true }
            }
            
            // Firebase Sync Section
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: syncSectionContent.height + vscale(32)
                radius: hscale(12)
                color: "#ffffff"
                border.color: "#e2e8f0"
                border.width: 1
                
                ColumnLayout {
                    id: syncSectionContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: hscale(20)
                    spacing: vscale(16)
                    
                    // Section header
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: hscale(12)
                        
                        Rectangle {
                            width: hscale(40)
                            height: hscale(40)
                            radius: hscale(8)
                            color: "#fef3c7"
                            
                            Text {
                                anchors.centerIn: parent
                                text: "🔥"
                                font.pixelSize: hscale(20)
                            }
                        }
                        
                        Column {
                            Layout.fillWidth: true
                            spacing: vscale(2)
                            
                            Text {
                                text: "Firebase Cloud Sync"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(16)
                                font.weight: Font.DemiBold
                                color: "#1e293b"
                            }
                            
                            Text {
                                text: "Manually sync your data with Firebase cloud storage"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(11)
                                color: "#64748b"
                            }
                        }
                    }
                    
                    // Divider
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#e2e8f0"
                    }
                    
                    // Sync buttons row
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: hscale(16)
                        
                        // Upload button
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: uploadContent.height + vscale(24)
                            radius: hscale(10)
                            color: uploadMouseArea.containsMouse && !isSyncing ? "#dbeafe" : "#eff6ff"
                            border.color: "#bfdbfe"
                            border.width: 1
                            opacity: isSyncing ? 0.6 : 1.0
                            
                            ColumnLayout {
                                id: uploadContent
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: hscale(16)
                                spacing: vscale(8)
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: hscale(8)
                                    
                                    Text {
                                        text: "⬆"
                                        font.pixelSize: hscale(24)
                                        color: "#2563eb"
                                    }
                                    
                                    Column {
                                        Layout.fillWidth: true
                                        spacing: vscale(2)
                                        
                                        Text {
                                            text: "Upload to Firebase"
                                            font.family: "PT Sans Caption"
                                            font.pixelSize: tscale(14)
                                            font.weight: Font.DemiBold
                                            color: "#1e40af"
                                        }
                                        
                                        Text {
                                            text: "Push local data to cloud"
                                            font.family: "PT Sans Caption"
                                            font.pixelSize: tscale(10)
                                            color: "#3b82f6"
                                        }
                                    }
                                }
                                
                                // Last upload time
                                Text {
                                    text: "Last upload: " + formatTimestamp(lastUploadTime)
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: tscale(10)
                                    color: "#64748b"
                                }
                            }
                            
                            MouseArea {
                                id: uploadMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: isSyncing ? Qt.ForbiddenCursor : Qt.PointingHandCursor
                                onClicked: {
                                    if (!isSyncing) {
                                        settingsPage.uploadRequested()
                                    }
                                }
                            }
                        }
                        
                        // Download button
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: downloadContent.height + vscale(24)
                            radius: hscale(10)
                            color: downloadMouseArea.containsMouse && !isSyncing ? "#dcfce7" : "#f0fdf4"
                            border.color: "#bbf7d0"
                            border.width: 1
                            opacity: isSyncing ? 0.6 : 1.0
                            
                            ColumnLayout {
                                id: downloadContent
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: hscale(16)
                                spacing: vscale(8)
                                
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: hscale(8)
                                    
                                    Text {
                                        text: "⬇"
                                        font.pixelSize: hscale(24)
                                        color: "#16a34a"
                                    }
                                    
                                    Column {
                                        Layout.fillWidth: true
                                        spacing: vscale(2)
                                        
                                        Text {
                                            text: "Download from Firebase"
                                            font.family: "PT Sans Caption"
                                            font.pixelSize: tscale(14)
                                            font.weight: Font.DemiBold
                                            color: "#166534"
                                        }
                                        
                                        Text {
                                            text: "Pull cloud data to local"
                                            font.family: "PT Sans Caption"
                                            font.pixelSize: tscale(10)
                                            color: "#22c55e"
                                        }
                                    }
                                }
                                
                                // Last download time
                                Text {
                                    text: "Last download: " + formatTimestamp(lastDownloadTime)
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: tscale(10)
                                    color: "#64748b"
                                }
                            }
                            
                            MouseArea {
                                id: downloadMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: isSyncing ? Qt.ForbiddenCursor : Qt.PointingHandCursor
                                onClicked: {
                                    if (!isSyncing) {
                                        settingsPage.downloadRequested()
                                    }
                                }
                            }
                        }
                    }
                    
                    // Warning message
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: warningText.height + vscale(16)
                        radius: hscale(8)
                        color: "#fef3c7"
                        border.color: "#fcd34d"
                        border.width: 1
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: hscale(12)
                            spacing: hscale(8)
                            
                            Text {
                                text: "⚠"
                                font.pixelSize: hscale(16)
                                color: "#b45309"
                            }
                            
                            Text {
                                id: warningText
                                text: "Download will overwrite local data. Upload will overwrite cloud data. Make sure to backup important data before syncing."
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(10)
                                color: "#92400e"
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                        }
                    }
                }
            }
            
            // Storage Info Section
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: storageSectionContent.height + vscale(32)
                radius: hscale(12)
                color: "#ffffff"
                border.color: "#e2e8f0"
                border.width: 1
                
                ColumnLayout {
                    id: storageSectionContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: hscale(20)
                    spacing: vscale(16)
                    
                    // Section header
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: hscale(12)
                        
                        Rectangle {
                            width: hscale(40)
                            height: hscale(40)
                            radius: hscale(8)
                            color: "#e0e7ff"
                            
                            Text {
                                anchors.centerIn: parent
                                text: "💾"
                                font.pixelSize: hscale(20)
                            }
                        }
                        
                        Column {
                            Layout.fillWidth: true
                            spacing: vscale(2)
                            
                            Text {
                                text: "Local Storage"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(16)
                                font.weight: Font.DemiBold
                                color: "#1e293b"
                            }
                            
                            Text {
                                text: "Data is stored locally in SQLite database"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(11)
                                color: "#64748b"
                            }
                        }
                    }
                    
                    // Divider
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#e2e8f0"
                    }
                    
                    // Storage info
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2
                        rowSpacing: vscale(8)
                        columnSpacing: hscale(16)
                        
                        Text {
                            text: "Storage Type:"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(12)
                            color: "#64748b"
                        }
                        
                        Text {
                            text: migrationStatus === "completed" ? "SQLite Database" : "Legacy Pickle Files"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(12)
                            font.weight: Font.DemiBold
                            color: migrationStatus === "completed" ? "#16a34a" : "#f59e0b"
                        }
                        
                        Text {
                            text: "Database Path:"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(12)
                            color: "#64748b"
                        }
                        
                        Text {
                            text: databasePath || "Not available"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(10)
                            color: "#1e293b"
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                        }
                        
                        Text {
                            text: "Total Snapshots:"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(12)
                            color: "#64748b"
                        }
                        
                        Text {
                            text: totalSnapshotCount.toString()
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(12)
                            font.weight: Font.DemiBold
                            color: "#1e293b"
                        }
                        
                        Text {
                            text: "Total Cheque Reports:"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(12)
                            color: "#64748b"
                        }
                        
                        Text {
                            text: totalChequeReportCount.toString()
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(12)
                            font.weight: Font.DemiBold
                            color: "#1e293b"
                        }
                    }
                }
            }
            
            // Database Migration Section
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: migrationSectionContent.height + vscale(32)
                radius: hscale(12)
                color: "#ffffff"
                border.color: migrationStatus === "pending" ? "#fcd34d" : "#e2e8f0"
                border.width: migrationStatus === "pending" ? 2 : 1
                
                ColumnLayout {
                    id: migrationSectionContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: hscale(20)
                    spacing: vscale(16)
                    
                    // Section header
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: hscale(12)
                        
                        Rectangle {
                            width: hscale(40)
                            height: hscale(40)
                            radius: hscale(8)
                            color: migrationStatus === "pending" ? "#fef3c7" : "#e8f5e9"
                            
                            Text {
                                anchors.centerIn: parent
                                text: "🗄"
                                font.pixelSize: hscale(20)
                            }
                        }
                        
                        Column {
                            Layout.fillWidth: true
                            spacing: vscale(2)
                            
                            Text {
                                text: "Database Migration"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(16)
                                font.weight: Font.DemiBold
                                color: "#1e293b"
                            }
                            
                            Text {
                                text: "Migrate data from legacy pickle files to SQLite database"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(11)
                                color: "#64748b"
                            }
                        }
                    }
                    
                    // Divider
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#e2e8f0"
                    }
                    
                    // Migration Status
                    Rectangle {
                        Layout.fillWidth: true
                        height: vscale(60)
                        color: "#f8fafc"
                        radius: hscale(8)
                        border.color: "#e2e8f0"
                        border.width: 1
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: hscale(15)
                            spacing: hscale(15)
                            
                            Rectangle {
                                width: hscale(12)
                                height: hscale(12)
                                radius: hscale(6)
                                color: migrationStatus === "completed" ? "#22c55e" :
                                       migrationStatus === "pending" ? "#f59e0b" :
                                       migrationStatus === "in_progress" ? "#3b82f6" : "#94a3b8"
                            }
                            
                            Column {
                                Layout.fillWidth: true
                                spacing: vscale(2)
                                
                                Text {
                                    text: "Migration Status"
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: tscale(12)
                                    font.weight: Font.DemiBold
                                    color: "#1e293b"
                                }
                                
                                Text {
                                    text: migrationStatus === "completed" ? "✓ Migration completed - Using SQLite database" :
                                          migrationStatus === "pending" ? "⚠ Legacy pickle files detected - Migration recommended" :
                                          migrationStatus === "in_progress" ? "⏳ Migration in progress..." :
                                          "Checking status..."
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: tscale(11)
                                    color: "#64748b"
                                }
                            }
                        }
                    }
                    
                    // Pickle Files Info (visible when pending)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: pickleInfoColumn.height + vscale(20)
                        color: "#fffbeb"
                        radius: hscale(8)
                        border.color: "#fcd34d"
                        border.width: 1
                        visible: migrationStatus === "pending"
                        
                        Column {
                            id: pickleInfoColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: hscale(12)
                            spacing: vscale(6)
                            
                            Text {
                                text: "Detected Legacy Files:"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(11)
                                font.weight: Font.DemiBold
                                color: "#92400e"
                            }
                            
                            Text {
                                text: "• tableSnapshotCollection.filv2: " + pickleSnapshotCount + " snapshots"
                                font.family: "Consolas"
                                font.pixelSize: tscale(10)
                                color: "#b45309"
                            }
                            
                            Text {
                                text: "• ChequeReportCollection.fil: " + pickleChequeCount + " reports"
                                font.family: "Consolas"
                                font.pixelSize: tscale(10)
                                color: "#b45309"
                            }
                        }
                    }
                    
                    // Migration Progress (visible during migration)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: vscale(90)
                        color: "#eff6ff"
                        radius: hscale(8)
                        border.color: "#bfdbfe"
                        border.width: 1
                        visible: migrationStatus === "in_progress"
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: hscale(15)
                            spacing: vscale(8)
                            
                            Text {
                                text: migrationProgressText
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(12)
                                color: "#1d4ed8"
                            }
                            
                            ProgressBar {
                                id: migrationProgressBar
                                Layout.fillWidth: true
                                from: 0
                                to: migrationTotal > 0 ? migrationTotal : 1
                                value: migrationCurrent
                                
                                background: Rectangle {
                                    implicitHeight: vscale(8)
                                    color: "#bfdbfe"
                                    radius: vscale(4)
                                }
                                
                                contentItem: Item {
                                    implicitHeight: vscale(8)
                                    
                                    Rectangle {
                                        width: migrationProgressBar.visualPosition * parent.width
                                        height: parent.height
                                        radius: vscale(4)
                                        color: "#3b82f6"
                                    }
                                }
                            }
                            
                            Text {
                                text: migrationCurrent + " of " + migrationTotal
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(10)
                                color: "#64748b"
                            }
                        }
                    }
                    
                    // Migration Button
                    Rectangle {
                        Layout.fillWidth: true
                        height: vscale(50)
                        radius: hscale(10)
                        color: {
                            if (migrationStatus === "completed") return "#e2e8f0"
                            if (migrationStatus === "in_progress") return "#bfdbfe"
                            if (migrateMouseArea.containsMouse) return "#4338ca"
                            return "#4f46e5"
                        }
                        
                        Text {
                            anchors.centerIn: parent
                            text: migrationStatus === "in_progress" ? "⏳ Migration in Progress..." :
                                  migrationStatus === "completed" ? "✓ Already Migrated" :
                                  "🔄 Migrate to SQLite Database"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(14)
                            font.weight: Font.DemiBold
                            color: migrationStatus === "completed" ? "#64748b" : "#ffffff"
                        }
                        
                        MouseArea {
                            id: migrateMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: migrationStatus === "pending" ? Qt.PointingHandCursor : Qt.ArrowCursor
                            enabled: migrationStatus === "pending"
                            onClicked: settingsPage.migrationRequested()
                        }
                    }
                    
                    // Info text
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: infoText.height + vscale(16)
                        color: "#f0fdf4"
                        radius: hscale(8)
                        border.color: "#bbf7d0"
                        border.width: 1
                        
                        Text {
                            id: infoText
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: hscale(12)
                            text: "ℹ Migration converts your data from legacy pickle files to a modern SQLite database. This improves performance, data integrity, and enables better search capabilities. A backup of your original files will be created automatically."
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(10)
                            color: "#166534"
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
            
            // About Section
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: aboutSectionContent.height + vscale(32)
                radius: hscale(12)
                color: "#ffffff"
                border.color: "#e2e8f0"
                border.width: 1
                
                ColumnLayout {
                    id: aboutSectionContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: hscale(20)
                    spacing: vscale(16)
                    
                    // Section header
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: hscale(12)
                        
                        Rectangle {
                            width: hscale(40)
                            height: hscale(40)
                            radius: hscale(8)
                            color: "#f0fdf4"
                            
                            Text {
                                anchors.centerIn: parent
                                text: "ℹ"
                                font.pixelSize: hscale(20)
                                color: "#16a34a"
                            }
                        }
                        
                        Column {
                            Layout.fillWidth: true
                            spacing: vscale(2)
                            
                            Text {
                                text: "About Record Matcher"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(16)
                                font.weight: Font.DemiBold
                                color: "#1e293b"
                            }
                            
                            Text {
                                text: "Version 2.0 - SQLite Edition"
                                font.family: "PT Sans Caption"
                                font.pixelSize: tscale(11)
                                color: "#64748b"
                            }
                        }
                    }
                }
            }
            
            // Spacer
            Item {
                Layout.fillHeight: true
                Layout.minimumHeight: vscale(24)
            }
        }
    }
}
