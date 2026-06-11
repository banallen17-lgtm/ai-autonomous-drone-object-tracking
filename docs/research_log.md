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

## Entry 4

* Date: 6/8/2026
* Goal: Improve object tracking reliability and begin autonomous drone simulation development.
* What I did: Replaced ID-dependent tracking with a hybrid YOLO + CSRT tracking architecture. Improved target persistence through visual tracking and Kalman prediction. Implemented virtual drone control commands and developed a 2D autonomous drone simulation environment. Added vision radius, search mode, target reacquisition, target evasion behavior, camera field of view limitations, confidence tracking, and multi-target tracking capabilities.
* What worked: The CSRT tracker significantly improved tracking stability compared to relying solely on ByteTrack IDs. The drone simulation successfully demonstrated autonomous target following, search behavior, target reacquisition, and persistent target locking in a multi-target environment. The bird evasion system created a more realistic tracking scenario.
* What failed: Initial simulation attempts used perfect target information, making the environment unrealistic. Multi-target implementation required restructuring portions of the simulation and revealed issues with target selection and variable management. Several debugging iterations were needed to correctly integrate target locking.
* What I learned: Real-world tracking systems require more than object detection. Maintaining target identity, handling target loss, and reacquiring targets are major challenges in autonomous systems. I also learned how tracking, control systems, and autonomous decision-making interact within a robotics pipeline.
* Next step: Implement target memory and target reacquisition logic for multi-target environments. Begin designing a higher-fidelity simulation architecture and prepare for future 3D simulation using PyBullet.

## Entry 5

* Date: 6/10/2026
* Goal: Improve the autonomous drone simulation by adding target memory, reacquisition behavior, and camera gimbal simulation.
* What I did: Expanded the 2D autonomous drone simulation from simple target following into a more realistic autonomous tracking system. Added multi-target tracking, manual target selection by bird ID, last-known-position memory, REACQUIRING and SEARCHING states, local search behavior around the last seen marker, tracking confidence, and separate camera heading from drone body heading. Also shifted the roadmap toward camera gimbal and servo control simulation before moving into full 3D PyBullet simulation.
* What worked: The drone can now track a selected target, remember its last known location after losing sight, move/search around that last seen area, and reacquire the target. Manual target selection makes the simulation closer to a real operator-controlled target assignment system. Separating camera direction from drone body direction also made the simulation more realistic for future gimbal control.
* What failed: Some experimental versions of the gimbal logic caused camera over-rotation, duplicated reacquisition logic, and confusing search behavior. The simulation needed several debugging iterations to cleanly separate drone movement, camera movement, target memory, and heading control.
* What I learned: A realistic autonomous tracking system requires more than pursuit logic. The drone needs memory, search behavior, target identity persistence, and a camera control layer. I also learned that a camera gimbal should be modeled separately from the drone body because real drones often track targets with the camera before the drone fully turns.
* Next step: Continue improving the camera gimbal simulation, then move into servo control simulation. After the gimbal and servo logic are stable, begin building a 3D PyBullet simulation.
