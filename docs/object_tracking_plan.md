# Object Tracking Plan

## Goal

The goal of this stage is to build a camera-based AI vision system that can detect and track a selected object in real time.

## First Target

The first target should be a simple non-human object, such as:

- colored box
- water bottle
- toy car
- backpack
- ArUco marker
- AprilTag marker

## Tracking Options

### Option 1: OpenCV Color Tracking

Pros:
- Simple
- Fast
- Good for first prototype

Cons:
- Sensitive to lighting
- Only works well with clear colors

### Option 2: YOLO Object Detection

Pros:
- More advanced
- Can detect real-world objects
- Better for research presentation

Cons:
- Requires more setup
- Needs stronger computer for real-time performance

### Option 3: ArUco or AprilTag Tracking

Pros:
- Very accurate
- Great for robotics
- Easy to measure position

Cons:
- Requires printed markers
- Less “AI-looking” than YOLO

## Current Decision

Start with OpenCV or ArUco tracking first, then upgrade to YOLO later.

## Success Criteria

The system should be able to:

- Open webcam video
- Detect the target
- Draw a box or marker around it
- Track its center position
- Output whether the target is left, right, center, closer, or farther
