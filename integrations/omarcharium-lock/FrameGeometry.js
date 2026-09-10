.pragma library

function point(entity, frame, width, height) {
    return {x: entity.x * width / frame.width, y: entity.y * height / frame.height}
}
