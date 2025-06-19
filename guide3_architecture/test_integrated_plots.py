#!/usr/bin/env python3
"""
Test script to verify the integrated plotting functionality in Guide3GUI
"""

import tkinter as tk
from Guide3GUI import Guide3GUI

def test_plot_options_integration():
    """Test that plot options are properly integrated in the main GUI"""
    print("Testing integrated plot options...")
    
    try:
        # Create GUI instance
        app = Guide3GUI()
        
        # Check that plot_vars exists
        assert hasattr(app, 'plot_vars'), "plot_vars should exist"
        assert len(app.plot_vars) == 7, "Should have 7 plot options"
        
        # Check that all plot options are present
        expected_plots = [
            'wpe_vs_length', 'gain_vs_length', 'pin_vs_length',
            'wpe_vs_wavelength', 'gain_vs_wavelength', 'pin_vs_wavelength',
            'saturation_vs_wavelength'
        ]
        
        for plot_name in expected_plots:
            assert plot_name in app.plot_vars, f"Plot option {plot_name} should exist"
            assert app.plot_vars[plot_name].get() == True, f"Plot option {plot_name} should be enabled by default"
        
        print("✓ Plot options are properly integrated")
        
        # Check that generate_plots method exists
        assert hasattr(app, 'generate_plots'), "generate_plots method should exist"
        
        print("✓ generate_plots method exists")
        
        app.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def test_plot_methods():
    """Test that all plotting methods exist"""
    print("Testing plotting methods...")
    
    try:
        app = Guide3GUI()
        
        # Check that all plotting methods exist
        plotting_methods = [
            '_create_plots', '_plot_wpe_vs_length', '_plot_gain_vs_length',
            '_plot_pin_vs_length', '_plot_wpe_vs_wavelength', '_plot_gain_vs_wavelength',
            '_plot_pin_vs_wavelength', '_plot_saturation_vs_wavelength'
        ]
        
        for method_name in plotting_methods:
            assert hasattr(app, method_name), f"Method {method_name} should exist"
        
        print("✓ All plotting methods exist")
        
        app.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Method test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing integrated plotting functionality...\n")
    
    tests = [
        test_plot_options_integration,
        test_plot_methods
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All integration tests passed! Plot options are properly integrated.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 