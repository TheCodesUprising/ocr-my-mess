import subprocess
import os
from pathlib import Path
import pytest
from pypdf import PdfReader
import shutil

EXECUTABLE_PATH = os.environ.get("OCR_MY_MESS_EXECUTABLE")

@pytest.mark.end_to_end
@pytest.mark.skipif(not EXECUTABLE_PATH, reason="OCR_MY_MESS_EXECUTABLE env var not set")
@pytest.mark.skipif(EXECUTABLE_PATH and not Path(EXECUTABLE_PATH).exists(), reason=f"Executable not found at path: {EXECUTABLE_PATH}")
def test_ocr_on_packaged_binary(tmp_path):
    """
    A full end-to-end test that runs the packaged binary on a sample PDF
    and verifies that the output PDF contains the expected OCR text.
    """
    input_pdf_file = Path(__file__).parent / "ocr_test_input.pdf"
    output_pdf = tmp_path / "output.pdf"

    # The text we expect to find in the PDF after OCR
    expected_text = "repository of all manpages contained."

    # Create a temporary input directory and copy the test PDF into it
    input_dir = tmp_path / "input_dir"
    input_dir.mkdir()
    shutil.copy(input_pdf_file, input_dir / input_pdf_file.name)

    command = [
        EXECUTABLE_PATH,
        "run", # Changed from "process"
        "--input", str(input_dir), # Changed from "--input-file"
        "--output", str(output_pdf), # Changed from "--output-file"
        "--force-ocr",
        "--no-reuse-cache" # Added this line
    ]

    result = subprocess.run(command, capture_output=True, text=True, check=False)

    assert result.returncode == 0, f"OCR process failed with exit code {result.returncode}:\n{result.stderr}"
    assert output_pdf.exists(), "Output PDF was not created."

    # Verify the content of the output PDF
    reader = PdfReader(output_pdf)
    assert len(reader.pages) > 0, "Output PDF is empty."
    page = reader.pages[0]
    text = page.extract_text()

    assert expected_text.lower() in text.lower(), f"Expected text not found in the output PDF. Found: \n{text}"
