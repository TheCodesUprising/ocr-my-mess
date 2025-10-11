"""
Core OCR processing functionality for ocrmyproject.
"""
import json
import logging
import os
import sys
import tempfile
from pathlib import Path
import fitz  # PyMuPDF for PDF merging only


def extract_zip_archives(source_dir):
    """
    Extracts all ZIP archives found in the source directory and its subdirectories.
    Files are extracted to a new subdirectory bearing the name of the ZIP archive.
    """
    import zipfile
    
    zip_found = False
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith('.zip'):
                zip_path = os.path.join(root, file)
                logging.info(f"ZIP archive found: {zip_path}")

                # Get the name of the ZIP archive without the extension
                zip_name = os.path.splitext(file)[0]
                # Set the extraction directory (a new subdirectory)
                extract_to_dir = os.path.join(root, zip_name)

                try:
                    # Create the new subdirectory for extraction if it doesn't exist
                    os.makedirs(extract_to_dir, exist_ok=True)

                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # Extract all contents to the new subdirectory
                        zip_ref.extractall(extract_to_dir)
                    logging.info(f"Archive '{file}' extracted successfully to '{extract_to_dir}'.")
                    zip_found = True
                    os.remove(zip_path)
                    logging.info(f"Archive '{file}' removed after extraction.")
                except zipfile.BadZipFile:
                    logging.error(f"Error: Archive '{file}' is corrupted and cannot be extracted.")
                except Exception as e:
                    logging.error(f"Error during extraction of '{file}': {e}")
    if zip_found:
        logging.info(
            "All ZIP archives have been processed. Rescanning to include new files.")
        return True  # Indicates that ZIP files were found and extracted
    return False  # Indicates that no ZIP files were found


def ocr_directory(source_dir, destination_dir, language='fra', force_ocr=False):
    """
    Walk through a source directory, process files with OCR, and copy results.
    Handles resumption and progress tracking.
    """
    import ocrmypdf

    # Check if directories exist
    if not os.path.isdir(source_dir):
        logging.error(f"Source directory '{source_dir}' does not exist or is not a valid directory.")
        sys.exit(1)

    os.makedirs(destination_dir, exist_ok=True)  # Create destination directory if it doesn't exist

    state_file = os.path.join(destination_dir, 'ocr_progress.json')
    processed_files = {}

    # First pass: Extract ZIP archives
    logging.info("Searching and extracting ZIP archives...")
    if extract_zip_archives(source_dir):
        # If ZIP files were extracted, we will reload the state
        # to ensure new files are accounted for in the total count
        logging.info("ZIP archives extracted. Resetting progress for complete scan.")
        if os.path.exists(state_file):
            os.remove(state_file)  # Remove state file to force a new complete scan
            logging.info("Progress file removed for new scan after ZIP extraction.")

    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                processed_files = json.load(f)
            logging.info("Resuming processing. Previously processed files loaded.")
        except json.JSONDecodeError:
            logging.warning("State file corrupted. Restarting processing.")
            processed_files = {}

    total_files = 0
    # Count all relevant files after ZIP extraction
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif')):
                total_files += 1

    processed_count = 0
    for root, dirs, files in os.walk(source_dir):
        # Create directory structure in destination
        relative_path = os.path.relpath(root, source_dir)
        current_destination_dir = os.path.join(destination_dir, relative_path)
        os.makedirs(current_destination_dir, exist_ok=True)

        for file in files:
            source_file_path = os.path.join(root, file)
            # Don't process ZIP archives themselves as OCR files
            if file.lower().endswith('.zip'):
                logging.info(f"ZIP file ignored for OCR (already extracted or not processable): {file}")
                continue

            destination_file_path = os.path.join(current_destination_dir, os.path.splitext(file)[0] + '.pdf')

            if source_file_path in processed_files and processed_files[source_file_path] == "completed":
                logging.info(f"File already processed (skipping): {file}")
                processed_count += 1
                continue

            if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif')):
                logging.info(f"Starting processing: {file}")
                if process_file_with_ocr(source_file_path, destination_file_path, language=language, force_ocr=force_ocr):
                    processed_files[source_file_path] = "completed"
                else:
                    processed_files[source_file_path] = "failed"
                processed_count += 1
                progress_percentage = (processed_count / total_files) * 100 if total_files > 0 else 0
                logging.info(f"Progress: {processed_count}/{total_files} ({progress_percentage:.2f}%)")

                # Save state after each processed file
                with open(state_file, 'w') as f:
                    json.dump(processed_files, f, indent=4)
            else:
                logging.info(f"File ignored (unsupported type for OCR): {file}")

    logging.info("Processing of individual files completed.")


