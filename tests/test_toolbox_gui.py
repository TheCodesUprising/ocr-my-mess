"""GUI smoke tests for the Fedora Atomic / secureblue Toolbx environment.

These tests are meant to run *inside* the container built from
``tests/Dockerfile.toolbox`` (a ``fedora-toolbox`` image dressed with the very
same dependencies as ``scripts/install_atomic.sh``). They verify that the
Tk/ttkbootstrap GUI:

1. can be created and laid out on an X display, with the expected widgets, and
2. can be launched as a real process (the ``ocr-my-mess`` console script, i.e.
   what ``toolbox run -c ocr-my-mess ocr-my-mess`` executes) and actually maps a
   window on screen.

The tests are opt-in: set ``OCR_MY_MESS_TOOLBOX_TEST=1`` to enable them. The
runner ``tests/run_toolbox_gui_test.sh`` does that for you. When no usable X
display is available, a private ``Xvfb`` server is started automatically.
"""

import os
import shutil
import signal
import subprocess
import sys
import time

import pytest

GUI_TITLE_PREFIX = "OCR My Mess"
WINDOW_NAME = "OCR My Mess"

pytestmark = [
    pytest.mark.toolbox_gui,
    pytest.mark.skipif(
        not os.environ.get("OCR_MY_MESS_TOOLBOX_TEST"),
        reason="Set OCR_MY_MESS_TOOLBOX_TEST=1 to run the Toolbx GUI tests "
        "(normally run through tests/run_toolbox_gui_test.sh)",
    ),
]


def _display_ok(display):
    """Return True when a Tk client can connect to ``display``."""
    if not display:
        return False
    previous = os.environ.get("DISPLAY")
    os.environ["DISPLAY"] = display
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
        return True
    except Exception:
        return False
    finally:
        if previous is None:
            os.environ.pop("DISPLAY", None)
        else:
            os.environ["DISPLAY"] = previous


@pytest.fixture(scope="session")
def display():
    """Yield a usable X display, starting Xvfb when needed."""
    current = os.environ.get("DISPLAY")
    if _display_ok(current):
        yield current
        return

    if shutil.which("Xvfb") is None:
        pytest.skip("No usable X display and Xvfb is not installed")

    display_name = os.environ.get("OCR_MY_MESS_TEST_DISPLAY", ":99")
    proc = subprocess.Popen(
        ["Xvfb", display_name, "-screen", "0", "1280x1000x24", "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 15
    while time.time() < deadline:
        if _display_ok(display_name):
            break
        if proc.poll() is not None:
            pytest.fail("Xvfb exited before becoming ready")
        time.sleep(0.2)
    else:
        proc.terminate()
        pytest.fail(f"Xvfb did not become ready on {display_name}")

    os.environ["DISPLAY"] = display_name
    try:
        yield display_name
    finally:
        if current is None:
            os.environ.pop("DISPLAY", None)
        else:
            os.environ["DISPLAY"] = current
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _find_notebook(widget):
    """Depth-first search for the first ttk.Notebook in the widget tree."""
    import ttkbootstrap as tb

    for child in widget.winfo_children():
        if isinstance(child, tb.Notebook):
            return child
        found = _find_notebook(child)
        if found is not None:
            return found
    return None


def _gui_command():
    """Command that starts the GUI, preferring the installed console script."""
    exe = shutil.which("ocr-my-mess")
    if exe:
        return [exe]
    return [sys.executable, "-m", "pdf_pipeline.main"]


def _run_xdotool(args, display):
    return subprocess.run(
        ["xdotool", *args],
        env=dict(os.environ, DISPLAY=display),
        capture_output=True,
        text=True,
    )


def _wait_for_window(display, proc, timeout=30):
    """Wait until the GUI window is mapped; return its window id."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            output = proc.stdout.read() if proc.stdout else ""
            pytest.fail(
                f"GUI process exited early with code {proc.returncode}:\n{output}"
            )
        result = _run_xdotool(["search", "--name", WINDOW_NAME], display)
        wids = [w for w in result.stdout.split() if w.strip()]
        if wids:
            return wids[-1]
        time.sleep(0.3)
    return None


def _terminate(proc):
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def test_gui_widgets_are_created(display):
    """The main window and its key widgets are built without errors."""
    from pdf_pipeline.gui import App

    app = App()
    try:
        app.update_idletasks()
        app.update()

        assert app.title().startswith(GUI_TITLE_PREFIX), app.title()
        assert app.winfo_width() > 100
        assert app.winfo_height() > 100

        assert app.run_button.cget("text") == "Lancer le Pipeline Complet"
        assert app.run_ocr_button.cget("text") == "Lancer l'OCR"
        assert app.run_merge_button.cget("text") == "Lancer la Fusion"

        notebook = _find_notebook(app)
        assert notebook is not None, "No ttk.Notebook found in the GUI"
        tabs = [notebook.tab(i, "text") for i in range(notebook.index("end"))]
        assert tabs == ["Pipeline Complet", "OCR Seulement", "Fusion des fichiers"], tabs
    finally:
        app.destroy()


def test_gui_launches_as_process(display, tmp_path):
    """Launch the real entry point and verify a window is mapped on screen."""
    if shutil.which("xdotool") is None:
        pytest.skip("xdotool is required to inspect the running GUI window")

    command = _gui_command()
    env = dict(os.environ, DISPLAY=display)
    proc = subprocess.Popen(
        command,
        env=env,
        cwd=str(tmp_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wid = _wait_for_window(display, proc)
        assert wid, f"No window named {WINDOW_NAME!r} appeared within 30s"

        name = _run_xdotool(["getwindowname", wid], display).stdout.strip()
        assert name.startswith(GUI_TITLE_PREFIX), name

        geometry = _run_xdotool(["getwindowgeometry", "--shell", wid], display).stdout
        geometry = dict(
            line.split("=") for line in geometry.splitlines() if "=" in line
        )
        assert int(geometry.get("WIDTH", 0)) > 100, geometry
        assert int(geometry.get("HEIGHT", 0)) > 100, geometry

        # A non-blank screenshot proves the theme actually rendered pixels.
        if shutil.which("import") and shutil.which("identify"):
            screenshot = tmp_path / "toolbox_gui.png"
            subprocess.run(
                ["import", "-window", "root", str(screenshot)],
                env=env,
                check=True,
            )
            colors = subprocess.run(
                ["identify", "-format", "%k", str(screenshot)],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            assert colors.isdigit() and int(colors) > 16, (
                f"GUI screenshot looks blank ({colors} unique colours): {screenshot}"
            )
    finally:
        _terminate(proc)
