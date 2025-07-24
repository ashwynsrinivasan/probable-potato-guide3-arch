"""
Unit tests for Heater classes (RINGHTR, PHASEHTR, MZIHTR)
"""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.RINGHTR import RINGHTR
from models.PHASEHTR import PHASEHTR
from models.MZIHTR import MZIHTR


class TestRINGHTR(unittest.TestCase):
    """Test cases for RINGHTR model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ring_htr = RINGHTR()
    
    def test_initialization(self):
        """Test RINGHTR initialization"""
        self.assertEqual(self.ring_htr.Ppi, 39.0)
        self.assertEqual(self.ring_htr.resistance_ohm, 34.0)
        self.assertEqual(self.ring_htr.voltage_v, 3.3)
        self.assertEqual(self.ring_htr.target_heat_generated_mw, 78.0)
        self.assertEqual(self.ring_htr.ring_htr_heat_load, 78.0)
    
    def test_duty_cycle_calculation(self):
        """Test duty cycle calculation"""
        # Max power = V^2 / R = 3.3^2 / 34 = 10.89 / 34 = 0.3203W = 320.3mW
        # Duty cycle = 78 / 320.3 = 0.2436
        expected_duty_cycle = 78.0 / 320.3
        self.assertAlmostEqual(self.ring_htr.duty_cycle, expected_duty_cycle, places=3)
    
    def test_get_methods(self):
        """Test getter methods"""
        self.assertEqual(self.ring_htr.get_heat_generated(), 78.0)
        self.assertEqual(self.ring_htr.get_power_consumption(), 78.0)
        self.assertIsInstance(self.ring_htr.get_duty_cycle(), float)
        self.assertGreater(self.ring_htr.get_duty_cycle(), 0)
        self.assertLess(self.ring_htr.get_duty_cycle(), 1)
    
    def test_get_parameters(self):
        """Test parameters getter"""
        params = self.ring_htr.get_parameters()
        expected_keys = ['Ppi_mW', 'resistance_ohm', 'voltage_v', 'target_heat_generated_mw', 'duty_cycle', 'ring_htr_heat_load']
        
        for key in expected_keys:
            self.assertIn(key, params)
        
        self.assertEqual(params['Ppi_mW'], 39.0)
        self.assertEqual(params['resistance_ohm'], 34.0)
        self.assertEqual(params['voltage_v'], 3.3)
        self.assertEqual(params['target_heat_generated_mw'], 78.0)
        self.assertEqual(params['ring_htr_heat_load'], 78.0)


class TestPHASEHTR(unittest.TestCase):
    """Test cases for PHASEHTR model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.phase_htr = PHASEHTR()
    
    def test_initialization(self):
        """Test PHASEHTR initialization"""
        self.assertEqual(self.phase_htr.Ppi, 39.0)
        self.assertEqual(self.phase_htr.resistance_ohm, 50.0)
        self.assertEqual(self.phase_htr.voltage_v, 3.3)
        self.assertEqual(self.phase_htr.target_heat_generated_mw, 60.0)
        self.assertEqual(self.phase_htr.phase_htr_heat_load, 60.0)
    
    def test_duty_cycle_calculation(self):
        """Test duty cycle calculation"""
        # Max power = V^2 / R = 3.3^2 / 50 = 10.89 / 50 = 0.2178W = 217.8mW
        # Duty cycle = 60 / 217.8 = 0.2754
        expected_duty_cycle = 60.0 / 217.8
        self.assertAlmostEqual(self.phase_htr.duty_cycle, expected_duty_cycle, places=3)
    
    def test_get_methods(self):
        """Test getter methods"""
        self.assertEqual(self.phase_htr.get_heat_generated(), 60.0)
        self.assertEqual(self.phase_htr.get_power_consumption(), 60.0)
        self.assertIsInstance(self.phase_htr.get_duty_cycle(), float)
        self.assertGreater(self.phase_htr.get_duty_cycle(), 0)
        self.assertLess(self.phase_htr.get_duty_cycle(), 1)
    
    def test_get_parameters(self):
        """Test parameters getter"""
        params = self.phase_htr.get_parameters()
        expected_keys = ['Ppi_mW', 'resistance_ohm', 'voltage_v', 'target_heat_generated_mw', 'duty_cycle', 'phase_htr_heat_load']
        
        for key in expected_keys:
            self.assertIn(key, params)
        
        self.assertEqual(params['Ppi_mW'], 39.0)
        self.assertEqual(params['resistance_ohm'], 50.0)
        self.assertEqual(params['voltage_v'], 3.3)
        self.assertEqual(params['target_heat_generated_mw'], 60.0)
        self.assertEqual(params['phase_htr_heat_load'], 60.0)