def process_file_with_ocr(file_path, output_path, language='fra', force_ocr=False):
    """
    Process a file (PDF or image) to add OCR using ocrmypdf.
    First convert images to PDF, then process with OCR.
    """
    from PIL import Image
    import ocrmypdf
    import os

    base_name = os.path.basename(file_path)

    try:
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.tif')):
            logging.info(f"Processing image with OCR: {base_name}")
            # First convert image to temporary PDF, then process with OCR
            
            # Open and verify the image
            with Image.open(file_path) as img:
                # Convert image to PDF first
                rgb_image = img.convert('RGB') if img.mode in ('RGBA', 'LA', 'P', 'CMYK') else img
                
                # Create temporary PDF from image
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                    temp_pdf_path = temp_pdf.name
                    rgb_image.save(temp_pdf_path, "PDF", resolution=300)
            
            try:
                # Process the temporary PDF with OCR
                ocrmypdf_options = {
                    'deskew': True,  # Correct skew if needed
                    'clean': True,   # Clean image before OCR
                    'rotate_pages': True,  # Auto-rotate pages
                    'language': language,  # OCR language
                    'use_threads': True,  # Use threads for better performance
                    'jbig2': False,  # Disable jbig2 compression to avoid permission issues
                }
                
                # Add force_ocr option if requested
                if force_ocr:
                    ocrmypdf_options['force_ocr'] = True

                ocrmypdf.ocr(
                    input_file=temp_pdf_path,
                    output_file=output_path,
                    **ocrmypdf_options
                )
                
                logging.info(f"Image converted and processed with OCR: {output_path}")
                return True
            finally:
                # Clean up temporary file
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
                    
        elif file_path.lower().endswith('.pdf'):
            logging.info(f"Processing existing PDF with OCR: {base_name}")
            # Process PDF with OCR - use only PDF-appropriate options
            ocrmypdf_options = {
                'deskew': True,  # Correct skew if needed
                'clean': True,   # Clean image before OCR
                'rotate_pages': True,  # Auto-rotate pages
                'language': language,  # OCR language
                'use_threads': True,  # Use threads for better performance
                'jbig2': False,  # Disable jbig2 compression to avoid permission issues
            }
            
            # Add force_ocr option if requested
            if force_ocr:
                ocrmypdf_options['force_ocr'] = True

            ocrmypdf.ocr(
                input_file=file_path,
                output_file=output_path,
                **ocrmypdf_options
            )
            
            logging.info(f"PDF processed with OCR: {output_path}")
            return True
        else:
            logging.info(f"File type not supported for OCR: {base_name}. Ignored.")
            return False

        logging.info(f"File processed with OCR: {output_path}")
        return True

    except Exception as e:
        logging.error(f"Error during OCR processing of '{base_name}': {e}")
        # Try a simpler approach with minimal options in case of failure
        try:
            logging.info(f"Retrying with minimal options for: {base_name}")
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.tif')):
                # For images, try direct processing with ocrmypdf as fallback
                ocrmypdf.ocr(
                    input_file=file_path,
                    output_file=output_path,
                    image_dpi=200,  # Lower DPI as fallback for images
                    language=language,
                    force_ocr=force_ocr,
                    jbig2=False  # Disable jbig2 compression
                )
            else:
                # For PDFs, try without DPI parameter
                ocrmypdf.ocr(
                    input_file=file_path,
                    output_file=output_path,
                    language=language,
                    force_ocr=force_ocr,
                    jbig2=False  # Disable jbig2 compression
                )
            logging.info(f"File processed with OCR (fallback): {output_path}")
            return True
        except Exception as e2:
            logging.error(f"Fallback OCR also failed for '{base_name}': {e2}")
            return False


