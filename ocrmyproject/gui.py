"""
Minimal GUI for ocrmyproject using tkinter.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path

from ocrmyproject.api import ocr_directory, merge_pdfs_with_toc


class OCRMyProjectGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR My Project")
        self.root.geometry("600x500")
        
        # Variables
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar(value="ocr_results")
        self.language = tk.StringVar(value="fra")
        self.force_ocr = tk.BooleanVar()
        self.operation_type = tk.StringVar(value="ocr")
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Operation type selection
        operation_frame = ttk.LabelFrame(main_frame, text="Operation Type", padding="10")
        operation_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Radiobutton(operation_frame, text="OCR Processing", variable=self.operation_type, 
                       value="ocr").grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(operation_frame, text="PDF Merging", variable=self.operation_type, 
                       value="merge").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(operation_frame, text="Complete Processing", variable=self.operation_type, 
                       value="all").grid(row=0, column=2, sticky=tk.W)
        
        # Input directory
        ttk.Label(main_frame, text="Input Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_dir, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_input).grid(row=1, column=2, pady=5)
        
        # Output directory/file
        ttk.Label(main_frame, text="Output Directory/File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_dir, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, pady=5)
        
        # Language selection
        ttk.Label(main_frame, text="Language:").grid(row=3, column=0, sticky=tk.W, pady=5)
        lang_combo = ttk.Combobox(main_frame, textvariable=self.language, 
                                 values=["fra", "eng", "deu", "spa", "ita", "por"], 
                                 state="readonly", width=10)
        lang_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Force OCR option
        ttk.Checkbutton(main_frame, text="Force OCR (better results, slower)", 
                       variable=self.force_ocr).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=5)
        
        # Process button
        ttk.Button(main_frame, text="Process", command=self.start_processing).grid(
            row=7, column=0, columnspan=3, pady=10)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
    
    def browse_input(self):
        directory = filedialog.askdirectory()
        if directory:
            self.input_dir.set(directory)
    
    def browse_output(self):
        if self.operation_type.get() == "merge":
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", 
                                                   filetypes=[("PDF files", "*.pdf")])
            if file_path:
                self.output_dir.set(file_path)
        else:
            directory = filedialog.askdirectory()
            if directory:
                self.output_dir.set(directory)
    
    def start_processing(self):
        # Start processing in a separate thread to keep UI responsive
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
    
    def process_files(self):
        self.root.after(0, lambda: self.progress.start())
        self.root.after(0, lambda: self.status_label.config(text="Processing..."))
        
        try:
            input_path = self.input_dir.get()
            output_path = self.output_dir.get()
            lang = self.language.get()
            force = self.force_ocr.get()
            
            if not input_path or not output_path:
                raise ValueError("Input and output paths are required")
            
            if self.operation_type.get() == "ocr":
                ocr_directory(input_path, output_path, language=lang, force_ocr=force)
            elif self.operation_type.get() == "merge":
                merge_pdfs_with_toc(input_path, output_path)
            elif self.operation_type.get() == "all":
                temp_dir = "temp_ocr_output"
                ocr_directory(input_path, temp_dir, language=lang, force_ocr=force)
                merge_pdfs_with_toc(temp_dir, output_path)
            
            self.root.after(0, lambda: self.status_label.config(text="Processing completed successfully!"))
            self.root.after(0, lambda: messagebox.showinfo("Success", "Processing completed successfully!"))
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self.status_label.config(text=error_msg))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        
        finally:
            self.root.after(0, lambda: self.progress.stop())


def main():
    root = tk.Tk()
    app = OCRMyProjectGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()