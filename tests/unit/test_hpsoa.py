"""
Unit tests for HPSOA (High Power Semiconductor Optical Amplifier) model
"""

import unittest
import sys
import os
import pandas as pd

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.HPSOA import HPSOA


class TestHPSOA(unittest.TestCase):
    """Test cases for HPSOA model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.hpsoa = HPSOA()
        self.test_temperature = 35
        self.test_current = 0.18
        self.test_wavelength = 1311
    
    def test_initialization(self):
        """Test HPSOA initialization"""
        self.assertIsInstance(self.hpsoa.revision_history, list)
        self.assertIsInstance(self.hpsoa.references, list)
        self.assertIsInstance(self.hpsoa.glossary, dict)
        self.assertIsInstance(self.hpsoa.performance_summary, dict)
        
        # Check performance data structure
        self.assertIn('operation_conditions', self.hpsoa.performance_summary)
        self.assertIn('data', self.hpsoa.performance_summary)
        self.assertEqual(len(self.hpsoa.performance_summary['data']), 36)  # 36 data points
    
    def test_dbm_to_mw_conversion(self):
        """Test dBm to mW conversion"""
        # Test known conversions
        self.assertAlmostEqual(self.hpsoa.dbm_to_mw(0), 1.0, places=3)    # 0 dBm = 1 mW
        self.assertAlmostEqual(self.hpsoa.dbm_to_mw(10), 10.0, places=3)  # 10 dBm = 10 mW
        self.assertAlmostEqual(self.hpsoa.dbm_to_mw(20), 100.0, places=3) # 20 dBm = 100 mW
        self.assertAlmostEqual(self.hpsoa.dbm_to_mw(-10), 0.1, places=3)  # -10 dBm = 0.1 mW
    
    def test_operating_voltage_calculation(self):
        """Test operating voltage calculation"""
        voltage = self.hpsoa.get_operating_voltage(self.test_current)
        
        # Expected calculation:
        # Rs_total = (2.89 * 5.47) / (2.89 + 5.47) = 15.8083 / 8.36 = 1.891 ohms
        # V = 1.05 + (0.18 * 1.891) = 1.05 + 0.340 = 1.390V
        self.assertAlmostEqual(voltage, 1.390, places=2)
    
    def test_heat_load_calculation(self):
        """Test heat load calculation for known data point"""
        heat_load = self.hpsoa.get_hpsoa_heat_load(self.test_temperature, self.test_current, self.test_wavelength)
        
        # For T=35°C, I=0.18A, λ=1311nm: Pout = 18.8 dBm = 75.86 mW
        # Electrical power = 0.18A * 1.390V * 1000 = 250.2 mW
        # Heat load = 250.2 - 75.86 = 174.34 mW
        self.assertAlmostEqual(heat_load, 174.34, places=0)  # Allow some tolerance
    
    def test_heat_load_no_matching_data(self):
        """Test heat load calculation with no matching data"""
        heat_load = self.hpsoa.get_hpsoa_heat_load(25, 0.15, 1300)  # Non-existent combination
        self.assertEqual(heat_load, 0.0)
    
    def test_heat_sources_breakdown(self):
        """Test heat sources breakdown"""
        heat_sources = self.hpsoa.get_heat_sources(self.test_temperature, self.test_current, self.test_wavelength)
        
        self.assertIn('HPSOA Gain Heat Load', heat_sources)
        self.assertIsInstance(heat_sources['HPSOA Gain Heat Load'], float)
        self.assertGreater(heat_sources['HPSOA Gain Heat Load'], 0)
    
    def test_power_consumption_breakdown(self):
        """Test power consumption breakdown"""
        power_consumption = self.hpsoa.get_power_consumption(self.test_temperature, self.test_current, self.test_wavelength)
        
        self.assertIn('HPSOA Gain', power_consumption)
        self.assertAlmostEqual(power_consumption['HPSOA Gain'], 250.2, places=0)
    
    def test_performance_data_integrity(self):
        """Test performance data integrity"""
        data = self.hpsoa.get_performance_summary_data()
        
        # Check all required fields are present
        required_fields = ['Index', 'T[°C]', 'I[A]', 'λ [nm]', 'Pin [dBm]', 'Pout [dBm]', 'WPE [%]', 'NF [dB]']
        for entry in data:
            for field in required_fields:
                self.assertIn(field, entry)
        
        # Check data ranges
        df = pd.DataFrame(data)
        self.assertTrue(df['T[°C]'].min() >= 35)
        self.assertTrue(df['T[°C]'].max() <= 80)
        self.assertTrue(df['I[A]'].min() >= 0.18)
        self.assertTrue(df['I[A]'].max() <= 0.28)
        self.assertTrue(df['λ [nm]'].min() >= 1304)
        self.assertTrue(df['λ [nm]'].max() <= 1318)
    
    def test_operation_conditions(self):
        """Test operation conditions"""
        conditions = self.hpsoa.get_performance_summary_conditions()
        
        expected_temps = [35, 55, 70, 80]
        expected_currents = [0.18, 0.23, 0.28]
        expected_wavelengths = [1304, 1311, 1318]
        
        self.assertEqual(conditions['temperature_celsius'], expected_temps)
        self.assertEqual(conditions['current_a'], expected_currents)
        self.assertEqual(conditions['wavelength_nm'], expected_wavelengths)
    
    def test_design_geometry(self):
        """Test design geometry parameters"""
        geometry = self.hpsoa.get_hpsoa_design_geometry()
        
        dimensions = geometry['iii_v_gain_sections']['dimensions']
        self.assertEqual(dimensions['W1_um'], 2)
        self.assertEqual(dimensions['L1_um'], 1260)
        self.assertEqual(dimensions['W2_um'], 4)
        self.assertEqual(dimensions['Lwt_um'], 60)
        self.assertEqual(dimensions['L2_um'], 400)
    
    def test_performance_equations(self):
        """Test performance equations and parameters"""
        performance = self.hpsoa.get_hpsoa_performance_equations()
        
        self.assertIn('wall_plug_efficiency_equation', performance)
        self.assertIn('voltage_equation', performance)
        self.assertIn('series_resistance_equation', performance)
        
        # Check equivalent circuit parameters
        circuit_params = performance['equivalent_circuit_parameters']
        self.assertEqual(circuit_params['V_turn_on'], 1.05)
        self.assertEqual(circuit_params['Rs1_ohm'], 2.89)
        self.assertEqual(circuit_params['Rs2_ohm'], 5.47)
    
    def test_getter_methods(self):
        """Test all getter methods"""
        # Test that all getter methods return expected types
        self.assertIsInstance(self.hpsoa.get_revision_history(), list)
        self.assertIsInstance(self.hpsoa.get_references(), list)
        self.assertIsInstance(self.hpsoa.get_glossary(), dict)
        self.assertIsInstance(self.hpsoa.get_document_scope(), str)
        self.assertIsInstance(self.hpsoa.get_introduction(), str)
        self.assertIsInstance(self.hpsoa.get_hpsoa_design_geometry(), dict)
        self.assertIsInstance(self.hpsoa.get_hpsoa_performance_equations(), dict)
        self.assertIsInstance(self.hpsoa.get_performance_summary_conditions(), dict)
        self.assertIsInstance(self.hpsoa.get_performance_summary_data(), list)
    
    def test_heat_load_calculations_all_data_points(self):
        """Test heat load calculations for all data points"""
        data = self.hpsoa.get_performance_summary_data()
        
        for entry in data:
            temp = entry['T[°C]']
            current = entry['I[A]']
            wavelength = entry['λ [nm]']
            
            heat_load = self.hpsoa.get_hpsoa_heat_load(temp, current, wavelength)
            
            # Heat load should always be positive and reasonable
            self.assertGreaterEqual(heat_load, 0)
            self.assertLess(heat_load, 1000)  # Should be less than 1W
    
    def test_wpe_consistency(self):
        """Test WPE consistency between data and calculations"""
        # Pick a known data point
        entry = self.hpsoa.get_performance_summary_data()[1]  # Index 2: 35°C, 0.18A, 1311nm
        
        temp = entry['T[°C]']
        current = entry['I[A]']
        wavelength = entry['λ [nm]']
        recorded_wpe = entry['WPE [%]']
        
        # Calculate WPE from our methods
        optical_power_mw = self.hpsoa.dbm_to_mw(entry['Pout [dBm]'])
        electrical_power_mw = current * self.hpsoa.get_operating_voltage(current) * 1000
        calculated_wpe = (optical_power_mw / electrical_power_mw) * 100
        
        # Should be reasonably close (allowing for measurement/model differences)
        self.assertAlmostEqual(calculated_wpe, recorded_wpe, delta=5.0)


if __name__ == '__main__':
    unittest.main() 