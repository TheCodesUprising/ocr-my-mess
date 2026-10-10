# ocr-my-mess

A complete and modular Python pipeline to convert, OCR, and merge all your documents into a single, searchable PDF.

## Pre-built Binaries (Simplest Method)

For the quickest start, pre-built executables for Windows, macOS, and Linux are available for download from the [GitHub Releases page](https://github.com/TheCodesUprising/ocr-my-mess/releases). These executables are standalone and do not require Python or any other dependencies to be installed on your system. Simply download the appropriate version for your operating system, extract it, and run.

## Features

- **Recursive Conversion**: Traverses a directory to find all supported files (images, office documents, archives, existing PDFs).
- **OCR Processing**: Applies OCR to all documents using `ocrmypdf` to make them text-searchable.
- **Hierarchical Merging**: Merges all generated PDFs into a single file with a table of contents that mirrors the original folder structure.
- **Dual Interfaces**: Usable as both a powerful Command-Line Interface (`ocr-my-mess-cli`) and a simple Graphical User Interface (`ocr-my-mess-gui`).
- **Cross-Platform**: Packaged with PyInstaller to run on Windows, macOS, and Linux.

## Installation

The simplest way to get started is the [pre-built binaries](#pre-built-binaries-simplest-method). Otherwise, see [From PyPI](#from-pypi) below.

### From PyPI

This method requires you to install system dependencies manually before installing the Python package.

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr jbig2dec libreoffice
```


    **Tails:**
    ```bash
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr jbig2dec libreoffice python3-pip
    # Accept to install those packages during system startup
    torsocks pip install ocr-my-mess --break-system-packages
    # Be sure you have '/home/amnesia/.local/bin' on your $PATH
    ```

    **macOS:**
    ```bash
    brew install tesseract jbig2dec
    brew install --cask libreoffice
    ```

    **Windows:**
    Installation on Windows is more complex. We recommend using the [official `ocrmypdf` Docker image](https://ocrmypdf.readthedocs.io/en/latest/docker.html) if possible. Otherwise, you will need to install the following dependencies manually:
    - Tesseract OCR: `choco install tesseract`
    - LibreOffice: `choco install libreoffice`
    - jbig2dec: These are not readily available on Chocolatey. Please refer to the `ocrmypdf` documentation for installation instructions.

    **Optional Dependencies:**
    - `jbig2enc`: For better PDF compression. See the [ocrmypdf documentation](https://ocrmypdf.readthedocs.io/en/latest/jbig2.html) for installation.

2.  **Install `ocr-my-mess` from PyPI**

    ```bash
    pip install ocr-my-mess
    ```


## Fedora Atomic & secureblue (Toolbx)

On Atomic desktops — including [secureblue](https://secureblue.dev), a hardened
Silverblue/Kinoite — the root filesystem is read-only, so `ocr-my-mess` runs
inside a [Toolbx](https://containertoolbx.org/) container.

**Install** (the script uses the local source if run from a clone, otherwise it
pulls `ocr-my-mess` from PyPI):

```bash
curl -fsSLO https://raw.githubusercontent.com/TheCodesUprising/ocr-my-mess/no-masters/scripts/install_atomic.sh
chmod +x install_atomic.sh && ./install_atomic.sh
```

This creates a container named `ocr-my-mess`. Run anything in it with
`toolbox run -c ocr-my-mess <command>`:

```bash
toolbox run -c ocr-my-mess ocr-my-mess          # GUI
toolbox run -c ocr-my-mess ocr-my-mess run --input ~/Documents --output ~/Documents/scan.pdf
```

> **GUI on secureblue:** Tkinter requires X11 and secureblue disables Xwayland
> by default, so the window never appears. Enable it once and reboot with
> `ujust set-xwayland on`.

**Manage it:**

```bash
toolbox run -c ocr-my-mess pip install --upgrade ocr-my-mess   # update
toolbox rm -f ocr-my-mess                                       # remove
```

**Automated GUI test** (reproduces this environment in Podman, no secureblue
host needed):

```bash
./tests/run_toolbox_gui_test.sh
```


## Usage

The application can be run in two modes:

- **Command-Line Interface (CLI)**: If you provide any arguments.
- **Graphical User Interface (GUI)**: If you run it without any arguments.

### Command-Line Interface (CLI)

The CLI provides several commands, including `run`, `convert` and `merge`.

```bash
# General help
ocr-my-mess --help

# Get version
ocr-my-mess -v

# Run the full pipeline on a directory
ocr-my-mess run --input /path/to/docs --output /path/to/final.pdf --lang en+fr

# Just convert and OCR all documents in a folder
ocr-my-mess convert --input-dir /path/to/docs --output-dir /path/to/output

# Just merge all PDFs in a folder into a single file
ocr-my-mess merge --input-dir /path/to/output --output-file /path/to/final.pdf
```

### Graphical User Interface (GUI)

For a more visual approach, you can launch the GUI by running the command without any arguments.

```bash
ocr-my-mess
```

This will open a window allowing you to:
- Select input and output directories.
- Choose OCR languages.
- Run the full pipeline.
- See live logs and progress.

## Development

The build and CI environment is defined with Conda. It bundles the Python dependencies and the external binaries (Tesseract, jbig2dec, Ghostscript) used to produce the standalone executables:

```bash
conda env create -f config/conda/environment.yml
conda activate ocr-my-mess
pip install -e .
```

**Note:** LibreOffice is not part of the Conda environment; install it separately if you need office document conversion.

### Running Tests

To ensure everything is working correctly, run the automated tests:

```bash
pytest
```

### Testing the Toolbx GUI

Builds a `fedora-toolbox` container and checks that the GUI really renders
(window mapped, theme drawn). Works on any Linux host with podman or docker:

```bash
./tests/run_toolbox_gui_test.sh
```

Use `OCR_MY_MESS_USE_HOST_DISPLAY=1` to reuse your own display instead of the
container's private Xvfb. The tests live in `tests/test_toolbox_gui.py` (marker
`toolbox_gui`) and are opt-in via `OCR_MY_MESS_TOOLBOX_TEST=1`.

### Building Executables

This project uses PyInstaller to create a standalone executable. A build script is provided in the `scripts/` directory.

```bash
# Build the executable
python scripts/build.py
```

The executable will be located in the `dist/` directory.

**Note**: When running the GUI from the executable on Windows or macOS, a console window will appear alongside the main application window. This is expected behavior.
