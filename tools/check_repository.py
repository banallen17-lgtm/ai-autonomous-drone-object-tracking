"""Check tracked Python syntax and relative Markdown file links without imports."""

import ast
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    )
    files = [ROOT / name for name in result.stdout.decode("utf-8").split("\0") if name]
    errors = []
    python_count = 0
    link_count = 0
    for path in files:
        if not path.is_file():
            errors.append(f"Missing tracked file: {path.relative_to(ROOT)}")
            continue
        if path.suffix == ".py":
            python_count += 1
            try:
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            except (SyntaxError, UnicodeError) as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc}")
        elif path.suffix == ".md":
            content = path.read_text(encoding="utf-8-sig")
            # Current docs use inline links; skip fenced examples and external URLs.
            content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
                target = target.strip().strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                link_count += 1
                destination = path.parent / unquote(parsed.path)
                if not destination.exists():
                    errors.append(f"{path.relative_to(ROOT)}: broken link: {target}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {python_count} Python files parsed; {link_count} relative Markdown file links exist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
