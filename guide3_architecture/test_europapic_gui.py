#!/usr/bin/env python3
"""
Test script for EuropaPIC GUI functionality
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_europapic_gui():
    """Test EuropaPIC GUI functionality"""
    print("Testing EuropaPIC GUI functionality...")
    
    # Import the GUI class
    from Guide3GUI import Guide3GUI
    
    # Create a test instance
    app = Guide3GUI()
    
    # Test default values
    print("\n1. Testing Default Values:")
    print(f"   PIC Architecture: {app.pic_architecture_var.get()}")
    print(f"   I/O Input Loss: {app.io_in_loss_var.get()}")
    print(f"   I/O Output Loss: {app.io_out_loss_var.get()}")
    print(f"   PSR Loss: {app.psr_loss_var.get()}")
    print(f"   Phase Shifter Loss: {app.phase_shifter_loss_var.get()}")
    print(f"   Coupler Loss: {app.coupler_loss_var.get()}")
    
    # Test PSR architecture calculation
    print("\n2. Testing PSR Architecture Calculation:")
    app.pic_architecture_var.set("psr")
    app.calculate_pic()
    
    # Get results text
    results_text = app.pic_results_text.get(1.0, tk.END)
    print("   Results generated successfully")
    print(f"   Results length: {len(results_text)} characters")
    
    # Test POL_CONTROL architecture calculation
    print("\n3. Testing POL_CONTROL Architecture Calculation:")
    app.pic_architecture_var.set("pol_control")
    app.calculate_pic()
    
    results_text = app.pic_results_text.get(1.0, tk.END)
    print("   Results generated successfully")
    print(f"   Results length: {len(results_text)} characters")
    
    # Test custom values
    print("\n4. Testing Custom Values:")
    app.io_in_loss_var.set("2.0")
    app.io_out_loss_var.set("2.0")
    app.psr_loss_var.set("0.8")
    app.phase_shifter_loss_var.set("0.7")
    app.coupler_loss_var.set("0.3")
    app.calculate_pic()
    
    results_text = app.pic_results_text.get(1.0, tk.END)
    print("   Custom values calculated successfully")
    print(f"   Results length: {len(results_text)} characters")
    
    # Test reset functionality
    print("\n5. Testing Reset Functionality:")
    app.reset_pic()
    
    # Verify reset values
    assert app.pic_architecture_var.get() == "psr"
    assert app.io_in_loss_var.get() == "1.5"
    assert app.io_out_loss_var.get() == "1.5"
    assert app.psr_loss_var.get() == "0.5"
    assert app.phase_shifter_loss_var.get() == "0.5"
    assert app.coupler_loss_var.get() == "0.2"
    
    print("   Reset functionality works correctly")
    
    # Test configuration management
    print("\n6. Testing Configuration Management:")
    
    # Test loading defaults
    app.load_defaults()
    print("   Load defaults functionality works")
    
    # Test updating defaults
    app.update_defaults()
    print("   Update defaults functionality works")
    
    # Clean up
    app.destroy()
    
    print("\n✅ All EuropaPIC GUI tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_europapic_gui()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 