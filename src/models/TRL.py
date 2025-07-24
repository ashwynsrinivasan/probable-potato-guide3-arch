import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

# Handle imports for both direct execution and module import
try:
    from .RINGHTR import RINGHTR
    from .PHASEHTR import PHASEHTR
except ImportError:
    from RINGHTR import RINGHTR
    from PHASEHTR import PHASEHTR

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
        
        # Initialize heater objects
        self.ring_htr_1 = RINGHTR()  # First ring heater
        self.ring_htr_2 = RINGHTR()  # Second ring heater
        self.phase_htr = PHASEHTR()  # Phase heater
        
        # Calculate heater heat loads
        self.trl_heater_heat_load = (
            self.ring_htr_1.ring_htr_heat_load + 
            self.ring_htr_2.ring_htr_heat_load + 
            self.phase_htr.phase_htr_heat_load
        )
        
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
    
    def get_total_wpe(self, temperature, current):
        """
        Calculate total wall-plug efficiency considering TRL gain power and all heater power consumption
        
        Args:
            temperature (float): Temperature in Celsius
            current (float): Current in mA
            
        Returns:
            float: Total wall-plug efficiency as percentage
        """
        # Optical output power from TRL gain
        optical_output_power = self.calculate_output_power(temperature, current)  # mW
        
        # Electrical power consumption from TRL gain
        trl_operating_voltage = self.get_operating_voltage(current)
        trl_electrical_power_mw = current * trl_operating_voltage  # P = I * V (mA * V = mW)
        
        # Total electrical power consumption (TRL + all heaters)
        total_electrical_power_mw = (
            trl_electrical_power_mw + 
            self.ring_htr_1.get_power_consumption() + 
            self.ring_htr_2.get_power_consumption() + 
            self.phase_htr.get_power_consumption()
        )
        
        # Total WPE = Optical Output Power / Total Electrical Power
        if total_electrical_power_mw > 0:
            return (optical_output_power / total_electrical_power_mw) * 100  # Percentage
        return 0.0
    
    def get_trl_gain_wpe(self, temperature, current):
        """
        Calculate TRL gain wall-plug efficiency using actual operating voltage
        
        Args:
            temperature (float): Temperature in Celsius
            current (float): Current in mA
            
        Returns:
            float: TRL gain wall-plug efficiency as percentage
        """
        output_power = self.calculate_output_power(temperature, current)
        operating_voltage = self.get_operating_voltage(current)
        input_power = (current / 1000.0) * operating_voltage  # Convert mA to A
        
        if input_power > 0:
            return (output_power / 1000.0) / input_power * 100  # Convert mW to W
        return 0.0
    
    def get_trl_gain_heat_load(self, temperature, current):
        """
        Calculate TRL gain heat load (remaining electrical power not converted to optical)
        
        Args:
            temperature (float): Temperature in Celsius
            current (float): Current in mA
            
        Returns:
            float: TRL gain heat load in mW
        """
        output_power = self.calculate_output_power(temperature, current)
        operating_voltage = self.get_operating_voltage(current)
        electrical_power_mw = current * operating_voltage  # P = I * V (mA * V = mW)
        
        # Heat load is electrical power minus optical power output
        heat_load = electrical_power_mw - output_power
        return max(0, heat_load)  # Ensure non-negative
    
    def get_trl_heat_load(self, temperature, current):
        """
        Calculate total TRL heat load (gain heat load + heater heat load)
        
        Args:
            temperature (float): Temperature in Celsius
            current (float): Current in mA
            
        Returns:
            float: Total TRL heat load in mW
        """
        gain_heat_load = self.get_trl_gain_heat_load(temperature, current)
        return gain_heat_load + self.trl_heater_heat_load
    
    def get_heat_sources(self, temperature, current):
        """
        Get breakdown of all heat sources
        
        Args:
            temperature (float): Temperature in Celsius
            current (float): Current in mA
            
        Returns:
            dict: Dictionary with heat source breakdown
        """
        return {
            'TRL Gain Heat Load': self.get_trl_gain_heat_load(temperature, current),
            'Ring Heater 1': self.ring_htr_1.ring_htr_heat_load,
            'Ring Heater 2': self.ring_htr_2.ring_htr_heat_load,
            'Phase Heater': self.phase_htr.phase_htr_heat_load
        }
    
    def create_interactive_plot(self, save_path='trl_interactive_plot.html'):
        """
        Create an interactive Plotly plot showing all temperatures simultaneously with heat source pie chart
        
        Args:
            save_path (str): Path to save the HTML file
        """
        # Available temperatures
        available_temps = [10, 35, 45, 55, 80]
        current_range = (0, 200, 1)
        
        # Operating point for annotations and pie charts
        annotation_current = 130  # mA
        annotation_temp = 35      # °C
        
        # Create subplots - 2x3 grid: Pout, I-V, TRL Gain WPE, Total WPE, Heat Sources Pie Chart, Power Consumption
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                'TRL Output Optical Power vs Current', 
                'TRL Current-Voltage (I-V) Characteristics',
                'TRL Gain Wall-Plug Efficiency vs Current',
                'TRL Total Wall-Plug Efficiency vs Current',
                f'Heat Sources Distribution (at {annotation_current}mA, {annotation_temp}°C)',
                f'Power Consumption Breakdown (at {annotation_current}mA, {annotation_temp}°C)'
            ),
            specs=[[{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "pie"}, {"type": "pie"}]],
            vertical_spacing=0.12,
            horizontal_spacing=0.08
        )
        
        # Color palette
        colors = px.colors.qualitative.Set1
        
        # Create traces for all temperatures (all visible)
        for i, temp in enumerate(available_temps):
            currents, powers = self.get_performance_curve(temp, current_range)
            
            # Calculate voltages for I-V plot
            voltages = [self.get_operating_voltage(current) for current in currents]
            
            # Calculate TRL Gain WPE and Total WPE
            trl_gain_wpe_values = [self.get_trl_gain_wpe(temp, current) for current in currents]
            total_wpe_values = [self.get_total_wpe(temp, current) for current in currents]
            
            color = colors[i % len(colors)]
            
            # Power plot (Row 1, Col 1) - Solid lines
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
            
            # I-V plot (Row 1, Col 2) - Solid lines
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=voltages,
                    mode='lines',
                    name=f'{temp}°C (I-V)',
                    line=dict(color=color, width=2),
                    legendgroup=f'temp_{temp}',
                    showlegend=False
                ),
                row=1, col=2
            )
            
            # TRL Gain WPE plot (Row 1, Col 3) - Solid lines
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=trl_gain_wpe_values,
                    mode='lines',
                    name=f'{temp}°C (Gain WPE)',
                    line=dict(color=color, width=2),
                    legendgroup=f'temp_{temp}',
                    showlegend=False
                ),
                row=1, col=3
            )
            
            # Total WPE plot (Row 2, Col 1) - Solid lines
            fig.add_trace(
                go.Scatter(
                    x=currents,
                    y=total_wpe_values,
                    mode='lines',
                    name=f'{temp}°C (Total WPE)',
                    line=dict(color=color, width=2),
                    legendgroup=f'temp_{temp}',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Add annotations at 130mA, 35°C
        annotation_power = self.calculate_output_power(annotation_temp, annotation_current)
        annotation_voltage = self.get_operating_voltage(annotation_current)
        annotation_gain_wpe = self.get_trl_gain_wpe(annotation_temp, annotation_current)
        annotation_total_wpe = self.get_total_wpe(annotation_temp, annotation_current)
        
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
        
        # Annotation for TRL Gain WPE plot
        fig.add_annotation(
            x=annotation_current, y=annotation_gain_wpe,
            text=f"{annotation_gain_wpe:.2f}%<br>@{annotation_current}mA, {annotation_temp}°C",
            showarrow=True, arrowhead=2, arrowcolor="red", arrowwidth=2,
            bgcolor="white", bordercolor="red", borderwidth=2,
            row=1, col=3
        )
        
        # Annotation for Total WPE plot
        fig.add_annotation(
            x=annotation_current, y=annotation_total_wpe,
            text=f"{annotation_total_wpe:.2f}%<br>@{annotation_current}mA, {annotation_temp}°C",
            showarrow=True, arrowhead=2, arrowcolor="red", arrowwidth=2,
            bgcolor="white", bordercolor="red", borderwidth=2,
            row=2, col=1
        )
        
        # Add pie chart for heat sources (at 130mA, 35°C)
        heat_sources = self.get_heat_sources(annotation_temp, annotation_current)
        fig.add_trace(
            go.Pie(
                labels=list(heat_sources.keys()),
                values=list(heat_sources.values()),
                name="Heat Sources",
                textinfo='label+percent+value',
                texttemplate='%{label}<br>%{value:.1f}mW<br>(%{percent})',
                hovertemplate='<b>%{label}</b><br>Heat Load: %{value:.1f}mW<br>Percentage: %{percent}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Add pie chart for power consumption breakdown (at 130mA, 35°C)
        trl_electrical_power = annotation_current * self.get_operating_voltage(annotation_current)  # mA * V = mW
        power_consumption = {
            'TRL Gain': trl_electrical_power,
            'Ring Heater 1': self.ring_htr_1.get_power_consumption(),
            'Ring Heater 2': self.ring_htr_2.get_power_consumption(),
            'Phase Heater': self.phase_htr.get_power_consumption()
        }
        
        fig.add_trace(
            go.Pie(
                labels=list(power_consumption.keys()),
                values=list(power_consumption.values()),
                name="Power Consumption",
                textinfo='label+percent+value',
                texttemplate='%{label}<br>%{value:.1f}mW<br>(%{percent})',
                hovertemplate='<b>%{label}</b><br>Power: %{value:.1f}mW<br>Percentage: %{percent}<extra></extra>',
                marker=dict(colors=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'])
            ),
            row=2, col=3
        )
        
        # Update layout
        fig.update_layout(
            title={
                'text': f'TRL Performance Characteristics with Thermal Management - Annotated at {annotation_current}mA, {annotation_temp}°C',
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
        fig.update_xaxes(title_text="Current [mA]", row=1, col=3)
        fig.update_xaxes(title_text="Current [mA]", row=2, col=1)
        
        # Update y-axes with appropriate ranges
        fig.update_yaxes(title_text="Pout [mW]", range=[0, 40], row=1, col=1)
        fig.update_yaxes(title_text="Voltage [V]", range=[1.0, 2.0], row=1, col=2)
        fig.update_yaxes(title_text="TRL Gain WPE [%]", range=[0, 20], row=1, col=3)
        fig.update_yaxes(title_text="Total WPE [%]", range=[0, 10], row=2, col=1)
        
        # Add grid to scatter plots
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
        
        # Operating point for annotations and pie charts
        annotation_current = 130  # mA
        annotation_temp = 35      # °C
        
        plt.figure(figsize=(18, 12))
        
        # Plot Pout vs Current
        plt.subplot(3, 2, 1)
        for i, temp in enumerate(temperatures):
            currents, powers = self.get_performance_curve(temp, current_range)
            color = colors[i % len(colors)]
            plt.plot(currents, powers, color=color, linewidth=2, 
                    label=f'Temperature: {temp}°C')
        
        # Add annotation at 130mA, 35°C
        annotation_power = self.calculate_output_power(annotation_temp, annotation_current)
        plt.annotate(f'{annotation_power:.1f}mW\n@{annotation_current}mA, {annotation_temp}°C',
                    xy=(annotation_current, annotation_power), xytext=(annotation_current+20, annotation_power+5),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red"),
                    fontsize=10, ha='left')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('Pout [mW]')
        plt.title('TRL Output Optical Power vs Current')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 40)
        plt.xlim(0, 200)
        
        # Plot I-V Characteristics
        plt.subplot(3, 2, 2)
        for i, temp in enumerate(temperatures):
            currents, _ = self.get_performance_curve(temp, current_range)
            voltages = [self.get_operating_voltage(current) for current in currents]
            color = colors[i % len(colors)]
            plt.plot(currents, voltages, color=color, linewidth=2, 
                    label=f'Temperature: {temp}°C')
        
        # Add annotation at 130mA
        annotation_voltage = self.get_operating_voltage(annotation_current)
        plt.annotate(f'{annotation_voltage:.3f}V\n@{annotation_current}mA',
                    xy=(annotation_current, annotation_voltage), xytext=(annotation_current+20, annotation_voltage+0.05),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red"),
                    fontsize=10, ha='left')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('Voltage [V]')
        plt.title('TRL Current-Voltage (I-V) Characteristics')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(1.0, 2.0)
        plt.xlim(0, 200)
        
        # Plot TRL Gain Wall-Plug Efficiency
        plt.subplot(3, 2, 3)
        for i, temp in enumerate(temperatures):
            currents, _ = self.get_performance_curve(temp, current_range)
            trl_gain_wpe_values = [self.get_trl_gain_wpe(temp, current) for current in currents]
            
            color = colors[i % len(colors)]
            plt.plot(currents, trl_gain_wpe_values, color=color, linewidth=2,
                    label=f'Temperature: {temp}°C')
        
        # Add annotation at 130mA, 35°C
        annotation_gain_wpe = self.get_trl_gain_wpe(annotation_temp, annotation_current)
        plt.annotate(f'{annotation_gain_wpe:.2f}%\n@{annotation_current}mA, {annotation_temp}°C',
                    xy=(annotation_current, annotation_gain_wpe), xytext=(annotation_current+20, annotation_gain_wpe+1),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red"),
                    fontsize=10, ha='left')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('TRL Gain WPE [%]')
        plt.title('TRL Gain Wall-Plug Efficiency vs Current')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 20)
        plt.xlim(0, 200)
        
        # Plot Total Wall-Plug Efficiency
        plt.subplot(3, 2, 4)
        for i, temp in enumerate(temperatures):
            currents, _ = self.get_performance_curve(temp, current_range)
            total_wpe_values = [self.get_total_wpe(temp, current) for current in currents]
            
            color = colors[i % len(colors)]
            plt.plot(currents, total_wpe_values, color=color, linewidth=2,
                    label=f'Temperature: {temp}°C')
        
        # Add annotation at 130mA, 35°C
        annotation_total_wpe = self.get_total_wpe(annotation_temp, annotation_current)
        plt.annotate(f'{annotation_total_wpe:.2f}%\n@{annotation_current}mA, {annotation_temp}°C',
                    xy=(annotation_current, annotation_total_wpe), xytext=(annotation_current+20, annotation_total_wpe+0.5),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="red"),
                    fontsize=10, ha='left')
        
        plt.xlabel('Current [mA]')
        plt.ylabel('Total WPE [%]')
        plt.title('TRL Total Wall-Plug Efficiency vs Current')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.ylim(0, 10)
        plt.xlim(0, 200)
        
        # Plot Heat Sources Pie Chart (at 130mA, 35°C)
        plt.subplot(3, 2, 5)
        heat_sources = self.get_heat_sources(annotation_temp, annotation_current)
        colors_pie = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
        plt.pie(heat_sources.values(), labels=heat_sources.keys(), autopct='%1.1f%%',
                colors=colors_pie, startangle=90)
        plt.title(f'Heat Sources Distribution\n(at {annotation_current}mA, {annotation_temp}°C)')
        
        # Plot Power Consumption Pie Chart (at 130mA, 35°C)
        plt.subplot(3, 2, 6)
        trl_electrical_power = annotation_current * self.get_operating_voltage(annotation_current)  # mA * V = mW
        power_consumption = {
            'TRL Gain': trl_electrical_power,
            'Ring HTR 1': self.ring_htr_1.get_power_consumption(),
            'Ring HTR 2': self.ring_htr_2.get_power_consumption(),
            'Phase HTR': self.phase_htr.get_power_consumption()
        }
        colors_pie2 = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
        plt.pie(power_consumption.values(), labels=power_consumption.keys(), autopct='%1.1f%%',
                colors=colors_pie2, startangle=90)
        plt.title(f'Power Consumption Breakdown\n(at {annotation_current}mA, {annotation_temp}°C)')
        
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
    
    # Print heater parameters
    print("Heater Parameters:")
    print(f"Ring Heater 1: {trl.ring_htr_1.ring_htr_heat_load}mW (Duty: {trl.ring_htr_1.get_duty_cycle()*100:.1f}%)")
    print(f"Ring Heater 2: {trl.ring_htr_2.ring_htr_heat_load}mW (Duty: {trl.ring_htr_2.get_duty_cycle()*100:.1f}%)")
    print(f"Phase Heater: {trl.phase_htr.phase_htr_heat_load}mW (Duty: {trl.phase_htr.get_duty_cycle()*100:.1f}%)")
    print(f"Total Heater Heat Load: {trl.trl_heater_heat_load}mW")
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
    
    # Show thermal analysis at 130mA, 35°C
    print("Thermal Analysis at 130mA, 35°C:")
    gain_heat_load = trl.get_trl_gain_heat_load(35, 130)
    total_heat_load = trl.get_trl_heat_load(35, 130)
    gain_wpe = trl.get_trl_gain_wpe(35, 130)
    total_wpe = trl.get_total_wpe(35, 130)
    trl_electrical_power = 130 * trl.get_operating_voltage(130)
    total_electrical_power = trl_electrical_power + trl.trl_heater_heat_load
    optical_output = trl.calculate_output_power(35, 130)
    
    print(f"Optical Output Power: {optical_output:.1f}mW")
    print(f"TRL Gain WPE: {gain_wpe:.2f}%")
    print(f"Total WPE (including heaters): {total_wpe:.2f}%")
    print(f"TRL Gain Heat Load: {gain_heat_load:.1f}mW")
    print(f"TRL Total Heat Load: {total_heat_load:.1f}mW")
    print(f"TRL Electrical Power: {trl_electrical_power:.1f}mW")
    print(f"Total Electrical Power (TRL + Heaters): {total_electrical_power:.1f}mW")
    print()
    
    # Show operating voltage examples
    print("Operating Voltage Examples:")
    for current in [80, 100, 140]:
        voltage = trl.get_operating_voltage(current)
        print(f"At {current}mA: {voltage:.3f}V")
    print()
    
    # Create interactive plot with dropdown
    print("Generating interactive TRL performance plot with thermal management...")
    trl.create_interactive_plot('trl_interactive_plot.html')
    
    # Create matplotlib plot for comparison (save but don't show)
    print("Generating and saving matplotlib plot...")
    
    # Determine the correct path for saving plots
    import os
    current_dir = os.getcwd()
    if current_dir.endswith('src/models'):
        # Running from src/models directory
        save_path = '../../data/plots/models/trl_performance.png'
    else:
        # Running from project root
        save_path = 'data/plots/models/trl_performance.png'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    trl.plot_performance_curves(
        temperatures=[10, 35, 45, 55, 80],
        current_range=(0, 200, 1),
        save_path=save_path,
        show_plot=False  # Don't display the plot
    )


if __name__ == "__main__":
    main() 