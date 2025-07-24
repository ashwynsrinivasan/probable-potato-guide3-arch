"""
Integration tests for SOA model interactions and system-level functionality
"""

import unittest
import sys
import os
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models import TRL, DFB, HPSOA, RINGHTR, PHASEHTR, MZIHTR


class TestModelIntegration(unittest.TestCase):
    """Integration tests for model interactions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.trl = TRL()
        self.dfb = DFB()
        self.hpsoa = HPSOA()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_trl_heater_integration(self):
        """Test TRL integration with heater components"""
        # TRL should have heater instances
        self.assertIsInstance(self.trl.ring_htr_1, RINGHTR)
        self.assertIsInstance(self.trl.ring_htr_2, RINGHTR)
        self.assertIsInstance(self.trl.phase_htr, PHASEHTR)
        
        # Total heater heat load should be sum of individual heaters
        expected_total = (
            self.trl.ring_htr_1.ring_htr_heat_load +
            self.trl.ring_htr_2.ring_htr_heat_load +
            self.trl.phase_htr.phase_htr_heat_load
        )
        self.assertEqual(self.trl.trl_heater_heat_load, expected_total)
        self.assertEqual(expected_total, 216.0)  # 78 + 78 + 60
    
    def test_thermal_calculations_consistency(self):
        """Test thermal calculations are consistent across models"""
        test_temp = 35.0
        test_current = 130.0
        
        # TRL thermal calculations
        trl_gain_heat = self.trl.get_trl_gain_heat_load(test_temp, test_current)
        trl_total_heat = self.trl.get_trl_heat_load(test_temp, test_current)
        
        # DFB thermal calculations  
        dfb_heat = self.dfb.get_dfb_heat_load(test_temp, test_current)
        
        # All heat loads should be positive
        self.assertGreater(trl_gain_heat, 0)
        self.assertGreater(trl_total_heat, 0)
        self.assertGreater(dfb_heat, 0)
        
        # TRL total heat should be gain heat + heater heat
        expected_trl_total = trl_gain_heat + self.trl.trl_heater_heat_load
        self.assertAlmostEqual(trl_total_heat, expected_trl_total, places=1)
    
    def test_wpe_calculations_consistency(self):
        """Test WPE calculations are consistent across models"""
        test_temp = 35.0
        test_current = 130.0
        
        # TRL WPE calculations
        trl_gain_wpe = self.trl.get_trl_gain_wpe(test_temp, test_current)
        trl_total_wpe = self.trl.get_total_wpe(test_temp, test_current)
        
        # DFB WPE calculations
        dfb_single_wpe = self.dfb.get_dfb_wpe_single_side(test_temp, test_current)
        dfb_total_wpe = self.dfb.get_dfb_wpe(test_temp, test_current)
        
        # All WPE values should be positive and reasonable
        for wpe in [trl_gain_wpe, trl_total_wpe, dfb_single_wpe, dfb_total_wpe]:
            self.assertGreater(wpe, 0)
            self.assertLess(wpe, 100)  # Should be less than 100%
        
        # Total WPE should be less than gain-only WPE (due to heater overhead)
        self.assertLess(trl_total_wpe, trl_gain_wpe)
        
        # DFB total WPE should be double single-side WPE
        self.assertAlmostEqual(dfb_total_wpe, 2 * dfb_single_wpe, places=1)
    
    def test_electrical_characteristics_consistency(self):
        """Test electrical characteristics are consistent across models"""
        test_current = 130.0  # mA
        
        # Both TRL and DFB should use same electrical model
        trl_voltage = self.trl.get_operating_voltage(test_current)
        dfb_voltage = self.dfb.get_operating_voltage(test_current)
        
        # Should be identical (same series resistance formula)
        self.assertAlmostEqual(trl_voltage, dfb_voltage, places=3)
        
        # Both should have same turn-on voltage
        self.assertEqual(self.trl.V_turn_on, self.dfb.V_turn_on)
        
        # Both should have same series resistance
        trl_resistance = self.trl.calculate_series_resistance_ohm()
        dfb_resistance = self.dfb.calculate_series_resistance_ohm()
        self.assertAlmostEqual(trl_resistance, dfb_resistance, places=3)
    
    def test_power_conservation(self):
        """Test power conservation across all models"""
        test_temp = 35.0
        test_current = 130.0
        
        # TRL power conservation
        trl_optical = self.trl.calculate_output_power(test_temp, test_current)
        trl_electrical = test_current * self.trl.get_operating_voltage(test_current)
        trl_heat = self.trl.get_trl_gain_heat_load(test_temp, test_current)
        
        # Electrical = Optical + Heat (within tolerance)
        self.assertAlmostEqual(trl_electrical, trl_optical + trl_heat, places=0)
        
        # DFB power conservation
        dfb_single_optical = self.dfb.calculate_output_power(test_temp, test_current)
        dfb_total_optical = 2 * dfb_single_optical
        dfb_electrical = test_current * self.dfb.get_operating_voltage(test_current)
        dfb_heat = self.dfb.get_dfb_heat_load(test_temp, test_current)
        
        # Electrical = Total Optical + Heat
        self.assertAlmostEqual(dfb_electrical, dfb_total_optical + dfb_heat, places=0)
    
    def test_heater_system_integration(self):
        """Test heater system integration"""
        # Create individual heaters
        ring_htr = RINGHTR()
        phase_htr = PHASEHTR()
        mzi_htr = MZIHTR()
        
        # Test power levels are different
        power_levels = [
            ring_htr.get_power_consumption(),
            phase_htr.get_power_consumption(),
            mzi_htr.get_power_consumption()
        ]
        
        # All should be different
        self.assertEqual(len(set(power_levels)), 3)
        
        # Test total system power
        total_heater_power = sum(power_levels)
        self.assertEqual(total_heater_power, 165.0)  # 78 + 60 + 27
        
        # Test duty cycles are all reasonable
        for heater in [ring_htr, phase_htr, mzi_htr]:
            duty_cycle = heater.get_duty_cycle()
            self.assertGreater(duty_cycle, 0)
            self.assertLess(duty_cycle, 1)
    
    def test_model_parameter_ranges(self):
        """Test model parameters are within reasonable ranges"""
        # Temperature range test
        for temp in [10, 25, 35, 55, 80]:
            # TRL should work across temperature range
            trl_power = self.trl.calculate_output_power(temp, 100)
            self.assertGreaterEqual(trl_power, 0)
            
            # DFB should work across temperature range
            dfb_power = self.dfb.calculate_output_power(temp, 100)
            self.assertGreaterEqual(dfb_power, 0)
        
        # Current range test
        for current in [50, 100, 150, 200]:
            trl_power = self.trl.calculate_output_power(35, current)
            dfb_power = self.dfb.calculate_output_power(35, current)
            
            self.assertGreaterEqual(trl_power, 0)
            self.assertGreaterEqual(dfb_power, 0)
    
    def test_hpsoa_data_integrity(self):
        """Test HPSOA data integrity and calculations"""
        # Test that all data points can be processed
        data = self.hpsoa.get_performance_summary_data()
        
        processed_count = 0
        for entry in data:
            temp = entry['T[°C]']
            current = entry['I[A]']
            wavelength = entry['λ [nm]']
            
            # Should be able to calculate heat load for each point
            heat_load = self.hpsoa.get_hpsoa_heat_load(temp, current, wavelength)
            self.assertGreaterEqual(heat_load, 0)
            
            # Should be able to get power consumption
            power_consumption = self.hpsoa.get_power_consumption(temp, current, wavelength)
            self.assertIn('HPSOA Gain', power_consumption)
            self.assertGreater(power_consumption['HPSOA Gain'], 0)
            
            processed_count += 1
        
        # Should process all 36 data points
        self.assertEqual(processed_count, 36)
    
    def test_plotting_integration(self):
        """Test plotting functionality integration"""
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        
        # Test that models can generate plots without errors
        try:
            # TRL plotting
            trl_fig = self.trl.create_interactive_plot(save_path=None)
            self.assertIsNotNone(trl_fig)
            
            # DFB plotting  
            dfb_fig = self.dfb.create_interactive_plot(save_path=None)
            self.assertIsNotNone(dfb_fig)
            
            # HPSOA plotting
            hpsoa_fig, _ = self.hpsoa.plot_performance_data(
                save_path=os.path.join(self.temp_dir, 'test_hpsoa.png')
            )
            self.assertIsNotNone(hpsoa_fig)
            
        except Exception as e:
            self.fail(f"Plotting integration failed: {e}")
    
    def test_model_imports(self):
        """Test that all models can be imported from package"""
        try:
            from models import TRL, DFB, HPSOA, RINGHTR, PHASEHTR, MZIHTR, SOA
            
            # Should be able to instantiate all models
            models = [TRL(), DFB(), HPSOA(), RINGHTR(), PHASEHTR(), MZIHTR()]
            
            for model in models:
                self.assertIsNotNone(model)
                
        except ImportError as e:
            self.fail(f"Model import failed: {e}")
    
    def test_cross_model_comparisons(self):
        """Test comparisons between different models"""
        test_temp = 35.0
        test_current = 130.0
        
        # Compare optical outputs
        trl_output = self.trl.calculate_output_power(test_temp, test_current)
        dfb_output = self.dfb.calculate_output_power(test_temp, test_current)
        
        # Both should be positive
        self.assertGreater(trl_output, 0)
        self.assertGreater(dfb_output, 0)
        
        # Compare heat loads
        trl_heat = self.trl.get_trl_gain_heat_load(test_temp, test_current)
        dfb_heat = self.dfb.get_dfb_heat_load(test_temp, test_current)
        
        # Both should be positive
        self.assertGreater(trl_heat, 0)
        self.assertGreater(dfb_heat, 0)
        
        # Compare WPE
        trl_wpe = self.trl.get_trl_gain_wpe(test_temp, test_current)
        dfb_wpe = self.dfb.get_dfb_wpe_single_side(test_temp, test_current)
        
        # Both should be positive and less than 100%
        for wpe in [trl_wpe, dfb_wpe]:
            self.assertGreater(wpe, 0)
            self.assertLess(wpe, 100)


class TestSystemLevelFunctionality(unittest.TestCase):
    """Test system-level functionality"""
    
    def test_complete_thermal_system(self):
        """Test complete thermal management system"""
        trl = TRL()
        
        # Test thermal system at operating point
        temp = 35.0
        current = 130.0
        
        # Get all thermal components
        gain_heat = trl.get_trl_gain_heat_load(temp, current)
        heater_heat = trl.trl_heater_heat_load
        total_heat = trl.get_trl_heat_load(temp, current)
        
        # Verify thermal balance
        self.assertAlmostEqual(total_heat, gain_heat + heater_heat, places=1)
        
        # Get heat source breakdown
        heat_sources = trl.get_heat_sources(temp, current)
        
        # Should have all expected sources
        expected_sources = ['TRL Gain Heat Load', 'Ring Heater 1', 'Ring Heater 2', 'Phase Heater']
        for source in expected_sources:
            self.assertIn(source, heat_sources)
        
        # Sum should equal total
        source_sum = sum(heat_sources.values())
        self.assertAlmostEqual(source_sum, total_heat, places=1)
    
    def test_multi_model_system(self):
        """Test system with multiple models"""
        models = {
            'TRL': TRL(),
            'DFB': DFB(), 
            'HPSOA': HPSOA()
        }
        
        # Test that all models can coexist and function
        for name, model in models.items():
            self.assertIsNotNone(model)
            
            # Test that each has expected methods
            if hasattr(model, 'calculate_output_power'):
                # Laser models
                power = model.calculate_output_power(35.0, 130.0)
                self.assertGreaterEqual(power, 0)
            
            if hasattr(model, 'get_operating_voltage'):
                # Models with electrical characteristics
                voltage = model.get_operating_voltage(130.0)
                self.assertGreater(voltage, 0)


if __name__ == '__main__':
    unittest.main() 