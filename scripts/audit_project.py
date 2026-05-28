from pathlib import Path
import subprocess
import sys


REQUIRED_PATHS = [
    "data",
    "data/.gitkeep",
    ".env.example",
    "AGENTS.md",
    "docker-compose.yml",
    "Dockerfile",
    "bot.py",
    "app/config.py",
    "app/handlers.py",
    "app/db.py",
    "app/lead_service.py",
]

FORBIDDEN_PYTHON_STRINGS = (
    "send_all",
    "mass_send",
    "autosend",
)


def check_env_not_tracked() -> bool:
    result = subprocess.run(
        ["git", "ls-files", ".env"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == ""


def find_forbidden_python_strings(project_root: Path) -> list[str]:
    errors: list[str] = []
    audit_file = Path(__file__).resolve()

    for path in project_root.rglob("*.py"):
        if path.resolve() == audit_file:
            continue
        if ".venv" in path.parts or "venv" in path.parts or "__pycache__" in path.parts:
            continue

        content = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_PYTHON_STRINGS:
            if forbidden in content:
                errors.append(f"Forbidden string '{forbidden}' found in {path.relative_to(project_root)}")

    return errors


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent

    errors: list[str] = []

    if not check_env_not_tracked():
        errors.append(".env is tracked in git index")

    for required in REQUIRED_PATHS:
        path = project_root / required
        if not path.exists():
            errors.append(f"Missing required path: {required}")

    errors.extend(find_forbidden_python_strings(project_root))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Audit checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
