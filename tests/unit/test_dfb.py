"""
Unit tests for DFB (Distributed Feedback Laser) model
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.DFB import DFB


class TestDFB(unittest.TestCase):
    """Test cases for DFB model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dfb = DFB()
        self.test_temperature = 35.0
        self.test_current = 186.0
        self.test_wavelength = 1550.0  # nm
    
    def test_initialization(self):
        """Test DFB initialization"""
        self.assertEqual(self.dfb.W_um, 2.0)
        self.assertEqual(self.dfb.temperature, 35.0)
        self.assertEqual(self.dfb.current, 186.0)
        self.assertEqual(self.dfb.L_active_mm, 1.1)
        self.assertEqual(self.dfb.L_active_um, 1100.0)
        self.assertEqual(self.dfb.L_tapers_um, 0.0)
        self.assertEqual(self.dfb.V_turn_on, 1.05)
    
    def test_threshold_currents(self):
        """Test threshold current values"""
        expected_thresholds = {10: 30.0, 35: 43.0, 80: 90.0}
        self.assertEqual(self.dfb.threshold_currents, expected_thresholds)
    
    def test_slope_efficiencies(self):
        """Test slope efficiency values"""
        expected_slopes = {10: 0.23, 35: 0.21, 80: 0.14}
        self.assertEqual(self.dfb.slope_efficiencies, expected_slopes)
    
    def test_series_resistance_calculation(self):
        """Test series resistance calculation"""
        resistance = self.dfb.calculate_series_resistance_ohm()
        # Expected: (4.34 / 2.0) + (2151 / 1100.0) - 0.992 = 2.17 + 1.955 - 0.992 = 3.133
        self.assertAlmostEqual(resistance, 3.133, places=3)
    
    def test_operating_voltage(self):
        """Test operating voltage calculation"""
        voltage = self.dfb.get_operating_voltage(self.test_current)
        # Expected: 1.05 + (0.186 * 3.133) = 1.05 + 0.583 = 1.633
        self.assertAlmostEqual(voltage, 1.633, places=3)
    
    def test_interpolate_parameters(self):
        """Test parameter interpolation"""
        threshold, slope, max_power = self.dfb.interpolate_parameters(35.0)
        self.assertAlmostEqual(threshold, 43.0, places=1)
        self.assertAlmostEqual(slope, 0.21, places=2)
        self.assertEqual(max_power, 200.0)
    
    def test_calculate_output_power(self):
        """Test optical output power calculation"""
        # Test below threshold
        power_below = self.dfb.calculate_output_power(35.0, 30.0)  # Below 43mA threshold
        self.assertLess(power_below, 1.0)  # Should be very small
        
        # Test above threshold
        power_above = self.dfb.calculate_output_power(35.0, 186.0)
        # Expected: 0.21 * (186 - 43) = 0.21 * 143 = 30.03
        self.assertAlmostEqual(power_above, 30.03, places=1)
    
    def test_get_performance_curve(self):
        """Test performance curve generation"""
        currents, powers = self.dfb.get_performance_curve(35.0, (0, 200, 50))
        self.assertEqual(len(currents), 5)  # 0, 50, 100, 150, 200
        self.assertEqual(len(powers), 5)
        self.assertTrue(all(p >= 0 for p in powers))  # All powers should be non-negative
    
    def test_single_side_wpe(self):
        """Test single-sided wall-plug efficiency calculation"""
        wpe = self.dfb.get_dfb_wpe_single_side(self.test_temperature, self.test_current)
        # Single-side optical: 30.03mW, Electrical: 186*1.633 = 303.7mW
        # WPE = (30.03/1000) / (303.7/1000) * 100 = 9.89%
        self.assertAlmostEqual(wpe, 9.89, places=1)
    
    def test_total_wpe(self):
        """Test total wall-plug efficiency calculation"""
        wpe = self.dfb.get_dfb_wpe(self.test_temperature, self.test_current)
        # Total optical: 60.06mW, Electrical: 303.7mW
        # WPE = (60.06/1000) / (303.7/1000) * 100 = 19.78%
        self.assertAlmostEqual(wpe, 19.78, places=1)
    
    def test_heat_load_calculation(self):
        """Test heat load calculation"""
        heat_load = self.dfb.get_dfb_heat_load(self.test_temperature, self.test_current)
        # Heat load = Electrical - Total Optical = 303.7 - 60.06 = 243.64mW
        self.assertAlmostEqual(heat_load, 243.64, places=1)
    
    def test_heat_sources(self):
        """Test heat sources breakdown"""
        heat_sources = self.dfb.get_heat_sources(self.test_temperature, self.test_current)
        self.assertIn('DFB Gain Heat Load', heat_sources)
        self.assertAlmostEqual(heat_sources['DFB Gain Heat Load'], 243.64, places=1)
    
    def test_power_consumption(self):
        """Test power consumption breakdown"""
        power_consumption = self.dfb.get_power_consumption(self.test_temperature, self.test_current)
        self.assertIn('DFB Gain', power_consumption)
        self.assertAlmostEqual(power_consumption['DFB Gain'], 303.7, places=1)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test zero current
        power_zero = self.dfb.calculate_output_power(35.0, 0.0)
        self.assertAlmostEqual(power_zero, 0.0, places=3)
        
        # Test temperature clamping
        threshold_low, _, _ = self.dfb.interpolate_parameters(5.0)  # Below 10°C
        threshold_high, _, _ = self.dfb.interpolate_parameters(90.0)  # Above 80°C
        self.assertIsInstance(threshold_low, float)
        self.assertIsInstance(threshold_high, float)
    
    def test_negative_values_protection(self):
        """Test protection against negative values"""
        # Heat load should never be negative
        heat_load = self.dfb.get_dfb_heat_load(10.0, 10.0)  # Very low current
        self.assertGreaterEqual(heat_load, 0.0)
        
        # Output power should never be negative
        power = self.dfb.calculate_output_power(80.0, 10.0)  # Below threshold
        self.assertGreaterEqual(power, 0.0)


if __name__ == '__main__':
    unittest.main() 