import QtQuick 6.5

MessageBox {
    property string timeData: ""
    text1: "Cheque Report Present"
    text2: ""
    // text3: "Last saved at 01/06/2021 17:08 p.m."
    text3: "Last save at " + timeData
}






