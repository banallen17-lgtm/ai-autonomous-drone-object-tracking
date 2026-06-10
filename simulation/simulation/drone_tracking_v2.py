import cv2
import numpy as np
import random
import math


# ------------------
# HELPER FUNCTIONS
# ------------------

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2 * math.pi

    while angle < -math.pi:
        angle += 2 * math.pi

    return angle


# ------------------
# WINDOW
# ------------------

WIDTH = 1600
HEIGHT = 1100


# ------------------
# DRONE
# ------------------

drone_x = 200.0
drone_y = 400.0

drone_vx = 0.0
drone_vy = 0.0

MAX_SPEED = 10
ACCELERATION = 0.25
FRICTION = 0.98

drone_heading = 0

LOCK_RADIUS = 40
VISION_RADIUS = 600
FOLLOW_DISTANCE = 150
FOV_ANGLE = 90
TURN_SPEED = 0.04

tracking_confidence = 0.0
locked_target_id = None

last_known_x = None
last_known_y = None
memory_timer = 0
MAX_MEMORY_TIME = 300
SEARCH_ORBIT_RADIUS = 120

reacquire_timer = 0
REACQUIRE_DISPLAY_TIME = 60
was_target_detected = False


# ------------------
# BIRDS
# ------------------

BIRD_NORMAL_SPEED = 3
BIRD_ESCAPE_SPEED = 6
BIRD_DETECTION_RADIUS = 220

birds = []

for i in range(3):
    birds.append({
        "id": i,
        "x": random.randint(300, WIDTH - 100),
        "y": random.randint(100, HEIGHT - 100),
        "vx": random.uniform(-3, 3),
        "vy": random.uniform(-3, 3),
        "direction_timer": 0,
    })


target_detected = False
search_mode = False


# ------------------
# MAIN LOOP
# ------------------

