import cv2
import numpy as np
import random
import math

# ------------------
# WINDOW
# ------------------

WIDTH = 1000
HEIGHT = 700

# ------------------
# DRONE
# ------------------

drone_x = 200.0
drone_y = 350.0

drone_speed = 4

# ------------------
# BIRD
# ------------------

bird_x = 800.0
bird_y = 350.0

bird_vx = 3
bird_vy = 2

# ------------------
# LOOP
# ------------------

while True:

    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # ------------------
    # Move Bird
    # ------------------

    bird_x += bird_vx
    bird_y += bird_vy

    if bird_x < 50 or bird_x > WIDTH - 50:
        bird_vx *= -1

    if bird_y < 50 or bird_y > HEIGHT - 50:
        bird_vy *= -1

    # ------------------
    # Tracking Logic
    # ------------------

    error_x = bird_x - drone_x
    error_y = bird_y - drone_y

    distance = math.sqrt(error_x**2 + error_y**2)

    if distance > 1:

        direction_x = error_x / distance
        direction_y = error_y / distance

        drone_x += direction_x * drone_speed
        drone_y += direction_y * drone_speed

    # ------------------
    # Draw Bird
    # ------------------

    cv2.circle(
        canvas,
        (int(bird_x), int(bird_y)),
        15,
        (0, 0, 255),
        -1,
    )

    # ------------------
    # Draw Drone
    # ------------------

    cv2.circle(
        canvas,
        (int(drone_x), int(drone_y)),
        20,
        (255, 0, 0),
        -1,
    )

    # ------------------
    # Tracking Line
    # ------------------

    cv2.line(
        canvas,
        (int(drone_x), int(drone_y)),
        (int(bird_x), int(bird_y)),
        (0, 255, 0),
        2,
    )

    # ------------------
    # Info
    # ------------------

    cv2.putText(
        canvas,
        f"Distance: {distance:.1f}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255,255,255),
        2,
    )

    cv2.putText(
        canvas,
        "Autonomous Tracking Drone Simulation",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255,255,255),
        2,
    )

    cv2.imshow(
        "2D Drone Tracking Simulation",
        canvas,
    )

    key = cv2.waitKey(20)

    if key == ord("q"):
        break

cv2.destroyAllWindows()