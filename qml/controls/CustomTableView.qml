import QtQuick 2.15
import QtQuick.Controls 1.4
import QtQuick.Controls 2.15 as C

TableView {
    highlightOnFocus: true
    clip: true
    headerVisible: true
    TableViewColumn {
        role: "title"
        title: "Title"
        width: 100
    }
    TableViewColumn {
        role: "author"
        title: "Author"
        width: 200
    }
    model:
        ListModel {
            id: libraryModel
            ListElement {
                title: "A Masterpiece"
                author: "Gabriel"
            }
            ListElement {
                title: "Brilliance"
                author: "Jens"
            }
            ListElement {
                title: "Outstanding"
                author: "Frederik"
            }
        }


}

/*##^##
Designer {
    D{i:0;formeditorZoom:3}
}
##^##*/
