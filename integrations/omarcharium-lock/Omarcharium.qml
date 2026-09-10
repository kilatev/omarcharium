import QtQuick
import Quickshell
import Quickshell.Io
import "FrameGeometry.js" as Geometry
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
        source: lock.frameData && lock.frameData.backdrop && lock.frameData.backdrop.source === "image"
            ? "file://" + lock.frameData.backdrop.imagePath.split("/").map(encodeURIComponent).join("/") : ""
        fillMode: lock.frameData && lock.frameData.backdrop && lock.frameData.backdrop.fitMode === "contain" ? Image.PreserveAspectFit : Image.PreserveAspectCrop
        opacity: lock.frameData && lock.frameData.backdrop ? 1 - lock.frameData.backdrop.dimming / 100 : 1
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
        interval: 100
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
            var scale = Math.min(cw, ch)
            var crumbs = f.crumbs || []
            ctx.fillStyle = "#f7d994"
            for (var c = 0; c < crumbs.length; ++c) {
                var crumb = Geometry.point(crumbs[c], f, width, height)
                ctx.beginPath()
                ctx.arc(crumb.x, crumb.y, Math.max(2, scale * 0.18), 0, Math.PI * 2)
                ctx.fill()
            }
            var shelters = f.shelters || []
            for (var s = 0; s < shelters.length; ++s) {
                var shelter = shelters[s]
                ctx.fillStyle = "#4de39a"
                ctx.fillRect(shelter.x * cw - scale * 0.2, shelter.y * ch - scale * 2, scale * 0.4, scale * 2)
                ctx.fillStyle = "#667c86"
                ctx.beginPath()
                ctx.ellipse(shelter.x * cw, shelter.y * ch, scale * 2, scale, 0, 0, Math.PI * 2)
                ctx.fill()
            }
            for (var i = 0; i < f.resources.length; ++i) {
                var resource = f.resources[i]
                ctx.fillStyle = "#4de39a"
                ctx.globalAlpha = 0.18 + resource.amount * 0.4
                ctx.beginPath()
                ctx.arc(resource.x * cw, resource.y * ch, resource.radius * scale, 0, Math.PI * 2)
                ctx.fill()
            }
            ctx.globalAlpha = 1
            for (var j = 0; j < f.organisms.length; ++j) {
                var fish = f.organisms[j]
                var position = Geometry.point(fish, f, width, height)
                var x = position.x, y = position.y
                var fishWidth = Math.max(scale * 1.4, fish.width * scale * 2.2)
                var fishHeight = Math.max(scale * 0.8, fish.height * scale * 1.2)
                ctx.fillStyle = fish.colour
                ctx.beginPath()
                ctx.ellipse(x, y, fishWidth, fishHeight, 0, 0, Math.PI * 2)
                ctx.fill()
                ctx.beginPath()
                ctx.moveTo(x - fish.direction * fishWidth, y)
                ctx.lineTo(x - fish.direction * fishWidth * 1.7, y - fishHeight * 0.85)
                ctx.lineTo(x - fish.direction * fishWidth * 1.7, y + fishHeight * 0.85)
                ctx.closePath()
                ctx.fill()
                ctx.fillStyle = "#07131a"
                ctx.beginPath()
                ctx.arc(x + fish.direction * fishWidth * 0.45, y - fishHeight * 0.18, Math.max(1.5, scale * 0.09), 0, Math.PI * 2)
                ctx.fill()
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
