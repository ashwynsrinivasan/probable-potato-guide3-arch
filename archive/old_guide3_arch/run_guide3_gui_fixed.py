#!/usr/bin/env python3
"""
Fixed launcher script for Guide3GUI with macOS compatibility
This script runs the Guide3GUI application with proper environment setup.
"""

import sys
import os

# Set environment variables for macOS Tkinter compatibility
os.environ['TK_SILENCE_DEPRECATION'] = '1'
os.environ['DISPLAY'] = ':0'

# Additional macOS-specific settings
if sys.platform == 'darwin':
    # Try to use a different Tkinter backend if available
    try:
        import tkinter
        # Force Tkinter to use a specific version
        os.environ['TK_LIBRARY'] = '/System/Library/Frameworks/Tk.framework/Versions/8.6/Resources/Scripts'
    except ImportError:
        pass

# Add the parent directory to Python path so we can import from architecture_datasoa
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

if __name__ == "__main__":
    try:
        print("Starting Guide3GUI with macOS compatibility settings...")
        
        # Import and run the GUI
        from architecture_datasoa.Guide3GUI import Guide3GUI
        
        print("Creating GUI application...")
        app = Guide3GUI()
        
        print("Starting main loop...")
        app.mainloop()
        
    except Exception as e:
        print(f"Error launching GUI: {e}")
        print("\nThis appears to be a macOS Tkinter compatibility issue.")
        print("\nPossible solutions:")
        print("1. Try running with: export TK_SILENCE_DEPRECATION=1 && python3 run_guide3_gui.py")
        print("2. Install Python 3.11: brew install python@3.11")
        print("3. Use a virtual environment with Python 3.11")
        print("4. Try the web-based alternative: python3 ../run_guide3_web.py")
        
        # Try alternative approach
        print("\nTrying alternative approach...")
        try:
            # Try to create a minimal Tkinter window first
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the window
            
            print("Basic Tkinter works, trying GUI again...")
            app = Guide3GUI()
            app.mainloop()
            
        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")
            print("\nRecommendation: Use the web-based interface instead.")
            print("Run: python3 ../run_guide3_web.py") 