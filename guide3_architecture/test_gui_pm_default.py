#!/usr/bin/env python3
"""
Test script to verify that the GUI loads with PM fiber input type as the default.
"""

import unittest
import tkinter as tk
from Guide3GUI import Guide3GUI

class TestGUIPMDefault(unittest.TestCase):
    """Test that the GUI loads with PM fiber input type as the default."""
    
    def setUp(self):
        """Set up the GUI for testing."""
        self.root = tk.Tk()
        self.app = Guide3GUI()
    
    def tearDown(self):
        """Clean up after testing."""
        self.app.destroy()
    
    def test_pm_default_in_gui(self):
        """Test that the GUI loads with PM fiber input type as the default."""
        # Check that fiber input type defaults to 'pm'
        self.assertEqual(self.app.fiber_input_type_var.get(), 'pm')
        
        # Check that PIC architecture defaults to 'psrless' (required for PM fiber)
        self.assertEqual(self.app.guide3a_architecture_var.get(), 'psrless')
        
        # Check that the combobox values are correct for PM fiber
        self.assertEqual(list(self.app.guide3a_architecture_combo['values']), ['psrless'])
        self.assertEqual(str(self.app.guide3a_architecture_combo['state']), 'disabled')
    
    def test_default_config_has_pm(self):
        """Test that the default configuration has PM fiber input type."""
        self.assertEqual(self.app.default_config['guide3a_parameters']['fiber_input_type'], 'pm')
        self.assertEqual(self.app.default_config['guide3a_parameters']['pic_architecture'], 'psrless')

if __name__ == '__main__':
    unittest.main() 