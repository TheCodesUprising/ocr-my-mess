import os
import shutil
from PIL import Image
import json
import logging
import sys
import zipfile
import ocrmypdf
import tempfile


# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_zip_archives(source_dir):
    """
    Extrait toutes les archives ZIP trouvées dans le dossier source et ses sous-dossiers.
    Les fichiers sont extraits dans un nouveau sous-dossier portant le nom de l'archive ZIP.
    """
    zip_found = False
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith('.zip'):
                zip_path = os.path.join(root, file)
                logging.info(f"Archive ZIP trouvée : {zip_path}")

                # Récupérer le nom de l'archive ZIP sans l'extension
                zip_name = os.path.splitext(file)[0]
                # Définir le répertoire d'extraction (un nouveau sous-dossier)
                extract_to_dir = os.path.join(root, zip_name)

                try:
                    # Créer le nouveau sous-dossier pour l'extraction s'il n'existe pas
                    os.makedirs(extract_to_dir, exist_ok=True)

                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        # Extraire tout le contenu dans le nouveau sous-dossier
                        zip_ref.extractall(extract_to_dir)
                    logging.info(f"Archive '{file}' extraite avec succès dans '{extract_to_dir}'.")
                    zip_found = True
                    os.remove(zip_path)
                    logging.info(f"Archive '{file}' supprimée après extraction.")
                except zipfile.BadZipFile:
                    logging.error(f"Erreur: L'archive '{file}' est corrompue et ne peut pas être extraite.")
                except Exception as e:
                    logging.error(f"Erreur lors de l'extraction de '{file}': {e}")
    if zip_found:
        logging.info(
            "Toutes les archives ZIP ont été traitées. Relance de la numérisation pour inclure les nouveaux fichiers.")
        return True  # Indique que des ZIPs ont été trouvés et extraits
    return False  # Indique qu'aucun ZIP n'a été trouvé


def process_file_with_ocr(file_path, output_path):
    """
    Traite un fichier (PDF ou image) pour ajouter l'OCR et l'enregistre.
    Utilise OCRmyPDF pour tous les traitements OCR (PDFs et images converties en PDF temporaires).
    """
    base_name = os.path.basename(file_path)
    output_pdf_path = output_path
    temp_pdf_file = None

    try:
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            logging.info(f"Conversion de l'image en PDF temporaire pour traitement OCRmyPDF : {base_name}")
            img = Image.open(file_path)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                temp_pdf_file = tmp_file.name
                # Sauvegarde l'image en PDF, 300 DPI pour une bonne qualité OCR
                img.save(temp_pdf_file, "PDF", resolution=300.0)

            logging.info(f"PDF temporaire créé : {temp_pdf_file}")
            file_to_process = temp_pdf_file

        elif file_path.lower().endswith('.pdf'):
            logging.info(f"Traitement du PDF avec OCR (via OCRmyPDF) : {base_name}")
            file_to_process = file_path  # Le fichier est déjà un PDF

        else:
            logging.info(f"Type de fichier non supporté pour OCR : {base_name}. Ignoré.")
            return False

        # --- Appel unifié à OCRmyPDF pour les PDF (originaux ou temporaires) ---
        logging.info(f"Application de l'OCR via OCRmyPDF sur {os.path.basename(file_to_process)}")
        try:
            ocrmypdf.ocr(
                input_file=file_to_process,
                output_file=output_pdf_path,
                language='fra',
                force_ocr=True,  # Force l'OCR même si le PDF a déjà du texte
                deskew=True,  # Redresse les pages inclinées
                optimize=1,  # Optimise la taille du fichier
                # output_type='pdfa1b', # Optionnel: pour générer un PDF/A
                progress_bar=False,  # Désactive la barre de progression interne
                skip_text=False  # S'assure de traiter toutes les pages
            )
            logging.info(f"Fichier traité avec OCR (via OCRmyPDF) : {output_pdf_path}")
            return True
        except ocrmypdf.exceptions.OCRmyPDFError as e:
            logging.error(f"Erreur OCRmyPDF lors du traitement de '{base_name}': {e}")
            return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la phase OCR pour '{base_name}': {e}")
            return False

    except Exception as e:
        logging.error(f"Erreur lors de la préparation ou du traitement initial de '{base_name}': {e}")
        return False
    finally:
        # Nettoyer le fichier PDF temporaire si un a été créé
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            try:
                os.remove(temp_pdf_file)
                logging.info(f"Fichier temporaire supprimé : {temp_pdf_file}")
            except Exception as e:
                logging.warning(f"Impossible de supprimer le fichier temporaire {temp_pdf_file}: {e}")


