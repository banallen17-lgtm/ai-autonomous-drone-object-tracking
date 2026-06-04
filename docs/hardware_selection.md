# Hardware Selection

## Objective

The goal is to select a drone platform and hardware capable of supporting real-time object tracking, autonomous navigation, and future AI-based obstacle avoidance while remaining affordable and achievable within a summer project timeline.

---

# Design Requirements

The system should be capable of:

* Stable quadcopter flight
* Real-time camera streaming
* Onboard AI processing
* Object detection and tracking
* Future obstacle avoidance
* Indoor testing
* Safe manual override
* Science fair demonstration

---

# Flight Controller Options

## Option 1: Pixhawk 6C

Pros:

* Industry standard
* Compatible with ArduPilot and PX4
* Large community support
* Expandable

Cons:

* More expensive

Status:
Current preferred option

---

## Option 2: Pixhawk 4

Pros:

* Reliable
* Well documented
* Lower cost

Cons:

* Older hardware

Status:
Backup option

---

# Companion Computer Options

## Option 1: Raspberry Pi 5

Pros:

* Affordable
* Easy to learn
* Large community support
* Good for OpenCV and basic AI

Cons:

* Slower than Jetson

Status:
Current preferred option

---

## Option 2: Jetson Orin Nano

Pros:

* Excellent AI performance
* Better for YOLO models
* Better long-term platform

Cons:

* Higher cost

Status:
Future upgrade option

---

# Camera Options

## Option 1: USB Webcam

Pros:

* Cheap
* Easy setup
* Good for early testing

Cons:

* Not optimized for drones

Status:
Preferred for prototype

---

## Option 2: Raspberry Pi Camera Module

Pros:

* Lightweight
* Designed for Raspberry Pi

Cons:

* Requires Raspberry Pi

Status:
Possible future option

---

# Drone Platform Options

## Option 1: Drone Kit

Pros:

* Faster development
* Reliable frame
* Easier troubleshooting

Cons:

* Less customization

Status:
Current preferred option

---

## Option 2: Full Custom Build

Pros:

* Maximum learning experience
* Full customization

Cons:

* Much more difficult
* Higher chance of delays

Status:
Not recommended for first prototype

---

# Preliminary Recommendation

Current recommended architecture:

Flight Controller:

* Pixhawk 6C

Companion Computer:

* Raspberry Pi 5

Camera:

* USB Webcam

Drone Platform:

* Quadcopter Kit

Development Environment:

* Python
* OpenCV
* ROS 2
* Gazebo Simulation

Reasoning:

This configuration provides the best balance between cost, learning value, project scope, and likelihood of producing a working prototype by the end of summer.

---

# Future Hardware Upgrades

Possible future additions:

* LiDAR
* Intel RealSense depth camera
* Jetson Orin Nano
* GPS module
* Optical flow sensor
* Additional obstacle avoidance sensors
