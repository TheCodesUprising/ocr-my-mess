# ocr-my-mess

A complete and modular Python pipeline to convert, OCR, and merge all your documents into a single, searchable PDF.

## Features

- **Recursive Conversion**: Traverses a directory to find all supported files (images, office documents, archives, existing PDFs).
- **OCR Processing**: Applies OCR to all documents using `ocrmypdf` to make them text-searchable.
- **Hierarchical Merging**: Merges all generated PDFs into a single file with a table of contents that mirrors the original folder structure.
- **Dual Interfaces**: Usable as both a powerful Command-Line Interface (`ocr-my-mess-cli`) and a simple Graphical User Interface (`ocr-my-mess-gui`).
- **Cross-Platform**: Packaged with PyInstaller to run on Windows, macOS, and Linux.

## Installation

### Using Conda (Recommended)

This is the easiest way to get started, as it handles all dependencies, including Python itself.

```bash
# 1. Create the conda environment
conda env create -f environment.yml

# 2. Activate the environment
conda activate ocr-my-mess

# 3. Install the project in editable mode
pip install -e .
```

### Using Pip

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the project in editable mode
pip install -e .
```

**Note**: For office document conversion, you must have `LibreOffice` installed and available in your system's PATH.

## Usage

### Command-Line Interface (CLI)

The CLI provides two main sub-commands: `convert` and `merge`.

```bash
# General help
ocr-my-mess-cli --help

# 1. Convert and OCR all documents in a folder
ocr-my-mess-cli convert --input-dir /path/to/docs --output-dir /path/to/output --lang en+fr

# 2. Merge all PDFs in the output folder into a single file
ocr-my-mess-cli merge --input-dir /path/to/output --output-file /path/to/final.pdf
```

### Graphical User Interface (GUI)

For a more visual approach, you can launch the GUI.

```bash
ocr-my-mess-gui
```

This will open a window allowing you to:
- Select input and output directories.
- Choose OCR languages.
- Run the "Convert + OCR" and "Merge" processes.
- See live logs and progress.

## Development

### Running Tests

To ensure everything is working correctly, run the automated tests:

```bash
pytest
```

### Building Executables

This project uses PyInstaller to create standalone executables. Build scripts are provided in the `scripts/` directory.

```bash
# Build the CLI executable
./scripts/build_cli.sh

# Build the GUI executable
./scripts/build_gui.sh
```

The executables will be located in the `dist/` directory.
