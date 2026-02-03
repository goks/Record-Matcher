import QtQuick 6.5
import QtQuick.Controls 6.5

Rectangle {
    id: optionsPage
    anchors.fill: parent
    color: "#ffffff"
    
    property real scaleFactorHeight: 1
    property real scaleFactorWidth: 1
    
    function hscale(size) {
        return Math.round(size * scaleFactorWidth)
    }
    function vscale(size) {
        return Math.round(size * scaleFactorHeight)
    }
    function tscale(size) {
        return Math.round((hscale(size) + vscale(size)) / 2) + 2
    }

    // Center container with proper sizing
    Item {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.85, hscale(550))
        height: contentColumn.height

        Column {
            id: contentColumn
            width: parent.width
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: vscale(20)
            
            // Icon placeholder
            Rectangle {
                width: hscale(120)
                height: hscale(120)
                radius: hscale(60)
                color: "#f0f4f8"
                anchors.horizontalCenter: parent.horizontalCenter
                border.color: "#d0dae5"
                border.width: 2
                
                Text {
                    anchors.centerIn: parent
                    text: "📋"
                    font.pixelSize: hscale(48)
                }
            }
            
            // Title
            Text {
                text: "Select Options to View Data"
                font.family: "PT Sans Caption"
                font.pixelSize: tscale(26)
                font.bold: true
                color: "#324254"
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            // Description
            Text {
                text: "Please select the following options from the left panel:"
                font.family: "PT Sans Caption"
                font.pixelSize: tscale(15)
                color: "#6a84a0"
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            // Options list container with background
            Rectangle {
                width: hscale(260)
                height: optionsColumn.height + vscale(28)
                color: "#f8fafc"
                radius: 10
                border.color: "#e2e8f0"
                border.width: 1
                anchors.horizontalCenter: parent.horizontalCenter
                
                Column {
                    id: optionsColumn
                    anchors.centerIn: parent
                    spacing: vscale(14)
                    
                    Row {
                        spacing: hscale(10)
                        Rectangle {
                            width: hscale(8)
                            height: hscale(8)
                            radius: hscale(4)
                            color: "#003366"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: "Company"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(15)
                            color: "#324254"
                        }
                    }
                    
                    Row {
                        spacing: hscale(10)
                        Rectangle {
                            width: hscale(8)
                            height: hscale(8)
                            radius: hscale(4)
                            color: "#003366"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: "Bank"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(15)
                            color: "#324254"
                        }
                    }
                    
                    Row {
                        spacing: hscale(10)
                        Rectangle {
                            width: hscale(8)
                            height: hscale(8)
                            radius: hscale(4)
                            color: "#003366"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: "Year"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(15)
                            color: "#324254"
                        }
                    }
                    
                    Row {
                        spacing: hscale(10)
                        Rectangle {
                            width: hscale(8)
                            height: hscale(8)
                            radius: hscale(4)
                            color: "#003366"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: "Month"
                            font.family: "PT Sans Caption"
                            font.pixelSize: tscale(15)
                            color: "#324254"
                        }
                    }
                }
            }
            
            // Hint text - full width with proper background
            Rectangle {
                width: parent.width
                height: hintRow.height + vscale(20)
                color: "#e8f4fd"
                radius: 8
                border.color: "#b8d4e8"
                border.width: 1
                anchors.horizontalCenter: parent.horizontalCenter
                
                Row {
                    id: hintRow
                    anchors.centerIn: parent
                    spacing: hscale(8)
                    
                    Text {
                        text: "💡"
                        font.pixelSize: tscale(14)
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Text {
                        text: "The bank statement will load automatically after selection"
                        font.family: "PT Sans Caption"
                        font.pixelSize: tscale(13)
                        color: "#1a5a8a"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }
    }
}

