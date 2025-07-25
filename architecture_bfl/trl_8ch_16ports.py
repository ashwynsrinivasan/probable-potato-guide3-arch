"""
TRL 8-Channel 16-Ports Architecture

This architecture contains 16 trl_8ch_1ports instances:
- Each port has the same optical power as a single trl_8ch_1ports
- Total optical power is the sum across all 16 ports
- Comprehensive power consumption and heat load analysis
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from arch.trl_8ch_1ports import Trl8ch1ports
except ImportError:
    # Fallback for direct import
    from src.arch.trl_8ch_1ports import Trl8ch1ports


class Trl8ch16ports:
    """
    TRL 8-channel 16-ports architecture class
    
    Contains 16 trl_8ch_1ports instances, each representing one port:
    - Each port: 8 operational TRL devices + 2 redundant TRL devices + RINGMUX circuit
    - Total: 128 operational TRL devices + 32 redundant TRL devices + 16 RINGMUX circuits
    - Comprehensive power and thermal analysis across all ports
    """
    
    def __init__(self, temperature: float = 35.0, current: float = 130.0, io_loss_db: float = 1.35):
        """
        Initialize TRL 8-channel 16-ports architecture
        
        Args:
            temperature (float): Operating temperature in Celsius (default: 35.0)
            current (float): Operating current per TRL in mA (default: 130.0)
            io_loss_db (float): Input/Output optical loss in dB (default: 1.35)
        """
        self.temperature = temperature
        self.current = current
        self.io_loss_db = io_loss_db
        self.num_ports = 16
        
        # Initialize 16 trl_8ch_1ports instances (one per port)
        self.port_instances = []
        for i in range(self.num_ports):
            port = Trl8ch1ports(temperature=temperature, current=current, io_loss_db=io_loss_db)
            self.port_instances.append(port)
        
        # Calculate architecture-wide parameters
        self._calculate_architecture_parameters()
    
    def _calculate_architecture_parameters(self):
        """Calculate architecture-wide parameters from all ports"""
        # ==== OPTICAL POWER PER PORT AND TOTAL ====
        # Each port has the same optical power
        self.optical_power_per_port = self.port_instances[0].get_total_optical_power()
        
        # Total optical power across all 16 ports
        self.total_optical_power = self.optical_power_per_port * self.num_ports
        
        # ==== TOTAL ELECTRICAL POWER ====
        self.total_electrical_power = 0.0
        for port in self.port_instances:
            self.total_electrical_power += port.get_total_electrical_power()
        
        # ==== TOTAL HEAT LOAD ====
        self.total_heat_load = 0.0
        for port in self.port_instances:
            self.total_heat_load += port.get_total_heat_load()
        
        # ==== DETAILED POWER CONSUMPTION BREAKDOWN ====
        self.power_consumption_breakdown = self._calculate_power_consumption_breakdown()
        
        # ==== DETAILED HEAT LOAD BREAKDOWN ====
        self.heat_load_breakdown = self._calculate_heat_load_breakdown()
    
    def _calculate_power_consumption_breakdown(self):
        """Calculate detailed power consumption breakdown across all ports"""
        # Get breakdown from one port and multiply by 16
        single_port_breakdown = self.port_instances[0].get_detailed_power_consumption_breakdown()
        
        breakdown = {}
        for component, power in single_port_breakdown.items():
            # Scale by number of ports
            breakdown[f"{component} (16 ports)"] = power * self.num_ports
        
        return breakdown
    
    def _calculate_heat_load_breakdown(self):
        """Calculate detailed heat load breakdown across all ports"""
        # Get breakdown from one port and multiply by 16
        single_port_heat_sources = self.port_instances[0].get_heat_sources_breakdown()
        
        breakdown = {}
        for source, heat in single_port_heat_sources.items():
            if source != 'Total Combined Heat Load':  # Skip total to avoid double counting
                # Scale by number of ports
                breakdown[f"{source} (16 ports)"] = heat * self.num_ports
        
        # Add total
        breakdown['Total Architecture Heat Load'] = self.total_heat_load
        
        return breakdown
    
    def get_optical_power_per_port(self):
        """
        Get optical power per port
        
        Returns:
            float: Optical power per port in mW
        """
        return self.optical_power_per_port
    
    def get_total_optical_power(self):
        """
        Get total optical power across all 16 ports
        
        Returns:
            float: Total optical power in mW
        """
        return self.total_optical_power
    
    def get_total_electrical_power(self):
        """
        Get total electrical power consumption across all ports
        
        Returns:
            float: Total electrical power in mW
        """
        return self.total_electrical_power
    
    def get_total_heat_load(self):
        """
        Get total heat load across all ports
        
        Returns:
            float: Total heat load in mW
        """
        return self.total_heat_load
    
    def get_power_consumption_breakdown(self):
        """
        Get detailed power consumption breakdown
        
        Returns:
            dict: Power consumption breakdown
        """
        return self.power_consumption_breakdown
    
    def get_heat_load_breakdown(self):
        """
        Get detailed heat load breakdown
        
        Returns:
            dict: Heat load breakdown
        """
        return self.heat_load_breakdown
    
    def create_power_consumption_pie_chart(self, save_path=None):
        """
        Create pie chart for power consumption distribution
        
        Args:
            save_path (str): Path to save the chart (optional)
        """
        plt.figure(figsize=(12, 8))
        
        # Get power breakdown (exclude total entries)
        power_data = {k: v for k, v in self.power_consumption_breakdown.items() 
                     if 'total' not in k.lower()}
        
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
        wedges, texts, autotexts = plt.pie(
            power_data.values(), 
            labels=[k.replace(' (16 ports)', '') for k in power_data.keys()], 
            autopct='%1.1f%%',
            colors=colors, 
            startangle=90,
            textprops={'fontsize': 10}
        )
        
        # Enhance the pie chart
        plt.title(f'TRL 16-Port Architecture Power Consumption\n'
                 f'Total: {self.total_electrical_power:.1f}mW across 16 ports '
                 f'({self.temperature}°C, {self.current}mA per TRL)',
                 fontsize=16, fontweight='bold', pad=20)
        
        # Add value annotations
        for i, (label, value) in enumerate(power_data.items()):
            angle = (wedges[i].theta1 + wedges[i].theta2) / 2
            x = 0.7 * np.cos(np.radians(angle))
            y = 0.7 * np.sin(np.radians(angle))
            plt.annotate(f'{value:.1f}mW', xy=(x, y), ha='center', va='center',
                        fontsize=9, fontweight='bold', color='white',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        
        plt.axis('equal')
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Power consumption pie chart saved to: {save_path}")
        else:
            plt.show()
    
    def create_heat_load_pie_chart(self, save_path=None):
        """
        Create pie chart for heat load distribution
        
        Args:
            save_path (str): Path to save the chart (optional)
        """
        plt.figure(figsize=(12, 8))
        
        # Get heat breakdown (exclude total entries)
        heat_data = {k: v for k, v in self.heat_load_breakdown.items() 
                    if 'total' not in k.lower()}
        
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        wedges, texts, autotexts = plt.pie(
            heat_data.values(), 
            labels=[k.replace(' (16 ports)', '') for k in heat_data.keys()], 
            autopct='%1.1f%%',
            colors=colors, 
            startangle=90,
            textprops={'fontsize': 9}
        )
        
        # Enhance the pie chart
        plt.title(f'TRL 16-Port Architecture Heat Load Distribution\n'
                 f'Total: {self.total_heat_load:.1f}mW across 16 ports '
                 f'({self.temperature}°C, {self.current}mA per TRL)',
                 fontsize=16, fontweight='bold', pad=20)
        
        # Add value annotations
        for i, (label, value) in enumerate(heat_data.items()):
            angle = (wedges[i].theta1 + wedges[i].theta2) / 2
            x = 0.7 * np.cos(np.radians(angle))
            y = 0.7 * np.sin(np.radians(angle))
            plt.annotate(f'{value:.1f}mW', xy=(x, y), ha='center', va='center',
                        fontsize=8, fontweight='bold', color='white',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        
        plt.axis('equal')
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Heat load pie chart saved to: {save_path}")
        else:
            plt.show()
    
    def get_architecture_summary(self):
        """
        Get comprehensive summary of the 16-port architecture
        
        Returns:
            dict: Architecture summary
        """
        return {
            'architecture_name': 'TRL 8-Channel 16-Ports',
            'num_ports': self.num_ports,
            'operating_conditions': {
                'temperature_c': self.temperature,
                'current_per_trl_ma': self.current,
                'io_loss_db': self.io_loss_db
            },
            'performance': {
                'optical_power_per_port_mw': self.optical_power_per_port,
                'total_optical_power_mw': self.total_optical_power,
                'total_electrical_power_mw': self.total_electrical_power,
                'total_heat_load_mw': self.total_heat_load,
                'power_balance_check': abs(self.total_electrical_power - 
                                         (self.total_optical_power + self.total_heat_load)) < 1e-3
            },
            'power_consumption_breakdown_mw': self.power_consumption_breakdown,
            'heat_load_breakdown_mw': self.heat_load_breakdown
        }


def main():
    """
    Main function to demonstrate TRL 8-channel 16-ports architecture
    """
    print("TRL 8-Channel 16-Ports Architecture Demo")
    print("=" * 60)
    
    # Create architecture instance
    arch = Trl8ch16ports(temperature=35.0, current=130.0, io_loss_db=1.35)
    
    # Get comprehensive summary
    summary = arch.get_architecture_summary()
    
    print(f"Architecture: {summary['architecture_name']}")
    print(f"Number of Ports: {summary['num_ports']}")
    
    operating_conditions = summary['operating_conditions']
    print(f"Operating Conditions:")
    print(f"  Temperature: {operating_conditions['temperature_c']}°C")
    print(f"  Current per TRL: {operating_conditions['current_per_trl_ma']}mA")
    print(f"  I/O Loss: {operating_conditions['io_loss_db']}dB")
    print()
    
    print("Performance Summary:")
    performance = summary['performance']
    print(f"  Optical Power per Port: {performance['optical_power_per_port_mw']:.1f} mW")
    print(f"  Total Optical Power (16 ports): {performance['total_optical_power_mw']:.1f} mW")
    print(f"  Total Electrical Power: {performance['total_electrical_power_mw']:.1f} mW")
    print(f"  Total Heat Load: {performance['total_heat_load_mw']:.1f} mW")
    print(f"  Power Balance Check: {performance['power_balance_check']} ✓")
    print(f"  Balance: {performance['total_electrical_power_mw']:.1f} = {performance['total_optical_power_mw']:.1f} + {performance['total_heat_load_mw']:.1f} = {performance['total_optical_power_mw'] + performance['total_heat_load_mw']:.1f} mW")
    print()
    
    print("Power Consumption Breakdown:")
    for component, power in summary['power_consumption_breakdown_mw'].items():
        print(f"  {component}: {power:.1f} mW")
    print()
    
    print("Heat Load Breakdown:")
    for source, heat in summary['heat_load_breakdown_mw'].items():
        print(f"  {source}: {heat:.1f} mW")
    print()
    
    # Create pie charts
    print("Creating Power Consumption and Heat Load Pie Charts...")
    
    # Power consumption pie chart
    power_chart_path = '../data/plots/arch/trl_8ch_16ports_power_pie.png'
    arch.create_power_consumption_pie_chart(save_path=power_chart_path)
    
    # Heat load pie chart
    heat_chart_path = '../data/plots/arch/trl_8ch_16ports_heat_pie.png'
    arch.create_heat_load_pie_chart(save_path=heat_chart_path)
    
    print()
    print("Architecture Statistics:")
    print(f"  Total TRL Devices: {16 * 10} (128 operational + 32 redundant)")
    print(f"  Total RINGMUX Circuits: 16")
    print(f"  Total RINGHTR Devices: {16 * 10} (128 operational + 32 redundant)")
    print(f"  Power Density: {performance['total_electrical_power_mw']/16:.1f} mW per port")
    print(f"  Heat Density: {performance['total_heat_load_mw']/16:.1f} mW per port")
    print(f"  Optical Efficiency: {(performance['total_optical_power_mw']/performance['total_electrical_power_mw'])*100:.2f}% overall")


if __name__ == "__main__":
    main() 