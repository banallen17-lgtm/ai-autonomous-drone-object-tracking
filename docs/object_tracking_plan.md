# Object Tracking Plan

## Current baseline

[The primary tracker](../vision/object_detection/yolo_tracking.py) acquires a cell phone with YOLOv8, follows its bounding box with CSRT, predicts its center with a Kalman filter, and displays virtual movement indications. Earlier ByteTrack work is recorded in the [research log](research_log.md).

The current default target is a cell phone. Alternative non-human objects or markers can be evaluated later. Color/ArUco tracking was an initial proposal, not the current implementation.

## Repair priorities

1. Resolve OpenCV dependency overlap and verify CSRT in a fresh environment.
2. Separate observed, predicted, lost, and searching states.
3. Gate reacquisition so a distant same-class detection is not automatically accepted.
4. Account for elapsed time and limit stale prediction use.
5. Reset filter uncertainty and virtual center consistently.
6. Extract import-safe processing and guarantee capture/window cleanup.
7. Make camera/video source and model settings configurable.

## Evaluation

Use recorded inputs with known target locations, including slow movement, rapid movement, temporary occlusion, target exit/reentry, and a second object of the same class.

Record center error, FPS/latency, lost duration, successful reacquisition, and identity switches. Compare identical clips before and after changes. Include reset and pause/resume behavior.

Success means repeatable results with explicit tracking validity. Numerical performance thresholds should be set after baseline measurements; no accuracy or FPS guarantee is established yet.

## Integration

Publish timestamped observations and validity state for a future simulation interface. The current virtual-center overlay is not a closed-loop flight or camera simulation. Complete the repairs and baseline measurements before integration.
