"""
Main entry point for the ocr-my-mess application.

This script checks the command-line arguments to determine whether to launch
the Graphical User Interface (GUI) or the Command-Line Interface (CLI).
"""

import sys


def main():
    """
    Launch either the GUI or the CLI based on the presence of command-line arguments.
    """
    if len(sys.argv) > 1:
        # If there are arguments, run the CLI
        from . import cli
        cli.main()
    else:
        # If there are no arguments, run the GUI
        from . import gui
        gui.main()


if __name__ == "__main__":
    main()
