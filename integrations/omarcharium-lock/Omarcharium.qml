import QtQuick
import Quickshell
import Quickshell.Io
import "../plugins/io.github.sirjul1337.lock-explorer/designs"

DesignBase {
    id: lock
    inputItem: field.input
    loadBackground: false
    property var frameData: null
    property bool pending: false
    readonly property int columns: Math.max(40, Math.min(240, Math.floor(width / 11)))
    readonly property int rows: Math.max(16, Math.min(100, Math.floor(height / 22)))
    readonly property string configHome: Quickshell.env("XDG_CONFIG_HOME") || (Quickshell.env("HOME") + "/.config")

    Rectangle { anchors.fill: parent; color: lock.frameData ? lock.frameData.background : "#061219" }
    Image {
        anchors.fill: parent
        source: lock.frameData && lock.frameData.backdrop.source === "image"
            ? "file://" + lock.frameData.backdrop.imagePath.split("/").map(encodeURIComponent).join("/") : ""
        fillMode: lock.frameData && lock.frameData.backdrop.fitMode === "contain" ? Image.PreserveAspectFit : Image.PreserveAspectCrop
        opacity: lock.frameData ? 1 - lock.frameData.backdrop.dimming / 100 : 1
        asynchronous: true
    }
    Process {
        id: renderer
        command: ["python3", "-u", lock.configHome + "/omarchy/lock-designs/omarcharium/bridge.py"]
        stdinEnabled: true
        running: lock.visible && lock.videoPlaying && !lock.snapshotMode
        onStarted: { lock.pending = false; lock.requestFrame() }
        onExited: lock.pending = false
        stdout: SplitParser {
            onRead: function(data) {
                lock.pending = false
                try { lock.frameData = JSON.parse(data); reef.requestPaint() }
                catch (e) { console.warn("Omarcharium frame:", e) }
            }
        }
    }
    function requestFrame() {
        if (!renderer.running || pending) return
        pending = true
        renderer.write(JSON.stringify([columns, rows]) + "\n")
    }
    Timer {
        interval: 42
        repeat: true
        running: renderer.running
        onTriggered: lock.requestFrame()
    }
    Canvas {
        id: reef
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            var f = lock.frameData
            if (!f) return
            var cw = width / f.width, ch = height / f.height
            var size = Math.min(ch * 0.88, cw / 0.61)
            ctx.font = size + "px monospace"
            ctx.textBaseline = "top"
            for (var i = 0; i < f.runs.length; ++i) {
                var r = f.runs[i]
                ctx.fillStyle = r[2]
                // Draw cells individually to preserve terminal-grid positioning.
                for (var j = 0; j < r[3].length; ++j)
                    ctx.fillText(r[3][j], (r[0] + j) * cw, r[1] * ch)
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onClicked: { lock.wakeRequested(); lock.forcePasswordFocus() }
        onPositionChanged: lock.wakeRequested()
    }
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: Math.max(24, parent.height * 0.06)
        width: Math.min(440, parent.width - 32)
        height: 138
        radius: 18
        color: "#d9061219"
        visible: !lock.snapshotBare
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 14
            text: Qt.formatTime(lock.now, "HH:mm")
            font.pixelSize: 30
            color: "#d7eef2"
        }
        PasswordField {
            id: field
            lock: lock
            anchors.horizontalCenter: parent.horizontalCenter
            y: 65
            width: parent.width - 40
            height: 54
        }
    }
}
