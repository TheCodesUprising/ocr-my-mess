import subprocess
import sys
from pathlib import Path
import pytest
import shutil
import tempfile

PROJECT_ROOT = Path(__file__).parent.parent
DIST_PATH = PROJECT_ROOT / "dist"
BUILD_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "build.py"
EXECUTABLE_NAME = "ocr-my-mess"

@pytest.fixture(scope="module")
def built_executable():
    """
    Fixture to build the executable once for all tests in this module.
    Cleans the dist folder before the build.
    """
    if DIST_PATH.exists():
        shutil.rmtree(DIST_PATH)
    
    executable_path = DIST_PATH / EXECUTABLE_NAME

    # 1. Run the build script
    build_process = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT_PATH)], 
        capture_output=True, 
        text=True, 
        check=False
    )
    assert build_process.returncode == 0, f"Build script failed: {build_process.stderr}"

    # 2. Check if the executable exists
    assert executable_path.exists(), f"Executable '{EXECUTABLE_NAME}' was not created in '{DIST_PATH}'."

    return executable_path

@pytest.mark.pyinstaller_build
@pytest.mark.skipif(sys.platform == "win32", reason="Build script is for Linux/macOS")
def test_cli_help(built_executable):
    """
    Tests if the built CLI executable runs with --help.
    """
    run_process = subprocess.run([str(built_executable), "--help"], capture_output=True, text=True, check=False)
    assert run_process.returncode == 0, f"Executable failed to run with --help: {run_process.stderr}"
    assert "Usage: ocr-my-mess" in run_process.stdout

@pytest.mark.pyinstaller_build
@pytest.mark.skipif(sys.platform == "win32", reason="Build script is for Linux/macOS")
def test_gui_runs_without_crashing(built_executable):
    """
    Tests if the GUI runs without crashing immediately.
    """
    try:
        process = subprocess.Popen([str(built_executable)])
        process.wait(timeout=5)
        if process.returncode != 0:
            stdout, stderr = process.communicate()
            pytest.fail(f"GUI executable crashed with code {process.returncode}.\nStderr: {stderr}")
    except subprocess.TimeoutExpired:
        process.kill()
        pass

@pytest.mark.pyinstaller_build
@pytest.mark.skipif(sys.platform != "linux", reason="This test is for the packaged Linux application")
def test_packaged_gui_for_tesseract_error(built_executable):
    """
    Tests the packaged GUI application in a clean environment to ensure it doesn't
    raise Tesseract-related errors.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_executable_path = Path(tmpdir) / EXECUTABLE_NAME
        shutil.copy(built_executable, tmp_executable_path)

        process = subprocess.Popen(
            [str(tmp_executable_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=tmpdir
        )

        try:
            stdout, stderr = process.communicate(timeout=10)
            
            if "impossible de trouver les langues de tessaract" in stderr.lower():
                pytest.fail(f"Tesseract language error found in stderr:\n{stderr}")

            if "tesseract" in stderr.lower() and "error" in stderr.lower():
                 pytest.fail(f"A Tesseract-related error was found in stderr:\n{stderr}")

            if process.returncode != 0:
                pytest.fail(f"Packaged app crashed with return code {process.returncode}.\nStderr:\n{stderr}")

        except subprocess.TimeoutExpired:
            process.kill()
            pass
