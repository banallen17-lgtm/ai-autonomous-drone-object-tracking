"""Validate the Windows dependency snapshot and exercise vision APIs without a camera."""

import hashlib
from importlib import metadata
import os
from pathlib import Path
import platform
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL_SHA256 = "f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36"


def check_dependencies():
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    if sys.version_info[:2] != (3, 12) or sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise RuntimeError("This snapshot supports Windows x64 with Python 3.12 only.")
    installed = {canonicalize_name(d.metadata["Name"]): d for d in metadata.distributions()}
    variants = {name for name in installed if name.startswith("opencv-")}
    if variants != {"opencv-contrib-python"}:
        raise RuntimeError(f"Expected only opencv-contrib-python; found {sorted(variants)}. Use a fresh virtual environment.")
    errors = []
    for line in (ROOT / "requirements-windows-py312.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        req = Requirement(line)
        name = canonicalize_name(req.name)
        if name not in installed or installed[name].version not in req.specifier:
            errors.append(f"Snapshot mismatch: {req}")
    # Check every installed distribution's active base dependencies, not optional extras.
    # The only substitution allowed is Ultralytics' regular OpenCV requirement.
    for name, dist in installed.items():
        for raw in dist.requires or []:
            req = Requirement(raw)
            if req.marker and not req.marker.evaluate({"extra": ""}):
                continue
            dependency = canonicalize_name(req.name)
            if name == "ultralytics" and dependency == "opencv-python":
                dependency = "opencv-contrib-python"
            if dependency not in installed:
                errors.append(f"{name} requires {req}")
            elif installed[dependency].version not in req.specifier:
                errors.append(f"{name} requires {req}; found {installed[dependency].version}")
    if errors:
        raise RuntimeError("\n".join(errors))
    print("PASS: pinned versions and active dependencies (explicit OpenCV substitution).")


def smoke_test():
    # Keep library settings/cache files inside ignored project output directories.
    (ROOT / "outputs" / "ultralytics").mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs" / "matplotlib").mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(ROOT / "outputs" / "ultralytics")
    os.environ["MPLCONFIGDIR"] = str(ROOT / "outputs" / "matplotlib")
    os.environ["YOLO_AUTOINSTALL"] = "false"
    import cv2
    import numpy as np
    from ultralytics import YOLO

    if re.search(r"GUI:\s+NONE", cv2.getBuildInformation()):
        raise RuntimeError("The demos need a GUI-enabled OpenCV build.")
    # Match the current application's choice of the legacy CSRT API when present.
    factory = getattr(getattr(cv2, "legacy", None), "TrackerCSRT_create", None)
    factory = factory or getattr(cv2, "TrackerCSRT_create", None)
    if factory is None:
        raise RuntimeError("CSRT factory is missing.")
    tracker = factory()
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    frame[80:140, 100:160] = np.random.default_rng(0).integers(0, 256, (60, 60, 3), dtype=np.uint8)
    initialized = tracker.init(frame, (100, 80, 60, 60))
    if initialized is False:
        raise RuntimeError("CSRT initialization failed.")
    success, box = tracker.update(frame.copy())
    if not success or abs(box[0] - 100) > 5 or abs(box[1] - 80) > 5:
        raise RuntimeError(f"CSRT synthetic-frame update failed: {success}, {box}")
    cv2.KalmanFilter(4, 2)
    print(f"PASS: OpenCV {cv2.__version__}, CSRT initialization/update, Kalman API.")
    model_path = ROOT / "yolov8n.pt"
    if not model_path.is_file() or hashlib.sha256(model_path.read_bytes()).hexdigest() != MODEL_SHA256:
        raise RuntimeError("Missing or changed yolov8n.pt; restore the tracked baseline model.")
    model = YOLO(str(model_path))
    results = model.predict(np.zeros((320, 320, 3), dtype=np.uint8), imgsz=320, device="cpu", verbose=False, save=False)
    if len(results) != 1 or results[0].orig_shape != (320, 320) or results[0].boxes is None:
        raise RuntimeError("YOLO inference returned an unexpected result.")
    print("PASS: tracked model checksum, YOLO load and CPU inference.")
    print("No camera or GUI window was opened. Tracking accuracy and live capture remain untested.")


if __name__ == "__main__":
    try:
        check_dependencies()
        smoke_test()
    except Exception as exc:
        print(f"Environment check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