def merge_pdfs_with_toc(source_directory, merged_output_file):
    """
    Merges all PDFs from a directory (and its subdirectories) into a single PDF file
    and creates a table of contents (bookmarks) based on the file hierarchy.
    
    Uses PyMuPDF for PDF manipulation.
    """
    # Create a new empty PDF document
    output_doc = fitz.open()
    
    logging.info(f"Starting PDF merging and TOC creation from: {source_directory}")
    
    # Collect all PDFs and their information
    all_pdf_paths = []
    for root, _, files in os.walk(source_directory):
        for file in files:
            # Exclude the merged file itself if the script is run again in the same directory
            if file.lower().endswith('.pdf') and os.path.join(root, file) != merged_output_file:
                all_pdf_paths.append(os.path.join(root, file))
    
    # Sort paths to ensure coherent order in the merged PDF and TOC
    all_pdf_paths.sort()
    
    if not all_pdf_paths:
        logging.warning(f"No PDFs found in directory '{source_directory}' to merge.")
        return False
    
    # Collect pages by path to determine proper positions in TOC
    pdf_info = []
    current_page_count = 0
    
    for pdf_path in all_pdf_paths:
        try:
            # Open source PDF
            input_doc = fitz.open(pdf_path)
            num_pages = len(input_doc)
            
            # Add the pages of the current PDF to the output document
            output_doc.insert_pdf(input_doc)
            
            # Prepare information for the bookmark structure
            relative_path = os.path.relpath(pdf_path, source_directory)
            path_parts = relative_path.split(os.sep)
            
            pdf_info.append({
                'path_parts': path_parts,
                'page_start': current_page_count,
                'title': os.path.basename(pdf_path)
            })
            
            logging.info(
                f"Added '{relative_path}' ({num_pages} pages) to merge. Starts at page {current_page_count}.")
            current_page_count += num_pages
            
            # Close source document
            input_doc.close()
            
        except Exception as e:
            logging.error(f"Error reading or adding PDF '{pdf_path}' for merging: {e}")
            # Continue with other files even if one file has an issue
            continue
    
    # Create hierarchical table of contents
    toc_entries = []
    added_paths = set()
    
    for info in pdf_info:
        path_parts = info['path_parts']
        page_start = info['page_start'] + 1  # PyMuPDF uses 1-based page indices
        file_title = info['title']
        
        # Create hierarchical TOC entries for folders
        current_path_parts = []
        for i, part in enumerate(path_parts[:-1]):
            current_path_parts.append(part)
            current_path_key = tuple(current_path_parts)
            
            # If this folder path has not been added yet
            if current_path_key not in added_paths:
                level = i + 1
                # Find all pages belonging to this folder to determine the first page
                first_page_in_folder = min(
                    item['page_start'] + 1 for item in pdf_info 
                    if len(item['path_parts']) > i and tuple(item['path_parts'][:i+1]) == current_path_key
                )
                toc_entries.append([level, part, first_page_in_folder])
                added_paths.add(current_path_key)
        
        # Add the entry for the PDF file itself
        level = len(path_parts)
        toc_entries.append([level, file_title, page_start])
    
    # Save the merged document
    if len(output_doc) > 0:
        # Set the table of contents
        if toc_entries:
            output_doc.set_toc(toc_entries)
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(merged_output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Output directory created: {output_dir}")
        
        output_doc.save(merged_output_file)
        output_doc.close()
        logging.info(f"All PDFs merged with table of contents in: {merged_output_file}")
        return True
    else:
        logging.warning("No PDFs were merged.")
        output_doc.close()
        return False