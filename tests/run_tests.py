#!/usr/bin/env python3
"""
Test Runner for SOA Models

This script runs all unit tests and integration tests for the src/models package.
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_all_tests():
    """Run all unit and integration tests"""
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    
    # Load unit tests
    unit_suite = loader.discover('unit', pattern='test_*.py')
    
    # Load integration tests
    integration_suite = loader.discover('integration', pattern='test_*.py')
    
    # Combine all test suites
    all_tests = unittest.TestSuite([unit_suite, integration_suite])
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(all_tests)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOVERALL RESULT: {'PASS' if success else 'FAIL'}")
    print("="*70)
    
    return success

def run_unit_tests_only():
    """Run only unit tests"""
    loader = unittest.TestLoader()
    suite = loader.discover('unit', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return len(result.failures) == 0 and len(result.errors) == 0

def run_integration_tests_only():
    """Run only integration tests"""
    loader = unittest.TestLoader()
    suite = loader.discover('integration', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == '__main__':
    # Change to tests directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'unit':
            print("Running unit tests only...")
            success = run_unit_tests_only()
        elif sys.argv[1] == 'integration':
            print("Running integration tests only...")
            success = run_integration_tests_only()
        else:
            print("Usage: python run_tests.py [unit|integration]")
            sys.exit(1)
    else:
        print("Running all tests...")
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 