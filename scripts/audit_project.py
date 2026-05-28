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
]


def check_env_not_tracked() -> bool:
    result = subprocess.run(
        ["git", "ls-files", ".env"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == ""


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent

    errors: list[str] = []

    if not check_env_not_tracked():
        errors.append(".env is tracked in git index")

    for required in REQUIRED_PATHS:
        path = project_root / required
        if not path.exists():
            errors.append(f"Missing required path: {required}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Audit checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
