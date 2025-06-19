#!/usr/bin/env python3
"""
Test script to verify that PM fiber input type is the default for Guide3A.
"""

import unittest
from Guide3A import Guide3A

class TestPMDefault(unittest.TestCase):
    """Test that PM fiber input type is the default."""
    
    def test_pm_default(self):
        """Test that PM fiber input type is the default when not specified."""
        # Create Guide3A instance without specifying fiber_input_type
        guide3a = Guide3A(pic_architecture='psrless', num_fibers=40)
        
        # Verify that fiber_input_type defaults to 'pm'
        self.assertEqual(guide3a.fiber_input_type, 'pm')
        self.assertEqual(guide3a.pic_architecture, 'psrless')
    
    def test_pm_explicit(self):
        """Test that PM fiber input type works when explicitly specified."""
        guide3a = Guide3A(pic_architecture='psrless', fiber_input_type='pm', num_fibers=40)
        
        self.assertEqual(guide3a.fiber_input_type, 'pm')
        self.assertEqual(guide3a.pic_architecture, 'psrless')
    
    def test_sm_still_works(self):
        """Test that SM fiber input type still works when explicitly specified."""
        guide3a = Guide3A(pic_architecture='psr', fiber_input_type='sm', num_fibers=40)
        
        self.assertEqual(guide3a.fiber_input_type, 'sm')
        self.assertEqual(guide3a.pic_architecture, 'psr')

if __name__ == '__main__':
    unittest.main() 