while True:
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # ------------------
    # SELECT TARGET BIRD
    # ------------------

    if locked_target_id is None:
        closest_distance = float("inf")

        for bird in birds:
            dx = bird["x"] - drone_x
            dy = bird["y"] - drone_y
            d = math.sqrt(dx**2 + dy**2)

            if d < closest_distance:
                closest_distance = d
                locked_target_id = bird["id"]

    target_bird = None

    for bird in birds:
        if bird["id"] == locked_target_id:
            target_bird = bird
            break

    if target_bird is None:
        print("Error: No target bird found.")
        break

    # ------------------
    # BIRD AI
    # ------------------

    for bird in birds:
        bird_error_x = bird["x"] - drone_x
        bird_error_y = bird["y"] - drone_y
        bird_distance_from_drone = math.sqrt(bird_error_x**2 + bird_error_y**2)

        if bird_distance_from_drone < BIRD_DETECTION_RADIUS and bird_distance_from_drone > 0:
            escape_x = bird_error_x / bird_distance_from_drone
            escape_y = bird_error_y / bird_distance_from_drone

            bird["vx"] += escape_x * 0.3
            bird["vy"] += escape_y * 0.3

            bird["vx"] = clamp(bird["vx"], -BIRD_ESCAPE_SPEED, BIRD_ESCAPE_SPEED)
            bird["vy"] = clamp(bird["vy"], -BIRD_ESCAPE_SPEED, BIRD_ESCAPE_SPEED)

        else:
            bird["direction_timer"] += 1

            if bird["direction_timer"] > 60:
                bird["vx"] += random.uniform(-1.5, 1.5)
                bird["vy"] += random.uniform(-1.5, 1.5)

                bird["vx"] = clamp(bird["vx"], -BIRD_NORMAL_SPEED, BIRD_NORMAL_SPEED)
                bird["vy"] = clamp(bird["vy"], -BIRD_NORMAL_SPEED, BIRD_NORMAL_SPEED)

                bird["direction_timer"] = 0

    # ------------------
    # MOVE ALL BIRDS
    # ------------------

    for bird in birds:
        bird["x"] += bird["vx"]
        bird["y"] += bird["vy"]

        if bird["x"] < 50:
            bird["x"] = 50
            bird["vx"] *= -1

        if bird["x"] > WIDTH - 50:
            bird["x"] = WIDTH - 50
            bird["vx"] *= -1

        if bird["y"] < 50:
            bird["y"] = 50
            bird["vy"] *= -1

        if bird["y"] > HEIGHT - 50:
            bird["y"] = HEIGHT - 50
            bird["vy"] *= -1

    # ------------------
    # DRONE TRACKING
    # ------------------

    error_x = target_bird["x"] - drone_x
    error_y = target_bird["y"] - drone_y

    distance = math.sqrt(error_x**2 + error_y**2)

    angle_to_target = math.atan2(
        target_bird["y"] - drone_y,
        target_bird["x"] - drone_x
    )

    angle_difference = normalize_angle(
        angle_to_target - drone_heading
    )

    target_in_fov = (
        abs(angle_difference)
        < math.radians(FOV_ANGLE / 2)
    )

    visible_now = (
        distance <= VISION_RADIUS
        and target_in_fov
    )

    if visible_now:
        tracking_confidence += 0.03

        last_known_x = target_bird["x"]
        last_known_y = target_bird["y"]
        memory_timer = 0

    else:
        tracking_confidence -= 0.05

    tracking_confidence = clamp(tracking_confidence, 0.0, 1.0)

    target_detected = tracking_confidence > 0.25

    if not target_detected:
        memory_timer += 1

    if target_detected and not was_target_detected:
        reacquire_timer = REACQUIRE_DISPLAY_TIME

    was_target_detected = target_detected

    if reacquire_timer > 0:
        reacquire_timer -= 1

    if target_detected:
        status = "TRACKING"

    elif last_known_x is not None and memory_timer < MAX_MEMORY_TIME:
        status = "REACQUIRING"

    else:
        status = "SEARCHING"

    distance_error = distance - FOLLOW_DISTANCE

    # ------------------
    # DRONE MOVEMENT LOGIC
    # ------------------

    if target_detected and distance > 0 and abs(distance_error) > 20:
        direction_x = error_x / distance
        direction_y = error_y / distance

        control_strength = distance_error / FOLLOW_DISTANCE

        drone_vx += direction_x * ACCELERATION * control_strength
        drone_vy += direction_y * ACCELERATION * control_strength

    elif status == "REACQUIRING" and last_known_x is not None:
        mem_error_x = last_known_x - drone_x
        mem_error_y = last_known_y - drone_y

        mem_distance = math.sqrt(mem_error_x**2 + mem_error_y**2)

        if mem_distance > SEARCH_ORBIT_RADIUS:
            mem_dir_x = mem_error_x / mem_distance
            mem_dir_y = mem_error_y / mem_distance

            drone_vx += mem_dir_x * ACCELERATION
            drone_vy += mem_dir_y * ACCELERATION

        else:
            drone_heading += TURN_SPEED * 2

    else:
        drone_heading += TURN_SPEED

    # ------------------
    # SPEED LIMIT + FRICTION
    # ------------------

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
        angle_to_target = math.atan2(
            target_bird["y"] - drone_y,
            target_bird["x"] - drone_x
        )

        angle_error = normalize_angle(
            angle_to_target - drone_heading
        )

        drone_heading += clamp(
            angle_error,
            -TURN_SPEED,
            TURN_SPEED
        )

    elif status == "REACQUIRING" and last_known_x is not None:
        angle_to_memory = math.atan2(
            last_known_y - drone_y,
            last_known_x - drone_x
        )

        angle_error = normalize_angle(
            angle_to_memory - drone_heading
        )

        drone_heading += clamp(
            angle_error,
            -TURN_SPEED,
            TURN_SPEED
        )

    # ------------------
    # DRAW ALL BIRDS
    # ------------------

    for bird in birds:
        color = (0, 0, 255)

        if bird["id"] == locked_target_id:
            color = (0, 255, 255)

        cv2.circle(
            canvas,
            (int(bird["x"]), int(bird["y"])),
            15,
            color,
            -1
        )

        cv2.putText(
            canvas,
            f"Bird {bird['id']}",
            (int(bird["x"]) + 20, int(bird["y"])),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

    # ------------------
    # FOLLOW DISTANCE CIRCLE
    # ------------------

    cv2.circle(
        canvas,
        (int(target_bird["x"]), int(target_bird["y"])),
        FOLLOW_DISTANCE,
        (0, 100, 255),
        1
    )

    # ------------------
    # VISION RADIUS
    # ------------------

    cv2.circle(
        canvas,
        (int(drone_x), int(drone_y)),
        VISION_RADIUS,
        (60, 60, 60),
        1
    )

    # ------------------
    # LAST KNOWN POSITION
    # ------------------

    if last_known_x is not None and not target_detected:
        cv2.circle(
            canvas,
            (int(last_known_x), int(last_known_y)),
            25,
            (255, 255, 0),
            2
        )

        cv2.putText(
            canvas,
            "LAST SEEN",
            (int(last_known_x) + 10, int(last_known_y) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 0),
            2
        )

    # ------------------
    # DRAW CAMERA FOV
    # ------------------

    left_angle = drone_heading - math.radians(FOV_ANGLE / 2)
    right_angle = drone_heading + math.radians(FOV_ANGLE / 2)

    left_x = drone_x + math.cos(left_angle) * VISION_RADIUS
    left_y = drone_y + math.sin(left_angle) * VISION_RADIUS

    right_x = drone_x + math.cos(right_angle) * VISION_RADIUS
    right_y = drone_y + math.sin(right_angle) * VISION_RADIUS

    cv2.line(
        canvas,
        (int(drone_x), int(drone_y)),
        (int(left_x), int(left_y)),
        (0, 255, 255),
        2,
    )

    cv2.line(
        canvas,
        (int(drone_x), int(drone_y)),
        (int(right_x), int(right_y)),
        (0, 255, 255),
        2,
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

    if target_detected:
        line_color = (0, 255, 0)
    elif status == "REACQUIRING":
        line_color = (255, 255, 0)
    else:
        line_color = (80, 80, 80)

    cv2.line(
        canvas,
        (int(drone_x), int(drone_y)),
        (int(target_bird["x"]), int(target_bird["y"])),
        line_color,
        2
    )

    # ------------------
    # TARGET LOCK
    # ------------------

    if distance < LOCK_RADIUS and target_detected:
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
            (int(target_bird["x"]), int(target_bird["y"])),
            30,
            (0, 255, 0),
            2
        )

    # ------------------
    # TARGET REACQUIRED MESSAGE
    # ------------------

    if reacquire_timer > 0:
        cv2.putText(
            canvas,
            "TARGET REACQUIRED",
            (430, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            3
        )

    # ------------------
    # HUD
    # ------------------

    bird_state = "EVADING" if math.sqrt(
        (target_bird["x"] - drone_x) ** 2
        + (target_bird["y"] - drone_y) ** 2
    ) < BIRD_DETECTION_RADIUS else "NORMAL"

    cv2.putText(
        canvas,
        f"Distance: {distance:.1f}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        canvas,
        f"Velocity: {speed:.2f}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        canvas,
        "AUTONOMOUS DRONE TRACKING V7",
        (20, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )

    cv2.putText(
        canvas,
        f"Status: {status}",
        (20, 170),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2
    )

    cv2.putText(
        canvas,
        f"Bird State: {bird_state}",
        (20, 210),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 165, 255),
        2
    )

    cv2.putText(
        canvas,
        f"Confidence: {tracking_confidence:.2f}",
        (20, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        canvas,
        f"Locked Target: Bird {locked_target_id}",
        (20, 290),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        canvas,
        f"Memory Timer: {memory_timer}/{MAX_MEMORY_TIME}",
        (20, 330),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 0),
        2
    )

    cv2.imshow(
        "Autonomous Drone Tracking V7",
        canvas
    )

    key = cv2.waitKey(20) & 0xFF

    if key == ord("q"):
        break

    elif key in [ord("0"), ord("1"), ord("2")]:
        selected_id = int(chr(key))

        valid_ids = [bird["id"] for bird in birds]

        if selected_id in valid_ids:
            locked_target_id = selected_id
            tracking_confidence = 0.0
            last_known_x = None
            last_known_y = None
            memory_timer = 0
            reacquire_timer = 0
            was_target_detected = False

            print(f"Manual target selected: Bird {locked_target_id}")

cv2.destroyAllWindows()