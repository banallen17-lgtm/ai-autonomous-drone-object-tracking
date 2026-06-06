# Research Log

## Entry Format

Each time I work on the project, I will record:

- Date:
- Goal:
- What I did:
- What worked:
- What failed:
- What I learned:
- Next step:

---

## Entry 1

- Date: 6/5/2026
- Goal: Start project planning and GitHub documentation.
- What I did: Created the GitHub repository structure, README, project proposal, roadmap, research log, and safety ethics document.
- What worked: Sucessfully visualized desired project plan for AI implemented drone. Organization and planned individual milestone and project architecture.
- What failed: Implementing AI agents to VS code for effitient debugging. Next entery will mention results.
- What I learned: Operation of Github on both website and desktop.
- Next step: Research possible drone kits, flight controllers, onboard computers, and simulation tools.

## Entry 2

* Date: 6/6/2026
* Goal: Establish a functional computer vision system capable of detecting and tracking objects through a live camera feed.
* What I did: Connected a USB camera to the computer and implemented a YOLOv8 object detection system using Python and OpenCV. Successfully displayed bounding boxes around detected objects and verified real-time detection performance. Set up VS Code development environment and experimented with AI coding assistants for debugging and development support.
* What worked: The camera successfully interfaced with the detection model and accurately identified multiple objects in real time, including people, cell phones, and bottles. Object detection performance was stable and responsive enough for future drone integration. Successfully configured local AI assistance using Ollama and Continue in VS Code.
* What failed: Initial attempts to use cloud-based AI assistants were limited by API credit restrictions. Continue initially failed to access project files correctly, requiring additional configuration. Object detection alone did not maintain target identity across frames.
* What I learned: Learned the fundamentals of integrating YOLOv8 with OpenCV, how object detection differs from object tracking, and how local large language models can assist software development workflows. Also gained experience debugging Python computer vision applications.
* Next step: Implement persistent object tracking using ByteTrack and develop a target selection system capable of following a specific object over time.

## Entry 3

* Date: 6/6/2026
* Goal: Improve the object detection system by introducing persistent target tracking and motion prediction.
* What I did: Integrated ByteTrack into the YOLO detection pipeline to assign unique IDs to detected objects. Developed a target selection system that automatically locks onto a detected cell phone and displays real-time position information. Implemented a Kalman Filter to predict future target positions and provide directional guidance relative to the center of the camera frame. Experimented with target re-identification methods to recover tracking after temporary target loss.
* What worked: Successfully tracked individual objects across multiple frames using ByteTrack IDs. The system could automatically select and follow a target phone while displaying movement directions such as left, right, up, and down. Kalman-based motion prediction improved tracking stability and demonstrated the foundation for future autonomous drone navigation.
* What failed: Tracking performance degraded when the target moved rapidly or became partially occluded. ByteTrack occasionally reassigned new IDs to the same object, causing the tracking system to lose target continuity. Re-identification methods improved recovery but were not sufficiently reliable for high-speed tracking.
* What I learned: Learned how multi-object tracking systems maintain object identity, how Kalman Filters estimate future object positions, and the limitations of ID-based tracking systems. Discovered that robust autonomous tracking requires combining object detection, visual tracking, motion prediction, and target re-identification techniques.
* Next step: Replace reliance on ByteTrack IDs with a hybrid tracking architecture using YOLOv8, CSRT visual tracking, and Kalman prediction to create a more robust target-following system suitable for future drone deployment.


