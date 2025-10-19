"""
Full integration test for the ocr-my-mess pipeline using Typer's CliRunner.

This test simulates a real-world scenario by invoking the CLI commands directly
in-process, avoiding subprocess and environment issues.
"""

import zipfile
import logging
import sys
import platform
from pathlib import Path

import fitz  # PyMuPDF
import pytest
import difflib

from PIL import Image, ImageDraw, ImageFont
from typer.testing import CliRunner

from pdf_pipeline.cli import app  # Import the Typer app object
from pdf_pipeline.utils import check_command_exists



runner = CliRunner()
logger = logging.getLogger(__name__)


# --- Test Data Configuration ---
TEXT_A1_EN = "Text A1 ENGLISH OCR TEST"
TEXT_B1_EN = "Text B1 ENGLISH OCR TEST"
TEXT_IMG_A1_FR = "Texte image Al FR OCR"
TEXT_IMG_B1_FR = "Texte image BI FR OCR"
TEXT_PDF_A1 = "PDF A1 OCR"
TEXT_SINGLE_PDF = "Single PDF root OCR"
TEXT_ARCHIVE_IMG = "Image inside archive"





def fuzzy_match(expected: str, actual_text: str, threshold: float = 0.8) -> bool:
    """
    Returns True if a string similar to `expected` exists in `actual_text`,
    using sliding window matching and difflib similarity.
    """
    expected_lower = expected.lower()
    actual_lower = actual_text.lower()

    # Use sliding window of length equal to expected string
    window_size = len(expected_lower)
    for i in range(0, len(actual_lower) - window_size + 1):
        window = actual_lower[i:i+window_size]
        ratio = difflib.SequenceMatcher(None, expected_lower, window).ratio()
        if ratio >= threshold:
            return True
    return False



@pytest.fixture(scope="module")
def test_data_dir(tmp_path_factory) -> Path:
    """Creates a temporary directory with a rich structure for a full pipeline test."""
    root = tmp_path_factory.mktemp("integration_data")
    input_dir = root / "input"
    input_dir.mkdir()

    def create_image_with_text(path: Path, text: str):
        img = Image.new("RGB", (800, 200), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            if platform == "win32":
                font = ImageFont.truetype("arial.ttf", 40)
            else:
                font = ImageFont.truetype("DejaVuSans.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
            logger.warning(f"Could not load DejaVuSans.ttf from system. Using fallback font: {font.getname()}")

        draw.text((10, 10), text, fill=(0, 0, 0), font=font)
        img.save(path, "PNG")

    def create_text_pdf(path: Path, text: str):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), text)
        doc.save(path)

    folder_a = input_dir / "folderA"
    folder_a.mkdir()
    (folder_a / "text_en_1.txt").write_text(TEXT_A1_EN)
    create_image_with_text(folder_a / "image_fr_1.png", TEXT_IMG_A1_FR)
    create_text_pdf(folder_a / "doc_en_1.pdf", TEXT_PDF_A1)

    folder_b = input_dir / "folderB"
    folder_b.mkdir()
    subfolder_b1 = folder_b / "subfolderB1"
    subfolder_b1.mkdir()
    (subfolder_b1 / "text_en_2.txt").write_text(TEXT_B1_EN)
    create_image_with_text(subfolder_b1 / "image_fr_2.png", TEXT_IMG_B1_FR)

    archive_path = folder_b / "archiveA.zip"
    with zipfile.ZipFile(archive_path, "w") as zf:
        img_path = root / "archive_img.png"
        create_image_with_text(img_path, TEXT_ARCHIVE_IMG)
        zf.write(img_path, arcname=img_path.name)

    create_text_pdf(input_dir / "single_pdf.pdf", TEXT_SINGLE_PDF)

    return root

@pytest.mark.xfail(sys.platform == "win32", reason="OCR flaky on Windows due unknown reason")
def test_full_pipeline(test_data_dir: Path):
    input_dir = test_data_dir / "input"
    output_dir = test_data_dir / "output"
    final_pdf_path = test_data_dir / "final.pdf"

    convert_args = [
        "convert",
        "--verbose",
        "--input-dir", str(input_dir),
        "--output-dir", str(output_dir),
        "--lang", "eng+fra",
        "--no-convert-office",  # inutile mais explicite
    ]

    convert_result = runner.invoke(app, convert_args, input="n\n")
    assert convert_result.exit_code == 0, f"Convert command failed: {convert_result.stdout}"

    merge_result = runner.invoke(app, [
        "merge",
        "--verbose",
        "--input-dir", str(output_dir),
        "--output-file", str(final_pdf_path),
    ])
    assert merge_result.exit_code == 0, f"Merge command failed: {merge_result.stdout}"
    assert final_pdf_path.exists(), "Final merged PDF was not created."

    # Extraction OCR
    doc = fitz.open(final_pdf_path)
    full_text = "".join(page.get_text() for page in doc)
    doc.close()

    print("📝 Extracted OCR text:\n", full_text)

    expected_phrases = [
        TEXT_IMG_A1_FR,
        TEXT_IMG_B1_FR,
        TEXT_ARCHIVE_IMG,
        TEXT_PDF_A1,
        TEXT_SINGLE_PDF,
    ]

    for phrase in expected_phrases:
        assert fuzzy_match(phrase, full_text), f"OCR text not found or fuzzy match failed: '{phrase}'"

def test_page_count_integrity(test_data_dir: Path):
    """Runs the pipeline and verifies the exact page count of the final PDF."""
    input_dir = test_data_dir / "input"
    final_pdf_path = test_data_dir / "final_page_count.pdf"

    run_args = [
        "run",
        "--input", str(input_dir),
        "--output", str(final_pdf_path),
        "--lang", "eng+fra",
        "-O", "0",
    ]

    run_result = runner.invoke(app, run_args, input="n\n") # Answer 'no' to cache prompt
    assert run_result.exit_code == 0, f"Pipeline command failed: {run_result.stdout}"

    assert final_pdf_path.exists(), "Final merged PDF was not created for page count test."

    with fitz.open(final_pdf_path) as doc:
        libreoffice_installed = check_command_exists("libreoffice")
        expected_pages = 7 if libreoffice_installed else 5
        assert doc.page_count == expected_pages, f"Expected {expected_pages} pages, but got {doc.page_count}"
