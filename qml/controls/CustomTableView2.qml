import QtQuick 6.5
import QtQuick.Controls 6.5
// Qt6: Old TableView (QtQuick.Controls 1.4) completely rewritten in Qt 6
// Using Flickable + Repeater for stable rendering

Rectangle {
    property var columns: []
    property var tableData: []
    property var selectedRows: []
    property var columnWidths: []  // Store user-defined column widths
    property int focusedRowIndex: -1  // Track which row is currently focused (clicked)
    id: tableBox
    anchors.fill: parent
    color: "#ffffff"
    border.color: "#e0e6ec"
    border.width: 0
    radius: 0
    opacity: 1.0
    z: 3
    visible: true

    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1
    property int minRowHeight: 36
    property int minColumnWidth: 60
    
    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        // Ensure minimum readable font size
        var scaled = Math.round((hscale(size) + vscale(size)) / 2) + 2
        return Math.max(scaled, 11) // minimum 11px font
    }

    // Color scheme matching app style
    property color headerBgColor: "#f8fafc"
    property color headerTextColor: "#475569"
    property color textColor: "#334155"
    property color textColorSecondary: "#64748b"
    property color rowBgColor: "#ffffff"
    property color rowBgColorAlt: "#f8fafc"
    property color rowBgColorHover: "#f1f5f9"
    property color rowBgColorFocused: "#e2e8f0"  // Stronger highlight for focused/clicked row
    property color rowBgColorSelected: "#e0f2fe"
    property color borderColor: "#e2e8f0"
    property color accentColor: "#003366"
    property color resizeHandleColor: "#cbd5e1"
    property color resizeHandleHoverColor: "#94a3b8"
    
    property bool useLegacyRendering: true
    
    // Recalculate column widths when table width changes
    onWidthChanged: {
        if (columns && columns.length > 0) {
            recalculateColumnWidths()
        }
    }
    
    // Initialize column widths when columns change
    onColumnsChanged: {
        recalculateColumnWidths()
    }
    
    // Calculate proportional column widths based on column types
    function recalculateColumnWidths() {
        if (!columns || columns.length === 0) return
        var numCols = columns.length
        var availableWidth = tableBox.width - hscale(24)
        
        // Calculate weights for each column
        var weights = []
        var totalWeight = 0
        for (var i = 0; i < numCols; i++) {
            var name = columns[i] ? columns[i].toLowerCase() : ""
            var w = 1.0
            if (name.indexOf("date") !== -1) w = 0.85
            else if (name.indexOf("narration") !== -1) w = 1.6
            else if (name.indexOf("chq") !== -1 || name.indexOf("cheque") !== -1) w = 0.8
            else if (name.indexOf("party") !== -1) w = 1.4
            else if (name === "credit" || name === "debit") w = 0.9
            else if (name.indexOf("closing") !== -1 || name.indexOf("balance") !== -1) w = 1.0
            weights.push(w)
            totalWeight += w
        }
        
        // Calculate widths based on weights
        var newWidths = []
        for (var j = 0; j < numCols; j++) {
            var colWidth = Math.max((availableWidth * weights[j]) / totalWeight, minColumnWidth)
            newWidths.push(colWidth)
        }
        columnWidths = newWidths
    }
    
    // Get column width
    function getColumnWidth(colIndex) {
        if (columnWidths && columnWidths[colIndex] && columnWidths[colIndex] > 0) {
            return columnWidths[colIndex]
        }
        // Fallback - equal distribution
        var numCols = columns ? columns.length : 1
        var availableWidth = tableBox.width - hscale(24)
        return Math.max(availableWidth / numCols, minColumnWidth)
    }
    
    // Update column width when user resizes
    function setColumnWidth(colIndex, newWidth) {
        if (!columnWidths) columnWidths = []
        var widths = columnWidths.slice()
        widths[colIndex] = Math.max(newWidth, minColumnWidth)
        columnWidths = widths
    }
    
    // Get total content width - sum of all column widths
    function getTotalContentWidth() {
        var total = hscale(24) // left + right padding
        for (var i = 0; i < (columns ? columns.length : 0); i++) {
            total += getColumnWidth(i)
        }
        return Math.max(total, tableBox.width)
    }

    // Native-style table using `tableModel` and `columns` when TableView module is unavailable
    Item {
        id: nativeTableContainer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        // Prefer native rendering only if not forcing legacy mode and we have headers
        visible: (!useLegacyRendering) && columns && columns.length > 0

        Item {
            id: nativeInner
            anchors.fill: parent

            // Header for the native-list based table
            Rectangle {
                id: nativeHeader
                anchors.left: parent.left
                anchors.right: parent.right
                height: Math.max(vscale(40), minRowHeight)
                color: "#f5f7fa"
                border.color: "#e0e6ec"
                border.width: 1

                Row {
                    anchors.fill: parent
                    anchors.leftMargin: hscale(10)
                    anchors.rightMargin: hscale(12)
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 0

                    Repeater {
                        model: columns
                        delegate: Text {
                            text: modelData !== undefined ? String(modelData) : ""
                            font.pointSize: tscale(10)
                            color: textColor
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignLeft
                            // Avoid reading nested objects; use container width fallback
                            width: Math.max(120, Math.round((tableBox.width - hscale(22)) / Math.max(1, columns.length)))
                        }
                    }
                }

                // Debug badge showing number of rows
                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.rightMargin: hscale(12)
                    text: "Rows: " + (tableModel ? tableModel.rowCount() : (tableData ? tableData.length : 0))
                    color: textColor
                    font.pointSize: tscale(9)
                    horizontalAlignment: Text.AlignRight
                    visible: true
                }
            }

            // Use ListView over the QAbstractTableModel; each delegate represents a row and exposes roles col0..colN
            ListView {
                id: nativeList
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: nativeHeader.bottom
                anchors.bottom: parent.bottom
                // Use native table model if available, else fall back to tableData (QVariantList)
                model: tableModel ? tableModel : tableData
                clip: true
                focus: true
                
                Keys.onSpacePressed: {
                    // Toggle selection on space bar press
                    if (focusedRowIndex >= 0) {
                        var idx = focusedRowIndex
                        var sel = (selectedRows || []).slice()
                        var pos = sel.indexOf(idx)
                        if (pos === -1) sel.push(idx)
                        else sel.splice(pos, 1)
                        if (typeof backend !== 'undefined' && backend.selectedRowsChanged) {
                            backend.selectedRowsChanged(sel)
                        } else {
                            selectedRows = sel
                        }
                    }
                }
                delegate: Rectangle {
                    id: rowDelegate
                    // Guard against parent being undefined during initialization
                    width: (nativeList && nativeList.width) ? nativeList.width : tableBox.width
                    height: Math.max(vscale(48), minRowHeight)
                    
                    property bool isFocused: focusedRowIndex === index
                    property bool isSelected: selectedRows && selectedRows.indexOf(index) !== -1
                    
                    color: {
                        if (isSelected) return rowBgColorSelected
                        if (isFocused) return rowBgColorFocused
                        return index % 2 === 0 ? rowBgColor : "#ffffff"
                    }
                    border.width: isFocused ? 2 : 1
                    border.color: isFocused ? "#64748b" : "#e6eef3"

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            // Only focus the row on click, don't select it
                            focusedRowIndex = index
                            nativeList.forceActiveFocus()
                        }
                    }

                    // Keyboard handling is done at ListView level

                    Row {
                        anchors.fill: parent
                        spacing: 10

                        Repeater {
                            model: columns
                            delegate: Text {
                                width: Math.max(120, Math.round((tableBox.width - 40) / Math.max(1, columns.length)))
                                height: vscale(48)
                                // Access named role dynamically (col0, col1, ...)
                                text: (rowDelegate["col" + index] !== undefined) ? String(rowDelegate["col" + index]) : ""
                                color: textColor
                                font.family: "PT Sans Caption"
                                font.pointSize: tscale(10)
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignLeft
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }
        }
    }

    // Header row - styled to match app aesthetic with resizable columns
    Rectangle {
        id: headerRow
        visible: useLegacyRendering || !nativeTableContainer.visible
        anchors.left: parent.left
        anchors.right: parent.right
        height: Math.max(vscale(44), minRowHeight)
        color: headerBgColor
        
        // Bottom border only
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 2
            color: borderColor
        }

        Flickable {
            id: headerFlick
            anchors.fill: parent
            contentX: tableFlick.contentX
            contentWidth: getTotalContentWidth()
            clip: true
            interactive: false
            
            Row {
                id: headerRowContent
                x: hscale(12)
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0
                
                Repeater {
                    model: columns
                    delegate: Item {
                        id: headerCell
                        width: getColumnWidth(index)
                        height: headerRow.height
                        
                        Text {
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.leftMargin: hscale(6)
                            anchors.right: resizeHandle.left
                            anchors.rightMargin: hscale(4)
                            text: modelData !== undefined ? String(modelData) : ""
                            font.family: "PT Sans Caption"
                            font.pixelSize: Math.max(tscale(12), 12)
                            font.weight: Font.DemiBold
                            color: headerTextColor
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignLeft
                        }
                        
                        // Resize handle - allows user to adjust column width
                        Rectangle {
                            id: resizeHandle
                            width: 8
                            height: parent.height - vscale(8)
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            color: resizeMouseArea.containsMouse || resizeMouseArea.pressed ? resizeHandleHoverColor : "transparent"
                            radius: 2
                            
                            // Visual indicator line
                            Rectangle {
                                width: 2
                                height: parent.height - vscale(12)
                                anchors.centerIn: parent
                                color: resizeMouseArea.containsMouse || resizeMouseArea.pressed ? resizeHandleHoverColor : resizeHandleColor
                                radius: 1
                            }
                            
                            MouseArea {
                                id: resizeMouseArea
                                anchors.fill: parent
                                anchors.margins: -4
                                hoverEnabled: true
                                cursorShape: Qt.SplitHCursor
                                
                                property real startX: 0
                                property real startWidth: 0
                                
                                onPressed: function(mouse) {
                                    startX = mouse.x + mapToItem(tableBox, 0, 0).x
                                    startWidth = getColumnWidth(index)
                                }
                                
                                onPositionChanged: function(mouse) {
                                    if (pressed) {
                                        var currentX = mouse.x + mapToItem(tableBox, 0, 0).x
                                        var delta = currentX - startX
                                        var newWidth = Math.max(startWidth + delta, minColumnWidth)
                                        setColumnWidth(index, newWidth)
                                    }
                                }
                            }
                        }
                        
                        // Column separator line
                        Rectangle {
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            anchors.topMargin: vscale(8)
                            anchors.bottomMargin: vscale(8)
                            width: 1
                            color: borderColor
                            visible: index < columns.length - 1
                        }
                    }
                }
            }
        }
        
        // Row count badge
        Rectangle {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: hscale(12)
            width: rowCountText.width + hscale(16)
            height: vscale(24)
            radius: vscale(12)
            color: "#e2e8f0"
            visible: tableData && tableData.length > 0
            z: 2
            
            Text {
                id: rowCountText
                anchors.centerIn: parent
                text: "Rows: " + (tableData ? tableData.length : 0)
                color: textColorSecondary
                font.family: "PT Sans Caption"
                font.pixelSize: tscale(9)
            }
        }
    }

    // ScrollView wrapper for proper scrollbar handling
    ScrollView {
        id: tableScrollView
        visible: useLegacyRendering || !nativeTableContainer.visible
        anchors.top: headerRow.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        clip: true
        
        ScrollBar.vertical.policy: ScrollBar.AlwaysOn
        ScrollBar.horizontal.policy: ScrollBar.AsNeeded
        
        // Flickable table rendering
        Flickable {
            id: tableFlick
            contentHeight: tableRepeater.childrenRect.height
            contentWidth: getTotalContentWidth()
            flickableDirection: Flickable.AutoFlickIfNeeded
            boundsBehavior: Flickable.StopAtBounds
            focus: true
            
            Keys.onSpacePressed: {
                // Toggle selection on space bar press
                if (focusedRowIndex >= 0) {
                    var idx = focusedRowIndex
                    var sel = (selectedRows || []).slice()
                    var pos = sel.indexOf(idx)
                    if (pos === -1) sel.push(idx)
                    else sel.splice(pos, 1)
                    if (typeof backend !== 'undefined' && backend.selectedRowsChanged) {
                        backend.selectedRowsChanged(sel)
                    } else {
                        selectedRows = sel
                    }
                }
            }
            
            Keys.onUpPressed: {
                if (focusedRowIndex > 0) {
                    focusedRowIndex = focusedRowIndex - 1
                }
            }
            
            Keys.onDownPressed: {
                if (tableData && focusedRowIndex < tableData.length - 1) {
                    focusedRowIndex = focusedRowIndex + 1
                }
            }

            Column {
            id: tableRepeater
            width: getTotalContentWidth()
            spacing: 0

            Repeater {
                id: rowsRepeater
                model: tableData

                Rectangle {
                    id: rowRect
                    width: getTotalContentWidth()
                    height: Math.max(vscale(36), minRowHeight)
                    
                    property bool isSelected: selectedRows && selectedRows.indexOf(index) !== -1
                    property bool isFocused: focusedRowIndex === index
                    property bool isHovered: rowMouseArea.containsMouse
                    property var currentRowData: modelData
                    property int rowIndex: index
                    
                    color: {
                        if (isSelected) return rowBgColorSelected
                        if (isFocused) return rowBgColorFocused
                        if (isHovered) return rowBgColorHover
                        return index % 2 === 0 ? rowBgColor : rowBgColorAlt
                    }
                    
                    // Bottom border
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: borderColor
                    }
                    
                    // Left accent for selected rows
                    Rectangle {
                        visible: rowRect.isSelected
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 3
                        color: accentColor
                    }
                    
                    // Border highlight for focused row
                    Rectangle {
                        visible: rowRect.isFocused && !rowRect.isSelected
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 3
                        color: "#64748b"
                    }

                    MouseArea {
                        id: rowMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            // Only focus the row on click, don't permanently select it
                            focusedRowIndex = rowRect.rowIndex
                            tableFlick.forceActiveFocus()
                        }
                    }

                    Row {
                        anchors.fill: parent
                        anchors.leftMargin: hscale(12)
                        spacing: 0

                        Repeater {
                            id: cellsRepeater
                            model: (columns && columns.length > 0) ? columns.length : (Array.isArray(rowRect.currentRowData) ? rowRect.currentRowData.length : 0)
                            
                            delegate: Item {
                                width: getColumnWidth(index)
                                height: rowRect.height
                                
                                property var rowData: rowRect.currentRowData
                                property int cellIndex: index
                                
                                property var computedCell: {
                                    var rd = rowData;
                                    var ci = cellIndex;
                                    if (Array.isArray(rd) && ci < rd.length) {
                                        return rd[ci] !== undefined ? rd[ci] : "";
                                    }
                                    if (rd && typeof rd === 'object' && !Array.isArray(rd)) {
                                        if (columns && columns.length > ci) {
                                            var key = columns[ci];
                                            if (rd[key] !== undefined) return rd[key];
                                        }
                                        return rd[ci] !== undefined ? rd[ci] : "";
                                    }
                                    return "";
                                }

                                Text {
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.leftMargin: hscale(6)
                                    width: parent.width - hscale(12)
                                    text: computedCell !== undefined && computedCell !== null ? String(computedCell) : ""
                                    color: rowRect.isSelected ? accentColor : textColor
                                    font.family: "PT Sans Caption"
                                    font.pixelSize: Math.max(tscale(12), 12)
                                    font.weight: cellIndex === 0 ? Font.Medium : Font.Normal
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: Text.AlignLeft
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }
                }
            }
        }

        // Empty state
        Item {
            visible: tableData ? tableData.length === 0 : true
            anchors.fill: parent
            z: 5
            
            Column {
                anchors.centerIn: parent
                spacing: vscale(12)
                
                Text {
                    text: "📊"
                    font.pixelSize: hscale(48)
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                
                Text {
                    text: "No data to display"
                    color: textColorSecondary
                    font.family: "PT Sans Caption"
                    font.pixelSize: tscale(14)
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }
        }  // Close Flickable
    }  // Close ScrollView
    
    function calculateContentWidth() {
        // Use parent width to fill available space
        return tableBox.width
    }
    
    function addColumn(name) {
        // No-op in fallback
    }

    onTableDataChanged: {
        if (tableFlick) {
            tableFlick.contentY = 0
        }
    }

    Component.onCompleted: {
        if (useLegacyRendering) console.warn("CustomTableView2: Using legacy Flickable renderer (forced)")
        else console.warn("CustomTableView2: Using native renderer when available")
    }
}
