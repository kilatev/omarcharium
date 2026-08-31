import QtQuick
import Qt.labs.platform 1.1 as Platform
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

Item {
  id: root

  property var shell: null
  property var manifest: null
  property bool configLoaded: false
  property bool idleIntegrationEnabled: true
  readonly property string pluginId: "dailen.omarcharium"
  readonly property string pluginDir: manifest && manifest.__sourceDir
    ? String(manifest.__sourceDir) : ""
  readonly property string launcherPath: pluginDir + "/scripts/launch-aquarium"
  readonly property string integrationPath: pluginDir + "/scripts/idle-integration"
  readonly property var idleConfig: shell && shell.shellConfig && shell.shellConfig.idle
    ? shell.shellConfig.idle : ({})
  readonly property int screensaverTimeout: {
    var value = Number(idleConfig.screensaver)
    return isFinite(value) && value >= 1 ? Math.round(value) : 150
  }

  function openControlRoom() {
    if (shell && typeof shell.summon === "function") {
      shell.summon(pluginId, "{}")
      return
    }
    Quickshell.execDetached(["omarchy-shell", "shell", "summon", pluginId, "{}"])
  }

  function startAquarium() {
    if (!pluginDir) return
    Quickshell.execDetached(["bash", launcherPath, "force"])
  }

  function stopAquarium() {
    Quickshell.execDetached(["pkill", "-f", "[o]rg.omarchy.screensaver"])
  }

  function applyIdleIntegration(enabled) {
    if (!pluginDir) return
    Quickshell.execDetached(["bash", integrationPath, enabled ? "enable" : "disable"])
  }

  function loadConfig(raw) {
    var enabled = true
    try {
      var parsed = JSON.parse(raw)
      if (parsed.integration && parsed.integration.idleEnabled !== undefined)
        enabled = !!parsed.integration.idleEnabled
    } catch (error) {
      enabled = true
    }
    idleIntegrationEnabled = enabled
    configLoaded = true
    applyIdleIntegration(enabled)
  }

  onPluginDirChanged: {
    if (configLoaded) applyIdleIntegration(idleIntegrationEnabled)
  }

  FileView {
    id: configFile
    path: Quickshell.env("HOME") + "/.config/omarcharium/config.json"
    watchChanges: true
    printErrors: false
    onLoaded: root.loadConfig(text())
    onFileChanged: reload()
    onLoadFailed: root.loadConfig("{}")
  }

  IdleMonitor {
    enabled: root.configLoaded && root.idleIntegrationEnabled
    timeout: root.screensaverTimeout
    respectInhibitors: true
    onIsIdleChanged: {
      if (isIdle) root.startAquarium()
    }
  }

  Platform.SystemTrayIcon {
    id: trayIcon
    visible: true
    tooltip: "Omarcharium · click to configure · middle-click to immerse"
    icon.source: Qt.resolvedUrl("assets/tray.svg")
    menu: Platform.Menu {
      Platform.MenuItem {
        text: "Open Control Room"
        onTriggered: root.openControlRoom()
      }
      Platform.MenuItem {
        text: "Immerse Now"
        onTriggered: root.startAquarium()
      }
      Platform.MenuSeparator { }
      Platform.MenuItem {
        text: "Report Bug"
        onTriggered: Qt.openUrlExternally("https://github.com/DailenG/omarcharium/issues")
      }
    }

    onActivated: function(reason) {
      if (reason === Platform.SystemTrayIcon.MiddleClick) {
        root.startAquarium()
      } else if (reason === Platform.SystemTrayIcon.Trigger
                 || reason === Platform.SystemTrayIcon.DoubleClick) {
        root.openControlRoom()
      }
    }
  }

  IpcHandler {
    target: "omarcharium"

    function configure(): void { root.openControlRoom() }
    function start(): void { root.startAquarium() }
    function stop(): void { root.stopAquarium() }
    function pluginDirectory(): string { return root.pluginDir }
  }

  Component.onDestruction: {
    if (root.pluginDir) Quickshell.execDetached(["bash", root.integrationPath, "disable"])
  }
}
