
import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    application_path = Path(sys._MEIPASS)
    tesseract_path = application_path
    os.environ['PATH'] = str(tesseract_path) + os.pathsep + os.environ['PATH']
    tessdata_path = application_path / 'tessdata'
    if tessdata_path.exists():
        os.environ['TESSDATA_PREFIX'] = str(tessdata_path)
