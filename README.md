# OCR My Project

A complete OCR and PDF management toolkit that processes documents with OCR and merges them with a hierarchical table of contents.

## Features

- **OCR Processing**: Convert images and scanned PDFs to searchable PDFs using ocrmypdf
- **Multi-format Support**: Handles PDF, PNG, JPG, JPEG, TIFF, and TIF files
- **Directory Processing**: Recursively processes entire directory structures
- **ZIP Archive Extraction**: Automatically extracts ZIP archives and processes contained files
- **Progress Tracking**: Resumes interrupted processing using JSON state files
- **PDF Merging**: Combines multiple PDFs with a hierarchical table of contents based on directory structure
- **Threaded Processing**: Uses multiple threads for faster processing
- **Force OCR Option**: Option to force OCR on all pages for better results
- **Multi-language Support**: Support for different OCR languages (default: French)

## Installation

### Option 1: Using System Python with System Tesseract (recommended)

1. **Install Tesseract OCR using system packages:**

   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install tesseract-ocr tesseract-ocr-fra libtesseract-dev
   ```

   **CentOS/RHEL/Fedora:**
   ```bash
   # For CentOS/RHEL
   sudo yum install tesseract tesseract-devel
   
   # For Fedora
   sudo dnf install tesseract tesseract-devel
   
   # Install French language pack
   sudo dnf install tesseract-langpack-fra  # For Fedora
   # or
   sudo yum install tesseract-langpack-fra  # For CentOS/RHEL
   ```

   **macOS:**
   ```bash
   # Install Homebrew if not already installed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Tesseract
   brew install tesseract
   
   # Install language packs
   brew install tesseract-lang
   # Or specifically for French
   brew install tesseract-lang fra
   ```

   **Windows:**
   - Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
   - Add the installation directory (usually `C:\Program Files\Tesseract-OCR`) to your PATH
   - Install language packs as needed

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

### Option 2: Using Miniconda with Environment File (recommended)

1. **Install Miniconda:**

   **Linux:**
   ```bash
   # Download the latest Miniconda installer
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   
   # Run the installer
   bash Miniconda3-latest-Linux-x86_64.sh
   
   # Follow the prompts and restart your terminal or source the bashrc
   source ~/.bashrc
   ```

   **macOS:**
   ```bash
   # Download the latest Miniconda installer
   curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
   
   # Run the installer
   bash Miniconda3-latest-MacOSX-x86_64.sh
   
   # Follow the prompts and restart your terminal or source the bash_profile
   source ~/.bash_profile
   ```

   **Windows:**
   - Download from: https://docs.conda.io/en/latest/miniconda.html
   - Run the installer with default options
   - Use Anaconda Prompt for command line operations

2. **Create and activate the conda environment:**
   ```bash
   # Create environment using the provided environment file
   conda env create -f environment.yml
   
   # Activate the environment
   conda activate ocrmyproject
   
   # Install the package in development mode
   pip install -e .
   ```

### From source:
```bash
git clone https://github.com/yourusername/ocrmyproject.git
cd ocrmyproject

# Using Option 1: System packages
pip install -r requirements.txt
pip install -e .

