import cv2
import numpy as np
import random
import math
import time


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
def calculate_target_visibility(
    drone_x, drone_y, target_x, target_y,
    camera_heading, camera_fov, vision_radius
):
    """Calculate target geometry and whether the camera can see it."""
    error_x = target_x - drone_x
    error_y = target_y - drone_y
    distance = math.hypot(error_x, error_y)

    angle_to_target = math.atan2(error_y, error_x)
    angle_difference = normalize_angle(angle_to_target - camera_heading)

    target_in_fov = abs(angle_difference) < math.radians(camera_fov / 2)
    visible = distance <= vision_radius and target_in_fov

    return error_x, error_y, distance, angle_difference, visible

# ------------------
# WINDOW
# ------------------

WIDTH = 1700
HEIGHT = 1000


# ------------------
# DRONE
# ------------------
def main():
    drone_x = 200.0
    drone_y = 400.0

    drone_vx = 0.0
    drone_vy = 0.0

    MAX_SPEED = 5.5
    ACCELERATION = 0.08
    FRICTION = 0.98

    drone_heading = 0
    camera_heading = 0

    CAMERA_TURN_SPEED = 0.03
    CAMERA_FOV = 40

    LOCK_RADIUS = 50
    VISION_RADIUS = 500
    FOLLOW_DISTANCE = 150
    FOV_ANGLE = 90
    TURN_SPEED = 0.05

    tracking_confidence = 0.0
    locked_target_id = None

    last_known_x = None
    last_known_y = None

    previous_target_x = None
    previous_target_y = None

    last_known_vx = 0.0
    last_known_vy = 0.0

    predicted_x = None
    predicted_y = None

    PREDICTION_TIME = 15
    PREDICTION_SMOOTHING = 0.85

    memory_timer = 0
    MAX_MEMORY_TIME = 100
    SEARCH_ORBIT_RADIUS = 120

    reacquire_timer = 0
    REACQUIRE_DISPLAY_TIME = 60
    was_target_detected = False

    last_angle_error = 0.0
    search_direction = 1
    SEARCH_MOVE_RADIUS = 300
    SEARCH_TANGENTIAL_SPEED = 0.3


    # ------------------
    # BIRDS
    # ------------------

    BIRD_NORMAL_SPEED = 3.2
    BIRD_ESCAPE_SPEED = 5.6

    birds = []

    for i in range(3):
        birds.append({
            "id": i,
            "x": random.randint(300, WIDTH - 100),
            "y": random.randint(100, HEIGHT - 100),
            "vx": random.uniform(-3, 3),
            "vy": random.uniform(-3, 3),
            "direction_timer": 0,
            "evade_until": 0.0,
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

        now = time.monotonic()

        for bird in birds:
            is_tracked = (bird["id"] == locked_target_id and target_detected)

            if is_tracked:
                bird["evade_until"] = now + 2.0

            bird["evading"] = is_tracked or now < bird["evade_until"]

            if bird["evading"]:
                dx = bird["x"] - drone_x
                dy = bird["y"] - drone_y
                distance_from_drone = math.hypot(dx, dy)

                if distance_from_drone > 0:
                    escape_x = dx / distance_from_drone
                    escape_y = dy / distance_from_drone
                else:
                    escape_x = 1.0
                    escape_y = 0

                bird["vx"] += escape_x * 0.3
                bird["vy"] += escape_y * 0.3
                bird["direction_timer"] = 0
                speed_limit = BIRD_ESCAPE_SPEED

            else:
                bird["direction_timer"] += 1

                if bird["direction_timer"] > 60:
                    bird["vx"] = random.uniform(-BIRD_NORMAL_SPEED, BIRD_NORMAL_SPEED)
                    bird["vy"] = random.uniform(-BIRD_NORMAL_SPEED, BIRD_NORMAL_SPEED)
                    bird["direction_timer"] = 0

                speed_limit = BIRD_NORMAL_SPEED
            # Steer away from walls before reaching them.
            wall_margin = 120
            wall_turn_strength = 0.8

            if bird["x"] < wall_margin:
                bird["vx"] += wall_turn_strength
            elif bird["x"] > WIDTH - wall_margin:
                bird["vx"] -= wall_turn_strength

            if bird["y"] < wall_margin:
                bird["vy"] += wall_turn_strength
            elif bird["y"] > HEIGHT - wall_margin:
                bird["vy"] -= wall_turn_strength

            speed = math.hypot(bird["vx"], bird["vy"])

            if speed > speed_limit:
                scale = speed_limit / speed
                bird["vx"] *= scale
                bird["vy"] *= scale


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

        error_x, error_y, distance, angle_difference, visible_now = (
            calculate_target_visibility(
                drone_x=drone_x,
                drone_y=drone_y,
                target_x=target_bird["x"],
                target_y=target_bird["y"],
                camera_heading=camera_heading,
                camera_fov=CAMERA_FOV,
                vision_radius=VISION_RADIUS,
            )
        )

        if visible_now:
            tracking_confidence += 0.03

            # Calculate target velocity from frame-to-frame movement
            if previous_target_x is not None and previous_target_y is not None:
                raw_vx = target_bird["x"] - previous_target_x
                raw_vy = target_bird["y"] - previous_target_y

                last_known_vx = last_known_vx * 0.85 + raw_vx * 0.15
                last_known_vy = last_known_vy * 0.85 + raw_vy * 0.15

            previous_target_x = target_bird["x"]
            previous_target_y = target_bird["y"]

            last_known_x = target_bird["x"]
            last_known_y = target_bird["y"]

            # Smooth prediction
            raw_predicted_x = last_known_x + last_known_vx * PREDICTION_TIME
            raw_predicted_y = last_known_y + last_known_vy * PREDICTION_TIME

            raw_predicted_x = clamp(raw_predicted_x, 50, WIDTH - 50)
            raw_predicted_y = clamp(raw_predicted_y, 50, HEIGHT - 50)

            if predicted_x is None or predicted_y is None:
                predicted_x = raw_predicted_x
                predicted_y = raw_predicted_y
            else:
                predicted_x = predicted_x * PREDICTION_SMOOTHING + raw_predicted_x * (1 - PREDICTION_SMOOTHING)
                predicted_y = predicted_y * PREDICTION_SMOOTHING + raw_predicted_y * (1 - PREDICTION_SMOOTHING)

            memory_timer = 0

            last_angle_error = angle_difference
            search_direction = 1 if angle_difference > 0 else -1

        else:
            tracking_confidence -= 0.05

        tracking_confidence = clamp(tracking_confidence, 0.0, 1.0)

        target_detected = visible_now and tracking_confidence > 0.25
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

        else:
            pass

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

        if visible_now:
            desired_camera_heading = math.atan2(
                target_bird["y"] - drone_y,
                target_bird["x"] - drone_x
                )
            camera_error = normalize_angle(desired_camera_heading - camera_heading)

            camera_heading += clamp(camera_error, -CAMERA_TURN_SPEED, CAMERA_TURN_SPEED)

        elif last_known_x is not None and memory_timer < MAX_MEMORY_TIME:
            search_x = predicted_x if predicted_x is not None else last_known_x
            search_y = predicted_y if predicted_y is not None else last_known_y

            mem_error_x = search_x - drone_x
            mem_error_y = search_y - drone_y
            mem_distance = math.hypot(mem_error_x, mem_error_y)

            search_heading = math.atan2(mem_error_y, mem_error_x)
            scan_offset = math.radians(45)*math.sin(memory_timer * 0.04)
            desired_camera_heading = search_heading + scan_offset

            camera_error = normalize_angle(desired_camera_heading - camera_heading)

            camera_heading += clamp(camera_error, -CAMERA_TURN_SPEED, CAMERA_TURN_SPEED)

            if status == "REACQUIRING":
                if mem_distance > SEARCH_MOVE_RADIUS:
                    mem_dir_x = mem_error_x / mem_distance
                    mem_dir_y = mem_error_y / mem_distance

                    drone_vx += mem_dir_x * ACCELERATION * 0.2
                    drone_vy += mem_dir_y * ACCELERATION * 0.2

                else:
                    orbit_x = -mem_error_y / max(mem_distance, 1)
                    orbit_y = mem_error_x / max(mem_distance, 1)

                    drone_vx += orbit_x * SEARCH_TANGENTIAL_SPEED
                    drone_vy += orbit_y * SEARCH_TANGENTIAL_SPEED
        else:
            camera_heading += search_direction * CAMERA_TURN_SPEED

        camera_heading = normalize_angle(camera_heading)

        body_error = normalize_angle(camera_heading - drone_heading)
        drone_heading += clamp(body_error, -TURN_SPEED, TURN_SPEED)
        drone_heading = normalize_angle(drone_heading)





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

        # Always show prediction
        if predicted_x is not None:
            cv2.circle(
                canvas,
                (int(predicted_x), int(predicted_y)),
                30,
                (255, 0, 255),
                2
            )

            cv2.putText(
                canvas,
                "PREDICTED",
                (int(predicted_x) + 10, int(predicted_y) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 255),
                2
            )

        # ------------------
        # DRAW CAMERA FOV
        # ------------------

        left_angle = camera_heading - math.radians(CAMERA_FOV / 2)
        right_angle = camera_heading + math.radians(CAMERA_FOV / 2)

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

        bird_state = "EVADING" if target_bird["evading"] else "NORMAL"

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

        cv2.putText(
            canvas,
            f"Target Velocity: ({last_known_vx:.1f}, {last_known_vy:.1f})",
            (20, 370),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 255),
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

                # Clear detection and confidence.
                tracking_confidence = 0.0
                target_detected = False
                was_target_detected = False

                # Clear the previous target's observed positions.
                last_known_x = None
                last_known_y = None
                previous_target_x = None
                previous_target_y = None

                # Clear velocity and prediction.
                last_known_vx = 0.0
                last_known_vy = 0.0
                predicted_x = None
                predicted_y = None

                # Restart memory and search behavior.
                memory_timer = 0
                reacquire_timer = 0
                last_angle_error = 0.0
                search_direction = 1

                print(f"Manual target selected: Bird {locked_target_id}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()