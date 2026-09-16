from ultralytics import YOLO
import cv2
import numpy as np
import time

# -----------------------------
# SETTINGS
# -----------------------------
MODEL_PATH = "yolov8n.pt"
CAMERA_INDEX = 0
TARGET_CLASS = "cell phone"

DEAD_ZONE = 50
YOLO_CONF = 0.25          # 0.15 was very low and can cause unstable reacquisition
REDETECT_EVERY = 60       # only used for optional correction while tracking
CONTROL_THRESHOLD = 0.15
MAX_LOST_FRAMES = 10      # do not instantly reset tracker after one bad frame
USE_PERIODIC_YOLO_CORRECTION = False  # turn True only if tracker slowly drifts

SIMULATION_MODE = True
SIM_SPEED = 75

# -----------------------------
# LOAD MODEL
# -----------------------------
model = YOLO(MODEL_PATH)

# -----------------------------
# KALMAN FILTER
# -----------------------------
kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array(
    [[1, 0, 0, 0],
     [0, 1, 0, 0]],
    np.float32
)
kalman.transitionMatrix = np.array(
    [[1, 0, 1, 0],
     [0, 1, 0, 1],
     [0, 0, 1, 0],
     [0, 0, 0, 1]],
    np.float32
)
kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.08
kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.5
kalman.errorCovPost = np.eye(4, dtype=np.float32)
kalman_initialized = False

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def initialize_kalman(x, y):
    global kalman_initialized
    state = np.array(
        [[np.float32(x)],
         [np.float32(y)],
         [0],
         [0]],
        dtype=np.float32
    )
    kalman.statePre = state
    kalman.statePost = state
    kalman_initialized = True


def create_csrt_tracker():
    if hasattr(cv2, "legacy") and hasattr(cv2.legacy, "TrackerCSRT_create"):
        return cv2.legacy.TrackerCSRT_create()
    return cv2.TrackerCSRT_create()


def bbox_center(bbox):
    x, y, w, h = bbox
    return int(x + w / 2), int(y + h / 2)


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def calculate_control_signal(error_x, error_y, frame_width, frame_height):
    pan_signal = clamp(error_x / (frame_width / 2), -1.0, 1.0)
    tilt_signal = clamp(error_y / (frame_height / 2), -1.0, 1.0)
    return pan_signal, tilt_signal


def get_virtual_drone_command(pan_signal, tilt_signal):
    if pan_signal > CONTROL_THRESHOLD:
        yaw_command = "YAW RIGHT"
    elif pan_signal < -CONTROL_THRESHOLD:
        yaw_command = "YAW LEFT"
    else:
        yaw_command = "YAW STABLE"

    if tilt_signal > CONTROL_THRESHOLD:
        vertical_command = "MOVE DOWN"
    elif tilt_signal < -CONTROL_THRESHOLD:
        vertical_command = "MOVE UP"
    else:
        vertical_command = "ALTITUDE STABLE"

    return yaw_command, vertical_command


def yolo_find_target(frame, preferred_center=None):
    """Find the best target. If preferred_center exists, choose the detection closest to the current tracked target."""
    results = model(frame, conf=YOLO_CONF, verbose=False)
    candidates = []

    if results and results[0].boxes is not None:
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            conf = float(box.conf[0])

            if class_name != TARGET_CLASS:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            bbox = (x1, y1, x2 - x1, y2 - y1)
            cx, cy = bbox_center(bbox)

            if preferred_center is None:
                score = conf
            else:
                px, py = preferred_center
                dist = np.hypot(cx - px, cy - py)
                score = conf - 0.002 * dist

            candidates.append((score, bbox, conf))

    if not candidates:
        return None, 0

    candidates.sort(key=lambda item: item[0], reverse=True)
    _, best_box, best_conf = candidates[0]
    return best_box, best_conf

# -----------------------------
# CAMERA SETUP
# -----------------------------
cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

tracker = None
tracking_active = False
frame_count = 0
lost_frames = 0
paused = False

virtual_center_x = None
virtual_center_y = None
last_bbox = None
last_center = None
predicted_x = None
predicted_y = None

prev_time = time.time()
fps = 0

