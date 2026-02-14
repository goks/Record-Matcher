import QtQuick 6.5
import QtQuick.Controls 6.5
import "../controls"

// Modern scrollable ListView with improved visual design
ListView {
    id: listView
    
    // Public properties (same interface as before for compatibility)
    property var data: [
        {"name": "HDFC", "value": "hdfc"},
        {"name": "ICICI", "value": "icici"}
    ]
    property string selected: ''
    property string selectedName: ''
    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1
    
    // List spacing and behavior
    spacing: vscale(2)
    topMargin: vscale(2)
    bottomMargin: vscale(2)
    leftMargin: hscale(4)
    rightMargin: hscale(4)
    clip: true
    
    // Smooth scrolling configuration - reduced speed for better control
    boundsBehavior: Flickable.StopAtBounds
    flickDeceleration: 5000
    maximumFlickVelocity: 800
    
    // Internal model
    model: ListModel { id: model }
    
    // Helper functions
    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return (Math.round((hscale(size) + vscale(size)) / 2) + 2)
    }

    // Modern color palette
    property color textColorDefault: "#475569"
    property color textColorSelected: "#1e40af"
    property color textColorHover: "#334155"
    property color bgSelected: "#dbeafe"
    property color bgUnselected: "transparent"
    property color bgHover: "#f1f5f9"
    property color accentColor: "#3b82f6"
    property real itemBorderRadius: 6
    
    // Update model when data changes from backend
    onDataChanged: {
        model.clear()
        for (var i = 0; i < data.length; i++) {
            model.append(data[i])
        }
    }
    
    // Update parent properties when selection changes
    onCurrentIndexChanged: {
        if (currentIndex >= 0 && currentIndex < model.count) {
            // Set selectedName first before selected to ensure it's available when onSelectedChanged fires
            selectedName = model.get(currentIndex).name
            selected = model.get(currentIndex).value
            console.log(model.get(currentIndex).name + ' selected')
        } else {
            selectedName = ''
            selected = ''
            console.log('selection cleared')
        }
    }
    
    // Auto-scroll to current item when selection changes externally
    onCurrentItemChanged: {
        if (currentItem) {
            positionViewAtIndex(currentIndex, ListView.Contain)
        }
    }
    
    Component.onCompleted: {
        // Model is already populated by onDataChanged when data property is set
        // Only set initial selection if valid
        if (model.count > 0 && currentIndex >= 0 && currentIndex < model.count) {
            listView.currentIndex = currentIndex
        }
    }
    
    // Highlight component (selection indicator)
    highlight: Rectangle {
        color: bgSelected
        radius: 4
        
        // Left accent bar
        Rectangle {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 3
            radius: 1
            color: accentColor
        }
        
        Behavior on y {
            SmoothedAnimation { 
                velocity: 600
                duration: 100
            }
        }
    }
    highlightFollowsCurrentItem: true
    highlightMoveDuration: 100
    
    // List item delegate
    delegate: Item {
        id: delegateItem
        width: listView.width - listView.leftMargin - listView.rightMargin
        height: vscale(28)
        
        property bool isCurrentItem: delegateItem.ListView.isCurrentItem
        property bool isHovered: itemMouseArea.containsMouse
        
        Rectangle {
            id: itemBackground
            anchors.fill: parent
            radius: 4
            color: {
                if (delegateItem.isCurrentItem) return "transparent" // Highlight handles this
                if (delegateItem.isHovered) return bgHover
                return bgUnselected
            }
            
            Behavior on color {
                ColorAnimation { duration: 100 }
            }

            // Mouse interaction
            MouseArea {
                id: itemMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    listView.currentIndex = index
                }
                onDoubleClicked: {
                    if (listView.currentIndex === index) {
                        listView.currentIndex = -1
                    }
                }
            }
            
            // Content row
            Row {
                anchors.fill: parent
                anchors.leftMargin: hscale(10)
                anchors.rightMargin: hscale(8)
                spacing: hscale(10)
                
                // Selection indicator dot
                Rectangle {
                    width: hscale(6)
                    height: hscale(6)
                    radius: hscale(3)
                    anchors.verticalCenter: parent.verticalCenter
                    color: delegateItem.isCurrentItem ? accentColor : (delegateItem.isHovered ? "#94a3b8" : "#cbd5e1")
                    
                    Behavior on color {
                        ColorAnimation { duration: 100 }
                    }
                }
                
                // Item text
                Text {
                    id: listText
                    text: model.name
                    elide: Text.ElideRight
                    width: parent.width - hscale(26)
                    anchors.verticalCenter: parent.verticalCenter
                    verticalAlignment: Text.AlignVCenter
                    font.family: "PT Sans Caption"
                    font.pixelSize: tscale(12)
                    font.weight: delegateItem.isCurrentItem ? Font.DemiBold : Font.Normal
                    color: {
                        if (delegateItem.isCurrentItem) return textColorSelected
                        if (delegateItem.isHovered) return textColorHover
                        return textColorDefault
                    }
                    
                    Behavior on color {
                        ColorAnimation { duration: 100 }
                    }
                }
            }
            
            // Subtle right chevron for selected item
            Text {
                visible: delegateItem.isCurrentItem
                anchors.right: parent.right
                anchors.rightMargin: hscale(8)
                anchors.verticalCenter: parent.verticalCenter
                text: "›"
                font.pixelSize: tscale(16)
                font.weight: Font.Bold
                color: accentColor
                opacity: 0.7
            }
        }
    }
    
    // Empty state
    Item {
        visible: model.count === 0
        anchors.fill: parent
        
        Column {
            anchors.centerIn: parent
            spacing: vscale(8)
            
            Text {
                text: "—"
                font.pixelSize: hscale(24)
                color: "#94a3b8"
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Text {
                text: "No items"
                font.family: "PT Sans Caption"
                font.pixelSize: tscale(11)
                color: "#94a3b8"
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }
    
    // Custom scrollbar
    ScrollBar.vertical: ScrollBar {
        id: scrollBar
        policy: ScrollBar.AsNeeded
        visible: listView.contentHeight > listView.height
        width: 8
        background: Rectangle {
            color: "transparent"
        }
        contentItem: Rectangle {
            implicitWidth: 4
            radius: 2
            color: "#cbd5e1"
            opacity: 0.8
        }
    }
}





