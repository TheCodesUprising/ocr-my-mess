sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-fra  # Tesseract et le pack de langue française
sudo apt install ghostscript                      # Traitement PostScript et PDF
sudo apt install unpaper                         # Pour le prétraitement d'images (optionnel mais recommandé par OCRmyPDF)
sudo apt install poppler-utils                   # Pour le traitement des PDF
sudo apt install ocrmypdf                         # Installe OCRmyPDF via apt (peut ne pas être la toute dernière version, voir étape suivante pour pip)

pip install ocrmypdf Pillow pypdf PyPDF2 pytesseract pdf2image
