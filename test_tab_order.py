#!/usr/bin/env python3
"""
Test script to verify the tab order and transfer functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'guide3_architecture'))

from Guide3GUI import Guide3GUI
import tkinter as tk

def test_tab_order():
    """Test that Guide3A is the first tab and EuropaSOA is the second tab"""
    app = Guide3GUI()
    
    # Get the notebook - look more carefully through the widget hierarchy
    notebook = None
    for child in app.winfo_children():
        print(f"Child: {type(child).__name__}")
        if isinstance(child, tk.Frame):
            for grandchild in child.winfo_children():
                print(f"  Grandchild: {type(grandchild).__name__}")
                if isinstance(grandchild, tk.ttk.Notebook):
                    notebook = grandchild
                    break
                elif isinstance(grandchild, tk.Frame):
                    # Look deeper
                    for great_grandchild in grandchild.winfo_children():
                        print(f"    Great-grandchild: {type(great_grandchild).__name__}")
                        if isinstance(great_grandchild, tk.ttk.Notebook):
                            notebook = great_grandchild
                            break
                    if notebook:
                        break
            if notebook:
                break
    
    if notebook:
        # Check tab order
        tabs = [notebook.tab(i, "text") for i in range(notebook.index("end"))]
        print(f"Tab order: {tabs}")
        
        # Verify Guide3A is first and EuropaSOA is second
        if tabs[0] == "Guide3A" and tabs[1] == "EuropaSOA":
            print("✓ Tab order is correct: Guide3A first, EuropaSOA second")
        else:
            print("✗ Tab order is incorrect")
            return False
        
        # Test transfer functionality
        print("\nTesting transfer functionality...")
        
        # Set some Guide3A parameters
        app.fiber_input_type_var.set("pm")
        app.guide3a_architecture_var.set("psrless")
        app.num_fibers_var.set("40")
        app.guide3a_target_pout_var.set("-3.3")
        app.guide3a_target_pout_3sigma_var.set("-0.3")
        app.guide3a_soa_penalty_var.set("2")
        app.guide3a_soa_penalty_3sigma_var.set("2")
        app.num_wavelengths_var.set("8")
        
        # Calculate Guide3A
        app.calculate_guide3a()
        
        # Test transfer
        try:
            app.transfer_to_europasoa()
            print("✓ Transfer functionality works")
        except Exception as e:
            print(f"✗ Transfer functionality failed: {e}")
            return False
        
        # Test use_guide3a_results
        try:
            app.use_guide3a_results()
            print("✓ Use Guide3A results functionality works")
        except Exception as e:
            print(f"✗ Use Guide3A results functionality failed: {e}")
            return False
        
        print("\n✓ All tests passed!")
        return True
    else:
        print("✗ Could not find notebook")
        return False

if __name__ == "__main__":
    success = test_tab_order()
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
        sys.exit(1) 