"""
Command line interface for ocrmyproject.
"""
import argparse
import logging
import sys
import os
from pathlib import Path

from ocrmyproject.api import ocr_directory, merge_pdfs_with_toc


def main():
    """Main CLI entry point."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(
        description="Complete OCR and PDF merging toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  ocrmyproject ocr -i /path/to/images -o /path/to/results
  ocrmyproject merge -i /path/to/pdfs -o /path/to/output.pdf
  ocrmyproject all -i /path/to/documents -o /path/to/merged_output.pdf
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    # OCR command
    ocr_parser = subparsers.add_parser("ocr", help="Process files with OCR")
    ocr_parser.add_argument("-i", "--input", required=True, help="Input directory containing files to process")
    ocr_parser.add_argument("-o", "--output", help="Output directory for results (default: ocr_results)")
    ocr_parser.add_argument("--force-ocr", action="store_true", help="Force OCR on all pages (better results, slower processing)")
    ocr_parser.add_argument("--language", "-l", default="fra", help="OCR language (default: fra for French)")
    
    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge PDFs with table of contents")
    merge_parser.add_argument("-i", "--input", required=True, help="Input directory containing PDFs to merge")
    merge_parser.add_argument("-o", "--output", help="Output PDF file path (default: merged_output.pdf)")
    
    # Complete command (OCR + merge)
    all_parser = subparsers.add_parser("all", help="Complete processing (OCR + merge)")
    all_parser.add_argument("-i", "--input", required=True, help="Input directory containing documents to process")
    all_parser.add_argument("-o", "--output", help="Output PDF file path (default: all_processed_output.pdf)")
    all_parser.add_argument("--force-ocr", action="store_true", help="Force OCR on all pages (better results, slower processing)")
    all_parser.add_argument("--language", "-l", default="fra", help="OCR language (default: fra for French)")
    
    args = parser.parse_args()
    
    # Check if ocrmypdf is available
    try:
        import ocrmypdf
    except ImportError:
        logging.error("ocrmypdf is not installed. Please install it using: pip install ocrmypdf")
        sys.exit(1)
    
    if args.command == "ocr":
        output_dir = args.output if args.output else "ocr_results"
        logging.info(f"OCR processing - Input directory: {args.input}, Output directory: {output_dir}, Language: {args.language}")
        ocr_directory(args.input, output_dir, language=args.language, force_ocr=args.force_ocr)
        logging.info("OCR processing completed.")
        
    elif args.command == "merge":
        if args.output:
            output_file = args.output
        else:
            input_basename = os.path.basename(os.path.normpath(args.input))
            input_basename_safe = input_basename.replace(" ", "_")
            output_file = f"{input_basename_safe}_merged.pdf"
        logging.info(f"PDF merging - Input directory: {args.input}, Output file: {output_file}")
        merge_pdfs_with_toc(args.input, output_file)
        logging.info("PDF merging completed.")
        
    elif args.command == "all":
        if args.output:
            output_file = args.output
        else:
            input_basename = os.path.basename(os.path.normpath(args.input))
            input_basename_safe = input_basename.replace(" ", "_")
            output_file = f"{input_basename_safe}_merged.pdf"
        temp_ocr_dir = "temp_ocr_output"  # Temporary directory for OCR processing
        logging.info(f"Complete processing - Input directory: {args.input}, Output file: {output_file}, Language: {args.language}")
        ocr_directory(args.input, temp_ocr_dir, language=args.language, force_ocr=args.force_ocr)
        logging.info("OCR processing completed, starting merging...")
        merge_pdfs_with_toc(temp_ocr_dir, output_file)
        logging.info("Complete processing completed.")
        
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())