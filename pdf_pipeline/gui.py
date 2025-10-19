"""
Graphical User Interface for the ocr-my-mess project.

This module provides a simple GUI built with Tkinter. It allows users to:
- Select input and output directories.
- Specify OCR languages.
- Trigger the conversion and merging processes.
- View live logs and progress updates.

The core processing logic is run in a separate thread to keep the GUI responsive.
"""
import logging
import queue
import shutil
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext
from typing import Optional, List
from importlib import metadata

import ttkbootstrap as ttk
from ttkbootstrap.constants import (BOTH, DANGER, FLAT, LEFT, RIGHT, SECONDARY, SUCCESS, X, NORMAL, DISABLED, INVERSE)
from ttkbootstrap.tooltip import ToolTip

# Add project root to sys.path for absolute imports when bundled by PyInstaller
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from pdf_pipeline import convert as convert_module, merge as merge_module, utils  # noqa: E402


class QueueHandler(logging.Handler):
    """A logging handler that sends records to a queue."""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

class LanguageSelector(ttk.Frame):
    """A widget for selecting multiple OCR languages."""
    def __init__(self, parent, all_languages: List[str], european_languages: List[str], initial_lang: str = "fra"):
        super().__init__(parent)
        self.all_languages = all_languages
        self.european_languages = european_languages
        
        self.selected_languages = tk.StringVar(value=initial_lang)

        # Frame for selected languages display
        selected_frame = ttk.Frame(self)
        selected_frame.pack(fill=X, expand=True, pady=(0, 5))
        ttk.Label(selected_frame, text="Langues OCR:").pack(side=LEFT, padx=(0, 5))
        self.selected_entry = ttk.Entry(selected_frame, textvariable=self.selected_languages, state="readonly")
        self.selected_entry.pack(side=LEFT, fill=X, expand=True)

        # Frame for adding/removing languages
        add_remove_frame = ttk.Frame(self)
        add_remove_frame.pack(fill=X, expand=True)

        self.lang_to_add = tk.StringVar()
        self.lang_combobox = ttk.Combobox(add_remove_frame, textvariable=self.lang_to_add, state="readonly", width=20)
        
        # Populate combobox
        self.lang_combobox['values'] = self._get_sorted_language_list()
        self.lang_combobox.set("---" * 7 + " Langues européennes " + "---" * 7)
        
        self.lang_combobox.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        add_button = ttk.Button(add_remove_frame, text="Ajouter", command=self.add_language, width=8)
        add_button.pack(side=LEFT)
        remove_button = ttk.Button(add_remove_frame, text="Enlever", command=self.remove_language, width=8)
        remove_button.pack(side=LEFT, padx=(5, 0))

    def _get_sorted_language_list(self) -> List[str]:
        """Return a sorted list of languages with European ones first."""
        other_languages = sorted(list(set(self.all_languages) - set(self.european_languages)))
        return self.european_languages + ["-" * 20] + other_languages

    def add_language(self):
        """Add the selected language to the list."""
        lang_to_add = self.lang_to_add.get()
        if not lang_to_add or "---" in lang_to_add:
            return
        
        current_langs = self.selected_languages.get()
        langs_list = current_langs.split('+') if current_langs else []
        
        if lang_to_add not in langs_list:
            langs_list.append(lang_to_add)
            self.selected_languages.set("+".join(langs_list))

    def remove_language(self):
        """Remove the last added language from the list."""
        current_langs = self.selected_languages.get()
        langs_list = current_langs.split('+') if current_langs else []
        if langs_list:
            langs_list.pop()
            self.selected_languages.set("+".join(langs_list))

    def get(self) -> str:
        """Get the string of selected languages."""
        return self.selected_languages.get()

