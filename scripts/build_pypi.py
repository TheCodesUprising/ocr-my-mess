import subprocess
import sys
import shutil
from pathlib import Path

def build_pypi_package():
    """Builds the PyPI source distribution and wheel."""
    project_root = Path(__file__).parent.parent
    print("Building PyPI package...")

    # Clean up previous builds
    if project_root.joinpath("dist").exists():
        shutil.rmtree(project_root.joinpath("dist"))
    if project_root.joinpath("ocr_my_mess.egg-info").exists():
        shutil.rmtree(project_root.joinpath("ocr_my_mess.egg-info"))

    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "build"], check=True)
    subprocess.run([sys.executable, "-m", "build", "--sdist", "--wheel", project_root], check=True)

    print("PyPI package build complete. Files are in the dist/ folder.")

if __name__ == "__main__":
    build_pypi_package()
