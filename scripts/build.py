import subprocess
import sys
from pathlib import Path

def def_get_ocrmypdf_data_path():
    import ocrmypdf.data
    return ocrmypdf.data.__path__[0]

def build(target: str):
    """Builds the specified target (cli or gui)."""
    project_root = Path(__file__).parent.parent
    
    if target not in ["cli", "gui"]:
        raise ValueError("Invalid target. Must be 'cli' or 'gui'.")

    print(f"Building ocr-my-mess-{target}...")

    ocrmypdf_data_path = def_get_ocrmypdf_data_path()

    command = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--name", f"ocr-my-mess-{target}",
        "--add-data", f"{ocrmypdf_data_path}:ocrmypdf/data",
    ]

    if target == "gui":
        command.append("--windowed")
        command.append("--hidden-import=PIL._tkinter_finder")
        command.append(str(project_root / "pdf_pipeline" / "gui.py"))
    else: # cli
        command.append(str(project_root / "pdf_pipeline" / "cli.py"))

    subprocess.run(command, check=True, cwd=project_root)

    print(f"{target.upper()} build complete. Executable is in the dist/ folder.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["cli", "gui", "all"], default="all", nargs="?")
    args = parser.parse_args()

    if args.target == "all":
        build("cli")
        build("gui")
    else:
        build(args.target)
