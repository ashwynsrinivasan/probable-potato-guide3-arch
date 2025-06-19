#!/usr/bin/env python3
"""
Test script for EuropaPIC functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from EuropaPIC import EuropaPIC

def test_europapic():
    """Test EuropaPIC calculations"""
    print("Testing EuropaPIC functionality...")
    
    # Test PSR architecture
    print("\n1. Testing PSR Architecture:")
    pic_psr = EuropaPIC('psr')
    total_loss_psr = pic_psr.get_total_loss()
    print(f"   PSR Architecture Total Loss: {total_loss_psr:.1f} dB")
    print(f"   Expected: {pic_psr.io_in_loss + pic_psr.io_out_loss + 2*pic_psr.psr_loss:.1f} dB")
    
    # Test POL_CONTROL architecture
    print("\n2. Testing POL_CONTROL Architecture:")
    pic_pol = EuropaPIC('pol_control')
    total_loss_pol = pic_pol.get_total_loss()
    print(f"   POL_CONTROL Architecture Total Loss: {total_loss_pol:.1f} dB")
    expected_pol = (pic_pol.io_in_loss + pic_pol.io_out_loss + 
                   2*pic_pol.psr_loss + 2*pic_pol.phase_shifter_loss + 2*pic_pol.coupler_loss)
    print(f"   Expected: {expected_pol:.1f} dB")
    
    # Test custom loss values
    print("\n3. Testing Custom Loss Values:")
    pic_custom = EuropaPIC('pol_control')
    pic_custom.io_in_loss = 2.0
    pic_custom.io_out_loss = 2.0
    pic_custom.psr_loss = 0.8
    pic_custom.phase_shifter_loss = 0.7
    pic_custom.coupler_loss = 0.3
    
    total_loss_custom = pic_custom.get_total_loss()
    print(f"   Custom POL_CONTROL Total Loss: {total_loss_custom:.1f} dB")
    expected_custom = (pic_custom.io_in_loss + pic_custom.io_out_loss + 
                      2*pic_custom.psr_loss + 2*pic_custom.phase_shifter_loss + 2*pic_custom.coupler_loss)
    print(f"   Expected: {expected_custom:.1f} dB")
    
    # Verify calculations
    assert abs(total_loss_psr - (pic_psr.io_in_loss + pic_psr.io_out_loss + 2*pic_psr.psr_loss)) < 0.1
    assert abs(total_loss_pol - expected_pol) < 0.1
    assert abs(total_loss_custom - expected_custom) < 0.1
    
    print("\n✅ All EuropaPIC tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_europapic()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1) 