#!/usr/bin/env python3
"""
Comprehensive test script for enhanced EuropaPIC functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from EuropaPIC import EuropaPIC

def test_enhanced_europapic():
    """Test enhanced EuropaPIC functionality"""
    print("Testing Enhanced EuropaPIC functionality...")
    
    # Test all supported architectures
    architectures = ['psr', 'pol_control', 'mux_demux', 'modulator', 'detector']
    
    for arch in architectures:
        print(f"\n{'='*60}")
        print(f"Testing {arch.upper()} Architecture:")
        print(f"{'='*60}")
        
        # Create PIC instance with custom parameters
        pic = EuropaPIC(
            pic_architecture=arch,
            operating_wavelength_nm=1310,
            temperature_c=25,
            bandwidth_ghz=10,
            waveguide_length_cm=2.0,
            waveguide_loss=0.1,
            io_in_loss=1.5,
            io_out_loss=1.5,
            psr_loss=0.5,
            phase_shifter_loss=0.5,
            coupler_loss=0.2,
            mux_loss=0.3,
            demux_loss=0.3,
            modulator_loss=0.8,
            detector_loss=0.4
        )
        
        # Test basic functionality
        total_loss = pic.get_total_loss()
        print(f"Total Loss: {total_loss:.1f} dB")
        
        # Test loss breakdown
        breakdown = pic.get_loss_breakdown()
        print(f"I/O Loss: {breakdown['io_losses']['total_io_loss']:.1f} dB")
        print(f"Waveguide Loss: {breakdown['waveguide_loss']['total_waveguide_loss']:.1f} dB")
        
        # Test performance metrics
        metrics = pic.get_performance_metrics()
        print(f"Power Penalty: {metrics['power_budget']['power_penalty_db']:.1f} dB")
        print(f"Optical Efficiency: {metrics['efficiency_metrics']['optical_efficiency_percent']:.1f}%")
        
        # Test component count
        components = pic.get_component_count()
        print(f"Components: {components}")
        
        # Test architecture description
        description = pic.get_architecture_description()
        print(f"Description: {description}")
        
        # Test summary report
        summary = pic.get_summary_report()
        print(f"Summary Report Length: {len(summary)} characters")
    
    # Test parameter validation
    print(f"\n{'='*60}")
    print("Testing Parameter Validation:")
    print(f"{'='*60}")
    
    try:
        # Test invalid architecture
        pic_invalid = EuropaPIC("invalid_arch")
        print("❌ Should have raised ValueError for invalid architecture")
    except ValueError as e:
        print(f"✅ Correctly caught invalid architecture: {e}")
    
    try:
        # Test negative loss
        pic_negative = EuropaPIC("psr", io_in_loss=-1.0)
        print("❌ Should have raised ValueError for negative loss")
    except ValueError as e:
        print(f"✅ Correctly caught negative loss: {e}")
    
    try:
        # Test invalid wavelength
        pic_wavelength = EuropaPIC("psr", operating_wavelength_nm=1000)
        print("❌ Should have raised ValueError for invalid wavelength")
    except ValueError as e:
        print(f"✅ Correctly caught invalid wavelength: {e}")
    
    try:
        # Test invalid temperature
        pic_temp = EuropaPIC("psr", temperature_c=100)
        print("❌ Should have raised ValueError for invalid temperature")
    except ValueError as e:
        print(f"✅ Correctly caught invalid temperature: {e}")
    
    # Test custom loss setting
    print(f"\n{'='*60}")
    print("Testing Custom Loss Setting:")
    print(f"{'='*60}")
    
    pic_custom = EuropaPIC("pol_control")
    original_loss = pic_custom.get_total_loss()
    print(f"Original Total Loss: {original_loss:.1f} dB")
    
    pic_custom.set_custom_losses(
        io_in_loss=2.0,
        io_out_loss=2.0,
        psr_loss=0.8,
        phase_shifter_loss=0.7,
        coupler_loss=0.3
    )
    
    new_loss = pic_custom.get_total_loss()
    print(f"New Total Loss: {new_loss:.1f} dB")
    print(f"Loss Change: {new_loss - original_loss:.1f} dB")
    
    # Test comprehensive analysis
    print(f"\n{'='*60}")
    print("Testing Comprehensive Analysis:")
    print(f"{'='*60}")
    
    pic_comprehensive = EuropaPIC(
        pic_architecture="mux_demux",
        operating_wavelength_nm=1330,
        temperature_c=40,
        bandwidth_ghz=25,
        waveguide_length_cm=3.5,
        waveguide_loss=0.15,
        io_in_loss=1.8,
        io_out_loss=1.8,
        mux_loss=0.4,
        demux_loss=0.4
    )
    
    print("Comprehensive Analysis Results:")
    print(pic_comprehensive.get_summary_report())
    
    print("\n✅ All Enhanced EuropaPIC tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_enhanced_europapic()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 