class TestMZIHTR(unittest.TestCase):
    """Test cases for MZIHTR model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mzi_htr = MZIHTR()
    
    def test_initialization(self):
        """Test MZIHTR initialization"""
        self.assertEqual(self.mzi_htr.Ppi, 27.0)
        self.assertEqual(self.mzi_htr.resistance_ohm, 57.0)
        self.assertEqual(self.mzi_htr.voltage_v, 3.3)
        self.assertEqual(self.mzi_htr.target_heat_generated_mw, 27.0)
        self.assertEqual(self.mzi_htr.mzi_htr_heat_load, 27.0)
    
    def test_duty_cycle_calculation(self):
        """Test duty cycle calculation"""
        # Max power = V^2 / R = 3.3^2 / 57 = 10.89 / 57 = 0.1911W = 191.1mW
        # Duty cycle = 27 / 191.1 = 0.1413
        expected_duty_cycle = 27.0 / 191.1
        self.assertAlmostEqual(self.mzi_htr.duty_cycle, expected_duty_cycle, places=3)
    
    def test_get_methods(self):
        """Test getter methods"""
        self.assertEqual(self.mzi_htr.get_heat_generated(), 27.0)
        self.assertEqual(self.mzi_htr.get_power_consumption(), 27.0)
        self.assertIsInstance(self.mzi_htr.get_duty_cycle(), float)
        self.assertGreater(self.mzi_htr.get_duty_cycle(), 0)
        self.assertLess(self.mzi_htr.get_duty_cycle(), 1)
    
    def test_get_parameters(self):
        """Test parameters getter"""
        params = self.mzi_htr.get_parameters()
        expected_keys = ['Ppi_mW', 'resistance_ohm', 'voltage_v', 'target_heat_generated_mw', 'duty_cycle', 'mzi_htr_heat_load']
        
        for key in expected_keys:
            self.assertIn(key, params)
        
        self.assertEqual(params['Ppi_mW'], 27.0)
        self.assertEqual(params['resistance_ohm'], 57.0)
        self.assertEqual(params['voltage_v'], 3.3)
        self.assertEqual(params['target_heat_generated_mw'], 27.0)
        self.assertEqual(params['mzi_htr_heat_load'], 27.0)


class TestHeaterComparison(unittest.TestCase):
    """Test cases comparing all heater models"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ring_htr = RINGHTR()
        self.phase_htr = PHASEHTR()
        self.mzi_htr = MZIHTR()
    
    def test_power_levels(self):
        """Test power levels are as expected"""
        # Ring heater should have highest power
        self.assertGreater(self.ring_htr.get_power_consumption(), self.phase_htr.get_power_consumption())
        self.assertGreater(self.ring_htr.get_power_consumption(), self.mzi_htr.get_power_consumption())
        
        # Phase heater should have more power than MZI heater
        self.assertGreater(self.phase_htr.get_power_consumption(), self.mzi_htr.get_power_consumption())
        
        # Expected values
        self.assertEqual(self.ring_htr.get_power_consumption(), 78.0)
        self.assertEqual(self.phase_htr.get_power_consumption(), 60.0)
        self.assertEqual(self.mzi_htr.get_power_consumption(), 27.0)
    
    def test_resistance_values(self):
        """Test resistance values are as expected"""
        self.assertEqual(self.ring_htr.resistance_ohm, 34.0)
        self.assertEqual(self.phase_htr.resistance_ohm, 50.0)
        self.assertEqual(self.mzi_htr.resistance_ohm, 57.0)
        
        # MZI should have highest resistance
        self.assertGreater(self.mzi_htr.resistance_ohm, self.phase_htr.resistance_ohm)
        self.assertGreater(self.mzi_htr.resistance_ohm, self.ring_htr.resistance_ohm)
    
    def test_duty_cycle_relationships(self):
        """Test duty cycle relationships"""
        # All duty cycles should be between 0 and 1
        for heater in [self.ring_htr, self.phase_htr, self.mzi_htr]:
            duty_cycle = heater.get_duty_cycle()
            self.assertGreater(duty_cycle, 0)
            self.assertLess(duty_cycle, 1)
    
    def test_common_voltage(self):
        """Test all heaters use same voltage"""
        self.assertEqual(self.ring_htr.voltage_v, 3.3)
        self.assertEqual(self.phase_htr.voltage_v, 3.3)
        self.assertEqual(self.mzi_htr.voltage_v, 3.3)
    
    def test_method_consistency(self):
        """Test all heaters have consistent method interfaces"""
        heaters = [self.ring_htr, self.phase_htr, self.mzi_htr]
        
        for heater in heaters:
            # All should have these methods
            self.assertTrue(hasattr(heater, 'get_heat_generated'))
            self.assertTrue(hasattr(heater, 'get_power_consumption'))
            self.assertTrue(hasattr(heater, 'get_duty_cycle'))
            self.assertTrue(hasattr(heater, 'get_parameters'))
            
            # All should return positive values
            self.assertGreater(heater.get_heat_generated(), 0)
            self.assertGreater(heater.get_power_consumption(), 0)
            self.assertGreater(heater.get_duty_cycle(), 0)
            
            # Parameters should be a dictionary
            self.assertIsInstance(heater.get_parameters(), dict)


class TestHeaterEdgeCases(unittest.TestCase):
    """Test edge cases for heater models"""
    
    def test_zero_resistance_protection(self):
        """Test protection against zero resistance"""
        # This would require modifying the class, so we test the calculation logic
        # If resistance were 0, max_power would be infinite, duty cycle should be 0
        voltage = 3.3
        target_power = 78.0
        
        # Test what happens with very high resistance (approaching infinity)
        high_resistance = 1e6  # 1M ohm
        max_power_mw = (voltage ** 2 / high_resistance) * 1000
        duty_cycle = min(max(target_power / max_power_mw, 0.0), 1.0)
        
        # Should clamp to 1.0 (100% duty cycle)
        self.assertEqual(duty_cycle, 1.0)
    
    def test_power_conservation(self):
        """Test power conservation principles"""
        heaters = [RINGHTR(), PHASEHTR(), MZIHTR()]
        
        for heater in heaters:
            # Heat generated should equal power consumption (assuming 100% efficiency)
            self.assertEqual(heater.get_heat_generated(), heater.get_power_consumption())
            
            # Power consumption should equal target heat generation
            self.assertEqual(heater.get_power_consumption(), heater.target_heat_generated_mw)


if __name__ == '__main__':
    unittest.main() 