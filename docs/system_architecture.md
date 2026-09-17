# System Architecture

## Current implementation

The repository contains two independent prototypes.

### Live-camera vision

```text
USB camera (Windows DirectShow)
  -> YOLO cell-phone acquisition
  -> CSRT tracking
  -> Kalman position prediction
  -> on-screen direction and virtual control indications
```

[yolo_tracking.py](../vision/object_detection/yolo_tracking.py) is the primary tracker. YOLO is used for acquisition and reacquisition; periodic correction is optional and disabled by default. The script does not command a flight controller. Its moving virtual center is an overlay, not a simulated camera.

[webcam_yolo.py](../vision/object_detection/webcam_yolo.py) is the detection-only demo. [camera_test.py](../vision/object_detection/camera_test.py) diagnoses camera indices. ByteTrack belongs to earlier experiments recorded in the research log.

### 2D simulation

```text
Synthetic target movement
  -> range/field-of-view visibility calculation
  -> confidence, memory, and target prediction
  -> following/reacquisition/search logic
  -> drone and camera heading updates
  -> OpenCV rendering
```

[drone_tracking_advanced.py](../simulation/drone_tracking_advanced.py) is the primary simulation. The earlier [gimbal prototype](../simulation/simulation/drone_tracking_v2.py) and [pursuit demo](../simulation/2d_drone_tracking_sim.py) remain historical references.

The simulator uses world coordinates directly; it does not infer positions from camera images. Visibility and controller state are not yet cleanly separated, which is a priority correctness fix. Motion and timers currently advance per frame.

## Current limitations

- No shared interface connects vision and simulation.
- No depth estimation, obstacle avoidance, 3D physics, ROS 2/Gazebo nodes, or hardware control is implemented.
- Camera capture, tracking, control indications, and display share a top-level loop.
- Simulation dynamics, perception, decision logic, and rendering share a top-level loop.
- Quantitative experiment logging and behavioral regression tests are pending.
- The Windows x64 / Python 3.12 dependency snapshot passes isolated CSRT and YOLO CPU checks; live camera and interactive launch validation remain pending. See [dependency setup](dependencies.md).

## Planned integration

Separate capture/world updates, observations, state estimation, control, rendering, and logging. A future observation interface should include timestamp, target identity, measured position/bounding box, confidence, visibility, and prediction age. A controller must distinguish measurements from stale estimates.

First validate target switching, loss, reacquisition, timing, and reset. Then connect the components through this interface and evaluate a simulated camera environment.

The longer-term architecture is:

```text
Camera / sensors -> perception -> state estimation -> navigation
  -> flight controller -> drone movement
                         -> experiment logging
```

Flight-controller selection, companion computing, depth sensors, and manual override are planned components. See the [hardware notes](hardware_selection.md), [roadmap](roadmap.md), and [safety plan](safety_ethics.md).
