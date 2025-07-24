"""
TRL 8-Channel 1-Port Architecture

This architecture contains 10 TRL devices and 1 RINGMUX_10x1ports circuit:
- 8 operational TRL devices (optical power combined)
- 2 redundant TRL devices (not powered, for backup)
- 1 RINGMUX_10x1ports circuit (with 8 operational + 2 redundant RINGHTR components)
"""

import sys
import os

# Add models and circuits to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from models.TRL import TRL
    from circuits.RINGMUX_10x1ports import RINGMUX_10x1ports
except ImportError:
    # Fallback for direct import
    from src.models.TRL import TRL
    from src.circuits.RINGMUX_10x1ports import RINGMUX_10x1ports


class Trl8ch1ports:
    """
    TRL 8-channel 1-ports architecture class
    
    Contains 10 TRL devices and 1 RINGMUX_10x1ports circuit with redundancy:
    - TRL Devices 0-7: Operational (powered and contributing to output)
    - TRL Devices 8-9: Redundant (not powered, for backup purposes)
    - RINGMUX circuit: Manages thermal control for all TRL devices
    """
    
    def __init__(self, temperature: float = 35.0, current: float = 130.0):
        """
        Initialize TRL 8-channel 1-port architecture
        
        Args:
            temperature (float): Operating temperature in Celsius (default: 35.0)
            current (float): Operating current per TRL in mA (default: 130.0)
        """
        self.temperature = temperature
        self.current = current
        
        # Initialize 10 TRL devices
        self.trl_devices = []
        for i in range(10):
            trl = TRL(temperature=temperature, current=current)
            self.trl_devices.append(trl)
        
        # Initialize 1 RINGMUX_10x1ports circuit (replaces individual RINGHTR devices)
        self.ringmux_circuit = RINGMUX_10x1ports()
        
        # Define operational and redundant device indices
        self.operational_indices = list(range(8))  # Devices 0-7 are operational
        self.redundant_indices = [8, 9]           # Devices 8-9 are redundant
        
        # Calculate combined parameters
        self._calculate_combined_parameters()
    
    def _calculate_combined_parameters(self):
        """Calculate combined parameters for all operational devices and circuits"""
        # ==== TOTAL OPTICAL POWER ====
        # Total optical power from 8 operational TRL devices (RINGMUX doesn't produce optical power)
        self.total_optical_power = 0.0
        for i in self.operational_indices:
            self.total_optical_power += self.trl_devices[i].get_total_optical_power(
                self.temperature, self.current
            )
        # RINGMUX circuit optical power (always 0 for heater circuits)
        self.total_optical_power += self.ringmux_circuit.get_total_optical_power()
        
        # ==== TOTAL ELECTRICAL POWER ====
        # Total electrical power from 8 operational TRL devices (including their internal heaters)
        self.total_electrical_power = 0.0
        for i in self.operational_indices:
            self.total_electrical_power += self.trl_devices[i].get_total_electrical_power(
                self.temperature, self.current
            )
        # RINGMUX circuit electrical power
        self.total_electrical_power += self.ringmux_circuit.get_total_electrical_power()
        
        # ==== TOTAL HEAT LOAD ====
        # Total heat load from 8 operational TRL devices (including their internal heaters)
        self.total_heat_load = 0.0
        for i in self.operational_indices:
            self.total_heat_load += self.trl_devices[i].get_total_heat_load(
                self.temperature, self.current
            )
        # RINGMUX circuit heat load
        self.total_heat_load += self.ringmux_circuit.get_total_heat_load()
        
        # ==== LEGACY PARAMETERS (for backward compatibility) ====
        # Keep existing parameters for backward compatibility
        self.combined_optical_power = self.total_optical_power  # Same as total optical power
        
        # Combined TRL gain heat load from 8 operational devices
        self.combined_trl_gain_heat_load = 0.0
        for i in self.operational_indices:
            self.combined_trl_gain_heat_load += self.trl_devices[i].get_trl_gain_heat_load(
                self.temperature, self.current
            )
        
        # Combined TRL heater heat load from 8 operational devices
        self.combined_trl_heater_heat_load = 0.0
        for i in self.operational_indices:
            self.combined_trl_heater_heat_load += self.trl_devices[i].trl_heater_heat_load
        
        # RINGMUX circuit heat load (from 8 operational RINGHTR devices in the circuit)
        self.ringmux_heat_load = self.ringmux_circuit.get_combined_heat_load()
        
        # Total combined heat load (legacy name, same as total_heat_load)
        self.total_combined_heat_load = self.total_heat_load
        
        # Combined TRL electrical power from 8 operational devices (gain only, not including internal heaters)
        self.combined_electrical_power = 0.0
        for i in self.operational_indices:
            operating_voltage = self.trl_devices[i].get_operating_voltage(self.current)
            self.combined_electrical_power += self.current * operating_voltage
        
        # Combined TRL gain wall-plug efficiency (legacy calculation)
        if self.combined_electrical_power > 0:
            self.combined_wpe = (self.combined_optical_power / self.combined_electrical_power) * 100
        else:
            self.combined_wpe = 0.0
    
    def get_operational_devices(self):
        """
        Get operational TRL devices and RINGMUX circuit
        
        Returns:
            tuple: (operational_trl_devices, ringmux_circuit)
        """
        operational_trl = [self.trl_devices[i] for i in self.operational_indices]
        return operational_trl, self.ringmux_circuit
    
    def get_redundant_devices(self):
        """
        Get redundant TRL devices (not powered)
        
        Returns:
            list: List of redundant TRL devices
        """
        return [self.trl_devices[i] for i in self.redundant_indices]
    
    def get_combined_optical_power(self):
        """
        Get combined optical power from all 8 operational TRL devices
        
        Returns:
            float: Combined optical power in mW
        """
        return self.combined_optical_power
    
    def get_combined_heat_load(self):
        """
        Get total combined heat load from all operational devices
        
        Returns:
            float: Total combined heat load in mW
        """
        return self.total_combined_heat_load
    
    def get_total_optical_power(self):
        """
        Get total optical power from all operational components
        
        Returns:
            float: Total optical power in mW
        """
        return self.total_optical_power
    
    def get_total_electrical_power(self):
        """
        Get total electrical power from all operational components
        
        Returns:
            float: Total electrical power in mW
        """
        return self.total_electrical_power
    
    def get_total_heat_load(self):
        """
        Get total heat load from all operational components
        
        Returns:
            float: Total heat load in mW
        """
        return self.total_heat_load
    
    def get_heat_sources_breakdown(self):
        """
        Get detailed breakdown of heat sources from operational devices
        
        Returns:
            dict: Heat sources breakdown
        """
        return {
            'TRL Gain Heat Load (8 devices)': self.combined_trl_gain_heat_load,
            'TRL Heater Heat Load (8 devices)': self.combined_trl_heater_heat_load,
            'RINGMUX Circuit Heat Load': self.ringmux_heat_load,
            'Total Combined Heat Load': self.total_combined_heat_load
        }
    
    def get_power_consumption_breakdown(self):
        """
        Get power consumption breakdown for operational devices
        
        Returns:
            dict: Power consumption breakdown
        """
        # RINGMUX circuit electrical power
        ringmux_power = self.ringmux_circuit.get_combined_power_consumption()
        
        return {
            'TRL Electrical Power (8 devices)': self.combined_electrical_power,
            'RINGMUX Circuit Power': ringmux_power,
            'Total Electrical Power': self.combined_electrical_power + ringmux_power
        }
    
    def get_combined_wpe(self):
        """
        Get combined wall-plug efficiency for the architecture
        
        Returns:
            float: Combined WPE as percentage
        """
        return self.combined_wpe
    
    def get_device_status(self):
        """
        Get status of all devices in the architecture
        
        Returns:
            dict: Device status information
        """
        ringmux_status = self.ringmux_circuit.get_device_status()
        
        return {
            'total_trl_devices': len(self.trl_devices),
            'operational_trl_count': len(self.operational_indices),
            'redundant_trl_count': len(self.redundant_indices),
            'operational_indices': self.operational_indices,
            'redundant_indices': self.redundant_indices,
            'ringmux_circuit_status': ringmux_status
        }
    
    def activate_redundant_device(self, device_index):
        """
        Activate a redundant TRL device (move from redundant to operational)
        
        Args:
            device_index (int): Index of the TRL device to activate (must be in redundant_indices)
            
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
        Deactivate an operational TRL device (move from operational to redundant)
        
        Args:
            device_index (int): Index of the TRL device to deactivate (must be in operational_indices)
            
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
    
    def get_architecture_summary(self):
        """
        Get comprehensive summary of the architecture
        
        Returns:
            dict: Architecture summary
        """
        device_status = self.get_device_status()
        heat_sources = self.get_heat_sources_breakdown()
        power_consumption = self.get_power_consumption_breakdown()
        
        return {
            'architecture_name': 'TRL 8-Channel 1-Port with RINGMUX',
            'operating_conditions': {
                'temperature_c': self.temperature,
                'current_per_trl_ma': self.current
            },
            'device_status': device_status,
            'performance': {
                # Legacy parameters (for backward compatibility)
                'combined_optical_power': self.combined_optical_power,
                'combined_wpe': self.combined_wpe,
                'combined_heat_load': self.total_combined_heat_load,
                # New total parameters (all components combined)
                'total_optical_power': self.total_optical_power,
                'total_electrical_power': self.total_electrical_power,
                'total_heat_load': self.total_heat_load
            },
            'heat_sources_mw': heat_sources,
            'power_consumption_mw': power_consumption
        }


def main():
    """
    Main function to demonstrate TRL 8-channel 1-port architecture with RINGMUX
    """
    print("TRL 8-Channel 1-Port Architecture with RINGMUX Demo")
    print("=" * 60)
    
    # Create architecture instance
    arch = Trl8ch1ports(temperature=35.0, current=130.0)
    
    # Get comprehensive summary
    summary = arch.get_architecture_summary()
    
    print(f"Architecture: {summary['architecture_name']}")
    print(f"Operating Conditions: {summary['operating_conditions']['temperature_c']}°C, {summary['operating_conditions']['current_per_trl_ma']}mA per TRL")
    print()
    
    print("Device Status:")
    device_status = summary['device_status']
    print(f"  Total TRL Devices: {device_status['total_trl_devices']}")
    print(f"  Operational TRL: {device_status['operational_trl_count']} (indices: {device_status['operational_indices']})")
    print(f"  Redundant TRL: {device_status['redundant_trl_count']} (indices: {device_status['redundant_indices']})")
    
    # Display RINGMUX circuit status
    ringmux_status = device_status['ringmux_circuit_status']
    print(f"  RINGMUX Circuit:")
    print(f"    Total RINGHTR: {ringmux_status['total_ringhtr_devices']}")
    print(f"    Operational RINGHTR: {ringmux_status['operational_ringhtr_count']} (indices: {ringmux_status['operational_indices']})")
    print(f"    Redundant RINGHTR: {ringmux_status['redundant_ringhtr_count']} (indices: {ringmux_status['redundant_indices']})")
    print()
    
    print("Performance Summary:")
    performance = summary['performance']
    print("  Legacy TRL Performance (for backward compatibility):")
    print(f"    Combined Optical Power: {performance['combined_optical_power']:.1f} mW")
    print(f"    Combined Wall-Plug Efficiency: {performance['combined_wpe']:.2f} %")
    print(f"    Combined Heat Load: {performance['combined_heat_load']:.1f} mW")
    print()
    print("  Total Architecture Performance (all components):")
    print(f"    Total Optical Power: {performance['total_optical_power']:.1f} mW")
    print(f"    Total Electrical Power: {performance['total_electrical_power']:.1f} mW")
    print(f"    Total Heat Load: {performance['total_heat_load']:.1f} mW")
    print(f"    Power Balance Check: {performance['total_electrical_power']:.1f} = {performance['total_optical_power']:.1f} + {performance['total_heat_load']:.1f} = {performance['total_optical_power'] + performance['total_heat_load']:.1f} mW")
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
    print("Activating redundant TRL device 8...")
    success = arch.activate_redundant_device(8)
    if success:
        new_summary = arch.get_architecture_summary()
        print(f"  New operational TRL count: {new_summary['device_status']['operational_trl_count']}")
        print(f"  New combined optical power: {new_summary['performance']['combined_optical_power']:.1f} mW")
    else:
        print("  Failed to activate TRL device 8")


if __name__ == "__main__":
    main() 