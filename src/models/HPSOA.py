import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class HPSOA:
    def __init__(self):
        self.revision_history = [
            {"Rev": "1.0", "Date": "12/12/2022", "Revised by": "H. Zhao", "Comments": "Initial draft"},
            {"Rev": "2.0", "Date": "12/14/2022", "Revised by": "H. Zhao", "Comments": "Update document ID"}
        ]
        self.references = [
            "[1] L. Coldren, S. Q. Corzine, M. L. Mashanovitch, \"Diode lasers and photonic integrated circuits,\" John Wiley & Sons, Hoboken, 2nd ed, 2011.",
            "[2] R. Lennox et al., \"Impact of bias current distribution on the noise figure and power saturation of a multicontact semiconductor optical amplifier,\" Optics Lett., vol.36, pp. 2521-2523, 2011."
        ]
        self.glossary = {
            "HPSOA": "High Power Semiconductor Optical Amplifier",
            "SOI": "Silicon on Insulator substrates",
            "WPE": "Wall-Plug Efficiency",
            "NF": "Noise Figure"
        }
        self.document_scope = "This Application Note provides operation conditions and performance for OpenLight O-band high power Semiconductor Optical Amplifier (HPSOA)."
        self.introduction = (
            "Semiconductor optical amplifiers (SOAs) are designed to amplify optical signal through group III-V gain materials. "
            "High power semiconductor optical amplifiers (HPSOAs) on a hybrid platform enable >100mW optical power per waveguide with high wall-plug efficiency. "
            "As shown in Fig. 1, the III-V gain material is heterogeneously bonded onto Silicon on Insulator (SOI) substrates. "
            "Light is guided in and out of the SOA vias evanescent coupling by the Si waveguides underneath the gain material. "
            "The HPSOA described in this Application Note is designed for O-band operation (centered at 1311 nm). "
            "The III-V gain region is a multi-width structure, the detail of this design is discussed in Sec.6. "
            "For general use purpose, a lookup table for different operation conditions (temperature, current and wavelength) is covered in Sec. 7."
        )
        self.hpsoa_design_geometry = {
            "output_saturation_power_equation": r"$P_{os}=\frac{g_{o}ln2}{g_{o}-2}\frac{Wdhv}{a\Gamma\tau}$",
            "equation_parameters": "W and d are the width and thickness of the active layer, a is the differential gain of the materials, $\\Gamma$ is the confinement factor, t is the carrier lifetime, h is the Planck constant and v is the optical frequency.",
            "design_strategy": "To achieve a high $P_{os}$ the III-V epi layers are tailored for a low confinement factor and a multi-section SOA with flared width towards output is designed.",
            "iii_v_gain_sections": {
                "description": "The III-V gain contains three sections: narrow-ridge input ($L_{1}$), transition taper ($L_{wt}$) and wide-ridge output ($L_{2}$).",
                "dimensions": {
                    "W1_um": 2,
                    "L1_um": 1260,
                    "W2_um": 4,
                    "Lwt_um": 60,
                    "L2_um": 400
                }
            }
        }
        self.hpsoa_performance = {
            "noise_figure_equation": r"$NF=NF_{1}+\frac{NF_{2}-1}{G_{1}}$",
            "wall_plug_efficiency_equation": r"$WPE=\frac{P_{o}}{V\times1}$",
            "wall_plug_efficiency_parameters": "where V is the voltage, I is the current.",
            "diode_iv_characteristic_equation": r"$I=I_{0}exp[\frac{q}{nkT}(V-IR_{s})]$",
            "diode_iv_characteristic_parameters": "$I_{0}$ is the saturation current, n is the diode ideality, k is the Boltzmann constant, Rs is the series resistance, T is the temperature, and q is the unit charge.",
            "voltage_equation": r"$V=V_{turn-on}+IR_{s}=\frac{nkT}{q}[(Ln(I)-Ln(I_{0}))]+IR_{s}$",
            "turn_on_voltage": "1.05 V",
            "series_resistance_equation": r"$R_{s}=\frac{4.34}{W[um]}+\frac{2151}{L[um]}-0.992$",
            "series_resistance_parameters": "where W is the SOA ridge width and L is the length of the diode.",
            "equivalent_circuit_parameters": {
                "V_turn_on": 1.05,
                "Rs1_ohm": 2.89,
                "Rs2_ohm": 5.47
            },
            "current_relations": {
                "total_current": r"$I=I_{1}+I_{2}$",
                "current_i1": r"$I_{1}=(V-V_{turn-on})/R_{s1}$",
                "current_i2": r"$I_{2}=(V-V_{turn-on})/R_{s2}$"
            }
        }
        self.performance_summary = {
            "operation_conditions": {
                "temperature_celsius": [35, 55, 70, 80],
                "current_a": [0.18, 0.23, 0.28],
                "wavelength_nm": [1304, 1311, 1318]
            },
            "data": [
                {"Index": 1, "T[°C]": 35, "I[A]": 0.18, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 19.4, "WPE [%]": 35.1, "NF [dB]": 9.72},
                {"Index": 2, "T[°C]": 35, "I[A]": 0.18, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 18.8, "WPE [%]": 30.6, "NF [dB]": 9.31},
                {"Index": 3, "T[°C]": 35, "I[A]": 0.18, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 19.0, "WPE [%]": 32.1, "NF [dB]": 8.11},
                {"Index": 4, "T[°C]": 35, "I[A]": 0.23, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 20.8, "WPE [%]": 34.9, "NF [dB]": 9.68},
                {"Index": 5, "T[°C]": 35, "I[A]": 0.23, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 20.2, "WPE [%]": 30.3, "NF [dB]": 9.32},
                {"Index": 6, "T[°C]": 35, "I[A]": 0.23, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 20.4, "WPE [%]": 32.0, "NF [dB]": 8.12},
                {"Index": 7, "T[°C]": 35, "I[A]": 0.28, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 21.7, "WPE [%]": 33.8, "NF [dB]": 9.58},
                {"Index": 8, "T[°C]": 35, "I[A]": 0.28, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 21.1, "WPE [%]": 29.3, "NF [dB]": 9.27},
                {"Index": 9, "T[°C]": 35, "I[A]": 0.28, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 21.4, "WPE [%]": 31.0, "NF [dB]": 8.09},
                {"Index": 10, "T[°C]": 55, "I[A]": 0.18, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 18.8, "WPE [%]": 30.2, "NF [dB]": 9.24},
                {"Index": 11, "T[°C]": 55, "I[A]": 0.18, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 18.3, "WPE [%]": 27.0, "NF [dB]": 9.13},
                {"Index": 12, "T[°C]": 55, "I[A]": 0.18, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 18.5, "WPE [%]": 28.5, "NF [dB]": 8.17},
                {"Index": 13, "T[°C]": 55, "I[A]": 0.23, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 20.0, "WPE [%]": 29.5, "NF [dB]": 9.11},
                {"Index": 14, "T[°C]": 55, "I[A]": 0.23, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 19.5, "WPE [%]": 26.2, "NF [dB]": 9.08},
                {"Index": 15, "T[°C]": 55, "I[A]": 0.23, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 19.8, "WPE [%]": 27.9, "NF [dB]": 8.16},
                {"Index": 16, "T[°C]": 55, "I[A]": 0.28, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 20.9, "WPE [%]": 27.9, "NF [dB]": 8.97},
                {"Index": 17, "T[°C]": 55, "I[A]": 0.28, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 20.4, "WPE [%]": 24.7, "NF [dB]": 9.00},
                {"Index": 18, "T[°C]": 55, "I[A]": 0.28, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 20.7, "WPE [%]": 26.3, "NF [dB]": 8.12},
                {"Index": 19, "T[°C]": 70, "I[A]": 0.18, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 17.9, "WPE [%]": 24.5, "NF [dB]": 8.86},
                {"Index": 20, "T[°C]": 70, "I[A]": 0.18, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 17.6, "WPE [%]": 23.0, "NF [dB]": 8.96},
                {"Index": 21, "T[°C]": 70, "I[A]": 0.18, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 18.0, "WPE [%]": 25.1, "NF [dB]": 8.22},
                {"Index": 22, "T[°C]": 70, "I[A]": 0.23, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 19.1, "WPE [%]": 23.8, "NF [dB]": 8.65},
                {"Index": 23, "T[°C]": 70, "I[A]": 0.23, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 18.8, "WPE [%]": 22.0, "NF [dB]": 8.82},
                {"Index": 24, "T[°C]": 70, "I[A]": 0.23, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 19.1, "WPE [%]": 24.0, "NF [dB]": 8.13},
                {"Index": 25, "T[°C]": 70, "I[A]": 0.28, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 19.9, "WPE [%]": 22.1, "NF [dB]": 8.46},
                {"Index": 26, "T[°C]": 70, "I[A]": 0.28, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 19.6, "WPE [%]": 20.4, "NF [dB]": 8.69},
                {"Index": 27, "T[°C]": 70, "I[A]": 0.28, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 19.9, "WPE [%]": 22.2, "NF [dB]": 8.05},
                {"Index": 28, "T[°C]": 80, "I[A]": 0.18, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 16.9, "WPE [%]": 19.5, "NF [dB]": 8.62},
                {"Index": 29, "T[°C]": 80, "I[A]": 0.18, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 16.8, "WPE [%]": 19.2, "NF [dB]": 8.80},
                {"Index": 30, "T[°C]": 80, "I[A]": 0.18, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 17.4, "WPE [%]": 21.7, "NF [dB]": 8.20},
                {"Index": 31, "T[°C]": 80, "I[A]": 0.23, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 18.1, "WPE [%]": 19.1, "NF [dB]": 8.33},
                {"Index": 32, "T[°C]": 80, "I[A]": 0.23, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 18.0, "WPE [%]": 18.5, "NF [dB]": 8.59},
                {"Index": 33, "T[°C]": 80, "I[A]": 0.23, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 18.5, "WPE [%]": 20.7, "NF [dB]": 8.04},
                {"Index": 34, "T[°C]": 80, "I[A]": 0.28, "λ [nm]": 1304, "Pin [dBm]": 10, "Pout [dBm]": 18.9, "WPE [%]": 17.7, "NF [dB]": 8.12},
                {"Index": 35, "T[°C]": 80, "I[A]": 0.28, "λ [nm]": 1311, "Pin [dBm]": 10, "Pout [dBm]": 18.7, "WPE [%]": 16.9, "NF [dB]": 8.69},
                {"Index": 36, "T[°C]": 80, "I[A]": 0.28, "λ [nm]": 1318, "Pin [dBm]": 10, "Pout [dBm]": 19.2, "WPE [%]": 18.9, "NF [dB]": 7.92}
            ]
        }

    def dbm_to_mw(self, dbm):
        """
        Convert dBm to mW
        
        Args:
            dbm (float): Power in dBm
            
        Returns:
            float: Power in mW
        """
        return 10 ** (dbm / 10)

    def get_operating_voltage(self, current_a):
        """
        Calculate operating voltage based on current using equivalent circuit model
        
        Args:
            current_a (float): Current in Amperes
            
        Returns:
            float: Operating voltage in V
        """
        V_turn_on = self.hpsoa_performance["equivalent_circuit_parameters"]["V_turn_on"]
        Rs1_ohm = self.hpsoa_performance["equivalent_circuit_parameters"]["Rs1_ohm"]
        Rs2_ohm = self.hpsoa_performance["equivalent_circuit_parameters"]["Rs2_ohm"]
        
        # Using parallel resistance model: 1/Rs_total = 1/Rs1 + 1/Rs2
        Rs_total = (Rs1_ohm * Rs2_ohm) / (Rs1_ohm + Rs2_ohm)
        
        # Operating voltage: V = V_turn_on + I * Rs_total
        return V_turn_on + (current_a * Rs_total)

    def get_hpsoa_heat_load(self, temperature_c, current_a, wavelength_nm):
        """
        Calculate HPSOA heat load (remaining electrical power not converted to optical)
        
        Args:
            temperature_c (float): Temperature in Celsius
            current_a (float): Current in Amperes
            wavelength_nm (float): Wavelength in nm
            
        Returns:
            float: HPSOA heat load in mW
        """
        # Find matching data point
        df = pd.DataFrame(self.performance_summary["data"])
        mask = (df["T[°C]"] == temperature_c) & (df["I[A]"] == current_a) & (df["λ [nm]"] == wavelength_nm)
        matching_data = df[mask]
        
        if len(matching_data) == 0:
            return 0.0  # No matching data found
        
        row = matching_data.iloc[0]
        
        # Get optical output power in mW
        optical_output_mw = self.dbm_to_mw(row["Pout [dBm]"])
        
        # Calculate electrical power
        operating_voltage = self.get_operating_voltage(current_a)
        electrical_power_mw = current_a * operating_voltage * 1000  # Convert to mW
        
        # Heat load is electrical power minus optical power output
        heat_load = electrical_power_mw - optical_output_mw
        return max(0, heat_load)  # Ensure non-negative

    def get_heat_sources(self, temperature_c, current_a, wavelength_nm):
        """
        Get breakdown of heat sources (for HPSOA, only one source: the gain section)
        
        Args:
            temperature_c (float): Temperature in Celsius  
            current_a (float): Current in Amperes
            wavelength_nm (float): Wavelength in nm
            
        Returns:
            dict: Dictionary with heat source breakdown
        """
        return {
            'HPSOA Gain Heat Load': self.get_hpsoa_heat_load(temperature_c, current_a, wavelength_nm)
        }

    def get_power_consumption(self, temperature_c, current_a, wavelength_nm):
        """
        Get power consumption breakdown (for HPSOA, only electrical power to gain section)
        
        Args:
            temperature_c (float): Temperature in Celsius  
            current_a (float): Current in Amperes
            wavelength_nm (float): Wavelength in nm
            
        Returns:
            dict: Dictionary with power consumption breakdown
        """
        electrical_power_mw = current_a * self.get_operating_voltage(current_a) * 1000  # Convert to mW
        return {
            'HPSOA Gain': electrical_power_mw
        }
    
    def get_total_electrical_power(self, temperature_c, current_a, wavelength_nm):
        """
        Calculate total electrical power consumption (only HPSOA gain, no heaters)
        
        Args:
            temperature_c (float): Temperature in Celsius
            current_a (float): Current in Amperes
            wavelength_nm (float): Wavelength in nm
            
        Returns:
            float: Total electrical power in mW
        """
        # HPSOA only has gain electrical power, no heaters
        operating_voltage = self.get_operating_voltage(current_a)
        return current_a * operating_voltage * 1000  # Convert to mW
    
    def get_total_optical_power(self, temperature_c, current_a, wavelength_nm):
        """
        Calculate total optical power output
        
        Args:
            temperature_c (float): Temperature in Celsius
            current_a (float): Current in Amperes
            wavelength_nm (float): Wavelength in nm
            
        Returns:
            float: Total optical power in mW
        """
        # Find matching data point
        df = pd.DataFrame(self.performance_summary["data"])
        mask = (df["T[°C]"] == temperature_c) & (df["I[A]"] == current_a) & (df["λ [nm]"] == wavelength_nm)
        matching_data = df[mask]
        
        if len(matching_data) == 0:
            return 0.0  # No matching data found
        
        row = matching_data.iloc[0]
        # Convert dBm to mW
        return self.dbm_to_mw(row["Pout [dBm]"])
    
    def get_total_heat_load(self, temperature_c, current_a, wavelength_nm):
        """
        Calculate total heat load (same as HPSOA heat load)
        
        Args:
            temperature_c (float): Temperature in Celsius
            current_a (float): Current in Amperes
            wavelength_nm (float): Wavelength in nm
            
        Returns:
            float: Total heat load in mW
        """
        return self.get_hpsoa_heat_load(temperature_c, current_a, wavelength_nm)

    def get_revision_history(self):
        """Returns the revision history of the document."""
        return self.revision_history

    def get_references(self):
        """Returns the list of references."""
        return self.references

    def get_glossary(self):
        """Returns the glossary of terms."""
        return self.glossary

    def get_document_scope(self):
        """Returns the scope of the document."""
        return self.document_scope

    def get_introduction(self):
        """Returns the introduction section."""
        return self.introduction

    def get_hpsoa_design_geometry(self):
        """Returns details about the HPSOA design geometry."""
        return self.hpsoa_design_geometry

    def get_hpsoa_performance_equations(self):
        """Returns details about HPSOA performance equations and parameters."""
        return self.hpsoa_performance

    def get_performance_summary_conditions(self):
        """Returns the operation conditions for the performance summary."""
        return self.performance_summary["operation_conditions"]

    def get_performance_summary_data(self):
        """Returns the HPSOA performance summary data."""
        return self.performance_summary["data"]

    def plot_performance_data(self, figsize=(24, 12), save_path="data/plots/models/hpsoa.png"):
        """
        Plot HPSOA performance data with subplots organized by:
        - Columns: Output Power, WPE, NF, and Heat Load
        - Rows: Temperature
        - Each subplot: Different currents on x-axis
        
        Args:
            figsize (tuple): Figure size (width, height) in inches
            save_path (str): Path to save the plot (default: "data/plots/models/hpsoa.png")
        """
        # Convert data to pandas DataFrame for easier manipulation
        df = pd.DataFrame(self.performance_summary["data"])
        
        # Calculate heat load for each data point
        heat_loads = []
        for _, row in df.iterrows():
            heat_load = self.get_hpsoa_heat_load(row["T[°C]"], row["I[A]"], row["λ [nm]"])
            heat_loads.append(heat_load)
        df["Heat Load [mW]"] = heat_loads
        
        # Get unique temperatures and currents
        temperatures = sorted(df["T[°C]"].unique())
        currents = sorted(df["I[A]"].unique())
        wavelengths = sorted(df["λ [nm]"].unique())
        
        # Create subplot grid: rows = temperatures, cols = 4 (Pout, WPE, NF, Heat Load)
        fig, axes = plt.subplots(len(temperatures), 4, figsize=figsize)
        fig.suptitle('HPSOA Performance Analysis with Heat Load', fontsize=16, fontweight='bold')
        
        # Ensure axes is always 2D array
        if len(temperatures) == 1:
            axes = axes.reshape(1, -1)
        
        # Column titles
        column_titles = ['Output Power (dBm)', 'Wall-Plug Efficiency (%)', 'Noise Figure (dB)', 'Heat Load (mW)']
        
        # Color scheme for different currents
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green
        markers = ['o', 's', '^']  # Circle, Square, Triangle
        
        # Plot data for each temperature
        for i, temp in enumerate(temperatures):
            # Filter data for this temperature
            temp_data = df[df["T[°C]"] == temp]
            
            # Plot each metric (Pout, WPE, NF, Heat Load)
            for j, metric in enumerate(['Pout [dBm]', 'WPE [%]', 'NF [dB]', 'Heat Load [mW]']):
                ax = axes[i, j]
                
                # Plot data for each current
                for k, current in enumerate(currents):
                    # Filter data for this current and temperature
                    mask = (temp_data["I[A]"] == current)
                    subset = temp_data[mask].sort_values("λ [nm]")
                    
                    if len(subset) > 0:
                        # Plot the metric vs wavelength
                        ax.plot(subset["λ [nm]"], subset[metric], 
                               color=colors[k], marker=markers[k], linewidth=2, markersize=6,
                               label=f'I = {current}A')
                        
                        # Add data point annotations
                        for idx, row in subset.iterrows():
                            if metric == 'Pout [dBm]':
                                value_str = f'{row[metric]:.1f}'
                            elif metric == 'WPE [%]':
                                value_str = f'{row[metric]:.1f}%'
                            elif metric == 'NF [dB]':
                                value_str = f'{row[metric]:.2f}'
                            else:  # Heat Load [mW]
                                value_str = f'{row[metric]:.0f}'
                            
                            ax.annotate(value_str, 
                                      (row["λ [nm]"], row[metric]),
                                      xytext=(5, 5), textcoords='offset points',
                                      fontsize=7, color=colors[k])
                
                # Set labels and title
                ax.set_xlabel('Wavelength (nm)', fontsize=10)
                ax.set_ylabel(column_titles[j], fontsize=10)
                ax.set_title(f'{column_titles[j]} at T = {temp}°C', fontsize=11, fontweight='bold')
                
                # Add grid
                ax.grid(True, alpha=0.3)
                
                # Set x-axis limits with some padding
                x_min, x_max = wavelengths[0], wavelengths[-1]
                ax.set_xlim(x_min - 2, x_max + 2)
                
                # Add legend
                ax.legend(loc='best', fontsize=8)
                
                # Add temperature annotation
                ax.text(0.02, 0.98, f'T = {temp}°C', transform=ax.transAxes, 
                       fontsize=10, fontweight='bold', verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.92)
        
        # Add overall statistics
        fig.text(0.02, 0.02, 
                f'Data Summary: {len(df)} measurements | '
                f'Temperature: {min(temperatures)}-{max(temperatures)}°C | '
                f'Current: {min(currents)}-{max(currents)}A | '
                f'Wavelength: {min(wavelengths)}-{max(wavelengths)}nm | '
                f'Heat Load: {df["Heat Load [mW]"].min():.0f}-{df["Heat Load [mW]"].max():.0f}mW', 
                fontsize=9, style='italic')
        
        # Create directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save the plot
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()  # Close the figure to free memory
        
        # Print summary statistics
        print("\nHPSOA Performance Data Summary:")
        print("=" * 50)
        print(f"Temperature Range: {min(temperatures)}°C - {max(temperatures)}°C")
        print(f"Current Range: {min(currents)}A - {max(currents)}A")
        print(f"Wavelength Range: {min(wavelengths)}nm - {max(wavelengths)}nm")
        print(f"Output Power Range: {df['Pout [dBm]'].min():.1f} - {df['Pout [dBm]'].max():.1f} dBm")
        print(f"WPE Range: {df['WPE [%]'].min():.1f} - {df['WPE [%]'].max():.1f}%")
        print(f"Noise Figure Range: {df['NF [dB]'].min():.2f} - {df['NF [dB]'].max():.2f} dB")
        print(f"Heat Load Range: {df['Heat Load [mW]'].min():.0f} - {df['Heat Load [mW]'].max():.0f} mW")
        print(f"\nPlot saved to: {save_path}")
        
        return fig, axes

# Example Usage:
hpsoa_doc = HPSOA()

# Accessing information
print("Document Scope:", hpsoa_doc.get_document_scope())
print("\nRevision History:")
for rev in hpsoa_doc.get_revision_history():
    print(rev)
print("\nHPSOA Design Geometry Dimensions:")
print(hpsoa_doc.get_hpsoa_design_geometry()["iii_v_gain_sections"]["dimensions"])
print("\nFirst entry in Performance Summary Data:")
print(hpsoa_doc.get_performance_summary_data()[0])

# Plot the performance data
hpsoa_doc.plot_performance_data() 