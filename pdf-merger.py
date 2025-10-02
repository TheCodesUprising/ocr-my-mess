import os
import logging
import sys
from pypdf import PdfWriter, PdfReader

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def merge_pdfs_with_toc(source_directory, merged_output_file):
    """
    Fusionne tous les PDF d'un dossier (et ses sous-dossiers) en un seul fichier PDF
    et crée une table des matières (bookmarks) basée sur l'arborescence des fichiers,
    en incluant les signets existants des PDF originaux.

    Args:
        source_directory (str): Le chemin du dossier contenant les PDF à fusionner.
        merged_output_file (str): Le chemin et le nom du fichier PDF de sortie fusionné.

    Returns:
        bool: True si la fusion a réussi, False sinon.
    """
    pdf_writer = PdfWriter()
    # Cette liste stockera les informations nécessaires pour construire les signets
    # Format: {'path_parts': ['dossier', 'sous-dossier', 'fichier.pdf'], 'page_start': 0, 'reader': PdfReader, 'outline': []}
    pdf_structure = []

    logging.info(f"Début de la fusion des PDF et création de la table des matières depuis : {source_directory}")

    # 1. Collecter tous les PDF et leurs informations
    all_pdf_paths = []
    for root, _, files in os.walk(source_directory):
        for file in files:
            # Exclure le fichier fusionné lui-même si le script est relancé dans le même dossier
            if file.lower().endswith('.pdf') and os.path.join(root, file) != merged_output_file:
                all_pdf_paths.append(os.path.join(root, file))

    # Trier les chemins pour assurer un ordre cohérent dans le PDF fusionné et la TOC
    all_pdf_paths.sort()

    if not all_pdf_paths:
        logging.warning(f"Aucun PDF trouvé dans le dossier '{source_directory}' pour fusionner.")
        return False

    current_page_count = 0
    for pdf_path in all_pdf_paths:
        try:
            pdf_reader = PdfReader(pdf_path)
            num_pages = len(pdf_reader.pages)

            # Ajouter les pages du PDF actuel au writer
            pdf_writer.append_pages_from_reader(pdf_reader)

            # Préparer les informations pour la structure de signets
            relative_path = os.path.relpath(pdf_path, source_directory)
            path_parts = relative_path.split(
                os.sep)  # Ex: ['dossier1', 'fichier.pdf'] ou ['dossier1', 'sous-dossier', 'fichier.pdf']

            pdf_structure.append({
                'path_parts': path_parts,
                'page_start': current_page_count,
                'reader': pdf_reader,  # Garder une référence au reader pour extraire les signets internes
            })

            logging.info(
                f"Ajouté '{relative_path}' ({num_pages} pages) à la fusion. Débute à la page {current_page_count}.")
            current_page_count += num_pages

        except Exception as e:
            logging.error(f"Erreur lors de la lecture ou l'ajout du PDF '{pdf_path}' pour la fusion: {e}")
            # Continuer avec les autres fichiers même si un fichier pose problème
            continue

            # 2. Construire la table des matières hiérarchique
    # Utilise un dictionnaire pour stocker les signets parents à chaque niveau de chemin
    # Key: Tuple du chemin partiel (ex: ('dossier1', 'sous-dossier'))
    # Value: L'objet Bookmark du parent
    current_level_bookmarks = {(): None}  # Le tuple vide représente la racine du document (pas de parent)

    for pdf_info in pdf_structure:
        path_parts = pdf_info['path_parts']
        page_start = pdf_info['page_start']
        pdf_reader = pdf_info['reader']

        # Créer les signets pour les dossiers intermédiaires (Niveau 1, ...)
        current_path_tuple = ()
        for i, part in enumerate(path_parts[:-1]):  # Parcours les parties du chemin sauf le nom du fichier
            prev_path_tuple = current_path_tuple
            current_path_tuple = current_path_tuple + (part,)  # Ex: () -> ('dossier1',) -> ('dossier1', 'sous-dossier')

            if current_path_tuple not in current_level_bookmarks:
                parent_bookmark = current_level_bookmarks[prev_path_tuple]
                # Le titre du bookmark est le nom du dossier
                new_folder_bookmark = pdf_writer.add_outline_item(
                    title=part,
                    page_number=page_start,  # Les signets de dossier pointent vers la première page de leur contenu
                    parent=parent_bookmark
                )
                current_level_bookmarks[current_path_tuple] = new_folder_bookmark
                logging.debug(f"Added folder bookmark: {current_path_tuple} at level {len(current_path_tuple)}")
            else:
                # Si le dossier existe déjà comme signet, mettez à jour sa page de début si c'est la première fois
                # qu'un fichier de ce dossier est rencontré à cette page.
                # Pour pypdf, le page_number d'un parent n'est pas utilisé directement pour la navigation.
                pass  # L'important est d'avoir l'objet bookmark en tant que parent

        # Créer le signet pour le fichier PDF lui-même (Niveau 2)
        file_name = path_parts[-1]
        parent_for_file = current_level_bookmarks[current_path_tuple]
        file_bookmark = pdf_writer.add_outline_item(
            title=file_name,
            page_number=page_start,
            parent=parent_for_file
        )
        logging.debug(f"Added file bookmark: {file_name} at level {len(path_parts)}")

        # Ajouter les signets internes du PDF original (Niveau 3)
        # S'assurer que 'outline' n'est pas None et contient des éléments
        if pdf_reader.outline:
            # Iterate through the original PDF's outline
            # The add_outline_item_from_json method is very useful here.
            # It creates the outline items using JSON-like structure.
            # We need to adjust page numbers relative to the merged document.
            for item in pdf_reader.outline:
                if isinstance(item, list):  # Child outlines
                    # The outline structure can be nested lists or dicts
                    # We need to recursively add them
                    def add_nested_outline(outline_items, parent_bookmark_obj, base_page_offset):
                        for sub_item in outline_items:
                            if isinstance(sub_item, list):
                                add_nested_outline(sub_item, parent_bookmark_obj, base_page_offset)
                            else:  # This is a dictionary representing an outline item
                                sub_title = sub_item['/Title']
                                # pypdf outline items store page as PdfObject or indirect ref
                                # We need to get the actual page index and add the offset
                                sub_page_index = pdf_reader.get_destination_page_number(sub_item)

                                new_nested_bookmark = pdf_writer.add_outline_item(
                                    title=sub_title,
                                    page_number=base_page_offset + sub_page_index,
                                    parent=parent_bookmark_obj
                                )
                                logging.debug(
                                    f"Added nested bookmark: {sub_title} (page {base_page_offset + sub_page_index})")
                                # If this nested bookmark itself has children, we'd need to handle that recursively
                                # For simplicity, this assumes a flat list of nested bookmarks directly under the file bookmark.
                                # For deeper nesting of original bookmarks, more complex recursion is needed.

                    add_nested_outline(item, file_bookmark, page_start)
                else:  # This is a dictionary representing a top-level outline item in the original PDF
                    # This handles the top-level bookmarks of the *individual* PDF
                    title = item['/Title']
                    page_index = pdf_reader.get_destination_page_number(item)

                    pdf_writer.add_outline_item(
                        title=title,
                        page_number=page_start + page_index,
                        parent=file_bookmark
                    )
                    logging.debug(f"Added original PDF bookmark: {title} (page {page_start + page_index})")

    # 3. Écrire le PDF fusionné
    if len(pdf_writer.pages) > 0:
        # Assurer que le répertoire de sortie existe
        output_dir = os.path.dirname(merged_output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Création du répertoire de sortie : {output_dir}")

        with open(merged_output_file, 'wb') as f:
            pdf_writer.write(f)
        logging.info(f"Tous les PDF ont été fusionnés avec table des matières dans : {merged_output_file}")
        return True
    else:
        logging.warning("Aucun PDF n'a été fusionné.")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error(
            "Utilisation: python pdf_merger.py <chemin_dossier_source_pdfs> <chemin_fichier_pdf_fusionne_sortie>")
        sys.exit(1)

    INPUT_PDF_DIRECTORY = sys.argv[1]
    OUTPUT_MERGED_PDF_FILE = sys.argv[2]

    logging.info(f"Dossier PDF d'entrée : {INPUT_PDF_DIRECTORY}")
    logging.info(f"Fichier PDF fusionné de sortie : {OUTPUT_MERGED_PDF_FILE}")

    merge_pdfs_with_toc(INPUT_PDF_DIRECTORY, OUTPUT_MERGED_PDF_FILE)

    logging.info("Processus de fusion PDF terminé.")