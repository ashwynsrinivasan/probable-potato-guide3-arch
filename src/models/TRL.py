import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

class TRL:
    """
    TRL model class for calculating output optical power based on temperature and current
    """
    
    def __init__(self, W_um: float = 2.0):
        """
        Initialize TRL model with temperature-dependent parameters
        
        Args:
            W_um (float): Ridge width in micrometers (default: 2.0)
        """
        # TRL-specific geometric parameters
        self.L_active_mm = 1.1      # Active length in mm
        self.L_active_um = 1100.0   # Active length in micrometers (1.1mm)
        self.L_tapers_um = 0.0      # Taper length in micrometers (no tapers)
        self.W_um = W_um            # Ridge width in micrometers
        
        # Electrical parameters (copied from EuropaSOA)
        self.V_turn_on = 1.05       # Turn-on voltage in V
        
        # Temperature-dependent threshold currents (mA) - reverted to original values
        self.threshold_currents = {
            10: 22.0,   # 10°C threshold
            35: 25.0,   # 35°C threshold  
            45: 28.0,   # 45°C threshold
            55: 32.0,   # 55°C threshold
            80: 42.0    # 80°C threshold
        }
        
        # Calculate slope efficiencies based on specified power points and original thresholds
        
        # For 80C: 100mA -> 8mW, threshold = 42mA
        # slope = 0.275 mW/mA (specified by user)
        
        # For 55C: 100mA -> 17.5mW, threshold = 32mA  
        # slope = 17.5 / (100 - 32) = 17.5 / 68 = 0.257 mW/mA
        
        # For 35C: 100mA -> 22.5mW, threshold = 25mA
        # slope = 22.5 / (100 - 25) = 22.5 / 75 = 0.300 mW/mA
        
        # Temperature-dependent slope efficiencies (mW/mA) - calculated from power requirements
        self.slope_efficiencies = {
            10: 0.320,  # 10°C slope efficiency (extrapolated, higher than 35C)
            35: 0.300,  # 35°C slope efficiency (calculated: 22.5/(100-25))
            45: 0.280,  # 45°C slope efficiency (interpolated)
            55: 0.257,  # 55°C slope efficiency (calculated: 17.5/(100-32))
            80: 0.275   # 80°C slope efficiency (specified by user)
        }
        
        # Temperature-dependent maximum output powers (mW) - no clipping, allow natural progression
        self.max_powers = {
            10: 200.0,  # 10°C max power (high, no artificial limit)
            35: 200.0,  # 35°C max power (high, no artificial limit)
            45: 200.0,  # 45°C max power (high, no artificial limit)
            55: 200.0,  # 55°C max power (high, no artificial limit)
            80: 200.0   # 80°C max power (high, no artificial limit)
        }
        
        # Create polynomial coefficients for smooth interpolation
        self._create_polynomial_coefficients()
    
    def calculate_series_resistance_ohm(self) -> float:
        """
        Calculate series resistance based on TRL geometry (copied from EuropaSOA)
        
        Returns:
            float: Series resistance in ohms
        """
        # Total length for resistance calculation (active + tapers)
        Lt_um = self.L_active_um + self.L_tapers_um
        
        # Check for division by zero
        if self.W_um <= 1e-9 or Lt_um <= 1e-9:
            return float('inf')
        
        # Series resistance formula from EuropaSOA
        Rs_ohm = (4.34 / self.W_um) + (2151 / Lt_um) - 0.992
        
        # Ensure positive resistance
        return Rs_ohm if Rs_ohm > 0 else 1e-3
    
    def get_operating_voltage(self, I_mA: float) -> float:
        """
        Get operating voltage based on current (copied from EuropaSOA)
        
        Args:
            I_mA (float): Current in mA
            
        Returns:
            float: Operating voltage in V
        """
        Rs_ohm = self.calculate_series_resistance_ohm()
        I_Amps = I_mA * 1e-3  # Convert mA to A
        return self.V_turn_on + (I_Amps * Rs_ohm)
    
    def _create_polynomial_coefficients(self):
        """
        Create polynomial coefficients for smooth parameter interpolation
        """
        temps = sorted(self.threshold_currents.keys())
        threshold_values = [self.threshold_currents[t] for t in temps]
        slope_values = [self.slope_efficiencies[t] for t in temps]
        max_power_values = [self.max_powers[t] for t in temps]
        
        # Create polynomial coefficients with best fit (2nd degree)
        self.threshold_coeffs = np.polyfit(temps, threshold_values, deg=2)
        self.slope_coeffs = np.polyfit(temps, slope_values, deg=2)
        self.max_power_coeffs = np.polyfit(temps, max_power_values, deg=2)
    
    def interpolate_parameters(self, temperature):
        """
        Interpolate parameters for any temperature between 10°C and 80°C using polynomial interpolation
        
        Args:
            temperature (float): Temperature in Celsius
            
        Returns:
            tuple: (threshold_current, slope_efficiency, max_power)
        """
        # Clamp temperature to valid range
        temperature = np.clip(temperature, 10, 80)
        
        # Use polynomial interpolation
        threshold_current = float(np.polyval(self.threshold_coeffs, temperature))
        slope_efficiency = float(np.polyval(self.slope_coeffs, temperature))
        max_power = float(np.polyval(self.max_power_coeffs, temperature))
        
        return threshold_current, slope_efficiency, max_power
    
    def calculate_output_power(self, temperature, current):
        """
        Calculate output optical power based on temperature and current
        
        Args:
            temperature (float): Temperature in Celsius
            current (float): Current in mA
            
        Returns:
            float: Output optical power in mW
        """
        # Get temperature-dependent parameters
        threshold_current, slope_efficiency, max_power = self.interpolate_parameters(temperature)
        
        # Calculate output power
        if current <= threshold_current:
            # Below threshold: very low output power
            output_power = 0.001 * current  # Very small slope below threshold
        else:
            # Above threshold: linear relationship with current (no artificial clipping)
            output_power = slope_efficiency * (current - threshold_current)
        
        return max(0, output_power)  # Ensure non-negative output
    
    def get_performance_curve(self, temperature, current_range=None):
        """
        Get performance curve for a given temperature
        
        Args:
            temperature (float): Temperature in Celsius
            current_range (tuple): (start_current, end_current, step) in mA
            
        Returns:
            tuple: (currents, output_powers)
        """
        if current_range is None:
            current_range = (0, 200, 1)
        
        start_current, end_current, step = current_range
        currents = np.arange(start_current, end_current + step, step)
        output_powers = [self.calculate_output_power(temperature, current) for current in currents]
        
        return currents, output_powers
    
    def get_wall_plug_efficiency(self, temperature, current):
        """
        Calculate wall-plug efficiency using actual operating voltage
        
        Args:
            temperature (float): Temperature in Celsius
            current (float): Current in mA
            
        Returns:
            float: Wall-plug efficiency as percentage
        """
        output_power = self.calculate_output_power(temperature, current)
        operating_voltage = self.get_operating_voltage(current)
        input_power = (current / 1000.0) * operating_voltage  # Convert mA to A
        
        if input_power > 0:
            return (output_power / 1000.0) / input_power * 100  # Convert mW to W
        return 0.0
    
    def create_interactive_plot(self, save_path='trl_interactive_plot.html'):
        """
        Create an interactive Plotly plot showing all temperatures simultaneously
        
        Args:
            save_path (str): Path to save the HTML file
        """
        # Available temperatures
        available_temps = [10, 35, 45, 55, 80]
        current_range = (0, 200, 1)
        
        # Create subplots - 3 rows: Pout, I-V, WPE
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=(
                'TRL Output Optical Power vs Current', 
                'TRL Current-Voltage (I-V) Characteristics',
                'TRL Wall-Plug Efficiency vs Current'
            ),
            vertical_spacing=0.08
        )
        
        # Color palette
        colors = px.colors.qualitative.Set1
        
        # Create traces for all temperatures (all visible)
        for i, temp in enumerate(available_temps):
            currents, powers = self.get_performance_curve(temp, current_range)
            
            # Calculate voltages for I-V plot
            voltages = [self.get_operating_voltage(current) for current in currents]
            
            # Calculate WPE from I-V and output power
            wpe_values = []
            for j, current in enumerate(currents):
                if current > 0 and voltages[j] > 0:
                    electrical_power_mW = current * voltages[j]  # P = I * V (mA * V = mW)
                    optical_power_mW = powers[j]
                    if electrical_power_mW > 0:
                        wpe = (optical_power_mW / electrical_power_mW) * 100  # WPE percentage
                    else:
                        wpe = 0.0
                else:
                    wpe = 0.0
                wpe_values.append(wpe)
            
            color = colors[i % len(colors)]
            
            # Power plot (Row 1)
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=powers,
                    mode='lines',
                    name=f'{temp}°C',
                    line=dict(color=color, width=2),
                    legendgroup=f'temp_{temp}',
                    showlegend=True
                ),
                row=1, col=1
            )
            
            # I-V plot (Row 2)
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=voltages,
                    mode='lines',
                    name=f'{temp}°C (I-V)',
                    line=dict(color=color, width=2, dash='dot'),
                    legendgroup=f'temp_{temp}',
                    showlegend=False
                ),
                row=2, col=1
            )
            
            # WPE plot (Row 3)
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=wpe_values,
                    mode='lines',
                    name=f'{temp}°C (WPE)',
                    line=dict(color=color, width=2, dash='dash'),
                    legendgroup=f'temp_{temp}',
                    showlegend=False
                ),
                row=3, col=1
            )
        
        # Update layout (no dropdown needed)
        fig.update_layout(
            title={
                'text': 'TRL Performance Characteristics - All Temperatures',
                'x': 0.5,
                'xanchor': 'center'
            },
            height=1000,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            )
        )
        
        # Update x-axes
        fig.update_xaxes(title_text="Current [mA]", row=1, col=1)
        fig.update_xaxes(title_text="Current [mA]", row=2, col=1)
        fig.update_xaxes(title_text="Current [mA]", row=3, col=1)
        
        # Update y-axes with appropriate ranges
        fig.update_yaxes(title_text="Pout [mW]", range=[0, 40], row=1, col=1)
        fig.update_yaxes(title_text="Voltage [V]", range=[1.0, 2.0], row=2, col=1)
        fig.update_yaxes(title_text="WPE [%]", range=[0, 20], row=3, col=1)
        
        # Add grid to all subplots
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        # Save as HTML file
        pyo.plot(fig, filename=save_path, auto_open=True)
        print(f"Interactive plot saved to: {save_path}")
        
        return fig
    
    def plot_performance_curves(self, temperatures=None, current_range=(0, 200, 1), save_path=None, show_plot=True):
        """
        Plot TRL performance curves for different temperatures (matplotlib version)
        
        Args:
            temperatures (list): List of temperatures to plot (default: [10, 35, 45, 55, 80])
            current_range (tuple): (start_current, end_current, step) in mA
            save_path (str): Path to save the plot (optional)
            show_plot (bool): Whether to display the plot (default: True)
        """
        if temperatures is None:
            temperatures = [10, 35, 45, 55, 80]
        
        colors = ['red', 'blue', 'purple', 'green', 'orange']
        
        plt.figure(figsize=(12, 12))
        
        # Plot Pout vs Current
        plt.subplot(3, 1, 1)
        for i, temp in enumerate(temperatures):
            currents, powers = self.get_performance_curve(temp, current_range)
            color = colors[i % len(colors)]
            plt.plot(currents, powers, color=color, linewidth=2, 
                    label=f'Temperature: {temp}°C')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('Pout [mW]')
        plt.title('TRL Output Optical Power vs Current')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 40)
        plt.xlim(0, 200)
        
        # Plot I-V Characteristics
        plt.subplot(3, 1, 2)
        for i, temp in enumerate(temperatures):
            currents, _ = self.get_performance_curve(temp, current_range)
            voltages = [self.get_operating_voltage(current) for current in currents]
            color = colors[i % len(colors)]
            plt.plot(currents, voltages, color=color, linewidth=2, linestyle=':', 
                    label=f'Temperature: {temp}°C')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('Voltage [V]')
        plt.title('TRL Current-Voltage (I-V) Characteristics')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(1.0, 2.0)
        plt.xlim(0, 200)
        
        # Plot Wall-Plug Efficiency (calculated from I-V and optical power)
        plt.subplot(3, 1, 3)
        for i, temp in enumerate(temperatures):
            currents, powers = self.get_performance_curve(temp, current_range)
            voltages = [self.get_operating_voltage(current) for current in currents]
            
            # Calculate WPE from I-V and output power
            wpe_values = []
            for j, current in enumerate(currents):
                if current > 0 and voltages[j] > 0:
                    electrical_power_mW = current * voltages[j]  # P = I * V (mA * V = mW)
                    optical_power_mW = powers[j]
                    if electrical_power_mW > 0:
                        wpe = (optical_power_mW / electrical_power_mW) * 100  # WPE percentage
                    else:
                        wpe = 0.0
                else:
                    wpe = 0.0
                wpe_values.append(wpe)
            
            color = colors[i % len(colors)]
            plt.plot(currents, wpe_values, color=color, linewidth=2, linestyle='--',
                    label=f'Temperature: {temp}°C')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('WPE [%]')
        plt.title('TRL Wall-Plug Efficiency vs Current (from I-V)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 20)
        plt.xlim(0, 200)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()  # Close the figure to free memory


def main():
    """
    Main function to demonstrate TRL model and create interactive plots
    """
    # Create TRL instance
    trl = TRL()
    
    # Print TRL parameters
    print("TRL Model Parameters:")
    print(f"Active Length: {trl.L_active_mm} mm ({trl.L_active_um} μm)")
    print(f"Taper Length: {trl.L_tapers_um} μm")
    print(f"Ridge Width: {trl.W_um} μm")
    print(f"Turn-on Voltage: {trl.V_turn_on} V")
    print(f"Series Resistance: {trl.calculate_series_resistance_ohm():.3f} Ω")
    print()
    
    # Verify the corrected values with original thresholds
    print("Verification of corrected parameters (with original thresholds):")
    print(f"80°C at 100mA: {trl.calculate_output_power(80, 100):.1f}mW (target: 8.0mW)")
    print(f"80°C at 140mA: {trl.calculate_output_power(80, 140):.1f}mW")
    print(f"55°C at 80mA: {trl.calculate_output_power(55, 80):.1f}mW (target: 12.5mW)")
    print(f"55°C at 100mA: {trl.calculate_output_power(55, 100):.1f}mW (target: 17.5mW)")
    print(f"35°C at 80mA: {trl.calculate_output_power(35, 80):.1f}mW (target: 17.5mW)")
    print(f"35°C at 100mA: {trl.calculate_output_power(35, 100):.1f}mW (target: 22.5mW)")
    print()
    
    # Show operating voltage examples
    print("Operating Voltage Examples:")
    for current in [80, 100, 140]:
        voltage = trl.get_operating_voltage(current)
        print(f"At {current}mA: {voltage:.3f}V")
    print()
    
    # Create interactive plot with dropdown
    print("Generating interactive TRL performance plot with temperature dropdown...")
    trl.create_interactive_plot('trl_interactive_plot.html')
    
    # Create matplotlib plot for comparison (save but don't show)
    print("Generating and saving matplotlib plot...")
    trl.plot_performance_curves(
        temperatures=[10, 35, 45, 55, 80],
        current_range=(0, 200, 1),
        save_path='data/plots/models/trl_performance.png',
        show_plot=False  # Don't display the plot
    )


if __name__ == "__main__":
    main() 