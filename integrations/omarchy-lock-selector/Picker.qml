// Carousel layout adapted from Omarchy's MIT-licensed ImagePicker.qml.
import Quickshell
import Quickshell.Wayland
import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
import qs.Commons
import "../io.github.sirjul1337.lock-explorer" as LockExplorer
import "../io.github.sirjul1337.lock-explorer/Designs.js" as Designs

Item {
  id: root
  property var shell: null
  property var manifest: null
  readonly property string pluginId: "vetalik.lock-selector"
  readonly property var lockService: shell ? shell.serviceFor("io.github.sirjul1337.lock-explorer") : null
  property bool opened: false
  property bool imagesLoaded: true
  property bool layoutSettled: true
  property bool showLabels: true
  property bool filterable: true
  property string filterText: ""
  property string errorText: ""
  property int selectedIndex: 0
  property var imageArray: []
  property color dimColor: Color.background
  property color foreground: Color.imagePicker.text
  property color scrim: Color.imagePicker.scrim
  property color selectedBorder: Color.imagePicker.selectedBorder
  property color unselectedBorder: Color.imagePicker.unselectedBorder
  property int expandedWidth: Math.min(768, panel.width - 100)
  property int expandedHeight: Math.round(expandedWidth * 475 / 768)
  property int sliceWidth: 108
  property int sliceHeight: Math.round(expandedHeight * 432 / 475)
  property int sliceSpacing: -30
  property int skewOffset: 28
  property int bottomChromeHeight: 104

  function refresh() {
    var selectedId = imageArray[selectedIndex] ? imageArray[selectedIndex].designId : ""
    imageArray = Designs.all().map(function(d) {
      return { designId: d.id, label: d.name, filePath: d.name, fileName: d.id, thumbnailPath: "" }
    })
    var wanted = selectedId || (lockService ? lockService.designId : "")
    selectedIndex = Math.max(0, imageArray.findIndex(function(d) { return d.designId === wanted }))
  }
  Connections {
    target: root.lockService
    function onDesignsRevisionChanged() { if (root.opened) root.refresh() }
  }
  function open(payload) {
    filterText = ""
    errorText = ""
    imageArray = []
    refresh()
    if (lockService) lockService.rescanUserDesigns()
    opened = true
    Qt.callLater(function() { carousel.forceActiveFocus() })
  }
  function close() { opened = false }
  function cancel() {
    opened = false
    if (shell) shell.hide(pluginId)
  }
  function applySelected() {
    if (!itemMatches(selectedIndex)) return
    var d = imageArray[selectedIndex]
    if (!lockService || !lockService.setDesign(d.designId)) {
      errorText = "Could not apply this design. Check that Lock Screen Explorer is enabled."
      return
    }
    cancel()
  }
  function currentLabel() {
    if (!itemMatches(selectedIndex)) return "No matching lock screens"
    var d = imageArray[selectedIndex]
    return d.label + (lockService && d.designId === lockService.designId ? "  ✓" : "")
  }
  function itemMatches(index) {
    return index >= 0 && index < imageArray.length && imageArray[index].label.toLowerCase().indexOf(filterText.toLowerCase()) !== -1
  }
  function filteredPosition(index) {
    var n = 0
    for (var i = 0; i < index; ++i) if (itemMatches(i)) ++n
    return n
  }
  function selectedFilteredPosition() { return filteredPosition(selectedIndex) }
  function select(index) { if (itemMatches(index)) selectedIndex = index }
  function selectAdjacent(direction) {
    for (var n = 1; n <= imageArray.length; ++n) {
      var i = (selectedIndex + direction * n + imageArray.length) % imageArray.length
      if (itemMatches(i)) { selectedIndex = i; return }
    }
  }
  function updateFilter(value) {
    filterText = value
    if (!itemMatches(selectedIndex)) {
      for (var i = 0; i < imageArray.length; ++i) if (itemMatches(i)) { selectedIndex = i; return }
    }
  }

  PanelWindow {
    id: panel

    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "omarchy-lock-selector"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: root.opened && root.imagesLoaded ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    exclusionMode: ExclusionMode.Ignore

    Rectangle {
      anchors.fill: parent
      visible: root.opened && root.imagesLoaded
      color: root.scrim
    }

    MouseArea {
      anchors.fill: parent
      enabled: root.opened && root.imagesLoaded
      onClicked: root.cancel()
    }

    Item {
      id: card
      visible: root.opened && root.imagesLoaded && root.layoutSettled && root.imageArray.length > 0
      width: Math.min(parent.width - 80, root.expandedWidth + 13 * (root.sliceWidth + root.sliceSpacing) + 40)
      height: root.expandedHeight + Style.space(30) + root.bottomChromeHeight
      anchors.centerIn: parent

        MouseArea { anchors.fill: parent; onClicked: {} }

        Item {
          id: carousel
          anchors.top: parent.top
          anchors.topMargin: Style.space(30)
          anchors.bottom: parent.bottom
          anchors.bottomMargin: root.bottomChromeHeight
          anchors.horizontalCenter: parent.horizontalCenter
          width: root.expandedWidth + 13 * (root.sliceWidth + root.sliceSpacing)
          clip: false
          focus: true

          readonly property real itemStep: root.sliceWidth + root.sliceSpacing
          readonly property real previewX: (width - root.expandedWidth) / 2

          Keys.priority: Keys.BeforeItem
          Keys.onPressed: function(event) {
            if (event.key === Qt.Key_Escape) {
              if (root.filterText) {
                root.updateFilter("")
              } else {
                root.cancel()
              }
              event.accepted = true
            } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
              root.applySelected()
              event.accepted = true
            } else if (root.filterable && Util.editsFilter(event, root.filterText)) {
              root.updateFilter(Util.editedFilter(event, root.filterText))
              event.accepted = true
            } else if (event.key === Qt.Key_Left || (event.key === Qt.Key_Tab && event.modifiers & Qt.ShiftModifier) || event.key === Qt.Key_Backtab) {
              root.selectAdjacent(-1)
              event.accepted = true
            } else if (event.key === Qt.Key_Right || event.key === Qt.Key_Tab) {
              root.selectAdjacent(1)
              event.accepted = true
            } else if (root.filterable && event.text && event.text.length === 1 && event.text.charCodeAt(0) >= 32 && event.text.charCodeAt(0) !== 127 && (event.modifiers === Qt.NoModifier || event.modifiers === Qt.ShiftModifier)) {
              root.updateFilter(root.filterText + event.text)
              event.accepted = true
            }
          }

          Component.onCompleted: forceActiveFocus()

          Repeater {
            model: root.imageArray.length

            delegate: Item {
              id: cell
              required property int index

              readonly property var imageData: root.imageArray[index]
              readonly property string filePath: imageData ? imageData.filePath : ""
              readonly property string fileName: imageData ? imageData.fileName : ""
              readonly property string thumbnailPath: imageData ? imageData.thumbnailPath : ""

              readonly property bool matched: root.itemMatches(index)
              readonly property int relativeIndex: root.filteredPosition(index) - root.selectedFilteredPosition()
              readonly property bool selected: matched && index === root.selectedIndex
              readonly property bool nearby: matched && Math.abs(relativeIndex) <= 5
              property bool sourceActivated: nearby
              onNearbyChanged: if (nearby) sourceActivated = true

              visible: nearby
              x: selected ? carousel.previewX : (relativeIndex < 0 ? carousel.previewX + relativeIndex * carousel.itemStep : carousel.previewX + root.expandedWidth + root.sliceSpacing + (relativeIndex - 1) * carousel.itemStep)
              width: selected ? root.expandedWidth : root.sliceWidth
              height: selected ? root.expandedHeight : root.sliceHeight
              y: selected ? 0 : (root.expandedHeight - root.sliceHeight) / 2
              z: selected ? 100 : 50 - Math.min(Math.abs(relativeIndex), 40)

              readonly property real skAbs: Math.abs(root.skewOffset)
              readonly property real topLeft: root.skewOffset >= 0 ? skAbs : 0
              readonly property real topRight: root.skewOffset >= 0 ? width : width - skAbs
              readonly property real bottomRight: root.skewOffset >= 0 ? width - skAbs : width
              readonly property real bottomLeft: root.skewOffset >= 0 ? 0 : skAbs

              Item {
                id: maskShape
                anchors.fill: parent
                visible: false
                layer.enabled: true

                Shape {
                  anchors.fill: parent
                  antialiasing: true
                  preferredRendererType: Shape.CurveRenderer
                  ShapePath {
                    fillColor: "white"
                    strokeColor: "transparent"
                    startX: cell.topLeft; startY: 0
                    PathLine { x: cell.topRight; y: 0 }
                    PathLine { x: cell.bottomRight; y: cell.height }
                    PathLine { x: cell.bottomLeft; y: cell.height }
                    PathLine { x: cell.topLeft; y: 0 }
                  }
                }
              }

              Item {
                anchors.fill: parent
                layer.enabled: true
                layer.smooth: true
                layer.effect: MultiEffect {
                  maskEnabled: true
                  maskSource: maskShape
                  maskThresholdMin: 0.3
                  maskSpreadAtMin: 0.3
                }

                Rectangle {
                  anchors.fill: parent
                  color: Color.background
                  clip: true
                  Item {
                    width: 1600
                    height: 990
                    scale: root.expandedWidth / 1600
                    transformOrigin: Item.TopLeft
                    x: (parent.width - root.expandedWidth) / 2
                    Loader {
                      anchors.fill: parent
                      active: root.opened && cell.nearby
                      asynchronous: true
                      sourceComponent: LockExplorer.LockHost {
                        designId: cell.imageData.designId
                        revision: root.lockService ? root.lockService.designsRevision : 0
                        backgroundPath: root.lockService ? root.lockService.backgroundPath : ""
                        backgroundVersion: root.lockService ? root.lockService.backgroundVersion : 0
                        avatarPath: root.lockService ? root.lockService.avatarPath : ""
                        avatarVersion: root.lockService ? root.lockService.avatarVersion : 0
                        inputEnabled: false
                        loadBackground: root.opened
                        passwordText: ""
                        videoPath: root.lockService ? root.lockService.videoPath : ""
                        videoPlaying: root.opened && cell.selected
                      }
                    }
                  }
                }

                Rectangle {
                  anchors.fill: parent
                  color: Util.alpha(root.dimColor, cell.selected ? 0 : 0.42)
                }
              }

              Shape {
                anchors.fill: parent
                antialiasing: true
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                  fillColor: "transparent"
                  strokeColor: cell.selected ? root.selectedBorder : root.unselectedBorder
                  strokeWidth: cell.selected ? 3 : 1
                  startX: cell.topLeft; startY: 0
                  PathLine { x: cell.topRight; y: 0 }
                  PathLine { x: cell.bottomRight; y: cell.height }
                  PathLine { x: cell.bottomLeft; y: cell.height }
                  PathLine { x: cell.topLeft; y: 0 }
                }
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: { root.select(index); root.applySelected() }
                onWheel: function(event) { root.selectAdjacent(event.angleDelta.y < 0 ? 1 : -1); event.accepted = true }
              }
            }
          }
        }

        Text {
          id: selectedLabel
          textFormat: Text.PlainText
          visible: root.showLabels
          anchors.top: carousel.bottom
          anchors.topMargin: Style.space(16)
          anchors.horizontalCenter: carousel.horizontalCenter
          width: root.expandedWidth
          text: root.currentLabel()
          color: root.foreground
          style: Text.Outline
          styleColor: Util.alpha(root.dimColor, 0.7)
          font.pixelSize: Style.font.display
          font.weight: Font.DemiBold
          horizontalAlignment: Text.AlignHCenter
          elide: Text.ElideRight
        }

        Text {
          textFormat: Text.PlainText
          visible: true
          anchors.top: selectedLabel.bottom
          anchors.topMargin: Style.space(8)
          anchors.horizontalCenter: carousel.horizontalCenter
          width: root.expandedWidth
          text: root.errorText || (root.filterText ? "Search: " + root.filterText : "← → Browse · Click or Enter to apply · Type to search · Esc to close")
          color: root.foreground
          opacity: 0.85
          style: Text.Outline
          styleColor: Util.alpha(root.dimColor, 0.7)
          font.pixelSize: Style.font.title
          horizontalAlignment: Text.AlignHCenter
          elide: Text.ElideRight
        }
    }
  }
}
