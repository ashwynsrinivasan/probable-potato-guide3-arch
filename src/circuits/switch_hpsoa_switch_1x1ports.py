"""
Switch-HPSOA-Switch 1x1 Ports Circuit

This circuit contains:
- 2 MZISWITCH components (all operational)
- 2 HPSOA components (1 operational, 1 redundant)
"""

import sys
import os

# Add models and circuits to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from models.HPSOA import HPSOA
    from circuits.MZISWITCH_2x2ports import MZISWITCH_2x2ports
except ImportError:
    # Fallback for direct import
    from src.models.HPSOA import HPSOA
    from src.circuits.MZISWITCH_2x2ports import MZISWITCH_2x2ports


class SWITCH_HPSOA_SWITCH_1x1ports:
    """
    Switch-HPSOA-Switch 1x1 ports circuit class
    
    Contains:
    - 2 MZISWITCH components (both operational)
    - 2 HPSOA components with redundancy:
      * HPSOA 0: Operational (powered and contributing to optical output)
      * HPSOA 1: Redundant (not powered, for backup purposes)
    """
    
    def __init__(self, temperature_c: float = 35.0, current_a: float = 0.23, wavelength_nm: float = 1311.0):
        """
        Initialize Switch-HPSOA-Switch 1x1 ports circuit
        
        Args:
            temperature_c (float): Operating temperature in Celsius (default: 35.0)
            current_a (float): Operating current in Amperes (default: 0.23)
            wavelength_nm (float): Operating wavelength in nm (default: 1311)
        """
        self.temperature_c = temperature_c
        self.current_a = current_a
        self.wavelength_nm = wavelength_nm
        
        # Initialize 2 MZISWITCH components (both operational)
        self.mziswitch_input = MZISWITCH_2x2ports()   # Input switch
        self.mziswitch_output = MZISWITCH_2x2ports()  # Output switch
        
        # Initialize 2 HPSOA components
        self.hpsoa_devices = []
        for i in range(2):
            hpsoa = HPSOA()
            self.hpsoa_devices.append(hpsoa)
        
        # Define operational and redundant HPSOA indices
        self.operational_hpsoa_indices = [0]  # HPSOA 0 is operational
        self.redundant_hpsoa_indices = [1]    # HPSOA 1 is redundant
        
        # Calculate combined parameters
        self._calculate_combined_parameters()
    
    def _calculate_combined_parameters(self):
        """Calculate combined parameters for all operational devices"""
        # ==== TOTAL OPTICAL POWER ====
        # Optical power from operational HPSOA devices only
        self.total_optical_power = 0.0
        for i in self.operational_hpsoa_indices:
            self.total_optical_power += self.hpsoa_devices[i].get_total_optical_power(
                self.temperature_c, self.current_a, self.wavelength_nm
            )
        # MZISWITCH components don't produce optical power
        
        # ==== TOTAL ELECTRICAL POWER ====
        # Electrical power from operational HPSOA devices
        self.total_electrical_power = 0.0
        for i in self.operational_hpsoa_indices:
            self.total_electrical_power += self.hpsoa_devices[i].get_total_electrical_power(
                self.temperature_c, self.current_a, self.wavelength_nm
            )
        # Add MZISWITCH electrical power
        self.total_electrical_power += self.mziswitch_input.get_total_electrical_power()
        self.total_electrical_power += self.mziswitch_output.get_total_electrical_power()
        
        # ==== TOTAL HEAT LOAD ====
        # Heat load from operational HPSOA devices
        self.total_heat_load = 0.0
        for i in self.operational_hpsoa_indices:
            self.total_heat_load += self.hpsoa_devices[i].get_total_heat_load(
                self.temperature_c, self.current_a, self.wavelength_nm
            )
        # Add MZISWITCH heat loads
        self.total_heat_load += self.mziswitch_input.get_total_heat_load()
        self.total_heat_load += self.mziswitch_output.get_total_heat_load()
    
    def get_total_optical_power(self):
        """
        Get total optical power from operational HPSOA devices
        
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
    
    def get_device_status(self):
        """
        Get status of all devices in the circuit
        
        Returns:
            dict: Device status information
        """
        return {
            'total_mziswitch_devices': 2,
            'operational_mziswitch_count': 2,
            'total_hpsoa_devices': len(self.hpsoa_devices),
            'operational_hpsoa_count': len(self.operational_hpsoa_indices),
            'redundant_hpsoa_count': len(self.redundant_hpsoa_indices),
            'operational_hpsoa_indices': self.operational_hpsoa_indices,
            'redundant_hpsoa_indices': self.redundant_hpsoa_indices
        }
    
    def get_heat_sources_breakdown(self):
        """
        Get detailed breakdown of heat sources from operational devices
        
        Returns:
            dict: Heat sources breakdown
        """
        # HPSOA heat loads (operational only)
        hpsoa_heat_load = 0.0
        for i in self.operational_hpsoa_indices:
            hpsoa_heat_load += self.hpsoa_devices[i].get_total_heat_load(
                self.temperature_c, self.current_a, self.wavelength_nm
            )
        
        return {
            'HPSOA Heat Load (operational devices)': hpsoa_heat_load,
            'Input MZISWITCH Heat Load': self.mziswitch_input.get_total_heat_load(),
            'Output MZISWITCH Heat Load': self.mziswitch_output.get_total_heat_load(),
            'Total Circuit Heat Load': self.total_heat_load
        }
    
    def get_power_consumption_breakdown(self):
        """
        Get power consumption breakdown for operational devices
        
        Returns:
            dict: Power consumption breakdown
        """
        # HPSOA electrical power (operational only)
        hpsoa_electrical_power = 0.0
        for i in self.operational_hpsoa_indices:
            hpsoa_electrical_power += self.hpsoa_devices[i].get_total_electrical_power(
                self.temperature_c, self.current_a, self.wavelength_nm
            )
        
        return {
            'HPSOA Power (operational devices)': hpsoa_electrical_power,
            'Input MZISWITCH Power': self.mziswitch_input.get_total_electrical_power(),
            'Output MZISWITCH Power': self.mziswitch_output.get_total_electrical_power(),
            'Total Circuit Power': self.total_electrical_power
        }
    
    def simulate_hpsoa_failure(self, hpsoa_index):
        """
        Simulate HPSOA device failure and automatically activate redundancy
        
        Args:
            hpsoa_index (int): Index of the operational HPSOA device that failed
            
        Returns:
            dict: Failure handling results
        """
        if hpsoa_index not in self.operational_hpsoa_indices:
            return {
                'success': False,
                'message': f'HPSOA device {hpsoa_index} is not operational, cannot fail',
                'redundancy_activated': False
            }
        
        # Check if redundant HPSOA devices are available
        if len(self.redundant_hpsoa_indices) == 0:
            return {
                'success': False,
                'message': f'HPSOA device {hpsoa_index} failed but no redundant HPSOA devices available',
                'redundancy_activated': False,
                'failed_device': hpsoa_index,
                'system_degraded': True
            }
        
        # Store old performance for comparison
        old_optical_power = self.total_optical_power
        old_electrical_power = self.total_electrical_power
        old_heat_load = self.total_heat_load
        
        # Remove failed HPSOA device from operational list
        self.operational_hpsoa_indices.remove(hpsoa_index)
        
        # Activate first available redundant HPSOA device
        redundant_hpsoa = self.redundant_hpsoa_indices.pop(0)
        self.operational_hpsoa_indices.append(redundant_hpsoa)
        
        # Recalculate combined parameters
        self._calculate_combined_parameters()
        
        return {
            'success': True,
            'message': f'HPSOA device {hpsoa_index} failed, activated redundant HPSOA device {redundant_hpsoa}',
            'redundancy_activated': True,
            'failed_device': hpsoa_index,
            'activated_device': redundant_hpsoa,
            'performance_maintained': {
                'optical_power': abs(self.total_optical_power - old_optical_power) < 1e-6,
                'electrical_power': abs(self.total_electrical_power - old_electrical_power) < 1e-6,
                'heat_load': abs(self.total_heat_load - old_heat_load) < 1e-6
            },
            'new_operational_count': len(self.operational_hpsoa_indices),
            'remaining_redundancy': len(self.redundant_hpsoa_indices)
        }
    
    def get_reliability_status(self):
        """
        Get reliability and redundancy status of the circuit
        
        Returns:
            dict: Reliability status information
        """
        total_hpsoa_devices = len(self.hpsoa_devices)
        operational_hpsoa_count = len(self.operational_hpsoa_indices)
        redundant_hpsoa_count = len(self.redundant_hpsoa_indices)
        
        # Calculate reliability metrics
        operational_ratio = operational_hpsoa_count / total_hpsoa_devices
        redundancy_ratio = redundant_hpsoa_count / total_hpsoa_devices
        
        # Determine system status
        if redundant_hpsoa_count >= 1:
            system_status = "Protected - HPSOA Redundancy Available"
        else:
            system_status = "At Risk - No HPSOA Redundancy"
        
        return {
            'total_mziswitch_devices': 2,
            'total_hpsoa_devices': total_hpsoa_devices,
            'operational_hpsoa_devices': operational_hpsoa_count,
            'redundant_hpsoa_devices': redundant_hpsoa_count,
            'operational_ratio': operational_ratio,
            'redundancy_ratio': redundancy_ratio,
            'system_status': system_status,
            'can_handle_hpsoa_failures': redundant_hpsoa_count > 0,
            'max_hpsoa_failures_tolerable': redundant_hpsoa_count
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
        reliability = self.get_reliability_status()
        
        return {
            'circuit_name': 'Switch-HPSOA-Switch 1x1 Ports',
            'operating_conditions': {
                'temperature_c': self.temperature_c,
                'current_a': self.current_a,
                'wavelength_nm': self.wavelength_nm
            },
            'device_status': device_status,
            'performance': {
                'total_optical_power_mw': self.total_optical_power,
                'total_electrical_power_mw': self.total_electrical_power,
                'total_heat_load_mw': self.total_heat_load
            },
            'heat_sources_mw': heat_sources,
            'power_consumption_mw': power_consumption,
            'reliability': reliability
        }


def main():
    """
    Main function to demonstrate Switch-HPSOA-Switch 1x1 ports circuit
    """
    print("Switch-HPSOA-Switch 1x1 Ports Circuit Demo")
    print("=" * 50)
    
    # Create circuit instance
    circuit = SWITCH_HPSOA_SWITCH_1x1ports(temperature_c=35.0, current_a=0.23, wavelength_nm=1311.0)
    
    # Get comprehensive summary
    summary = circuit.get_circuit_summary()
    
    print(f"Circuit: {summary['circuit_name']}")
    print(f"Operating Conditions:")
    conditions = summary['operating_conditions']
    print(f"  Temperature: {conditions['temperature_c']}°C")
    print(f"  Current: {conditions['current_a']}A")
    print(f"  Wavelength: {conditions['wavelength_nm']}nm")
    print()
    
    print("Device Status:")
    device_status = summary['device_status']
    print(f"  MZISWITCH Devices: {device_status['total_mziswitch_devices']} (all operational)")
    print(f"  HPSOA Devices: {device_status['total_hpsoa_devices']}")
    print(f"    Operational HPSOA: {device_status['operational_hpsoa_count']} (indices: {device_status['operational_hpsoa_indices']})")
    print(f"    Redundant HPSOA: {device_status['redundant_hpsoa_count']} (indices: {device_status['redundant_hpsoa_indices']})")
    print()
    
    print("Performance Summary:")
    performance = summary['performance']
    print(f"  Total Optical Power: {performance['total_optical_power_mw']:.1f} mW")
    print(f"  Total Electrical Power: {performance['total_electrical_power_mw']:.1f} mW")
    print(f"  Total Heat Load: {performance['total_heat_load_mw']:.1f} mW")
    print(f"  Power Balance: {performance['total_electrical_power_mw']:.1f} = {performance['total_optical_power_mw']:.1f} + {performance['total_heat_load_mw']:.1f} = {performance['total_optical_power_mw'] + performance['total_heat_load_mw']:.1f} mW")
    print()
    
    print("Heat Sources Breakdown:")
    for source, value in summary['heat_sources_mw'].items():
        print(f"  {source}: {value:.1f} mW")
    print()
    
    print("Power Consumption Breakdown:")
    for component, value in summary['power_consumption_mw'].items():
        print(f"  {component}: {value:.1f} mW")
    print()
    
    # Show reliability status
    reliability = summary['reliability']
    print("Reliability Status:")
    print(f"  System Status: {reliability['system_status']}")
    print(f"  Can handle HPSOA failures: {reliability['can_handle_hpsoa_failures']}")
    print(f"  Max HPSOA failures tolerable: {reliability['max_hpsoa_failures_tolerable']}")
    print()
    
    # Demonstrate HPSOA failure and redundancy activation
    print("HPSOA Failure and Redundancy Activation Demo:")
    print("Simulating failure of operational HPSOA device 0...")
    failure_result = circuit.simulate_hpsoa_failure(0)
    
    if failure_result['success']:
        print(f"  ✓ {failure_result['message']}")
        print(f"  Performance maintained:")
        perf = failure_result['performance_maintained']
        print(f"    Optical power: {perf['optical_power']}")
        print(f"    Electrical power: {perf['electrical_power']}")
        print(f"    Heat load: {perf['heat_load']}")
        print(f"  New operational HPSOA count: {failure_result['new_operational_count']}")
        print(f"  Remaining HPSOA redundancy: {failure_result['remaining_redundancy']}")
    else:
        print(f"  ✗ {failure_result['message']}")
    
    # Check reliability status after failure
    reliability_after = circuit.get_reliability_status()
    print(f"  System status after failure: {reliability_after['system_status']}")


if __name__ == "__main__":
    main() 