#!/usr/bin/env python3
"""
Test script for Guide3GUI fiber input type validation.
Tests the GUI functionality for the new fiber input type logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch, MagicMock

# Import the GUI class
from Guide3GUI import Guide3GUI

class TestGuide3GUIFiberValidation(unittest.TestCase):
    """Test cases for Guide3GUI fiber input type validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.app = Guide3GUI()
        
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'app'):
            self.app.destroy()
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_pm_fiber_architecture_auto_set(self):
        """Test that PM fiber automatically sets architecture to psrless"""
        # Set fiber type to PM
        self.app.fiber_input_type_var.set("pm")
        
        # Trigger the callback
        self.app.on_fiber_type_change(None)
        
        # Check that architecture is set to psrless
        self.assertEqual(self.app.guide3a_architecture_var.get(), "psrless")
        
        # Check that combobox is disabled and only shows psrless
        self.assertEqual(list(self.app.guide3a_architecture_combo['values']), ["psrless"])
        self.assertEqual(self.app.guide3a_architecture_combo['state'], "disabled")
    
    def test_sm_fiber_architecture_options(self):
        """Test that SM fiber allows psr and pol_control options"""
        # Set fiber type to SM
        self.app.fiber_input_type_var.set("sm")
        
        # Trigger the callback
        self.app.on_fiber_type_change(None)
        
        # Check that architecture is set to psr (default)
        self.assertEqual(self.app.guide3a_architecture_var.get(), "psr")
        
        # Check that combobox is enabled and shows both options
        self.assertEqual(list(self.app.guide3a_architecture_combo['values']), ["psr", "pol_control"])
        self.assertEqual(self.app.guide3a_architecture_combo['state'], "readonly")
    
    def test_calculate_guide3a_pm_fiber(self):
        """Test calculation with PM fiber (should auto-set to psrless)"""
        # Set up PM fiber configuration
        self.app.fiber_input_type_var.set("pm")
        self.app.num_fibers_var.set("40")
        self.app.guide3a_wavelength_var.set("1310")
        self.app.guide3a_temp_var.set("40")
        self.app.guide3a_io_in_loss_var.set("1.5")
        self.app.guide3a_io_out_loss_var.set("1.5")
        self.app.guide3a_psr_loss_var.set("0.5")
        self.app.guide3a_phase_shifter_loss_var.set("0.5")
        self.app.guide3a_coupler_loss_var.set("0.2")
        
        # Mock messagebox to avoid GUI popups during testing
        with patch('tkinter.messagebox.showerror') as mock_error:
            # Call calculate method
            self.app.calculate_guide3a()
            
            # Should not have any errors
            mock_error.assert_not_called()
            
            # Check that results are displayed
            results_text = self.app.guide3a_results_text.get(1.0, tk.END)
            self.assertIn("Guide3A Enhanced Analysis Results", results_text)
            self.assertIn("psrless", results_text.lower())
    
    def test_calculate_guide3a_sm_fiber_psr(self):
        """Test calculation with SM fiber and psr architecture"""
        # Set up SM fiber with psr configuration
        self.app.fiber_input_type_var.set("sm")
        self.app.guide3a_architecture_var.set("psr")
        self.app.num_fibers_var.set("40")
        self.app.guide3a_wavelength_var.set("1310")
        self.app.guide3a_temp_var.set("40")
        self.app.guide3a_io_in_loss_var.set("1.5")
        self.app.guide3a_io_out_loss_var.set("1.5")
        self.app.guide3a_psr_loss_var.set("0.5")
        self.app.guide3a_phase_shifter_loss_var.set("0.5")
        self.app.guide3a_coupler_loss_var.set("0.2")
        
        # Mock messagebox to avoid GUI popups during testing
        with patch('tkinter.messagebox.showerror') as mock_error:
            # Call calculate method
            self.app.calculate_guide3a()
            
            # Should not have any errors
            mock_error.assert_not_called()
            
            # Check that results are displayed
            results_text = self.app.guide3a_results_text.get(1.0, tk.END)
            self.assertIn("Guide3A Enhanced Analysis Results", results_text)
            self.assertIn("psr", results_text.lower())
    
    def test_calculate_guide3a_sm_fiber_pol_control(self):
        """Test calculation with SM fiber and pol_control architecture"""
        # Set up SM fiber with pol_control configuration
        self.app.fiber_input_type_var.set("sm")
        self.app.guide3a_architecture_var.set("pol_control")
        self.app.num_fibers_var.set("40")
        self.app.guide3a_wavelength_var.set("1310")
        self.app.guide3a_temp_var.set("40")
        self.app.guide3a_io_in_loss_var.set("1.5")
        self.app.guide3a_io_out_loss_var.set("1.5")
        self.app.guide3a_psr_loss_var.set("0.5")
        self.app.guide3a_phase_shifter_loss_var.set("0.5")
        self.app.guide3a_coupler_loss_var.set("0.2")
        
        # Mock messagebox to avoid GUI popups during testing
        with patch('tkinter.messagebox.showerror') as mock_error:
            # Call calculate method
            self.app.calculate_guide3a()
            
            # Should not have any errors
            mock_error.assert_not_called()
            
            # Check that results are displayed
            results_text = self.app.guide3a_results_text.get(1.0, tk.END)
            self.assertIn("Guide3A Enhanced Analysis Results", results_text)
            self.assertIn("pol_control", results_text.lower())
    
    def test_invalid_combination_error(self):
        """Test that invalid fiber/architecture combinations show error"""
        # Set up invalid combination: SM fiber with psrless architecture (which should be invalid)
        self.app.fiber_input_type_var.set("sm")
        self.app.guide3a_architecture_var.set("psrless")  # This should be invalid for SM
        self.app.num_fibers_var.set("40")
        self.app.guide3a_wavelength_var.set("1310")
        self.app.guide3a_temp_var.set("40")
        self.app.guide3a_io_in_loss_var.set("1.5")
        self.app.guide3a_io_out_loss_var.set("1.5")
        self.app.guide3a_psr_loss_var.set("0.5")
        self.app.guide3a_phase_shifter_loss_var.set("0.5")
        self.app.guide3a_coupler_loss_var.set("0.2")
        
        # Mock messagebox to capture error messages
        with patch('tkinter.messagebox.showerror') as mock_error:
            # Call calculate method
            self.app.calculate_guide3a()
            
            # Should show error for invalid combination
            mock_error.assert_called()
            error_message = mock_error.call_args[0][1]
            self.assertIn("For SM fiber", error_message)
    
    def test_reset_guide3a_defaults(self):
        """Test that reset sets correct defaults"""
        # Set some non-default values
        self.app.fiber_input_type_var.set("pm")
        self.app.guide3a_architecture_var.set("psrless")
        self.app.num_fibers_var.set("60")
        self.app.guide3a_wavelength_var.set("1320")
        self.app.guide3a_temp_var.set("50")
        
        # Call reset
        self.app.reset_guide3a()
        
        # Check that defaults are restored
        self.assertEqual(self.app.fiber_input_type_var.get(), "sm")
        self.assertEqual(self.app.guide3a_architecture_var.get(), "psr")
        self.assertEqual(self.app.num_fibers_var.get(), "40")
        self.assertEqual(self.app.guide3a_wavelength_var.get(), "1310")
        self.assertEqual(self.app.guide3a_temp_var.get(), "40")

def main():
    """Run the tests"""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGuide3GUIFiberValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main()) 