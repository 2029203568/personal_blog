import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    backend_dir = project_root / "backend"

    if not backend_dir.exists():
        raise FileNotFoundError(f"Backend directory not found: {backend_dir}")

    os.chdir(backend_dir)

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]

    print("Starting website at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop.")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