def ocr_directory(source_dir, destination_dir):
    """
    Parcourt un répertoire source, traite les fichiers avec OCR et copie les résultats.
    Gère la reprise et l'état d'avancement.
    """
    # Vérifier si les dossiers existent
    if not os.path.isdir(source_dir):
        logging.error(f"Le dossier source '{source_dir}' n'existe pas ou n'est pas un répertoire valide.")
        sys.exit(1)

    os.makedirs(destination_dir, exist_ok=True)  # Créer le dossier de destination s'il n'existe pas

    state_file = os.path.join(destination_dir, 'ocr_progress.json')
    processed_files = {}

    # Première passe : Extraction des archives ZIP
    logging.info("Recherche et extraction des archives ZIP...")
    if extract_zip_archives(source_dir):
        # Si des ZIP ont été extraits, nous allons recharger l'état
        # pour s'assurer que les nouveaux fichiers sont pris en compte dans le décompte total
        logging.info("Archives ZIP extraites. Réinitialisation de la progression pour une numérisation complète.")
        if os.path.exists(state_file):
            os.remove(state_file)  # Supprime le fichier d'état pour forcer un nouveau scan complet
            logging.info("Fichier de progression supprimé pour un nouveau scan après extraction ZIP.")

    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                processed_files = json.load(f)
            logging.info("Reprise du traitement. Fichiers déjà traités chargés.")
        except json.JSONDecodeError:
            logging.warning("Fichier d'état corrompu. Redémarrage du traitement.")
            processed_files = {}

    total_files = 0
    # Compter tous les fichiers pertinents après l'extraction des ZIPs
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                total_files += 1

    processed_count = 0
    for root, dirs, files in os.walk(source_dir):
        # Créer l'arborescence dans le dossier de destination
        relative_path = os.path.relpath(root, source_dir)
        current_destination_dir = os.path.join(destination_dir, relative_path)
        os.makedirs(current_destination_dir, exist_ok=True)

        for file in files:
            source_file_path = os.path.join(root, file)
            # Ne pas traiter les archives ZIP elles-mêmes comme des fichiers OCR
            if file.lower().endswith('.zip'):
                logging.info(f"Fichier ZIP ignoré pour OCR (déjà extrait ou non traitable) : {file}")
                continue

            destination_file_path = os.path.join(current_destination_dir, os.path.splitext(file)[0] + '.pdf')

            if source_file_path in processed_files and processed_files[source_file_path] == "completed":
                logging.info(f"Fichier déjà traité (sauter) : {file}")
                processed_count += 1
                continue

            if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                logging.info(f"Début du traitement : {file}")
                if process_file_with_ocr(source_file_path, destination_file_path):
                    processed_files[source_file_path] = "completed"
                else:
                    processed_files[source_file_path] = "failed"
                processed_count += 1
                progress_percentage = (processed_count / total_files) * 100 if total_files > 0 else 0
                logging.info(f"Avancement : {processed_count}/{total_files} ({progress_percentage:.2f}%)")

                # Sauvegarder l'état après chaque fichier traité
                with open(state_file, 'w') as f:
                    json.dump(processed_files, f, indent=4)
            else:
                logging.info(f"Fichier ignoré (type non supporté pour OCR) : {file}")

    logging.info("Traitement terminé des fichiers individuels.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Utilisation: python ocr_all.py <chemin_dossier_source> <chemin_dossier_destination>")
        sys.exit(1)

    SOURCE_DIRECTORY = sys.argv[1]
    DESTINATION_DIRECTORY = sys.argv[2]

    logging.info(f"Dossier source : {SOURCE_DIRECTORY}")
    logging.info(f"Dossier de destination : {DESTINATION_DIRECTORY}")

    # Étape 1: Extraire les ZIP et traiter tous les fichiers individuellement
    ocr_directory(SOURCE_DIRECTORY, DESTINATION_DIRECTORY)

    # Étape 2: La fusion avec table des matières sera appelée séparément.
    logging.info("Le traitement OCR des fichiers individuels est terminé.")
    logging.info(
        f"Pour fusionner les PDF, exécutez 'python pdf_merger.py {DESTINATION_DIRECTORY} <votre_fichier_de_sortie.pdf>'.")

    logging.info("Processus de traitement OCR des fichiers terminé.")
