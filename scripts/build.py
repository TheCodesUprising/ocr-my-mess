import subprocess
import sys
from pathlib import Path
import site
import glob
import os
import shutil

def def_get_ocrmypdf_data_path():
    import ocrmypdf.data
    return ocrmypdf.data.__path__[0]

def get_ocrmypdf_dist_info_path():
    for site_package_dir in site.getsitepackages():
        dist_info_paths = glob.glob(os.path.join(site_package_dir, "ocrmypdf-*.dist-info"))
        if dist_info_paths:
            return dist_info_paths[0]
    return None

def build():
    """Builds the ocr-my-mess executable."""
    project_root = Path(__file__).parent.parent

    print("Building ocr-my-mess...")

    print("--- Tesseract Info ---")
    subprocess.run(["tesseract", "--version"], check=True)
    subprocess.run(["tesseract", "--list-langs"], check=True)

    conda_prefix = os.environ.get("CONDA_PREFIX")
    tessdata_path = None
    if conda_prefix:
        tessdata_path = Path(conda_prefix) / "share" / "tessdata"
        if not tessdata_path.exists():
            print("--- Tesseract tessdata directory not found ---")
            tessdata_path = None
    else:
        print("--- CONDA_PREFIX not found, cannot locate tessdata ---")
    print("----------------------")

    ocrmypdf_data_path = def_get_ocrmypdf_data_path()
    command = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--name", "ocr-my-mess",
        "--add-data", f"{ocrmypdf_data_path}:ocrmypdf/data",
        "--hidden-import=PIL._tkinter_finder",
        "--collect-submodules", "ocrmypdf",
        "--hidden-import",
        "pdf_pipeline.utils",
        "--hidden-import",
        "ocrmypdf",
        "--runtime-hook", "scripts/pyi_rth_dependencies.py",
    ]

    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        print(f"--- Bundling Tesseract executable from: {tesseract_path} ---")
        command.extend(["--add-binary", f"{tesseract_path}:."])
    else:
        print("Warning: Tesseract executable not found in PATH. OCR functionality may fail.")

    ghostscript_path = shutil.which("gs")
    if ghostscript_path:
        print(f"--- Bundling Ghostscript executable from: {ghostscript_path} ---")
        command.extend(["--add-binary", f"{ghostscript_path}:."])
    else:
        print("Warning: Ghostscript executable not found in PATH. PDF processing may fail.")

    ocrmypdf_dist_info = get_ocrmypdf_dist_info_path()
    if ocrmypdf_dist_info:
        command.extend(["--add-data", f"{ocrmypdf_dist_info}:{Path(ocrmypdf_dist_info).name}"])

    if sys.platform == "linux":
        command.extend(["--exclude-module", "libstdc++.so.6"])

    if tessdata_path:
        desired_languages = [
            'rus',  # Russian
            'deu',  # German
            'fra',  # French
            'eng',  # English
            'ita',  # Italian
            'spa',  # Spanish
            'pol',  # Polish
            'ukr',  # Ukrainian
            'ron',  # Romanian
            'nld',  # Dutch
        ]
        print(f"--- Bundling {len(desired_languages)} Tesseract languages ---")
        for lang in desired_languages:
            lang_file = tessdata_path / f"{lang}.traineddata"
            if lang_file.exists():
                command.extend(["--add-data", f"{lang_file}:tessdata"])
            else:
                print(f"Warning: language file not found for '{lang}' at {lang_file}")

        for item in ['configs', 'tessconfigs', 'pdf.ttf']:
            item_path = tessdata_path / item
            if item_path.exists():
                if item_path.is_dir():
                    command.extend(["--add-data", f"{item_path}:tessdata/{item}"])
                else:
                    command.extend(["--add-data", f"{item_path}:tessdata"])

    command.append(str(project_root / "pdf_pipeline" / "main.py"))

    subprocess.run(command, check=True, cwd=project_root)

    print("Build complete. Executable is in the dist/ folder.")

if __name__ == "__main__":
    build()