print("Starting fixed YOLO + CSRT + Kalman + Virtual Drone Command System...")
print("Press q to quit | r to reset target | p to pause/resume")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    frame_count += 1
    annotated_frame = frame.copy()
    frame_height, frame_width = frame.shape[:2]
    frame_center_x = frame_width // 2
    frame_center_y = frame_height // 2

    now = time.time()
    dt = now - prev_time
    prev_time = now
    if dt > 0:
        fps = 0.9 * fps + 0.1 * (1.0 / dt)

    if virtual_center_x is None:
        virtual_center_x = frame_center_x
        virtual_center_y = frame_center_y

    if paused:
        cv2.putText(annotated_frame, "PAUSED - Press P to resume", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.imshow("YOLO + CSRT + Drone Command", annotated_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("p"):
            paused = False
            print("Tracking resumed.")
        elif key == ord("q"):
            break
        continue

    # --------------------------------------------------
    # 1. YOLO only when we do NOT currently have a tracker
    # --------------------------------------------------
    if not tracking_active:
        target_bbox, target_conf = yolo_find_target(frame, preferred_center=last_center)
        if target_bbox is not None:
            tracker = create_csrt_tracker()
            tracker.init(frame, target_bbox)
            tracking_active = True
            lost_frames = 0
            last_bbox = target_bbox
            cx, cy = bbox_center(target_bbox)
            last_center = (cx, cy)
            initialize_kalman(cx, cy)
            print(f"Target acquired with YOLO. Confidence: {target_conf:.2f}")

    # --------------------------------------------------
    # 2. CSRT tracks every frame. Do NOT reset unless lost
    # --------------------------------------------------
    if tracking_active and tracker is not None:
        success, bbox = tracker.update(frame)

        if success:
            lost_frames = 0
            x, y, w, h = map(int, bbox)
            last_bbox = (x, y, w, h)
            cx, cy = bbox_center(last_bbox)
            last_center = (cx, cy)

            measurement = np.array([[np.float32(cx)], [np.float32(cy)]], dtype=np.float32)
            prediction = kalman.predict()
            kalman.correct(measurement)
            predicted_x = int(prediction[0, 0])
            predicted_y = int(prediction[1, 0])

            # Optional correction: disabled by default because YOLO is slow on CPU
            if USE_PERIODIC_YOLO_CORRECTION and frame_count % REDETECT_EVERY == 0:
                yolo_bbox, yolo_conf = yolo_find_target(frame, preferred_center=last_center)
                if yolo_bbox is not None:
                    tracker = create_csrt_tracker()
                    tracker.init(frame, yolo_bbox)
                    last_bbox = yolo_bbox
                    last_center = bbox_center(yolo_bbox)
                    print(f"YOLO correction applied. Confidence: {yolo_conf:.2f}")

        else:
            lost_frames += 1
            prediction = kalman.predict()
            predicted_x = int(prediction[0, 0])
            predicted_y = int(prediction[1, 0])
            cv2.putText(annotated_frame, f"CSRT lost frame {lost_frames}/{MAX_LOST_FRAMES}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if lost_frames >= MAX_LOST_FRAMES:
                tracking_active = False
                tracker = None
                kalman_initialized = False
                print("Tracker lost target. Re-detecting with YOLO...")

        # --------------------------------------------------
        # 3. Draw/control if we have either measured or predicted position
        # --------------------------------------------------
        if predicted_x is not None and predicted_y is not None:
            if SIMULATION_MODE:
                error_x = predicted_x - int(virtual_center_x)
                error_y = predicted_y - int(virtual_center_y)
            else:
                error_x = predicted_x - frame_center_x
                error_y = predicted_y - frame_center_y

            pan_signal, tilt_signal = calculate_control_signal(error_x, error_y, frame_width, frame_height)
            yaw_command, vertical_command = get_virtual_drone_command(pan_signal, tilt_signal)

            if SIMULATION_MODE:
                virtual_center_x += error_x * 0.05
                virtual_center_y += error_y * 0.05
                virtual_center_y += tilt_signal * SIM_SPEED
                virtual_center_x = clamp(virtual_center_x, 0, frame_width)
                virtual_center_y = clamp(virtual_center_y, 0, frame_height)

            if error_x > DEAD_ZONE:
                direction_x = "MOVE RIGHT"
            elif error_x < -DEAD_ZONE:
                direction_x = "MOVE LEFT"
            else:
                direction_x = "CENTERED X"

            if error_y > DEAD_ZONE:
                direction_y = "MOVE DOWN"
            elif error_y < -DEAD_ZONE:
                direction_y = "MOVE UP"
            else:
                direction_y = "CENTERED Y"

            if last_bbox is not None:
                x, y, w, h = last_bbox
                cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.circle(annotated_frame, last_center, 5, (0, 0, 255), -1)
                cv2.putText(annotated_frame, "TARGET - CSRT", (x, max(y - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            cv2.circle(annotated_frame, (predicted_x, predicted_y), 8, (0, 255, 255), -1)
            cv2.putText(annotated_frame, f"Prediction: ({predicted_x}, {predicted_y})", (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(annotated_frame, f"Error X: {error_x}, Error Y: {error_y}", (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(annotated_frame, f"Direction: {direction_x} | {direction_y}", (20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(annotated_frame, f"Control - Pan: {pan_signal:.2f}, Tilt: {tilt_signal:.2f}", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(annotated_frame, f"Virtual Drone: {yaw_command} | {vertical_command}", (20, 190),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    else:
        cv2.putText(annotated_frame, "Searching with YOLO...", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Draw real camera center
    cv2.circle(annotated_frame, (frame_center_x, frame_center_y), 5, (100, 100, 100), -1)

    # Draw virtual drone/camera center
    display_center_x = int(virtual_center_x) if SIMULATION_MODE else frame_center_x
    display_center_y = int(virtual_center_y) if SIMULATION_MODE else frame_center_y
    cv2.circle(annotated_frame, (display_center_x, display_center_y), 7, (255, 255, 255), -1)
    cv2.line(annotated_frame, (display_center_x - 25, display_center_y),
             (display_center_x + 25, display_center_y), (255, 255, 255), 2)
    cv2.line(annotated_frame, (display_center_x, display_center_y - 25),
             (display_center_x, display_center_y + 25), (255, 255, 255), 2)
    cv2.putText(annotated_frame, "Virtual Drone Center", (display_center_x + 10, display_center_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (20, frame_height - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("YOLO + CSRT + Drone Command", annotated_frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break
    elif key == ord("r"):
        tracker = None
        tracking_active = False
        kalman_initialized = False
        lost_frames = 0
        last_bbox = None
        last_center = None
        predicted_x = None
        predicted_y = None
        print("Target reset.")
    elif key == ord("p"):
        paused = True
        print("Tracking paused.")

cap.release()
cv2.destroyAllWindows()
