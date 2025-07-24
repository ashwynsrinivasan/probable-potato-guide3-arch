import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

class DFB:
    """
    DFB (Distributed Feedback Laser) model class for calculating output optical power based on temperature and current
    """
    
    def __init__(self, W_um: float = 2.0, temperature: float = 35.0, current: float = 130.0):
        """
        Initialize DFB model with temperature-dependent parameters
        
        Args:
            W_um (float): Ridge width in micrometers (default: 2.0)
            temperature (float): Operating temperature in Celsius (default: 35.0)
            current (float): Operating current in mA (default: 130.0)
        """
        # Operating parameters
        self.temperature = temperature
        self.current = current
        
        # DFB-specific geometric parameters
        self.L_active_mm = 1.1      # Active length in mm
        self.L_active_um = 1100.0   # Active length in micrometers (1.1mm)
        self.L_tapers_um = 0.0      # Taper length in micrometers (no tapers)
        self.W_um = W_um            # Ridge width in micrometers
        
        # Electrical parameters (copied from TRL)
        self.V_turn_on = 1.05       # Turn-on voltage in V
        
        # DFB has no heaters (unlike TRL)
        
        # Temperature-dependent threshold currents (mA) - based on image analysis
        self.threshold_currents = {
            10: 50.0,   # 10°C threshold (blue line starts around 50mA)
            35: 80.0,   # 35°C threshold (red line starts around 80mA)
            80: 120.0   # 80°C threshold (green line starts around 120mA)
        }
        
        # Temperature-dependent slope efficiencies (mW/mA) - based on image analysis
        # From the image: all lines appear to have similar slopes, approximately 0.2 mW/mA
        self.slope_efficiencies = {
            10: 0.20,   # 10°C slope efficiency
            35: 0.20,   # 35°C slope efficiency
            80: 0.18    # 80°C slope efficiency (slightly lower at high temp)
        }
        
        # Temperature-dependent maximum output powers (mW) - no clipping, allow natural progression
        self.max_powers = {
            10: 200.0,  # 10°C max power
            35: 200.0,  # 35°C max power
            80: 200.0   # 80°C max power
        }
        
        # Create polynomial coefficients for smooth interpolation
        self._create_polynomial_coefficients()
    
    def calculate_series_resistance_ohm(self) -> float:
        """
        Calculate series resistance based on DFB geometry (copied from TRL)
        
        Returns:
            float: Series resistance in ohms
        """
        # Total length for resistance calculation (active + tapers)
        Lt_um = self.L_active_um + self.L_tapers_um
        
        # Check for division by zero
        if self.W_um <= 1e-9 or Lt_um <= 1e-9:
            return float('inf')
        
        # Series resistance formula from TRL/EuropaSOA
        Rs_ohm = (4.34 / self.W_um) + (2151 / Lt_um) - 0.992
        
        # Ensure positive resistance
        return Rs_ohm if Rs_ohm > 0 else 1e-3
    
    def get_operating_voltage(self, I_mA: float) -> float:
        """
        Get operating voltage based on current (copied from TRL)
        
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
            # Above threshold: linear relationship with current
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
            current_range = (0, 300, 1)  # Extended range for DFB
        
        start_current, end_current, step = current_range
        currents = np.arange(start_current, end_current + step, step)
        output_powers = [self.calculate_output_power(temperature, current) for current in currents]
        
        return currents, output_powers
    
    def get_dfb_wpe(self, temperature, current):
        """
        Calculate DFB wall-plug efficiency using actual operating voltage
        
        Args:
            temperature (float): Temperature in Celsius
            current (float): Current in mA
            
        Returns:
            float: DFB wall-plug efficiency as percentage
        """
        output_power = self.calculate_output_power(temperature, current)
        operating_voltage = self.get_operating_voltage(current)
        input_power = (current / 1000.0) * operating_voltage  # Convert mA to A
        
        if input_power > 0:
            return (output_power / 1000.0) / input_power * 100  # Convert mW to W
        return 0.0
    
    def create_interactive_plot(self, save_path=None):
        """
        Create an interactive Plotly plot showing all temperatures simultaneously
        
        Args:
            save_path (str): Path to save the HTML file (optional, not saved by default)
        """
        # Available temperatures (only 3 for DFB based on image)
        available_temps = [10, 35, 80]
        current_range = (0, 300, 1)  # Extended range for DFB
        
        # Operating point for annotations
        annotation_current = 130  # mA
        annotation_temp = 35      # °C
        
        # Create subplots - 2x2 grid: Pout, I-V, DFB WPE, Power Consumption
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'DFB Output Optical Power vs Current', 
                'DFB Current-Voltage (I-V) Characteristics',
                'DFB Wall-Plug Efficiency vs Current',
                f'DFB Performance Summary (at {annotation_current}mA, {annotation_temp}°C)'
            ),
            specs=[[{"type": "scatter"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "table"}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # Color palette
        colors = ['blue', 'red', 'green']  # Match image colors
        
        # Create traces for all temperatures (all visible)
        for i, temp in enumerate(available_temps):
            currents, powers = self.get_performance_curve(temp, current_range)
            
            # Calculate voltages for I-V plot
            voltages = [self.get_operating_voltage(current) for current in currents]
            
            # Calculate DFB WPE
            dfb_wpe_values = [self.get_dfb_wpe(temp, current) for current in currents]
            
            color = colors[i]
            
            # Power plot (Row 1, Col 1) - Solid lines
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=powers,
                    mode='lines',
                    name=f'{temp}°C',
                    line=dict(color=color, width=3),
                    legendgroup=f'temp_{temp}',
                    showlegend=True
                ),
                row=1, col=1
            )
            
            # I-V plot (Row 1, Col 2) - Solid lines
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=voltages,
                    mode='lines',
                    name=f'{temp}°C (I-V)',
                    line=dict(color=color, width=3),
                    legendgroup=f'temp_{temp}',
                    showlegend=False
                ),
                row=1, col=2
            )
            
            # DFB WPE plot (Row 2, Col 1) - Solid lines
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=dfb_wpe_values,
                    mode='lines',
                    name=f'{temp}°C (WPE)',
                    line=dict(color=color, width=3),
                    legendgroup=f'temp_{temp}',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Add annotations at 130mA, 35°C
        annotation_power = self.calculate_output_power(annotation_temp, annotation_current)
        annotation_voltage = self.get_operating_voltage(annotation_current)
        annotation_wpe = self.get_dfb_wpe(annotation_temp, annotation_current)
        
        # Annotation for Power plot
        fig.add_annotation(
            x=annotation_current, y=annotation_power,
            text=f"{annotation_power:.1f}mW<br>@{annotation_current}mA, {annotation_temp}°C",
            showarrow=True, arrowhead=2, arrowcolor="red", arrowwidth=2,
            bgcolor="white", bordercolor="red", borderwidth=2,
            row=1, col=1
        )
        
        # Annotation for I-V plot
        fig.add_annotation(
            x=annotation_current, y=annotation_voltage,
            text=f"{annotation_voltage:.3f}V<br>@{annotation_current}mA",
            showarrow=True, arrowhead=2, arrowcolor="red", arrowwidth=2,
            bgcolor="white", bordercolor="red", borderwidth=2,
            row=1, col=2
        )
        
        # Annotation for WPE plot
        fig.add_annotation(
            x=annotation_current, y=annotation_wpe,
            text=f"{annotation_wpe:.2f}%<br>@{annotation_current}mA, {annotation_temp}°C",
            showarrow=True, arrowhead=2, arrowcolor="red", arrowwidth=2,
            bgcolor="white", bordercolor="red", borderwidth=2,
            row=2, col=1
        )
        
        # Add performance summary table
        electrical_power = annotation_current * self.get_operating_voltage(annotation_current)
        fig.add_trace(
            go.Table(
                header=dict(values=['Parameter', 'Value', 'Unit'],
                           fill_color='lightblue',
                           align='left'),
                cells=dict(values=[
                    ['Operating Current', 'Operating Temperature', 'Optical Output', 'Operating Voltage', 'Electrical Power', 'Wall-Plug Efficiency'],
                    [f'{annotation_current}', f'{annotation_temp}', f'{annotation_power:.1f}', f'{annotation_voltage:.3f}', f'{electrical_power:.1f}', f'{annotation_wpe:.2f}'],
                    ['mA', '°C', 'mW', 'V', 'mW', '%']
                ],
                fill_color='white',
                align='left')
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title={
                'text': f'DFB Performance Characteristics - Annotated at {annotation_current}mA, {annotation_temp}°C',
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
        fig.update_xaxes(title_text="Current [mA]", row=1, col=2)
        fig.update_xaxes(title_text="Current [mA]", row=2, col=1)
        
        # Update y-axes with appropriate ranges
        fig.update_yaxes(title_text="Pout [mW]", range=[0, 40], row=1, col=1)
        fig.update_yaxes(title_text="Voltage [V]", range=[1.0, 2.5], row=1, col=2)
        fig.update_yaxes(title_text="WPE [%]", range=[0, 25], row=2, col=1)
        
        # Add grid to scatter plots
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        # Only save HTML file if save_path is provided
        if save_path:
            pyo.plot(fig, filename=save_path, auto_open=True)
            print(f"Interactive plot saved to: {save_path}")
        else:
            fig.show()
        
        return fig
    
    def plot_performance_curves(self, temperatures=None, current_range=(0, 300, 1), save_path=None, show_plot=True):
        """
        Plot DFB performance curves for different temperatures (matplotlib version)
        
        Args:
            temperatures (list): List of temperatures to plot (default: [10, 35, 80])
            current_range (tuple): (start_current, end_current, step) in mA
            save_path (str): Path to save the plot (optional)
            show_plot (bool): Whether to display the plot (default: True)
        """
        if temperatures is None:
            temperatures = [10, 35, 80]
        
        colors = ['blue', 'red', 'green']  # Match image colors
        
        # Operating point for annotations
        annotation_current = 130  # mA
        annotation_temp = 35      # °C
        
        plt.figure(figsize=(15, 10))
        
        # Plot Pout vs Current
        plt.subplot(2, 2, 1)
        for i, temp in enumerate(temperatures):
            currents, powers = self.get_performance_curve(temp, current_range)
            color = colors[i % len(colors)]
            plt.plot(currents, powers, color=color, linewidth=3, 
                    label=f'Temperature: {temp}°C')
        
        # Add annotation at 130mA, 35°C
        annotation_power = self.calculate_output_power(annotation_temp, annotation_current)
        plt.annotate(f'{annotation_power:.1f}mW\n@{annotation_current}mA, {annotation_temp}°C',
                    xy=(annotation_current, annotation_power), xytext=(annotation_current+30, annotation_power+5),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red"),
                    fontsize=10, ha='left')
        
        plt.xlabel('DFB Current [mA]')
        plt.ylabel('Power - One Side [mW]')
        plt.title('DFB Output Optical Power vs Current')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 40)
        plt.xlim(0, 300)
        
        # Plot I-V Characteristics
        plt.subplot(2, 2, 2)
        for i, temp in enumerate(temperatures):
            currents, _ = self.get_performance_curve(temp, current_range)
            voltages = [self.get_operating_voltage(current) for current in currents]
            color = colors[i % len(colors)]
            plt.plot(currents, voltages, color=color, linewidth=3, 
                    label=f'Temperature: {temp}°C')
        
        # Add annotation at 130mA
        annotation_voltage = self.get_operating_voltage(annotation_current)
        plt.annotate(f'{annotation_voltage:.3f}V\n@{annotation_current}mA',
                    xy=(annotation_current, annotation_voltage), xytext=(annotation_current+30, annotation_voltage+0.1),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red"),
                    fontsize=10, ha='left')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('Voltage [V]')
        plt.title('DFB Current-Voltage (I-V) Characteristics')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(1.0, 2.5)
        plt.xlim(0, 300)
        
        # Plot DFB Wall-Plug Efficiency
        plt.subplot(2, 2, 3)
        for i, temp in enumerate(temperatures):
            currents, _ = self.get_performance_curve(temp, current_range)
            dfb_wpe_values = [self.get_dfb_wpe(temp, current) for current in currents]
            
            color = colors[i % len(colors)]
            plt.plot(currents, dfb_wpe_values, color=color, linewidth=3,
                    label=f'Temperature: {temp}°C')
        
        # Add annotation at 130mA, 35°C
        annotation_wpe = self.get_dfb_wpe(annotation_temp, annotation_current)
        plt.annotate(f'{annotation_wpe:.2f}%\n@{annotation_current}mA, {annotation_temp}°C',
                    xy=(annotation_current, annotation_wpe), xytext=(annotation_current+30, annotation_wpe+2),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red"),
                    fontsize=10, ha='left')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('WPE [%]')
        plt.title('DFB Wall-Plug Efficiency vs Current')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 25)
        plt.xlim(0, 300)
        
        # Plot Performance Summary Table
        plt.subplot(2, 2, 4)
        plt.axis('off')
        
        # Create performance summary
        electrical_power = annotation_current * self.get_operating_voltage(annotation_current)
        summary_data = [
            ['Operating Current', f'{annotation_current} mA'],
            ['Operating Temperature', f'{annotation_temp} °C'],
            ['Optical Output Power', f'{annotation_power:.1f} mW'],
            ['Operating Voltage', f'{annotation_voltage:.3f} V'],
            ['Electrical Power', f'{electrical_power:.1f} mW'],
            ['Wall-Plug Efficiency', f'{annotation_wpe:.2f} %'],
            ['Threshold Current (35°C)', f'{self.threshold_currents[35]:.0f} mA'],
            ['Slope Efficiency (35°C)', f'{self.slope_efficiencies[35]:.3f} mW/mA']
        ]
        
        table = plt.table(cellText=summary_data,
                         colLabels=['Parameter', 'Value'],
                         cellLoc='left',
                         loc='center',
                         colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        
        # Style the table
        for i in range(len(summary_data) + 1):
            for j in range(2):
                cell = table[(i, j)]
                if i == 0:  # Header
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
        
        plt.title(f'DFB Performance Summary\n(at {annotation_current}mA, {annotation_temp}°C)', pad=20)
        
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
    Main function to demonstrate DFB model and create interactive plots
    """
    # Create DFB instance with default parameters (130mA, 35°C)
    dfb = DFB()
    
    # Print DFB parameters
    print("DFB Model Parameters:")
    print(f"Default Operating Point: {dfb.current}mA, {dfb.temperature}°C")
    print(f"Active Length: {dfb.L_active_mm} mm ({dfb.L_active_um} μm)")
    print(f"Taper Length: {dfb.L_tapers_um} μm")
    print(f"Ridge Width: {dfb.W_um} μm")
    print(f"Turn-on Voltage: {dfb.V_turn_on} V")
    print(f"Series Resistance: {dfb.calculate_series_resistance_ohm():.3f} Ω")
    print()
    
    # Print threshold and slope parameters
    print("DFB Characteristics:")
    for temp in [10, 35, 80]:
        print(f"{temp}°C - Threshold: {dfb.threshold_currents[temp]:.0f}mA, Slope: {dfb.slope_efficiencies[temp]:.3f}mW/mA")
    print()
    
    # Show performance analysis at default operating point (130mA, 35°C)
    print(f"Performance Analysis at {dfb.current}mA, {dfb.temperature}°C:")
    optical_output = dfb.calculate_output_power(dfb.temperature, dfb.current)
    operating_voltage = dfb.get_operating_voltage(dfb.current)
    electrical_power = dfb.current * operating_voltage
    wpe = dfb.get_dfb_wpe(dfb.temperature, dfb.current)
    
    print(f"Optical Output Power: {optical_output:.1f}mW")
    print(f"Operating Voltage: {operating_voltage:.3f}V")
    print(f"Electrical Power: {electrical_power:.1f}mW")
    print(f"Wall-Plug Efficiency: {wpe:.2f}%")
    print()
    
    # Show operating voltage examples
    print("Operating Voltage Examples:")
    for current in [100, 150, 200]:
        voltage = dfb.get_operating_voltage(current)
        print(f"At {current}mA: {voltage:.3f}V")
    print()
    
    # Create interactive plot (no HTML save by default)
    print("Generating interactive DFB performance plot...")
    dfb.create_interactive_plot()
    
    # Create matplotlib plot for comparison (save but don't show)
    print("Generating and saving matplotlib plot...")
    
    # Determine the correct path for saving plots
    import os
    current_dir = os.getcwd()
    if current_dir.endswith('src/models'):
        # Running from src/models directory
        save_path = '../../data/plots/models/dfb_performance.png'
    else:
        # Running from project root
        save_path = 'data/plots/models/dfb_performance.png'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    dfb.plot_performance_curves(
        temperatures=[10, 35, 80],
        current_range=(0, 300, 1),
        save_path=save_path,
        show_plot=False  # Don't display the plot
    )


if __name__ == "__main__":
    main() 