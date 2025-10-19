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

There are two main ways to install `ocr-my-mess`: from Conda or from PyPI.

### From Conda (Recommended)

This is the easiest and most reliable way to get started. The Conda environment, defined in the `config/conda/environment.yml` file, includes all Python dependencies as well as external binaries like Tesseract, Unpaper, and jbig2dec. This ensures you have the latest compiled versions, which are often more recent and performant than the ones provided by your operating system's package manager.

1.  **Create and activate the Conda environment:**
    ```bash
    conda env create -f environment.yml
    conda activate ocr-my-mess
    ```
2.  **Run the application:**
    Once the environment is activated, you can run the application directly.
    ```bash
    ocr-my-mess
    ```

**For development:** If you want to modify the source code, you can install the project in editable mode after activating the environment:
```bash
pip install -e .
```

**Note on LibreOffice**: The Conda environment does not include LibreOffice. If you need to convert office documents, you must install it separately on your system (see the PyPI installation section for instructions).

### From PyPI

This method requires you to install system dependencies manually before installing the Python package.

1.  **Install System Dependencies**

    This project relies on several external programs. Please install them using your system's package manager.

    **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr unpaper jbig2dec libreoffice
    ```

    **macOS:**
    ```bash
    brew install tesseract unpaper jbig2dec
    brew install --cask libreoffice
    ```

    **Windows:**
    Installation on Windows is more complex. We recommend using the [official `ocrmypdf` Docker image](https://ocrmypdf.readthedocs.io/en/latest/docker.html) if possible. Otherwise, you will need to install the following dependencies manually:
    - Tesseract OCR: `choco install tesseract`
    - LibreOffice: `choco install libreoffice`
    - Unpaper and jbig2dec: These are not readily available on Chocolatey. Please refer to the `ocrmypdf` documentation for installation instructions.

    **Optional Dependencies:**
    - `jbig2enc`: For better PDF compression. See the [ocrmypdf documentation](https://ocrmypdf.readthedocs.io/en/latest/jbig2.html) for installation.

2.  **Install `ocr-my-mess` from PyPI**

    ```bash
    pip install ocr-my-mess
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

### Running Tests

To ensure everything is working correctly, run the automated tests:

```bash
pytest
```

### Building Executables

This project uses PyInstaller to create a standalone executable. A build script is provided in the `scripts/` directory.

```bash
# Build the executable
python scripts/build.py
```

The executable will be located in the `dist/` directory.

**Note**: When running the GUI from the executable on Windows or macOS, a console window will appear alongside the main application window. This is expected behavior.
