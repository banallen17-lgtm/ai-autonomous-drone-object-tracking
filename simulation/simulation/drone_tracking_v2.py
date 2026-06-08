import cv2
import numpy as np
import random
import math

# ------------------
# WINDOW
# ------------------

WIDTH = 1200
HEIGHT = 800

# ------------------
# DRONE
# ------------------

drone_x = 200.0
drone_y = 400.0

drone_vx = 0.0
drone_vy = 0.0

MAX_SPEED = 8
ACCELERATION = 0.25
FRICTION = 0.98

drone_heading = 0

LOCK_RADIUS = 40
VISION_RADIUS = 400
FOLLOW_DISTANCE = 150

# ------------------
# BIRD
# ------------------

BIRD_NORMAL_SPEED = 3
BIRD_ESCAPE_SPEED = 6
BIRD_DETECTION_RADIUS = 220

bird_x = 900.0
bird_y = 400.0

bird_vx = 3
bird_vy = 2

direction_timer = 0
target_detected = False
search_mode = False

# ------------------
# MAIN LOOP
# ------------------

while True:

    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # ------------------
    # BIRD AI
    # ------------------

    bird_error_x = bird_x - drone_x
    bird_error_y = bird_y - drone_y
    bird_distance_from_drone = math.sqrt(bird_error_x**2 + bird_error_y**2)

    if bird_distance_from_drone < BIRD_DETECTION_RADIUS:
        escape_x = bird_error_x / bird_distance_from_drone
        escape_y = bird_error_y / bird_distance_from_drone

        bird_vx += escape_x * 0.3
        bird_vy += escape_y * 0.3

        bird_vx = max(-BIRD_ESCAPE_SPEED, min(BIRD_ESCAPE_SPEED, bird_vx))
        bird_vy = max(-BIRD_ESCAPE_SPEED, min(BIRD_ESCAPE_SPEED, bird_vy))
    else:
        direction_timer += 1

        if direction_timer > 60:
            bird_vx += random.uniform(-1.5, 1.5)
            bird_vy += random.uniform(-1.5, 1.5)

            bird_vx = max(-BIRD_NORMAL_SPEED, min(BIRD_NORMAL_SPEED, bird_vx))
            bird_vy = max(-BIRD_NORMAL_SPEED, min(BIRD_NORMAL_SPEED, bird_vy))

            direction_timer = 0

    bird_state = "EVADING" if bird_distance_from_drone < BIRD_DETECTION_RADIUS else "NORMAL"
    bird_x += bird_vx
    bird_y += bird_vy

    if bird_x < 50:
        bird_x = 50
        bird_vx *= -1

    if bird_x > WIDTH - 50:
        bird_x = WIDTH - 50
        bird_vx *= -1

    if bird_y < 50:
        bird_y = 50
        bird_vy *= -1

    if bird_y > HEIGHT - 50:
        bird_y = HEIGHT - 50
        bird_vy *= -1

    cv2.putText(
        canvas,
        f"Bird State: {bird_state}",
        (20, 210),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 165, 255),
        2
    )
    # ------------------
    # DRONE TRACKING
    # ------------------

    error_x = bird_x - drone_x
    error_y = bird_y - drone_y

    distance = math.sqrt(error_x**2 + error_y**2)

    if distance <= VISION_RADIUS:
        target_detected = True
        search_mode = False
    else:
        target_detected = False
        search_mode = True

    status = "TRACKING" if target_detected else "SEARCHING"

    distance_error = distance - FOLLOW_DISTANCE

    if target_detected and abs(distance_error) > 20:

        direction_x = error_x / distance
        direction_y = error_y / distance

        control_strength = distance_error / FOLLOW_DISTANCE

        drone_vx += direction_x * ACCELERATION * control_strength
        drone_vy += direction_y * ACCELERATION * control_strength

    speed = math.sqrt(drone_vx**2 + drone_vy**2)

    if speed > MAX_SPEED:

        scale = MAX_SPEED / speed

        drone_vx *= scale
        drone_vy *= scale

    drone_vx *= FRICTION
    drone_vy *= FRICTION

    drone_x += drone_vx
    drone_y += drone_vy

    # ------------------
    # DRONE HEADING
    # ------------------

    if target_detected:

        drone_heading = math.atan2(
            bird_y - drone_y,
            bird_x - drone_x
        )

    else:

        drone_heading += 0.05

    # ------------------
    # DRAW BIRD
    # ------------------
    cv2.circle(
        canvas,
        (int(bird_x), int(bird_y)),
        15,
        (0, 0, 255),
        -1
    )

    cv2.circle(
        canvas,
        (int(bird_x), int(bird_y)),
        FOLLOW_DISTANCE,
        (0, 100, 255),
        1
    )

    cv2.putText(
        canvas,
        "BIRD",
        (int(bird_x) + 20, int(bird_y)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 0, 255),
        2
    )

    cv2.circle(
        canvas,
        (int(drone_x), int(drone_y)),
        VISION_RADIUS,
        (60, 60, 60),
        1
    )
    # ------------------
    # DRAW DRONE TRIANGLE
    # ------------------

    size = 25

    front_x = drone_x + math.cos(drone_heading) * size
    front_y = drone_y + math.sin(drone_heading) * size

    left_x = drone_x + math.cos(drone_heading + 2.5) * size
    left_y = drone_y + math.sin(drone_heading + 2.5) * size

    right_x = drone_x + math.cos(drone_heading - 2.5) * size
    right_y = drone_y + math.sin(drone_heading - 2.5) * size

    points = np.array([
        [front_x, front_y],
        [left_x, left_y],
        [right_x, right_y]
    ], dtype=np.int32)

    cv2.fillPoly(
        canvas,
        [points],
        (255, 0, 0)
    )

    # ------------------
    # TRACKING LINE
    # ------------------

    cv2.line(
        canvas,
        (int(drone_x), int(drone_y)),
        (int(bird_x), int(bird_y)),
        (0, 255, 0),
        2
    )

    # ------------------
    # TARGET LOCK
    # ------------------

    if distance < LOCK_RADIUS:

        cv2.putText(
            canvas,
            "TARGET LOCKED",
            (450, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            3
        )

        cv2.circle(
            canvas,
            (int(bird_x), int(bird_y)),
            30,
            (0, 255, 0),
            2
        )

    # ------------------
    # HUD
    # ------------------

    cv2.putText(
        canvas,
        f"Distance: {distance:.1f}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255,255,255),
        2
    )

    cv2.putText(
        canvas,
        f"Velocity: {speed:.2f}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255,255,255),
        2
    )

    cv2.putText(
        canvas,
        "AUTONOMOUS DRONE TRACKING V2",
        (20, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255,255,255),
        2
    )

    cv2.putText(
        canvas,
        f"Status: {status}",
        (20, 170),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0,255,255),
        2
    )

    cv2.imshow(
        "Autonomous Drone Tracking V2",
        canvas
    )

    key = cv2.waitKey(20)

    if key == ord("q"):
        break

cv2.destroyAllWindows()