class App(ttk.Window):
    """The main application window for the ocr-my-mess GUI."""

    def __init__(self):
        super().__init__(themename="litera")
        try:
            version = metadata.version("ocr-my-mess")
        except metadata.PackageNotFoundError:
            version = "unknown"
        self.title(f"OCR My Mess v{version}")
        self.geometry("800x850")

        self.thread = None
        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.start_time = 0
        self.final_pdf_path: Optional[Path] = None
        self.active_button_info = None

        # --- Language data ---
        self.all_languages = utils.get_tesseract_languages()
        if not self.all_languages:
            messagebox.showwarning("Tesseract non trouvé", "Impossible de trouver les langues de Tesseract. Assurez-vous que Tesseract est installé et dans votre PATH.")
        self.european_languages = sorted([
            "fra", "eng", "deu", "spa", "ita", "por", "nld", "swe", "dan", 
            "nor", "fin", "pol", "ces", "slk", "hun", "ron"
        ])

        # --- Pipeline variables ---
        self.source_dir = tk.StringVar()
        self.dest_file = tk.StringVar()
        self.force_pdf = tk.BooleanVar()
        self.optimize_level = tk.IntVar(value=0)
        self.pipeline_lang_selector: Optional[LanguageSelector] = None

        # --- OCR only variables ---
        self.ocr_source_dir = tk.StringVar()
        self.ocr_dest_dir = tk.StringVar()
        self.ocr_force_pdf = tk.BooleanVar()
        self.ocr_optimize_level = tk.IntVar(value=0)
        self.ocr_lang_selector: Optional[LanguageSelector] = None

        # --- Merge only variables ---
        self.merge_source_dir = tk.StringVar()
        self.merge_dest_file = tk.StringVar()

        utils.setup_logging("INFO")
        self.logger = logging.getLogger()
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        self.logger.addHandler(QueueHandler(self.log_queue))

        self.create_widgets()
        self.after(100, self.process_queues)

    def create_widgets(self):
        """Create and layout all the widgets in the main window."""
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, pady=5)

        pipeline_tab = ttk.Frame(notebook, padding="10")
        ocr_tab = ttk.Frame(notebook, padding="10")
        merge_tab = ttk.Frame(notebook, padding="10")

        notebook.add(pipeline_tab, text="Pipeline Complet")
        notebook.add(ocr_tab, text="OCR Seulement")
        notebook.add(merge_tab, text="Fusion des fichiers")

        self.create_pipeline_tab(pipeline_tab)
        self.create_ocr_tab(ocr_tab)
        self.create_merge_tab(merge_tab)

        progress_frame = ttk.LabelFrame(main_frame, text="Progression", padding="10")
        progress_frame.pack(fill=X, pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, mode='determinate'
        )
        self.progress_bar.pack(fill=X, expand=True, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="En attente...")
        self.progress_label.pack(fill=X, expand=True)

        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")
        log_frame.pack(fill=BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, state="disabled", height=10, relief=FLAT)
        self.log_text.pack(fill=BOTH, expand=True)
        self.log_text.tag_config("INFO", foreground="#00006b")
        self.log_text.tag_config("WARNING", foreground="#b8860b")
        self.log_text.tag_config("ERROR", foreground="#ff0000")
        self.log_text.tag_config("DEBUG", foreground="#808080")

    def create_pipeline_tab(self, parent_frame):
        """Create the widgets for the 'Full Pipeline' tab."""
        ttk.Label(parent_frame, text="Exécute le pipeline complet : OCR sur les fichiers d'un dossier source, puis fusionne les résultats dans un seul PDF.", wraplength=700).pack(fill=X, pady=(0, 10))
        
        files_frame = ttk.LabelFrame(parent_frame, text="Fichiers", padding="10")
        files_frame.pack(fill=X, pady=5)

        source_frame = ttk.Frame(files_frame)
        source_frame.pack(fill=X, expand=True, pady=(0, 5))
        ttk.Label(source_frame, text="Dossier Source:").pack(side=LEFT)
        ttk.Entry(source_frame, textvariable=self.source_dir).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(source_frame, text="Parcourir...", command=self.browse_source_directory).pack(side=LEFT)

        dest_frame = ttk.Frame(files_frame)
        dest_frame.pack(fill=X, expand=True)
        ttk.Label(dest_frame, text="PDF Destination:").pack(side=LEFT)
        ttk.Entry(dest_frame, textvariable=self.dest_file).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(dest_frame, text="Parcourir...", command=self.browse_destination_file).pack(side=LEFT)

        options_frame = ttk.LabelFrame(parent_frame, text="Options", padding="10")
        options_frame.pack(fill=X, pady=10)

        self.pipeline_lang_selector = LanguageSelector(options_frame, self.all_languages, self.european_languages)
        self.pipeline_lang_selector.pack(fill=X, expand=True, pady=5)

        optim_frame = ttk.Frame(options_frame)
        optim_frame.pack(fill=X, expand=True, pady=5)
        
        optimize_label = ttk.Label(optim_frame, text="Optimisation du PDF:")
        optimize_label.pack(side=LEFT, padx=(0, 5))
        ToolTip(optimize_label, text="Réduit la taille du PDF final, mais augmente le temps de traitement.\n0 = pas d'optimisation, 3 = meilleure optimisation.", bootstyle=(SUCCESS, INVERSE))

        ttk.Combobox(
            optim_frame,
            textvariable=self.optimize_level,
            values=[0, 1, 2, 3],
            width=5,
            state="readonly",
        ).pack(side=LEFT, padx=5)

        force_ocr_check = ttk.Checkbutton(
            optim_frame, text="Forcer l'OCR sur tous les PDFs", variable=self.force_pdf, bootstyle="round-toggle"
        )
        force_ocr_check.pack(side=RIGHT, padx=10)
        ToolTip(force_ocr_check, text="Ré-applique l'OCR sur les pages ayant déjà du texte. Utile si un document mélange des images et du texte existant.", bootstyle=(SUCCESS, INVERSE))

        action_frame = ttk.LabelFrame(parent_frame, text="Actions", padding="10")
        action_frame.pack(fill=X, pady=10)

        self.run_button = ttk.Button(
            action_frame, text="Lancer le Pipeline Complet", command=self.start_full_pipeline, bootstyle=SUCCESS
        )
        self.run_button.pack(side=LEFT, fill=X, expand=True, ipady=10, padx=(0, 5))

        self.open_pdf_button = ttk.Button(
            action_frame, text="Ouvrir le PDF", command=self.open_final_pdf, bootstyle=SECONDARY, state=DISABLED
        )
        self.open_pdf_button.pack(side=LEFT, ipady=10, padx=(5, 0))

    def create_ocr_tab(self, parent_frame):
        """Create the widgets for the 'OCR Only' tab."""
        ttk.Label(parent_frame, text="Applique l'OCR sur tous les fichiers d'un dossier source et enregistre les PDFs résultants dans un dossier de destination.", wraplength=700).pack(fill=X, pady=(0, 10))

        files_frame = ttk.LabelFrame(parent_frame, text="Fichiers", padding="10")
        files_frame.pack(fill=X, pady=5)

        source_frame = ttk.Frame(files_frame)
        source_frame.pack(fill=X, expand=True, pady=(0, 5))
        ttk.Label(source_frame, text="Dossier Source:").pack(side=LEFT)
        ttk.Entry(source_frame, textvariable=self.ocr_source_dir).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(source_frame, text="Parcourir...", command=lambda: self.browse_directory(self.ocr_source_dir)).pack(side=LEFT)

        dest_frame = ttk.Frame(files_frame)
        dest_frame.pack(fill=X, expand=True)
        ttk.Label(dest_frame, text="Dossier Destination:").pack(side=LEFT)
        ttk.Entry(dest_frame, textvariable=self.ocr_dest_dir).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(dest_frame, text="Parcourir...", command=lambda: self.browse_directory(self.ocr_dest_dir)).pack(side=LEFT)

        options_frame = ttk.LabelFrame(parent_frame, text="Options", padding="10")
        options_frame.pack(fill=X, pady=10)

        self.ocr_lang_selector = LanguageSelector(options_frame, self.all_languages, self.european_languages)
        self.ocr_lang_selector.pack(fill=X, expand=True, pady=5)

        optim_frame = ttk.Frame(options_frame)
        optim_frame.pack(fill=X, expand=True, pady=5)

        optimize_label = ttk.Label(optim_frame, text="Optimisation du PDF:")
        optimize_label.pack(side=LEFT, padx=(0, 5))
        ToolTip(optimize_label, text="Réduit la taille du PDF final, mais augmente le temps de traitement.\n0 = pas d'optimisation, 3 = meilleure optimisation.", bootstyle=(SUCCESS, INVERSE))

        ttk.Combobox(
            optim_frame,
            textvariable=self.ocr_optimize_level,
            values=[0, 1, 2, 3],
            width=5,
            state="readonly",
        ).pack(side=LEFT, padx=5)

        force_ocr_check = ttk.Checkbutton(
            optim_frame, text="Forcer l'OCR sur tous les PDFs", variable=self.ocr_force_pdf, bootstyle="round-toggle"
        )
        force_ocr_check.pack(side=RIGHT, padx=10)
        ToolTip(force_ocr_check, text="Ré-applique l'OCR sur les pages ayant déjà du texte. Utile si un document mélange des images et du texte existant.", bootstyle=(SUCCESS, INVERSE))

        action_frame = ttk.LabelFrame(parent_frame, text="Actions", padding="10")
        action_frame.pack(fill=X, pady=10)

        self.run_ocr_button = ttk.Button(
            action_frame, text="Lancer l'OCR", command=self.start_ocr_only, bootstyle=SUCCESS
        )
        self.run_ocr_button.pack(fill=X, expand=True, ipady=10)

    def create_merge_tab(self, parent_frame):
        """Create the widgets for the 'Merge Files' tab."""
        ttk.Label(parent_frame, text="Fusionne tous les fichiers PDF d'un dossier source en un seul fichier PDF de destination.", wraplength=700).pack(fill=X, pady=(0, 10))

        files_frame = ttk.LabelFrame(parent_frame, text="Fichiers", padding="10")
        files_frame.pack(fill=X, pady=5)

        source_frame = ttk.Frame(files_frame)
        source_frame.pack(fill=X, expand=True, pady=(0, 5))
        ttk.Label(source_frame, text="Dossier Source:").pack(side=LEFT)
        ttk.Entry(source_frame, textvariable=self.merge_source_dir).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(source_frame, text="Parcourir...", command=lambda: self.browse_directory(self.merge_source_dir)).pack(side=LEFT)

        dest_frame = ttk.Frame(files_frame)
        dest_frame.pack(fill=X, expand=True)
        ttk.Label(dest_frame, text="PDF Destination:").pack(side=LEFT)
        ttk.Entry(dest_frame, textvariable=self.merge_dest_file).pack(side=LEFT, fill=X, expand=True, padx=5)
        ttk.Button(dest_frame, text="Parcourir...", command=lambda: self.browse_save_as(self.merge_dest_file)).pack(side=LEFT)

        action_frame = ttk.LabelFrame(parent_frame, text="Actions", padding="10")
        action_frame.pack(fill=X, pady=10)

        self.run_merge_button = ttk.Button(
            action_frame, text="Lancer la Fusion", command=self.start_merge_only, bootstyle=SUCCESS
        )
        self.run_merge_button.pack(fill=X, expand=True, ipady=10)

    def browse_directory(self, string_var):
        path = filedialog.askdirectory(title="Sélectionnez un dossier")
        if path:
            string_var.set(path)

    def browse_save_as(self, string_var):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf")],
            title="Enregistrer le fichier sous...",
        )
        if path:
            string_var.set(path)

    def browse_source_directory(self):
        self.browse_directory(self.source_dir)

    def browse_destination_file(self):
        self.browse_save_as(self.dest_file)

    def process_queues(self):
        self.process_log_queue()
        self.process_progress_queue()
        self.after(100, self.process_queues)

    def process_log_queue(self):
        try:
            while True:
                record = self.log_queue.get_nowait()
                msg = record.getMessage()
                self.log_text.configure(state=NORMAL)
                self.log_text.insert(tk.END, msg + "\n", record.levelname)
                self.log_text.configure(state=DISABLED)
                self.log_text.yview(tk.END)
        except queue.Empty:
            pass

    def process_progress_queue(self):
        try:
            while True:
                current, total = self.progress_queue.get_nowait()
                if total > 0:
                    percentage = (current / total) * 100
                    self.progress_var.set(percentage)

                    elapsed_time = time.time() - self.start_time
                    if current > 0:
                        time_per_item = elapsed_time / current
                        remaining_items = total - current
                        eta = remaining_items * time_per_item
                        
                        eta_seconds = int(eta)
                        hours, remainder = divmod(eta_seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        if hours > 0:
                            eta_str = f"{hours}h {minutes}m {seconds}s"
                        elif minutes > 0:
                            eta_str = f"{minutes}m {seconds}s"
                        else:
                            eta_str = f"{seconds}s"
                        label_text = f"Fichier {current}/{total} | Temps restant estimé: {eta_str}"
                    else:
                        label_text = f"Fichier {current}/{total}"
                    self.progress_label.config(text=label_text)
        except queue.Empty:
            pass

    def start_full_pipeline(self):
        input_dir = self.source_dir.get()
        output_file = self.dest_file.get()

        if not input_dir or not output_file:
            messagebox.showwarning("Champs manquants", "Veuillez sélectionner un dossier source et un fichier de destination.")
            return

        cache_dir = Path(".ocr-my-mess-cache")
        if cache_dir.exists():
            reuse_cache = messagebox.askyesno(
                "Cache existant trouvé",
                f"Le dossier cache '{cache_dir}' existe déjà.\nVoulez-vous le réutiliser pour continuer le traitement ?"
            )
            if not reuse_cache:
                self.logger.info(f"Suppression du cache existant: {cache_dir}")
                try:
                    shutil.rmtree(cache_dir)
                except OSError as e:
                    self.logger.error(f"Erreur lors de la suppression du cache: {e}")
                    messagebox.showerror("Erreur de cache", f"Impossible de supprimer le dossier cache: {e}")
                    return

        self.final_pdf_path = Path(output_file)
        self.start_task(
            self._full_pipeline_worker,
            self.run_button,
            "Lancer le Pipeline Complet",
            self.start_full_pipeline,
            Path(input_dir),
            self.final_pdf_path,
        )

    def start_ocr_only(self):
        input_dir = self.ocr_source_dir.get()
        output_dir = self.ocr_dest_dir.get()

        if not input_dir or not output_dir:
            messagebox.showwarning("Champs manquants", "Veuillez sélectionner un dossier source et un dossier de destination.")
            return

        self.final_pdf_path = None
        self.start_task(
            self._ocr_only_worker,
            self.run_ocr_button,
            "Lancer l'OCR",
            self.start_ocr_only,
            Path(input_dir),
            Path(output_dir),
        )

    def start_merge_only(self):
        input_dir = self.merge_source_dir.get()
        output_file = self.merge_dest_file.get()

        if not input_dir or not output_file:
            messagebox.showwarning("Champs manquants", "Veuillez sélectionner un dossier source et un fichier de destination.")
            return
        
        self.final_pdf_path = Path(output_file)
        self.start_task(
            self._merge_only_worker,
            self.run_merge_button,
            "Lancer la Fusion",
            self.start_merge_only,
            Path(input_dir),
            self.final_pdf_path,
        )

    def open_final_pdf(self):
        if self.final_pdf_path and self.final_pdf_path.exists():
            webbrowser.open(self.final_pdf_path.as_uri())
        else:
            messagebox.showwarning("Fichier non trouvé", "Le fichier PDF final n'a pas été trouvé ou n'a pas encore été créé.")

    def _progress_callback(self, current, total):
        self.progress_queue.put((current, total))

    def stop_task(self):
        if self.thread and self.thread.is_alive():
            self.logger.info("Arrêt du traitement demandé par l'utilisateur...")
            self.stop_event.set()

    def start_task(self, target, button, original_text, original_command, *args):
        if self.thread and self.thread.is_alive():
            messagebox.showwarning("Occupé", "Une tâche est déjà en cours.")
            return

        self.stop_event.clear()
        self.active_button_info = {
            "button": button,
            "text": original_text,
            "command": original_command,
        }
        
        self.run_button.config(state=DISABLED)
        self.run_ocr_button.config(state=DISABLED)
        self.run_merge_button.config(state=DISABLED)
        
        button.config(text="Arrêter le traitement", command=self.stop_task, bootstyle=DANGER, state=NORMAL)
        
        if self.open_pdf_button:
            self.open_pdf_button.config(state=DISABLED, bootstyle=SECONDARY)
        self.progress_var.set(0)
        self.progress_label.config(text="Démarrage...")
        self.start_time = time.time()

        self.thread = threading.Thread(target=target, args=args, daemon=True)
        self.thread.start()
        self.after(100, self.check_thread)

    def _full_pipeline_worker(self, input_dir, output_file):
        try:
            cache_dir = Path(".ocr-my-mess-cache")
            cache_dir.mkdir(exist_ok=True)
            self.logger.info(f"Utilisation du dossier cache: {cache_dir}")

            force_ocr = self.force_pdf.get()
            skip_text = not force_ocr

            convert_module.process_folder(
                input_dir=input_dir,
                output_dir=cache_dir,
                lang=self.pipeline_lang_selector.get(),
                force_ocr=force_ocr,
                skip_text=skip_text,
                optimize=self.optimize_level.get(),
                progress_callback=self._progress_callback,
                stop_event=self.stop_event,
            )

            if self.stop_event.is_set():
                self.logger.warning("Le traitement a été arrêté.")
                return

            self.logger.info("Fusion des PDFs...")
            merge_module.merge_pdfs(input_dir=cache_dir, output_file=output_file)

            self.logger.info(f"Pipeline terminé ! Fichier final: {output_file}")
        except Exception as e:
            self.logger.error(f"Erreur durant le pipeline: {e}", exc_info=True)

    def _ocr_only_worker(self, input_dir, output_dir):
        try:
            output_dir.mkdir(exist_ok=True)
            self.logger.info(f"Dossier de destination: {output_dir}")

            force_ocr = self.ocr_force_pdf.get()
            skip_text = not force_ocr

            convert_module.process_folder(
                input_dir=input_dir,
                output_dir=output_dir,
                lang=self.ocr_lang_selector.get(),
                force_ocr=force_ocr,
                skip_text=skip_text,
                optimize=self.ocr_optimize_level.get(),
                progress_callback=self._progress_callback,
                stop_event=self.stop_event,
            )

            if self.stop_event.is_set():
                self.logger.warning("Le traitement a été arrêté.")
            else:
                self.logger.info("Traitement OCR terminé !")
        except Exception as e:
            self.logger.error(f"Erreur durant l'OCR: {e}", exc_info=True)

    def _merge_only_worker(self, input_dir, output_file):
        try:
            self.logger.info("Fusion des PDFs...")
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            merge_module.merge_pdfs(input_dir=input_dir, output_file=output_file)
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')

            if self.stop_event.is_set():
                self.logger.warning("La fusion a été arrêtée.")
            else:
                self.logger.info(f"Fusion terminée ! Fichier final: {output_file}")
        except Exception as e:
            self.logger.error(f"Erreur durant la fusion: {e}", exc_info=True)

    def check_thread(self):
        if self.thread and self.thread.is_alive():
            self.after(100, self.check_thread)
        else:
            if self.active_button_info:
                button = self.active_button_info["button"]
                button.config(
                    text=self.active_button_info["text"],
                    command=self.active_button_info["command"],
                    bootstyle=SUCCESS
                )
            
            self.run_button.config(state=NORMAL)
            self.run_ocr_button.config(state=NORMAL)
            self.run_merge_button.config(state=NORMAL)

            if self.thread:
                if self.stop_event.is_set():
                    self.progress_label.config(text="Tâche annulée.")
                else:
                    self.progress_var.set(100)
                    self.progress_label.config(text="Tâche terminée !")
                    if self.final_pdf_path and self.open_pdf_button:
                        self.open_pdf_button.config(state=NORMAL, bootstyle=SUCCESS)
                    messagebox.showinfo("Terminé", "La tâche est terminée !")
            self.thread = None
            self.active_button_info = None

def main():
    """The main entry point for the GUI application."""
    # Set DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError):
        pass
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()