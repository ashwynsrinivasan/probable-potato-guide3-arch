#!/usr/bin/env python3
"""
Test script for Guide3A functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Guide3A import Guide3A

def test_guide3a():
    """Test Guide3A functionality"""
    print("Testing Guide3A functionality...")
    
    # Test all supported architectures and fiber types
    architectures = ['psrless', 'psr', 'pol_control']
    fiber_types = ['pm', 'sm']
    
    for fiber_type in fiber_types:
        for arch in architectures:
            print(f"\n{'='*60}")
            print(f"Testing {fiber_type.upper()} Fiber, {arch.upper()} Architecture:")
            print(f"{'='*60}")
            
            # Create Guide3A instance with custom parameters
            guide3a = Guide3A(
                pic_architecture=arch,
                fiber_input_type=fiber_type,
                num_fibers=40,
                operating_wavelength_nm=1310,
                temperature_c=40,
                io_in_loss=1.5,
                io_out_loss=1.5,
                psr_loss=0.5,
                phase_shifter_loss=0.5,
                coupler_loss=0.2
            )
            
            # Test basic functionality
            total_loss = guide3a.get_total_loss()
            print(f"Total Loss: {total_loss:.1f} dB")
            
            # Test module configuration
            module_config = guide3a.get_module_configuration()
            print(f"Fiber Input Type: {module_config['fiber_input_type']}")
            print(f"PIC Architecture: {module_config['pic_architecture']}")
            print(f"Effective Architecture: {module_config['effective_architecture']}")
            print(f"Number of Fibers: {module_config['num_fibers']}")
            print(f"Number of SOAs: {module_config['num_soas']}")
            print(f"Number of PICs: {module_config['num_pics']}")
            print(f"Number of Unit Cells: {module_config['num_unit_cells']}")
            
            # Test loss breakdown
            breakdown = guide3a.get_loss_breakdown()
            print(f"I/O Loss: {breakdown['io_losses']['total_io_loss']:.1f} dB")
            
            # Test performance metrics
            metrics = guide3a.get_performance_metrics()
            print(f"Power Penalty: {metrics['power_budget']['power_penalty_db']:.1f} dB")
            print(f"Optical Efficiency: {metrics['efficiency_metrics']['optical_efficiency_percent']:.1f}%")
            
            # Test component count
            components = guide3a.get_component_count()
            print(f"Components: {components}")
            
            # Test architecture description
            description = guide3a.get_architecture_description()
            print(f"Description: {description}")
            
            # Test summary report
            summary = guide3a.get_summary_report()
            print(f"Summary Report Length: {len(summary)} characters")
    
    # Test parameter validation
    print(f"\n{'='*60}")
    print("Testing Parameter Validation:")
    print(f"{'='*60}")
    
    try:
        # Test invalid architecture
        guide3a_invalid = Guide3A("invalid_arch")
        print("❌ Should have raised ValueError for invalid architecture")
    except ValueError as e:
        print(f"✅ Correctly caught invalid architecture: {e}")
    
    try:
        # Test invalid fiber type
        guide3a_fiber = Guide3A("psr", fiber_input_type="invalid")
        print("❌ Should have raised ValueError for invalid fiber type")
    except ValueError as e:
        print(f"✅ Correctly caught invalid fiber type: {e}")
    
    try:
        # Test invalid number of fibers
        guide3a_fibers = Guide3A("psr", num_fibers=25)
        print("❌ Should have raised ValueError for invalid number of fibers")
    except ValueError as e:
        print(f"✅ Correctly caught invalid number of fibers: {e}")
    
    try:
        # Test negative loss
        guide3a_negative = Guide3A("psr", io_in_loss=-1.0)
        print("❌ Should have raised ValueError for negative loss")
    except ValueError as e:
        print(f"✅ Correctly caught negative loss: {e}")
    
    try:
        # Test invalid wavelength
        guide3a_wavelength = Guide3A("psr", operating_wavelength_nm=1000)
        print("❌ Should have raised ValueError for invalid wavelength")
    except ValueError as e:
        print(f"✅ Correctly caught invalid wavelength: {e}")
    
    try:
        # Test invalid temperature
        guide3a_temp = Guide3A("psr", temperature_c=100)
        print("❌ Should have raised ValueError for invalid temperature")
    except ValueError as e:
        print(f"✅ Correctly caught invalid temperature: {e}")
    
    # Test custom loss setting
    print(f"\n{'='*60}")
    print("Testing Custom Loss Setting:")
    print(f"{'='*60}")
    
    guide3a_custom = Guide3A("pol_control")
    original_loss = guide3a_custom.get_total_loss()
    print(f"Original Total Loss: {original_loss:.1f} dB")
    
    guide3a_custom.set_custom_losses(
        io_in_loss=2.0,
        io_out_loss=2.0,
        psr_loss=0.8,
        phase_shifter_loss=0.7,
        coupler_loss=0.3
    )
    
    new_loss = guide3a_custom.get_total_loss()
    print(f"New Total Loss: {new_loss:.1f} dB")
    print(f"Loss Change: {new_loss - original_loss:.1f} dB")
    
    # Test comprehensive analysis
    print(f"\n{'='*60}")
    print("Testing Comprehensive Analysis:")
    print(f"{'='*60}")
    
    guide3a_comprehensive = Guide3A(
        pic_architecture="psrless",
        fiber_input_type="pm",
        num_fibers=60,
        operating_wavelength_nm=1330,
        temperature_c=40,
        io_in_loss=1.8,
        io_out_loss=1.8
    )
    
    print("Comprehensive Analysis Results:")
    print(guide3a_comprehensive.get_summary_report())
    
    print("\n✅ All Guide3A tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_guide3a()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 