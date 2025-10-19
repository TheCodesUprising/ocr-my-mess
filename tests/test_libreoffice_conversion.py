import pytest
from pathlib import Path
from pdf_pipeline.convert import convert_office_to_pdf
from pdf_pipeline.utils import check_command_exists

@pytest.mark.integration
@pytest.mark.skipif(not check_command_exists("libreoffice"), reason="LibreOffice not found")
def test_libreoffice_txt_conversion(tmp_path: Path):
    """
    Test that LibreOffice can convert a .txt file to PDF.
    This is a simple proxy for testing general LibreOffice conversion.
    """
    # 1. Create a dummy .txt file
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    txt_file = source_dir / "test.txt"
    txt_file.write_text("This is a test for LibreOffice conversion.")

    # 2. Define output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # 3. Call the conversion function
    result_path = convert_office_to_pdf(txt_file, output_dir)

    # 4. Check for output
    expected_pdf = output_dir / "test.pdf"
    assert result_path is not None
    assert result_path == expected_pdf
    assert expected_pdf.exists()
    assert expected_pdf.stat().st_size > 0
