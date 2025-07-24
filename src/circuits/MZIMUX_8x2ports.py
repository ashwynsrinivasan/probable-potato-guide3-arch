"""
MZIMUX 8x2 Ports Circuit

This circuit contains 6 MZIHTR components for thermal management.
All 6 MZIHTR devices are operational (no redundancy in this circuit).
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


class MZIMUX_8x2ports:
    """
    MZIMUX 8x2 ports circuit class
    
    Contains 6 MZIHTR components for thermal management.
    All devices are operational (no redundancy configuration).
    """
    
    def __init__(self):
        """
        Initialize MZIMUX 8x2 ports circuit
        """
        # Initialize 6 MZIHTR devices
        self.mzihtr_devices = []
        for i in range(6):
            mzihtr = MZIHTR()
            self.mzihtr_devices.append(mzihtr)
        
        # All devices are operational (no redundancy)
        self.operational_indices = list(range(6))  # All devices 0-5 are operational
        
        # Calculate combined parameters
        self._calculate_combined_parameters()
    
    def _calculate_combined_parameters(self):
        """Calculate combined heat loads and power consumption for all devices"""
        # Combined MZIHTR heat load from all 6 devices
        self.combined_heat_load = 0.0
        for i in self.operational_indices:
            self.combined_heat_load += self.mzihtr_devices[i].get_heat_generated()
        
        # Combined power consumption from all 6 devices
        self.combined_power_consumption = 0.0
        for i in self.operational_indices:
            self.combined_power_consumption += self.mzihtr_devices[i].get_power_consumption()
        
        # For MZIHTR devices, heat load equals power consumption (100% efficiency)
        assert abs(self.combined_heat_load - self.combined_power_consumption) < 1e-6
    
    def get_operational_devices(self):
        """
        Get operational MZIHTR devices
        
        Returns:
            list: List of operational MZIHTR devices
        """
        return [self.mzihtr_devices[i] for i in self.operational_indices]
    
    def get_combined_heat_load(self):
        """
        Get total combined heat load from all devices
        
        Returns:
            float: Combined heat load in mW
        """
        return self.combined_heat_load
    
    def get_combined_power_consumption(self):
        """
        Get total combined power consumption from all devices
        
        Returns:
            float: Combined power consumption in mW
        """
        return self.combined_power_consumption
    
    def get_heat_sources_breakdown(self):
        """
        Get detailed breakdown of heat sources from all devices
        
        Returns:
            dict: Heat sources breakdown
        """
        return {
            'MZIHTR Heat Load (6 devices)': self.combined_heat_load,
            'Total Circuit Heat Load': self.combined_heat_load
        }
    
    def get_power_consumption_breakdown(self):
        """
        Get power consumption breakdown for all devices
        
        Returns:
            dict: Power consumption breakdown
        """
        return {
            'MZIHTR Power (6 devices)': self.combined_power_consumption,
            'Total Circuit Power': self.combined_power_consumption
        }
    
    def get_device_status(self):
        """
        Get status of all devices in the circuit
        
        Returns:
            dict: Device status information
        """
        return {
            'total_mzihtr_devices': len(self.mzihtr_devices),
            'operational_mzihtr_count': len(self.operational_indices),
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
            'circuit_name': 'MZIMUX 8x2 Ports',
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
    Main function to demonstrate MZIMUX 8x2 ports circuit
    """
    print("MZIMUX 8x2 Ports Circuit Demo")
    print("=" * 40)
    
    # Create circuit instance
    circuit = MZIMUX_8x2ports()
    
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