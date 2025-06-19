#!/usr/bin/env python3
"""
Test script for Guide3A fiber input type validation.
Tests the new logic where PM fiber requires psrless architecture.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Guide3A import Guide3A

def test_pm_fiber_psrless_requirement():
    """Test that PM fiber automatically requires psrless architecture"""
    print("Testing PM fiber with psrless architecture...")
    
    # This should work
    try:
        guide3a = Guide3A(
            pic_architecture="psrless",
            fiber_input_type="pm",
            num_fibers=40
        )
        print("✓ PM fiber with psrless architecture: PASS")
    except Exception as e:
        print(f"✗ PM fiber with psrless architecture: FAIL - {e}")
        return False
    
    # This should fail
    try:
        guide3a = Guide3A(
            pic_architecture="psr",
            fiber_input_type="pm",
            num_fibers=40
        )
        print("✗ PM fiber with psr architecture: FAIL - Should have raised error")
        return False
    except ValueError as e:
        print(f"✓ PM fiber with psr architecture: PASS - Correctly rejected: {e}")
    except Exception as e:
        print(f"✗ PM fiber with psr architecture: FAIL - Wrong error type: {e}")
        return False
    
    return True

def test_sm_fiber_architecture_validation():
    """Test that SM fiber requires psr or pol_control architecture"""
    print("\nTesting SM fiber architecture validation...")
    
    # Test psr architecture (should work)
    try:
        guide3a = Guide3A(
            pic_architecture="psr",
            fiber_input_type="sm",
            num_fibers=40
        )
        print("✓ SM fiber with psr architecture: PASS")
    except Exception as e:
        print(f"✗ SM fiber with psr architecture: FAIL - {e}")
        return False
    
    # Test pol_control architecture (should work)
    try:
        guide3a = Guide3A(
            pic_architecture="pol_control",
            fiber_input_type="sm",
            num_fibers=40
        )
        print("✓ SM fiber with pol_control architecture: PASS")
    except Exception as e:
        print(f"✗ SM fiber with pol_control architecture: FAIL - {e}")
        return False
    
    # Test psrless architecture (should fail)
    try:
        guide3a = Guide3A(
            pic_architecture="psrless",
            fiber_input_type="sm",
            num_fibers=40
        )
        print("✗ SM fiber with psrless architecture: FAIL - Should have raised error")
        return False
    except ValueError as e:
        print(f"✓ SM fiber with psrless architecture: PASS - Correctly rejected: {e}")
    except Exception as e:
        print(f"✗ SM fiber with psrless architecture: FAIL - Wrong error type: {e}")
        return False
    
    return True

def test_effective_architecture():
    """Test that effective architecture matches the input architecture"""
    print("\nTesting effective architecture calculation...")
    
    # Test PM fiber
    guide3a_pm = Guide3A(
        pic_architecture="psrless",
        fiber_input_type="pm",
        num_fibers=40
    )
    if guide3a_pm.effective_architecture == "psrless":
        print("✓ PM fiber effective architecture: PASS")
    else:
        print(f"✗ PM fiber effective architecture: FAIL - Expected psrless, got {guide3a_pm.effective_architecture}")
        return False
    
    # Test SM fiber with psr
    guide3a_sm_psr = Guide3A(
        pic_architecture="psr",
        fiber_input_type="sm",
        num_fibers=40
    )
    if guide3a_sm_psr.effective_architecture == "psr":
        print("✓ SM fiber with psr effective architecture: PASS")
    else:
        print(f"✗ SM fiber with psr effective architecture: FAIL - Expected psr, got {guide3a_sm_psr.effective_architecture}")
        return False
    
    # Test SM fiber with pol_control
    guide3a_sm_pol = Guide3A(
        pic_architecture="pol_control",
        fiber_input_type="sm",
        num_fibers=40
    )
    if guide3a_sm_pol.effective_architecture == "pol_control":
        print("✓ SM fiber with pol_control effective architecture: PASS")
    else:
        print(f"✗ SM fiber with pol_control effective architecture: FAIL - Expected pol_control, got {guide3a_sm_pol.effective_architecture}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("Guide3A Fiber Input Type Validation Tests")
    print("=" * 50)
    
    tests = [
        test_pm_fiber_psrless_requirement,
        test_sm_fiber_architecture_validation,
        test_effective_architecture
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 