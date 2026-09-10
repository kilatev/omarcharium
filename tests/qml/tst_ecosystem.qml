import QtQuick 2.15
import QtTest 1.3
import "../../integrations/omarcharium-lock/FrameGeometry.js" as Geometry

TestCase {
    name: "EcosystemPropertyTests"

    function test_world_position_scales_without_mutation() {
        var frame = {width: 80, height: 24}
        var fish = {x: 40, y: 12}
        var before = JSON.stringify(fish)
        var point = Geometry.point(fish, frame, 1920, 1080)
        compare(point.x, 960)
        compare(point.y, 540)
        compare(JSON.stringify(fish), before)
    }
}
