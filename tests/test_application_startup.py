import subprocess
import sys
import os
from unittest.mock import patch
import pytest

from pdf_pipeline.gui import App

def test_cli_help():
    """Test that the CLI starts and shows the help message."""
    # We use sys.executable to be sure we are using the python from the virtual env
    result = subprocess.run(
        [sys.executable, "-m", "pdf_pipeline.main", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout

@pytest.mark.skipif(sys.platform != "win32" and not os.environ.get("DISPLAY"), reason="No display available for GUI test")
@patch('tkinter.Tk.mainloop')
def test_gui_startup(mock_mainloop):
    """Test that the GUI application class can be instantiated without errors."""
    try:
        # We need to destroy the window, otherwise it can interfere with other tests
        # in some environments.
        app = App()
        # We need to process at least one event loop for the window to be created
        app.update_idletasks()
        app.destroy()
    except Exception as e:
        pytest.fail(f"GUI App instantiation failed: {e}")
