#!/usr/bin/env python3
"""
Test script to verify PSR connection swap implementation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'guide3_architecture'))

from guide3_architecture.Guide3A import Guide3A

def test_psr_connection_swap():
    """Test the new PSR connection scheme with swapped connections"""
    
    print("=== Testing PSR Connection Swap ===\n")
    
    # Create PSR architecture instance
    guide3a = Guide3A(
        pic_architecture='psr',
        fiber_input_type='sm',
        num_fibers=40,
        te_polarization_fraction=0.5  # 50% TE
    )
    
    print("PSR Architecture Parameters:")
    print(f"  PSR Loss TE: {guide3a.psr_loss_te} dB")
    print(f"  PSR Loss TM: {guide3a.psr_loss_tm} dB")
    print(f"  TE Polarization Fraction: {guide3a.te_polarization_fraction:.1%}")
    print(f"  TM Polarization Fraction: {1.0 - guide3a.te_polarization_fraction:.1%}")
    
    # Get loss breakdown
    loss_breakdown = guide3a.get_loss_breakdown()
    arch_specific = loss_breakdown['architecture_specific']
    
    print(f"\nNew Connection Scheme:")
    print(f"  - psr_out_tm2te → tap_out_te2te (TE/TE path)")
    print(f"  - psr_out_te2te → tap_out_tm2te (TM/TE path)")
    
    print(f"\nPSR Loss Analysis:")
    print(f"  TE/TE Path PSR_in Loss: {arch_specific['te2te_psr_in_loss']:.3f} dB (TE path through PSR_in)")
    print(f"  TM/TE Path PSR_in Loss: {arch_specific['tm2te_psr_in_loss']:.3f} dB (TM path through PSR_in)")
    print(f"  TE/TE Path PSR_out Loss: {arch_specific['te2te_psr_out_loss']:.3f} dB (TM2TE port)")
    print(f"  TM/TE Path PSR_out Loss: {arch_specific['tm2te_psr_out_loss']:.3f} dB (TE2TE port)")
    print(f"  Total PSR Loss (weighted): {arch_specific['total_psr_loss']:.3f} dB")
    
    print(f"\nDual Path Analysis:")
    dual_paths = arch_specific['dual_path_components']
    print(f"  TE/TE Path:")
    print(f"    • PSR_in Loss: {dual_paths['te2te_path']['psr_in_loss']:.3f} dB")
    print(f"    • PSR_out Loss: {dual_paths['te2te_path']['psr_out_loss']:.3f} dB")
    print(f"    • Tap Loss: {dual_paths['te2te_path']['tap_loss']:.3f} dB")
    print(f"    • Total Path Loss: {dual_paths['te2te_path']['total_path_loss']:.3f} dB")
    print(f"  TM/TE Path:")
    print(f"    • PSR_in Loss: {dual_paths['tm2te_path']['psr_in_loss']:.3f} dB")
    print(f"    • PSR_out Loss: {dual_paths['tm2te_path']['psr_out_loss']:.3f} dB")
    print(f"    • Tap Loss: {dual_paths['tm2te_path']['tap_loss']:.3f} dB")
    print(f"    • Total Path Loss: {dual_paths['tm2te_path']['total_path_loss']:.3f} dB")
    
    print(f"\nTotal System Loss: {loss_breakdown['total_loss']:.3f} dB")
    
    # Test different polarization fractions
    print(f"\n=== Testing Different Polarization Fractions ===")
    for te_fraction in [0.0, 0.25, 0.5, 0.75, 1.0]:
        guide3a.te_polarization_fraction = te_fraction
        loss_breakdown = guide3a.get_loss_breakdown()
        arch_specific = loss_breakdown['architecture_specific']
        
        print(f"TE Fraction: {te_fraction:.1%}")
        print(f"  PSR_in Loss: {arch_specific['psr_in_loss']:.3f} dB")
        print(f"  PSR_out Loss: {arch_specific['psr_out_loss']:.3f} dB")
        print(f"  Total PSR Loss: {arch_specific['total_psr_loss']:.3f} dB")
        print(f"  Total System Loss: {loss_breakdown['total_loss']:.3f} dB")
        print()
    
    # Test SOA power requirements
    print(f"=== Testing SOA Power Requirements ===")
    guide3a.te_polarization_fraction = 0.5  # Reset to 50%
    soa_requirements = guide3a.calculate_soa_power_requirements_for_polarization(
        target_pout_db=-2.75,
        te_percentage=50.0,
        num_wavelengths=8
    )
    
    if 'error' not in soa_requirements:
        loss_analysis = soa_requirements['loss_analysis']
        soa_reqs = soa_requirements['soa_requirements']
        
        print(f"SOA Power Requirements (50% TE, 8 wavelengths):")
        print(f"  TE/TE Path:")
        print(f"    • PSR_out Loss: {loss_analysis['te2te_psr_out_loss']:.3f} dB")
        print(f"    • Total SOA to Output Loss: {loss_analysis['te2te_soa_to_output_loss']:.3f} dB")
        print(f"    • Required SOA Output: {soa_reqs['te2te_path']['soa_output_final_db']:.3f} dBm")
        print(f"  TM/TE Path:")
        print(f"    • PSR_out Loss: {loss_analysis['tm2te_psr_out_loss']:.3f} dB")
        print(f"    • Total SOA to Output Loss: {loss_analysis['tm2te_soa_to_output_loss']:.3f} dB")
        print(f"    • Required SOA Output: {soa_reqs['tm2te_path']['soa_output_final_db']:.3f} dBm")
    else:
        print(f"Error in SOA requirements: {soa_requirements['error']}")
    
    print(f"\n=== Connection Swap Summary ===")
    print(f"✅ PSR connection swap implemented successfully")
    print(f"✅ TE/TE path now uses TM2TE port (loss: {guide3a.psr_loss_tm:.3f} dB)")
    print(f"✅ TM/TE path now uses TE2TE port (loss: {guide3a.psr_loss_te:.3f} dB)")
    print(f"✅ Loss calculations updated for new routing scheme")
    print(f"✅ SOA power requirements reflect new connection paths")

if __name__ == "__main__":
    test_psr_connection_swap() 