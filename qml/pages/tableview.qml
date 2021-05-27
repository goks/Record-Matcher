import QtQuick 2.12
import QtQuick.Controls 2.4

import "../controls"
//import Qt.labs.qmlmodels 1.0

    CustomTableView2{
        property var settableData: [
            { name: "Melbourne", country: "Australia", subcountry: "Victoria", latitude: -37.9716929, longitude: 144.7729583 },
            { name: "London", country: "United Kingdom", subcountry: "England", latitude: 51.5287718, longitude: -0.2416804 },
            { name: "Paris", country: "France", subcountry: "Île-de-France", latitude: 48.8589507, longitude: 2.2770205 },
            { name: "New York City", country: "United States", subcountry: "New York", latitude: 40.6976637, longitude: -74.1197639 },
            { name: "Tokyo", country: "Japan", subcountry: "Tokyo", latitude: 35.6735408 , longitude: 139.5703047 }
        ];
        tableData: settableData

        anchors.fill: parent
    }


/*##^##
Designer {
    D{i:0;formeditorZoom:0.75}
}
##^##*/

