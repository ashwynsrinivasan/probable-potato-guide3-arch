"""
RINGMUX 10x1 Ports Circuit

This circuit contains 10 RINGHTR components:
- 8 operational RINGHTR devices (powered and contributing to thermal management)
- 2 redundant RINGHTR devices (not powered, for backup)
"""

import sys
import os

# Add models to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from models.RINGHTR import RINGHTR
except ImportError:
    # Fallback for direct import
    from src.models.RINGHTR import RINGHTR


class RINGMUX_10x1ports:
    """
    RINGMUX 10x1 ports circuit class
    
    Contains 10 RINGHTR components with redundancy:
    - Devices 0-7: Operational (powered and contributing to thermal management)
    - Devices 8-9: Redundant (not powered, for backup purposes)
    """
    
    def __init__(self):
        """
        Initialize RINGMUX 10x1 ports circuit
        """
        # Initialize 10 RINGHTR devices
        self.ringhtr_devices = []
        for i in range(10):
            ringhtr = RINGHTR()
            self.ringhtr_devices.append(ringhtr)
        
        # Define operational and redundant device indices
        self.operational_indices = list(range(8))  # Devices 0-7 are operational
        self.redundant_indices = [8, 9]           # Devices 8-9 are redundant
        
        # Calculate combined parameters
        self._calculate_combined_parameters()
    
    def _calculate_combined_parameters(self):
        """Calculate combined heat loads and power consumption for operational devices"""
        # Combined RINGHTR heat load from 8 operational devices
        self.combined_heat_load = 0.0
        for i in self.operational_indices:
            self.combined_heat_load += self.ringhtr_devices[i].get_heat_generated()
        
        # Combined power consumption from 8 operational devices
        self.combined_power_consumption = 0.0
        for i in self.operational_indices:
            self.combined_power_consumption += self.ringhtr_devices[i].get_power_consumption()
        
        # For RINGHTR devices, heat load equals power consumption (100% efficiency)
        assert abs(self.combined_heat_load - self.combined_power_consumption) < 1e-6
    
    def get_operational_devices(self):
        """
        Get operational RINGHTR devices
        
        Returns:
            list: List of operational RINGHTR devices
        """
        return [self.ringhtr_devices[i] for i in self.operational_indices]
    
    def get_redundant_devices(self):
        """
        Get redundant RINGHTR devices (not powered)
        
        Returns:
            list: List of redundant RINGHTR devices
        """
        return [self.ringhtr_devices[i] for i in self.redundant_indices]
    
    def get_combined_heat_load(self):
        """
        Get total combined heat load from all operational devices
        
        Returns:
            float: Combined heat load in mW
        """
        return self.combined_heat_load
    
    def get_combined_power_consumption(self):
        """
        Get total combined power consumption from all operational devices
        
        Returns:
            float: Combined power consumption in mW
        """
        return self.combined_power_consumption
    
    def get_total_electrical_power(self):
        """
        Calculate total electrical power consumption from all operational devices
        
        Returns:
            float: Total electrical power in mW
        """
        return self.get_combined_power_consumption()
    
    def get_total_optical_power(self):
        """
        Calculate total optical power output (heaters don't produce optical power)
        
        Returns:
            float: Total optical power in mW (always 0 for heater circuits)
        """
        return 0.0  # Heater circuits don't produce optical power
    
    def get_total_heat_load(self):
        """
        Calculate total heat load from all operational devices
        
        Returns:
            float: Total heat load in mW
        """
        return self.get_combined_heat_load()
    
    def get_heat_sources_breakdown(self):
        """
        Get detailed breakdown of heat sources from operational devices
        
        Returns:
            dict: Heat sources breakdown
        """
        return {
            'RINGHTR Heat Load (8 operational devices)': self.combined_heat_load,
            'Total Circuit Heat Load': self.combined_heat_load
        }
    
    def get_power_consumption_breakdown(self):
        """
        Get power consumption breakdown for operational devices
        
        Returns:
            dict: Power consumption breakdown
        """
        return {
            'RINGHTR Power (8 operational devices)': self.combined_power_consumption,
            'Total Circuit Power': self.combined_power_consumption
        }
    
    def get_device_status(self):
        """
        Get status of all devices in the circuit
        
        Returns:
            dict: Device status information
        """
        return {
            'total_ringhtr_devices': len(self.ringhtr_devices),
            'operational_ringhtr_count': len(self.operational_indices),
            'redundant_ringhtr_count': len(self.redundant_indices),
            'operational_indices': self.operational_indices,
            'redundant_indices': self.redundant_indices
        }
    
    def activate_redundant_device(self, device_index):
        """
        Activate a redundant device (move from redundant to operational)
        
        Args:
            device_index (int): Index of the device to activate (must be in redundant_indices)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if device_index in self.redundant_indices:
            # Move from redundant to operational
            self.redundant_indices.remove(device_index)
            self.operational_indices.append(device_index)
            
            # Recalculate combined parameters
            self._calculate_combined_parameters()
            return True
        return False
    
    def deactivate_operational_device(self, device_index):
        """
        Deactivate an operational device (move from operational to redundant)
        
        Args:
            device_index (int): Index of the device to deactivate (must be in operational_indices)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if device_index in self.operational_indices and len(self.operational_indices) > 1:
            # Move from operational to redundant (ensure at least 1 operational remains)
            self.operational_indices.remove(device_index)
            self.redundant_indices.append(device_index)
            
            # Recalculate combined parameters
            self._calculate_combined_parameters()
            return True
        return False
    
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
            'circuit_name': 'RINGMUX 10x1 Ports',
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
    Main function to demonstrate RINGMUX 10x1 ports circuit
    """
    print("RINGMUX 10x1 Ports Circuit Demo")
    print("=" * 40)
    
    # Create circuit instance
    circuit = RINGMUX_10x1ports()
    
    # Get comprehensive summary
    summary = circuit.get_circuit_summary()
    
    print(f"Circuit: {summary['circuit_name']}")
    print()
    
    print("Device Status:")
    device_status = summary['device_status']
    print(f"  Total RINGHTR Devices: {device_status['total_ringhtr_devices']}")
    print(f"  Operational RINGHTR: {device_status['operational_ringhtr_count']} (indices: {device_status['operational_indices']})")
    print(f"  Redundant RINGHTR: {device_status['redundant_ringhtr_count']} (indices: {device_status['redundant_indices']})")
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
    print()
    
    # Demonstrate redundancy management
    print("Redundancy Management Demo:")
    print("Activating redundant device 8...")
    success = circuit.activate_redundant_device(8)
    if success:
        new_summary = circuit.get_circuit_summary()
        print(f"  New operational count: {new_summary['device_status']['operational_ringhtr_count']}")
        print(f"  New combined heat load: {new_summary['thermal_performance']['combined_heat_load_mw']:.1f} mW")
    else:
        print("  Failed to activate device 8")


if __name__ == "__main__":
    main() 