# helper to find bundled files whether running as a script or a PyInstaller exe
import sys
from pathlib import Path

def resource_path(relative: str) -> Path:
    # PyInstaller unpacks files into sys._MEIPASS when running as an exe
    # when running as a normal script, just use the folder next to this file
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).parent / relative