# Using Option 2: Conda environment (recommended)
conda env create -f environment.yml
conda activate ocrmyproject
pip install -e .
```

## Usage

The package provides both command-line interface and graphical user interface.

### Command-Line Interface

The package provides three main commands: `ocr`, `merge`, and `all`.

#### Launching the CLI

To launch the command-line interface:

```bash
ocrmyproject --help
```

#### Available Commands

**OCR Processing**
Process files with OCR to create searchable PDFs:

```bash
ocrmyproject ocr -i /path/to/input/directory -o /path/to/output/directory
```

**PDF Merging**
Merge multiple PDFs with a table of contents based on directory structure:

```bash
ocrmyproject merge -i /path/to/pdfs/directory -o merged_output.pdf
```

**Complete Processing (OCR + Merge)**
Perform OCR on all files and then merge them into a single PDF with TOC:

```bash
ocrmyproject all -i /path/to/documents -o all_processed_output.pdf
```

#### CLI Command Options

##### OCR Command:
- `-i, --input`: Input directory containing files to process
- `-o, --output`: Output directory for results (default: ocr_results)
- `--force-ocr`: Force OCR on all pages (better results, slower processing)
- `-l, --language`: OCR language (default: fra for French)

##### Merge Command:
- `-i, --input`: Input directory containing PDFs to merge
- `-o, --output`: Output PDF file path (default: merged_output.pdf)

##### All Command:
- `-i, --input`: Input directory containing documents to process
- `-o, --output`: Output PDF file path (default: all_processed_output.pdf)
- `--force-ocr`: Force OCR on all pages (better results, slower processing)
- `-l, --language`: OCR language (default: fra for French)

### Graphical User Interface

#### Launching the GUI

To launch the graphical user interface:

```bash
python -m ocrmyproject.gui
```

Or from the project root directory:

```bash
python -c "from ocrmyproject import gui; gui.main()"
```

The GUI provides a simple interface with:
- Input and output directory selection
- Operation type (OCR, merge, or complete processing)
- Language selection
- Force OCR option
- Progress tracking with file and page counts

With force OCR for better results:
```bash
ocrmyproject ocr --force-ocr -i /path/to/input/directory -o /path/to/output/directory
```

### Multi-language Support

Specify the OCR language (default is French):
```bash
ocrmyproject ocr --language eng -i /path/to/input/directory -o /path/to/output/directory
```

Supported languages can be any language supported by Tesseract OCR (e.g., `fra` for French, `eng` for English, `deu` for German, etc.)

The test files in the `tmp_tests` directory contain English text for testing purposes.

### PDF Merging

Merge multiple PDFs with a table of contents based on directory structure:

```bash
ocrmyproject merge -i /path/to/pdfs/directory -o merged_output.pdf
```

### Complete Processing (OCR + Merge)

Perform OCR on all files and then merge them into a single PDF with TOC:

```bash
ocrmyproject all -i /path/to/documents -o all_processed_output.pdf
```

With force OCR and specific language:
```bash
ocrmyproject all --force-ocr --language fra -i /path/to/documents -o all_processed_output.pdf
```

### Command Options

#### OCR Command:
- `-i, --input`: Input directory containing files to process
- `-o, --output`: Output directory for results (default: ocr_results)
- `--force-ocr`: Force OCR on all pages (better results, slower processing)
- `-l, --language`: OCR language (default: fra for French)
- `--help`: Show help information

#### Merge Command:
- `-i, --input`: Input directory containing PDFs to merge
- `-o, --output`: Output PDF file path (default: merged_output.pdf)
- `--help`: Show help information

#### All Command:
- `-i, --input`: Input directory containing documents to process
- `-o, --output`: Output PDF file path (default: all_processed_output.pdf)
- `--force-ocr`: Force OCR on all pages (better results, slower processing)
- `-l, --language`: OCR language (default: fra for French)
- `--help`: Show help information

### Default Behavior

- OCR command: Creates `ocr_results` directory if no output specified
- Merge command: Creates `<input_dir_name>_merged.pdf` if no output specified
- All command: Creates `all_processed_output.pdf` if no output specified

## Examples

Process images with OCR in French (default):
```bash
ocrmyproject ocr -i ./scanned_images -o ./ocr_results
```

Process with improved OCR quality in English:
```bash
ocrmyproject ocr --force-ocr --language eng -i ./important_docs -o ./processed_docs
```

Merge processed PDFs with table of contents:
```bash
ocrmyproject merge -i ./ocr_results -o ./final_merged_document.pdf
```

Complete process in one command with German OCR:
```bash
ocrmyproject all --force-ocr --language deu -i ./mixed_documents -o ./complete_document.pdf
```

## Requirements

- Python 3.7+
- System dependencies for ocrmypdf (Tesseract, QPDF, etc.)

## Dependencies

Install required Python packages:
```bash
pip install -r requirements.txt
```

## Package Structure

```
ocrmyproject/
├── ocrmyproject/
│   ├── __init__.py
│   ├── api.py          # Core OCR processing functionality
│   ├── cli.py          # Command-line interface
│   ├── utils/          # Utility modules
│   └── ...             # Other modules
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_ocrmyproject.py
├── setup.py
├── requirements.txt
├── README.md
└── ...
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run tests with verbose output
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=ocrmyproject
```

### Install in Development Mode

```bash
pip install -e .
```

### Build Distribution

```bash
pip install build
python -m build
```

## Graphical User Interface

To launch the GUI application:

```bash
python -m ocrmyproject.gui
```

The GUI provides a simple interface with:
- Input and output directory selection
- Operation type (OCR, merge, or complete processing)
- Language selection
- Force OCR option
- Progress tracking

## Architecture

The system handles:
- ZIP archives (automatically extracts and processes)
- Multi-level directory structures (preserves hierarchy in TOC)
- Resume functionality (continues from where it left off)
- Progress tracking (using JSON state files)
- File type filtering (processes only supported formats)
- Multi-language OCR support

## Troubleshooting

- Ensure ocrmypdf dependencies are installed (Tesseract, QPDF, etc.)
- Check that input directories exist and have read permissions
- Verify sufficient disk space for temporary and output files
- For OCR issues, try the `--force-ocr` option to ensure all pages are processed
- Language-specific issues may require installing additional Tesseract language packs

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run tests (`python -m pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request
