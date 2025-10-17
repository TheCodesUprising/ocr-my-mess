"""
Module for merging multiple PDFs into a single file with hierarchical bookmarks using PyMuPDF.

This module uses PyMuPDF (fitz) to:
1. Recursively scan a directory for PDF files.
2. Append all found PDFs into a single master PDF.
3. Build and set a hierarchical table of contents (bookmarks) that mirrors the
   original folder structure.
"""

import logging
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
from rich.progress import Progress

log = logging.getLogger(__name__)


def _build_toc_and_merge(
    main_doc: fitz.Document,
    folder_path: Path,
    toc_depth: int,
    current_depth: int,
) -> List:
    """
    Recursively builds a TOC list for PyMuPDF and merges PDFs into the main document.

    Args:
        main_doc: The main fitz.Document object to merge into.
        folder_path: The current folder to process.
        toc_depth: Maximum depth for the TOC.
        current_depth: The current recursion depth.

    Returns:
        A list of TOC entries for the current level, in PyMuPDF format.
    """
    toc_entries = []
    if current_depth > toc_depth:
        return toc_entries

    # Sort entries to ensure consistent order
    entries = sorted(list(folder_path.iterdir()), key=lambda p: p.name)

    for entry in entries:
        if entry.is_dir():
            # Recurse into subdirectory
            sub_toc = _build_toc_and_merge(
                main_doc, entry, toc_depth, current_depth + 1
            )
            if sub_toc:
                # For a folder, the bookmark should point to the first page of its content.
                first_page_of_content = sub_toc[0][2]
                toc_entries.append([current_depth, entry.name, first_page_of_content])
                toc_entries.extend(sub_toc)

        elif entry.is_file() and entry.suffix.lower() == ".pdf":
            try:
                page_count_before = main_doc.page_count
                # TOC entry format: [level, title, page_number (1-based)]
                toc_entries.append([current_depth, entry.stem, page_count_before + 1])

                with fitz.open(entry) as src_doc:
                    main_doc.insert_pdf(src_doc)
                log.debug(f"Appended {entry.name} to the final PDF.")
            except Exception as e:
                log.warning(
                    f"Could not process PDF {entry.name}. It may be corrupt or incompatible. Error: {e}"
                )

    return toc_entries


def merge_pdfs(
    input_dir: Path,
    output_file: Path,
    toc_depth: int = 3,
) -> None:
    """
    Merges all PDFs in a directory into a single file with a hierarchical TOC using PyMuPDF.

    Args:
        input_dir: The directory containing the processed PDFs.
        output_file: The path for the final merged PDF.
        toc_depth: The maximum depth for the table of contents.
    """
    pdf_files = list(input_dir.rglob("*.pdf"))
    if not pdf_files:
        log.warning("No PDF files found to merge.")
        return

    log.info(f"Merging {len(pdf_files)} PDF files into {output_file.name}...")

    with fitz.open() as main_doc:
        with Progress() as progress:
            task = progress.add_task("[magenta]Merging PDFs...", total=1)

            toc = _build_toc_and_merge(
                main_doc, folder_path=input_dir, toc_depth=toc_depth, current_depth=1
            )

            if toc:
                log.debug("Setting table of contents.")
                main_doc.set_toc(toc)

            progress.update(task, advance=1)

        if main_doc.page_count > 0:
            log.info(f"Saving final PDF to {output_file}...")
            # Use garbage collection to reduce file size
            main_doc.save(output_file, garbage=4, deflate=True)
            log.info("Merge complete.")
        else:
            log.warning("No pages were added. Output file not created.")