#!/usr/bin/env python3
"""
Launcher script for Guide3GUI
This script runs the Guide3GUI application.
"""

import sys
import os

# Add the parent directory to Python path so we can import from architecture_datasoa
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import and run the GUI
from architecture_datasoa.Guide3GUI import Guide3GUI

if __name__ == "__main__":
    app = Guide3GUI()
    app.mainloop() 