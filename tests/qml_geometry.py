"""Qt job entry point: production geometry with generated JSON frames."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from dataclasses import replace

from hypothesis import given, settings, strategies as st
from scripts.ecosystem_model import Crumb, initial_model
from scripts.ecosystem_view import Viewport, view


class QmlGeometryTests(unittest.TestCase):
    @settings(max_examples=5, deadline=None, print_blob=True)
    @given(st.integers(0, 10000), st.integers(40, 240), st.integers(16, 100))
    def test_generated_frame_coordinates(self, seed, width, height):
        runner = shutil.which("qmltestrunner") or next((str(p) for p in
            (Path("/usr/lib/qt6/bin/qmltestrunner"), Path("/usr/lib/qt5/bin/qmltestrunner")) if p.is_file()), None)
        self.assertIsNotNone(runner, "Qt Quick Test is required for generated geometry cases")
        helper = Path(__file__).resolve().parents[1] / "integrations/omarcharium-lock/FrameGeometry.js"
        model = replace(initial_model(seed), crumbs=(Crumb("crumb", .3, .4),))
        frame = view(model, Viewport(width, height))
        # The minimized JSON fixture appears in the failing subprocess assertion.
        source = '''import QtQuick
import QtTest
import %s as Geometry
TestCase {
    name: "GeneratedGeometry"
    property var frame: %s
    function test_coordinates() {
        var before = JSON.stringify(frame)
        var entities = frame.organisms.concat(frame.crumbs)
        for (var i = 0; i < entities.length; ++i) {
            var fish = entities[i]
            var p = Geometry.point(fish, frame, 1920, 1080)
            verify(p.x >= 0 && p.x <= 1920)
            verify(p.y >= 0 && p.y <= 1080)
            verify(Math.abs(p.x / 1920 - fish.x / frame.width) < 0.000001)
            verify(Math.abs(p.y / 1080 - fish.y / frame.height) < 0.000001)
        }
        compare(JSON.stringify(frame), before)
    }
}
''' % (json.dumps(helper.as_uri()), json.dumps(frame))
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        env.pop("WAYLAND_DISPLAY", None)
        env.pop("QT_QPA_PLATFORMTHEME", None)
        with tempfile.TemporaryDirectory(prefix="omarcharium-qml-") as directory:
            fixture = Path(directory) / "tst_generated.qml"
            fixture.write_text(source)
            result = subprocess.run([runner, "-input", str(fixture)], env=env,
                                    text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr + json.dumps(frame))
