# Project Roadmap

Baseline: September 16, 2026, commit `9a824be`. Checked items indicate existing code or documentation, not independently measured performance.

## Completed prototype milestones

- [x] Create repository, proposal, research log, and safety plan.
- [x] Document preliminary hardware options.
- [x] Implement USB-camera YOLO detection and save demonstration images.
- [x] Implement YOLO + CSRT tracking with Kalman prediction.
- [x] Display virtual directional commands and FPS.
- [x] Build a basic 2D pursuit simulation.
- [x] Add multiple targets, manual selection, field-of-view limits, and following distance.
- [x] Add separate camera/body headings and target memory.
- [x] Add velocity prediction to the advanced simulation.

## Priority 1: Repository baseline

- [x] Identify primary scripts and distinguish historical versions.
- [x] Update README links and current progress.
- [x] Add ignore rules and lightweight repository checks.
- [ ] Resolve OpenCV package overlap and define reproducible dependencies.
- [ ] Validate installation and documented launch commands in a fresh environment.
- [ ] Record model weight provenance and download/version policy.

Acceptance: a new checkout has accurate documentation, passes repository checks, and can launch the primary demos using a documented, validated environment.

## Priority 2: Simulation correctness

Primary file: [drone_tracking_advanced.py](../simulation/drone_tracking_advanced.py).

- [ ] Clear all observation, velocity, and prediction state on target changes.
- [ ] Remove duplicate search rotation and restore camera scanning during reacquisition.
- [ ] Separate true world state from observations available to the controller.
- [ ] Handle elapsed time and observation gaps correctly.
- [ ] Apply consistent control/physics ordering and enforce world boundaries.
- [ ] Extract simulation steps from rendering; add seeded, non-interactive regression scenarios.

Acceptance: target switching cannot reuse old target state; lost targets cannot supply hidden positions to control; search rates and boundaries hold in repeatable tests.

## Priority 3: Vision correctness and setup

Primary file: [yolo_tracking.py](../vision/object_detection/yolo_tracking.py).

- [ ] Resolve and verify CSRT dependencies in a clean environment.
- [ ] Add explicit observed, predicted, lost, and searching states.
- [ ] Reject implausible reacquisition candidates.
- [ ] Use elapsed time in prediction and virtual movement.
- [ ] Reset Kalman uncertainty and virtual control state consistently.
- [ ] Add import-safe entry points, configurable source/model settings, and reliable cleanup.
- [ ] Support recorded-video input for repeatable evaluation.

Acceptance: reset produces a fresh state; invalid/lost tracking cannot appear as a valid measured command; acquisition and loss scenarios are repeatable without a live camera.

## Priority 4: Measure and refine

- [ ] Record FPS, latency, center error, loss duration, and reacquisition success.
- [ ] Measure simulation following-distance error and boundary violations.
- [ ] Compare behavior before/after each fix with the same scenarios.
- [ ] Tune gimbal, prediction, and tracking parameters from results.
- [ ] Add experiment summaries and a current demo recording.

## Priority 5: Integration and future scope

- [ ] Define a shared timestamped observation/control interface.
- [ ] Connect the vision pipeline to a suitable simulated camera environment.
- [ ] Evaluate 3D simulation options after the 2D baseline is stable.
- [ ] Add depth estimation, path planning, and obstacle avoidance.
- [ ] Finalize hardware selection and assemble/test manual flight.
- [ ] Implement flight-controller communication and manual override.
- [ ] Validate controlled autonomous hardware tests.
- [ ] Write the research paper and prepare science fair materials.

The original summer timeline is historical. Schedule and hardware decisions remain open.
