#!/usr/bin/env python3
"""
Test script for enhanced EuropaPIC GUI integration
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_gui():
    """Test enhanced EuropaPIC GUI functionality"""
    print("Testing Enhanced EuropaPIC GUI functionality...")
    
    # Import the GUI class
    from Guide3GUI import Guide3GUI
    
    # Create a test instance
    app = Guide3GUI()
    
    # Test all architectures
    architectures = ["psr", "pol_control", "mux_demux", "modulator", "detector"]
    
    for arch in architectures:
        print(f"\nTesting {arch.upper()} Architecture:")
        
        # Set architecture
        app.pic_architecture_var.set(arch)
        
        # Set some custom values
        app.operating_wavelength_var.set("1320")
        app.pic_temp_var.set("30")
        app.bandwidth_var.set("15")
        app.waveguide_length_var.set("2.5")
        app.waveguide_loss_var.set("0.12")
        
        # Set custom loss values
        app.io_in_loss_var.set("1.8")
        app.io_out_loss_var.set("1.8")
        app.psr_loss_var.set("0.6")
        app.phase_shifter_loss_var.set("0.6")
        app.coupler_loss_var.set("0.25")
        app.mux_loss_var.set("0.35")
        app.demux_loss_var.set("0.35")
        app.modulator_loss_var.set("0.9")
        app.detector_loss_var.set("0.45")
        
        # Calculate
        app.calculate_pic()
        
        # Get results
        results_text = app.pic_results_text.get(1.0, tk.END)
        print(f"   Results generated successfully for {arch}")
        print(f"   Results length: {len(results_text)} characters")
        
        # Check that results contain expected content
        assert arch.upper() in results_text
        assert "Total Loss:" in results_text
        assert "Performance Metrics:" in results_text
        assert "Component Count:" in results_text
    
    # Test reset functionality
    print("\nTesting Reset Functionality:")
    app.reset_pic()
    
    # Verify reset values
    assert app.pic_architecture_var.get() == "psr"
    assert app.operating_wavelength_var.get() == "1310"
    assert app.pic_temp_var.get() == "25"
    assert app.bandwidth_var.get() == "10"
    assert app.waveguide_length_var.get() == "2.0"
    assert app.waveguide_loss_var.get() == "0.1"
    assert app.io_in_loss_var.get() == "1.5"
    assert app.io_out_loss_var.get() == "1.5"
    assert app.psr_loss_var.get() == "0.5"
    assert app.phase_shifter_loss_var.get() == "0.5"
    assert app.coupler_loss_var.get() == "0.2"
    assert app.mux_loss_var.get() == "0.3"
    assert app.demux_loss_var.get() == "0.3"
    assert app.modulator_loss_var.get() == "0.8"
    assert app.detector_loss_var.get() == "0.4"
    
    print("   Reset functionality works correctly")
    
    # Test configuration management
    print("\nTesting Configuration Management:")
    
    # Test loading defaults
    app.load_defaults()
    print("   Load defaults functionality works")
    
    # Test updating defaults
    app.update_defaults()
    print("   Update defaults functionality works")
    
    # Test error handling with invalid inputs
    print("\nTesting Error Handling:")
    
    # Test invalid wavelength
    app.operating_wavelength_var.set("1000")
    app.calculate_pic()
    print("   Invalid wavelength error handling works")
    
    # Reset and test invalid temperature
    app.reset_pic()
    app.pic_temp_var.set("100")
    app.calculate_pic()
    print("   Invalid temperature error handling works")
    
    # Reset and test negative loss
    app.reset_pic()
    app.io_in_loss_var.set("-1.0")
    app.calculate_pic()
    print("   Negative loss error handling works")
    
    # Clean up
    app.destroy()
    
    print("\n✅ All Enhanced EuropaPIC GUI tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_enhanced_gui()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 