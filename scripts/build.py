import subprocess
import sys
from pathlib import Path

def def_get_ocrmypdf_data_path():
    import ocrmypdf.data
    return ocrmypdf.data.__path__[0]

def build():
    """Builds the ocr-my-mess executable."""
    project_root = Path(__file__).parent.parent
    
    print("Building ocr-my-mess...")

    ocrmypdf_data_path = def_get_ocrmypdf_data_path()

    command = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--name", "ocr-my-mess",
        "--add-data", f"{ocrmypdf_data_path}:ocrmypdf/data",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=ocrmypdf",
        "--collect-all=ocrmypdf",
        str(project_root / "pdf_pipeline" / "main.py"),
    ]

    subprocess.run(command, check=True, cwd=project_root)

    print("Build complete. Executable is in the dist/ folder.")

if __name__ == "__main__":
    build()
