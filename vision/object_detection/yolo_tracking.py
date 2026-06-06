from ultralytics import YOLO
import cv2
import numpy as np
import math

MODEL_PATH = "yolov8n.pt"
CAMERA_INDEX = 0
TARGET_CLASS = "cell phone"

DEAD_ZONE = 50
MAX_LOST_FRAMES = 15
REID_DISTANCE = 180

model = YOLO(MODEL_PATH)

kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
kalman.transitionMatrix = np.array(
    [[1, 0, 1, 0],
     [0, 1, 0, 1],
     [0, 0, 1, 0],
     [0, 0, 0, 1]],
    np.float32
)

kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.5
kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.3
kalman.errorCovPost = np.eye(4, dtype=np.float32)

kalman_initialized = False
target_id = None
lost_frames = 0
last_prediction = None
paused = False


def initialize_kalman(x, y):
    global kalman_initialized

    state = np.array([[np.float32(x)], [np.float32(y)], [0], [0]], dtype=np.float32)
    kalman.statePre = state
    kalman.statePost = state
    kalman_initialized = True


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Starting tracking...")
print("Press q to quit, r to reset, p to pause.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame.")
        break

    if paused:
        cv2.putText(frame, "PAUSED - Press P to resume", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.imshow("YOLO Target Tracking", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("p"):
            paused = False
        elif key == ord("q"):
            break
        continue

    frame_height, frame_width = frame.shape[:2]
    frame_center_x = frame_width // 2
    frame_center_y = frame_height // 2

    annotated_frame = frame.copy()

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=0.15,
        iou=0.5,
        verbose=False
    )

    target_found = False
    target_measurement = None
    best_reid = None
    best_reid_distance = float("inf")

    if results and results[0].boxes is not None:
        boxes = results[0].boxes

        for box in boxes:
            if box.id is None:
                continue

            track_id = int(box.id[0])
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            object_center_x = (x1 + x2) // 2
            object_center_y = (y1 + y2) // 2
            center = (object_center_x, object_center_y)

            color = (255, 0, 0)
            label = f"{class_name} ID:{track_id}"

            # First time selecting target
            if target_id is None and class_name == TARGET_CLASS:
                target_id = track_id
                initialize_kalman(object_center_x, object_center_y)
                lost_frames = 0
                last_prediction = center
                print(f"Target selected: {TARGET_CLASS} ID {target_id}")

            # Normal tracking by same ID
            if track_id == target_id:
                target_found = True
                lost_frames = 0
                target_measurement = center
                color = (0, 255, 0)
                label = f"TARGET {class_name} ID:{track_id}"

            # Re-identification: new ID but close to predicted position
            elif (
                target_id is not None
                and class_name == TARGET_CLASS
                and last_prediction is not None
            ):
                d = distance(center, last_prediction)

                if d < best_reid_distance:
                    best_reid_distance = d
                    best_reid = {
                        "track_id": track_id,
                        "center": center,
                        "box": (x1, y1, x2, y2),
                    }

            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(annotated_frame, center, 5, color, -1)
            cv2.putText(annotated_frame, label, (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # If original ID was not found, try to re-identify target
    if not target_found and best_reid is not None and best_reid_distance < REID_DISTANCE:
        target_id = best_reid["track_id"]
        target_measurement = best_reid["center"]
        target_found = True
        lost_frames = 0
        print(f"Re-identified target with new ID: {target_id}")

    # Kalman update if target is found
    if target_found and target_measurement is not None:
        mx, my = target_measurement

        if not kalman_initialized:
            initialize_kalman(mx, my)

        measurement = np.array([[np.float32(mx)], [np.float32(my)]], dtype=np.float32)

        prediction = kalman.predict()
        kalman.correct(measurement)

        predicted_x = int(prediction[0, 0])
        predicted_y = int(prediction[1, 0])
        last_prediction = (predicted_x, predicted_y)

        error_x = predicted_x - frame_center_x
        error_y = predicted_y - frame_center_y

        direction_x = "CENTERED X"
        direction_y = "CENTERED Y"

        if error_x > DEAD_ZONE:
            direction_x = "MOVE RIGHT"
        elif error_x < -DEAD_ZONE:
            direction_x = "MOVE LEFT"

        if error_y > DEAD_ZONE:
            direction_y = "MOVE DOWN"
        elif error_y < -DEAD_ZONE:
            direction_y = "MOVE UP"

        cv2.circle(annotated_frame, last_prediction, 8, (0, 255, 255), -1)
        cv2.putText(annotated_frame, "Predicted Position",
                    (predicted_x + 10, predicted_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.putText(annotated_frame, f"Target ID: {target_id}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(annotated_frame, f"Predicted Error X: {error_x}, Y: {error_y}",
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(annotated_frame, f"{direction_x} | {direction_y}",
                    (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # If target is temporarily lost, keep predicting
    elif target_id is not None and kalman_initialized:
        prediction = kalman.predict()

        predicted_x = int(prediction[0, 0])
        predicted_y = int(prediction[1, 0])
        last_prediction = (predicted_x, predicted_y)

        lost_frames += 1

        cv2.circle(annotated_frame, last_prediction, 8, (0, 255, 255), -1)
        cv2.putText(annotated_frame, f"Predicting lost target... {lost_frames}/{MAX_LOST_FRAMES}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if lost_frames > MAX_LOST_FRAMES:
            target_id = None
            kalman_initialized = False
            last_prediction = None
            lost_frames = 0
            print("Target lost completely. Waiting for new target.")

    # Draw camera center
    cv2.circle(annotated_frame, (frame_center_x, frame_center_y), 6, (0, 0, 255), -1)
    cv2.line(annotated_frame, (frame_center_x - 20, frame_center_y),
             (frame_center_x + 20, frame_center_y), (0, 0, 255), 2)
    cv2.line(annotated_frame, (frame_center_x, frame_center_y - 20),
             (frame_center_x, frame_center_y + 20), (0, 0, 255), 2)

    cv2.imshow("YOLO Target Tracking", annotated_frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break
    elif key == ord("r"):
        target_id = None
        kalman_initialized = False
        last_prediction = None
        lost_frames = 0
        print("Target reset.")
    elif key == ord("p"):
        paused = True
        print("Tracking paused.")

cap.release()
cv2.destroyAllWindows()