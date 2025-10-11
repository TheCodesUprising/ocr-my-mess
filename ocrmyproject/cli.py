"""
Command line interface for ocrmyproject.
"""
# Standard library imports
import argparse
import logging
import os
import sys
from pathlib import Path

# Local imports
from ocrmyproject.api import ocr_directory, merge_pdfs_with_toc


def main():
    """Main CLI entry point."""
    # Standard library imports
    import argparse
    import glob
    import logging
    import os
    import shutil
    import sys
    from pathlib import Path

    # Third-party imports
    import ocrmypdf

    # Set up colored logging
    class ColoredFormatter(logging.Formatter):
        """Custom formatter to add colors to log levels."""
        # Define color codes
        COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        RESET = '\033[0m'  # Reset to default color

        def format(self, record):
            log_color = self.COLORS.get(record.levelname, self.RESET)
            record.levelname = f"{log_color}{record.levelname}{self.RESET}"
            return super().format(record)

    # Create colored handler
    colored_handler = logging.StreamHandler(sys.stdout)
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    colored_handler.setFormatter(colored_formatter)
    
    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Clear any existing handlers
    logger.handlers = []
    logger.addHandler(colored_handler)
    
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
        
        # Check if temporary directory already exists with PDFs
        if os.path.exists(temp_ocr_dir):
            import glob
            existing_pdfs = glob.glob(os.path.join(temp_ocr_dir, "**", "*.pdf"), recursive=True)
            if existing_pdfs:
                print(f"\nWarning: {len(existing_pdfs)} PDF files already exist in the temporary OCR directory '{temp_ocr_dir}'.")
                response = input("Do you want to reuse existing OCR results? (Y/n): ").strip().lower()
                if response in ['n', 'no']:
                    import shutil
                    print(f"Removing existing temporary directory: {temp_ocr_dir}")
                    shutil.rmtree(temp_ocr_dir)
                    os.makedirs(temp_ocr_dir, exist_ok=True)
                    logging.info(f"Temporary directory '{temp_ocr_dir}' removed and recreated.")
                else:
                    logging.info(f"Reusing existing OCR results from '{temp_ocr_dir}'.")
            else:
                logging.info(f"Temporary directory '{temp_ocr_dir}' exists but is empty or contains no PDFs.")
        else:
            logging.info(f"Creating new temporary directory: {temp_ocr_dir}")
        
        # Progress callback function for CLI
        def cli_progress_callback(processed_files, total_files, processed_pages, total_pages):
            # Create progress bar
            bar_length = 50
            percent_files = (processed_files / total_files) * 100 if total_files > 0 else 0
            percent_pages = (processed_pages / total_pages) * 100 if total_pages > 0 else 0
            
            filled_files = int(bar_length * processed_files // total_files) if total_files > 0 else 0
            bar_files = '█' * filled_files + '-' * (bar_length - filled_files)
            
            sys.stdout.write(f'\rFiles: |{bar_files}| {percent_files:.2f}% ({processed_files}/{total_files}) - Pages: {processed_pages}/{total_pages} ({percent_pages:.2f}%)')
            sys.stdout.flush()
        
        logging.info(f"Complete processing - Input directory: {args.input}, Output file: {output_file}, Language: {args.language}")
        ocr_directory(args.input, temp_ocr_dir, language=args.language, force_ocr=args.force_ocr, progress_callback=cli_progress_callback)
        
        # Clear the progress bar line
        print()  # Move to next line after progress bar
        
        logging.info("OCR processing completed, starting merging...")
        merge_pdfs_with_toc(temp_ocr_dir, output_file)
        logging.info("Complete processing completed.")
        
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())