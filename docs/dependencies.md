# Dependency setup

## Supported baseline

Windows x64, Python 3.12, desktop OpenCV, and CPU inference. The complete runtime snapshot is [requirements-windows-py312.txt](../requirements-windows-py312.txt). It pins direct and transitive packages, including NumPy 2.4.6, OpenCV contrib 4.13.0.92, Ultralytics 8.4.60, PyTorch 2.12.0, and torchvision 0.27.0. Other operating systems, Python versions, and CUDA configurations need their own validation.

## Install in a fresh environment

Run from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-deps --only-binary=:all: -r vision/object_detection/requirements.txt
.\.venv\Scripts\python.exe -B tools/check_environment.py
```

Use an empty environment without system site-packages. If `.venv` already contains conflicting packages, create a new environment under `venv` and substitute that path in the commands. Both directories are ignored by Git. Do not uninstall packages from your system Python to repair this project environment.

Select `.venv/Scripts/python.exe` as the editor interpreter. Use that same interpreter for both simulation and vision demos. Package downloads require network access; the smoke check uses only the tracked model and synthetic images.

## Why the installation uses --no-deps

Ultralytics 8.4.60 declares `opencv-python>=4.6.0`. This project needs the contrib build for CSRT. Installing both distributions would overlap their `cv2` files. The [OpenCV package instructions](https://pypi.org/project/opencv-contrib-python/) require choosing a single variant; the contrib desktop build contains the main and extra modules and supports the demos' GUI calls.

The full snapshot installs with `--no-deps` so pip does not add regular OpenCV. All runtime dependencies are listed explicitly. Do not omit this flag or run an ordinary `pip install -U ultralytics` in the environment: dependency resolution would reintroduce regular OpenCV.

`pip check` reports the upstream `ultralytics requires opencv-python` metadata mismatch even though contrib supplies the API. This is an intentional, documented substitution, not a claim that `pip check` is clean. [check_environment.py](../tools/check_environment.py) checks every installed distribution's active base requirements and pinned versions, allowing only that one substitution and requiring exactly one OpenCV distribution. It also creates/updates a CSRT tracker and runs CPU YOLO inference.

The script does not patch upstream package metadata. Optional training/export integrations are outside this runtime snapshot. For future upgrades, resolve and audit the complete runtime dependency set, preserve the single OpenCV variant, and rerun installation and smoke checks in a fresh environment.

## Model baseline

The tracked `yolov8n.pt` is retained, with SHA-256:

```text
f59b3d833e2ff32e194b5bb8e08d211dc7c5bdf144b90d2c8412c47ccfc83b36
```

This checksum identifies the existing repository artifact; its original download URL was not recorded. It is not proof of upstream authenticity. Restore it from Git if missing rather than silently substituting another model. Model inference remains YOLOv8; changing the package setup does not intentionally change model weights.

## Validation scope

The environment check covers installed metadata, CSRT initialization/update on a deterministic textured frame, Kalman construction, model checksum/load, and one CPU inference on a blank image. It does not measure detection accuracy or validate live camera access, interactive windows, or simulation behavior. Library settings are written under ignored `outputs/` directories. The existing system Python environment is untouched.
