# System Architecture

## Purpose

This document explains how the AI autonomous drone system will be organized. The system is divided into sensing, perception, decision-making, navigation, flight control, and data logging.

---

## High-Level System Flow

```text
Camera / Sensors
       ↓
Computer Vision Model
       ↓
Target Detection and Tracking
       ↓
Target Position Estimation
       ↓
Navigation and Path Planning
       ↓
Flight Controller
       ↓
Drone Motors and Movement
       ↓
Experiment Data Logging
```

---

## Main System Components

## 1. Camera and Sensors

The drone will use a camera to collect real-time visual information from the environment.

Possible sensors:

* USB camera
* Raspberry Pi camera
* IMU
* Depth camera
* LiDAR
* GPS for future outdoor testing

Purpose:

* Capture the target object
* Estimate drone movement
* Support future obstacle detection
* Provide data for navigation decisions

---

## 2. Computer Vision System

The computer vision system identifies the selected target object from the camera feed.

Possible methods:

* OpenCV color tracking
* ArUco marker tracking
* AprilTag tracking
* YOLO object detection

Initial plan:

Start with OpenCV or marker tracking because it is simpler and easier to test. Later, upgrade to YOLO for more advanced object detection.

Output:

```text
Target detected: yes/no
Target center: x, y
Target size: width, height
Confidence score: optional
```

---

## 3. Target Position Estimation

After the target is detected, the system estimates where the object is relative to the drone.

Example decisions:

```text
If target is left of center → move left
If target is right of center → move right
If target is too small → move forward
If target is too large → move backward
If target is centered → hover or continue tracking
```

This stage converts camera information into simple movement instructions.

---

## 4. Navigation and Path Planning

The navigation system decides how the drone should move based on the target position and the environment.

Basic version:

* Move toward target
* Keep target centered
* Maintain safe distance

Advanced version:

* Avoid obstacles
* Use depth estimation
* Plan smoother paths
* Use simulation to test safe navigation

---

## 5. Flight Controller

The flight controller handles low-level drone stability and motor control.

Possible options:

* Pixhawk
* PX4-compatible controller
* ArduPilot-compatible controller

Purpose:

* Stabilize the drone
* Control motors
* Read IMU data
* Receive movement commands from the companion computer

---

## 6. Companion Computer

The companion computer runs the AI and decision-making code.

Possible options:

* Raspberry Pi 5
* Jetson Orin Nano

Purpose:

* Run Python code
* Process camera input
* Run object detection
* Send movement commands to the flight controller
* Save experiment data

---

## 7. Data Logging

The system will record data for research and science fair analysis.

Possible data:

* Detection accuracy
* Tracking success rate
* Frame rate
* Latency
* Target position error
* Distance from target
* Obstacle avoidance success rate
* Battery/runtime data
* Failure cases

---

## MVP Architecture

The first working version will not control a real drone immediately.

The first version will be:

```text
Webcam
   ↓
OpenCV Tracking
   ↓
Target Center Detection
   ↓
Movement Command Output
```

Example output:

```text
Target detected
Target position: left
Command: move left
```

This allows the vision system to be tested safely before connecting it to drone hardware.

---

## Final Architecture Goal

The final goal is:

```text
Drone Camera
   ↓
Onboard Computer
   ↓
Object Detection Model
   ↓
Target Tracking Algorithm
   ↓
Navigation Planner
   ↓
Flight Controller
   ↓
Drone Movement
   ↓
Experiment Data
```

---

## Safety Design

The system should include:

* Manual override
* Emergency stop
* Low-speed testing
* Simulation before real flight
* Non-human target tracking
* Controlled testing environment
* Propeller guards when possible

---

## Current Development Priority

The current priority is to build and test the computer vision system first.

Next steps:

1. Test webcam input.
2. Build simple color tracking.
3. Output basic movement commands.
4. Save tracking data.
5. Upgrade to YOLO or marker-based tracking.
6. Test the system in simulation.
