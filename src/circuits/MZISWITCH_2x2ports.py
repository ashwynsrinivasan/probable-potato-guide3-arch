"""
MZISWITCH 2x2 Ports Circuit

This circuit contains 1 MZIHTR component for thermal management.
The single MZIHTR device is operational.
"""

import sys
import os

# Add models to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from models.MZIHTR import MZIHTR
except ImportError:
    # Fallback for direct import
    from src.models.MZIHTR import MZIHTR


class MZISWITCH_2x2ports:
    """
    MZISWITCH 2x2 ports circuit class
    
    Contains 1 MZIHTR component for thermal management.
    The single device is operational.
    """
    
    def __init__(self):
        """
        Initialize MZISWITCH 2x2 ports circuit
        """
        # Initialize 1 MZIHTR device
        self.mzihtr_device = MZIHTR()
        
        # Single device is operational
        self.operational_indices = [0]  # Device 0 is operational
        
        # Calculate combined parameters
        self._calculate_combined_parameters()
    
    def _calculate_combined_parameters(self):
        """Calculate heat load and power consumption for the single device"""
        # Heat load from the single MZIHTR device
        self.combined_heat_load = self.mzihtr_device.get_heat_generated()
        
        # Power consumption from the single MZIHTR device
        self.combined_power_consumption = self.mzihtr_device.get_power_consumption()
        
        # For MZIHTR devices, heat load equals power consumption (100% efficiency)
        assert abs(self.combined_heat_load - self.combined_power_consumption) < 1e-6
    
    def get_operational_device(self):
        """
        Get the operational MZIHTR device
        
        Returns:
            MZIHTR: The operational MZIHTR device
        """
        return self.mzihtr_device
    
    def get_combined_heat_load(self):
        """
        Get total heat load from the device
        
        Returns:
            float: Heat load in mW
        """
        return self.combined_heat_load
    
    def get_combined_power_consumption(self):
        """
        Get total power consumption from the device
        
        Returns:
            float: Power consumption in mW
        """
        return self.combined_power_consumption
    
    def get_heat_sources_breakdown(self):
        """
        Get detailed breakdown of heat sources from the device
        
        Returns:
            dict: Heat sources breakdown
        """
        return {
            'MZIHTR Heat Load (1 device)': self.combined_heat_load,
            'Total Circuit Heat Load': self.combined_heat_load
        }
    
    def get_power_consumption_breakdown(self):
        """
        Get power consumption breakdown for the device
        
        Returns:
            dict: Power consumption breakdown
        """
        return {
            'MZIHTR Power (1 device)': self.combined_power_consumption,
            'Total Circuit Power': self.combined_power_consumption
        }
    
    def get_device_status(self):
        """
        Get status of the device in the circuit
        
        Returns:
            dict: Device status information
        """
        return {
            'total_mzihtr_devices': 1,
            'operational_mzihtr_count': 1,
            'operational_indices': self.operational_indices
        }
    
    def get_circuit_summary(self):
        """
        Get comprehensive summary of the circuit
        
        Returns:
            dict: Circuit summary
        """
        device_status = self.get_device_status()
        heat_sources = self.get_heat_sources_breakdown()
        power_consumption = self.get_power_consumption_breakdown()
        
        return {
            'circuit_name': 'MZISWITCH 2x2 Ports',
            'device_status': device_status,
            'thermal_performance': {
                'combined_heat_load_mw': self.combined_heat_load,
                'combined_power_consumption_mw': self.combined_power_consumption
            },
            'heat_sources_mw': heat_sources,
            'power_consumption_mw': power_consumption
        }


def main():
    """
    Main function to demonstrate MZISWITCH 2x2 ports circuit
    """
    print("MZISWITCH 2x2 Ports Circuit Demo")
    print("=" * 40)
    
    # Create circuit instance
    circuit = MZISWITCH_2x2ports()
    
    # Get comprehensive summary
    summary = circuit.get_circuit_summary()
    
    print(f"Circuit: {summary['circuit_name']}")
    print()
    
    print("Device Status:")
    device_status = summary['device_status']
    print(f"  Total MZIHTR Devices: {device_status['total_mzihtr_devices']}")
    print(f"  Operational MZIHTR: {device_status['operational_mzihtr_count']} (indices: {device_status['operational_indices']})")
    print()
    
    print("Thermal Performance:")
    thermal = summary['thermal_performance']
    print(f"  Combined Heat Load: {thermal['combined_heat_load_mw']:.1f} mW")
    print(f"  Combined Power Consumption: {thermal['combined_power_consumption_mw']:.1f} mW")
    print()
    
    print("Heat Sources Breakdown:")
    for source, value in summary['heat_sources_mw'].items():
        print(f"  {source}: {value:.1f} mW")
    print()
    
    print("Power Consumption Breakdown:")
    for component, value in summary['power_consumption_mw'].items():
        print(f"  {component}: {value:.1f} mW")


if __name__ == "__main__":
    main() 