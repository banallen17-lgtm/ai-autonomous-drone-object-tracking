# Development workflow

## Work in focused branches

Start from an up-to-date main branch and create a branch such as `codex/repository-cleanup`. Keep repository/documentation changes separate from simulation and vision behavior fixes. Submit a pull request describing the problem, final changes, validation, and limitations.

## Primary entry points

- Simulation: `simulation/drone_tracking_advanced.py`
- Vision: `vision/object_detection/yolo_tracking.py`

Retain historical demo paths until a deliberate migration is documented. Git history preserves previous implementations; avoid adding more numbered copies as the primary development approach.

## Check changes

Run from the repository root:

```powershell
python -B tools/check_repository.py
git diff --check
git status --short
```

The repository check parses tracked Python files and verifies relative Markdown file links. It also includes newly added files once staged. It does not import demo modules, open cameras, install packages, or test behavior.

For simulation/vision fixes, add focused behavioral regression coverage and record relevant manual or recorded-video checks. A syntax pass alone is not proof of tracking correctness.

## Documentation and generated files

Update the roadmap and research log when a milestone changes. Distinguish implemented capabilities, observed results, and future plans. Keep historical research entries intact.

Keep virtual environments, secrets, caches, model downloads, and generated run outputs out of commits. The existing tracked model remains available; new model files are ignored by default. Add selected demo assets intentionally and explain their provenance. Do not commit private recordings or credentials.
