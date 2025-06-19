import tkinter as tk
from tkinter import ttk, messagebox
from EuropaSOA import EuropaSOA
import math

class Guide3GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Guide3 GUI")
        # Set window size to 30cm x 20cm (approximately 1134 x 756 pixels at 96 DPI)
        self.geometry("1134x756")
        self.link_loss_modes = {"median-loss": tk.BooleanVar(), "3-sigma-loss": tk.BooleanVar()}
        # Initialize default wavelengths
        self.default_wavelengths = ["1301.47", "1303.73", "1306.01", "1308.28", "1310.57", "1312.87", "1315.17", "1317.48"]
        self._create_widgets()

    def _create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Link Loss Section
        link_loss_frame = ttk.LabelFrame(main_frame, text="Link Loss", padding="10")
        link_loss_frame.pack(fill='x', pady=(0, 10))

        ttk.Checkbutton(link_loss_frame, text="median-loss", 
                       variable=self.link_loss_modes["median-loss"]).pack(anchor='w')
        ttk.Checkbutton(link_loss_frame, text="3-σL-loss", 
                       variable=self.link_loss_modes["3-sigma-loss"]).pack(anchor='w')

        # Set default selections
        self.link_loss_modes["median-loss"].set(True)
        self.link_loss_modes["3-sigma-loss"].set(True)

        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        # EuropaSOA Tab
        self.soa_tab = ttk.Frame(notebook)
        notebook.add(self.soa_tab, text='EuropaSOA')
        
        # Create main horizontal frame for inputs and results
        soa_main_frame = ttk.Frame(self.soa_tab)
        soa_main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left side - Input parameters with scrolling
        input_container = ttk.Frame(soa_main_frame)
        input_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Create canvas with both scrollbars for input parameters
        input_canvas = tk.Canvas(input_container, width=400, height=600)
        input_v_scrollbar = ttk.Scrollbar(input_container, orient="vertical", command=input_canvas.yview)
        input_h_scrollbar = ttk.Scrollbar(input_container, orient="horizontal", command=input_canvas.xview)
        input_scrollable_frame = ttk.Frame(input_canvas)

        input_scrollable_frame.bind(
            "<Configure>",
            lambda e: input_canvas.configure(scrollregion=input_canvas.bbox("all"))
        )

        input_canvas.create_window((0, 0), window=input_scrollable_frame, anchor="nw")
        input_canvas.configure(yscrollcommand=input_v_scrollbar.set, xscrollcommand=input_h_scrollbar.set)

        # Pack the canvas and scrollbars
        input_canvas.pack(side="left", fill="both", expand=True)
        input_v_scrollbar.pack(side="right", fill="y")
        input_h_scrollbar.pack(side="bottom", fill="x")
        
        # Bind mouse wheel scrolling
        input_canvas.bind_all("<MouseWheel>", lambda event: input_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        input_canvas.bind_all("<Shift-MouseWheel>", lambda event: input_canvas.xview_scroll(int(-1*(event.delta/120)), "units"))

        # Create 4 quadrants
        # Top-left quadrant
        top_left_frame = ttk.Frame(input_scrollable_frame)
        top_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(0, 5))
        
        # Top-right quadrant
        top_right_frame = ttk.Frame(input_scrollable_frame)
        top_right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=(0, 5))
        
        # Bottom-left quadrant
        bottom_left_frame = ttk.Frame(input_scrollable_frame)
        bottom_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(5, 0))
        
        # Bottom-right quadrant
        bottom_right_frame = ttk.Frame(input_scrollable_frame)
        bottom_right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=(5, 0))

        # --- Device Parameters (Top-left) ---
        device_frame = ttk.LabelFrame(top_left_frame, text="Device Parameters", padding="10")
        device_frame.pack(fill=tk.X, pady=5)

        ttk.Label(device_frame, text="Width (µm) [2.0-2.7]:").pack(pady=(5, 2), anchor='w')
        self.w_um_var = tk.StringVar(value="2.0")
        self.w_um_entry = ttk.Entry(device_frame, textvariable=self.w_um_var, width=15)
        self.w_um_entry.pack(anchor='w', padx=5)

        ttk.Label(device_frame, text="Active Length (µm) [40-880]:").pack(pady=(5, 2), anchor='w')
        self.l_active_var = tk.StringVar(value="790")
        self.l_active_entry = ttk.Entry(device_frame, textvariable=self.l_active_var, width=15)
        self.l_active_entry.pack(anchor='w', padx=5)

        # --- Operation Parameters (Top-left) ---
        operation_frame = ttk.LabelFrame(top_left_frame, text="Operation Parameters", padding="10")
        operation_frame.pack(fill=tk.X, pady=5)

        # Target P_out for Median Loss
        self.median_pout_frame = ttk.Frame(operation_frame)
        self.median_pout_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.median_pout_frame, text="Target P_out - Median (dBm) [0-20]:").pack(pady=(5, 2), anchor='w')
        self.pout_median_var = tk.StringVar(value="9")
        self.pout_median_entry = ttk.Entry(self.median_pout_frame, textvariable=self.pout_median_var, width=15)
        self.pout_median_entry.pack(anchor='w', padx=5)

        # Target P_out for 3-Sigma Loss
        self.sigma_pout_frame = ttk.Frame(operation_frame)
        self.sigma_pout_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.sigma_pout_frame, text="Target P_out - 3σ (dBm) [0-20]:").pack(pady=(5, 2), anchor='w')
        self.pout_sigma_var = tk.StringVar(value="13")
        self.pout_sigma_entry = ttk.Entry(self.sigma_pout_frame, textvariable=self.pout_sigma_var, width=15)
        self.pout_sigma_entry.pack(anchor='w', padx=5)

        # Current Density for Median Loss
        self.median_current_frame = ttk.Frame(operation_frame)
        self.median_current_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.median_current_frame, text="Current Density - Median (kA/cm²):").pack(pady=(5, 2), anchor='w')
        self.j_density_median_var = tk.StringVar(value="4")
        self.j_density_median_combo = ttk.Combobox(self.median_current_frame, textvariable=self.j_density_median_var,
                                                   values=["3", "4", "5", "6", "7"], width=12)
        self.j_density_median_combo.pack(anchor='w', padx=5)

        # Current Density for 3-Sigma Loss
        self.sigma_current_frame = ttk.Frame(operation_frame)
        self.sigma_current_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.sigma_current_frame, text="Current Density - 3σ (kA/cm²):").pack(pady=(5, 2), anchor='w')
        self.j_density_sigma_var = tk.StringVar(value="7")
        self.j_density_sigma_combo = ttk.Combobox(self.sigma_current_frame, textvariable=self.j_density_sigma_var,
                                                  values=["3", "4", "5", "6", "7"], width=12)
        self.j_density_sigma_combo.pack(anchor='w', padx=5)

        ttk.Label(operation_frame, text="Temperature (°C) [25-80]:").pack(pady=(5, 2), anchor='w')
        self.temp_var = tk.StringVar(value="40")
        self.temp_entry = ttk.Entry(operation_frame, textvariable=self.temp_var, width=15)
        self.temp_entry.pack(anchor='w', padx=5)

        # --- Wavelength Configuration (Top-right) ---
        wavelength_frame = ttk.LabelFrame(top_right_frame, text="Wavelength Configuration", padding="10")
        wavelength_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Number of wavelengths
        ttk.Label(wavelength_frame, text="Number of Wavelengths:").pack(pady=(5, 2), anchor='w')
        self.num_wavelengths_var = tk.StringVar(value="8")
        self.num_wavelengths_entry = ttk.Entry(wavelength_frame, textvariable=self.num_wavelengths_var, width=15)
        self.num_wavelengths_entry.pack(anchor='w', padx=5)
        
        ttk.Button(wavelength_frame, text="Update Wavelengths", command=self.update_wavelength_inputs).pack(anchor='w', padx=5, pady=(5, 10))

        # Individual wavelength inputs
        self.wavelength_vars = []
        self.wavelength_entries = []
        
        for i in range(8):
            ttk.Label(wavelength_frame, text=f"Wavelength {i+1} (nm) [1290-1330]:").pack(pady=(5, 2), anchor='w')
            wavelength_var = tk.StringVar(value=self.default_wavelengths[i])
            wavelength_entry = ttk.Entry(wavelength_frame, textvariable=wavelength_var, width=15)
            wavelength_entry.pack(anchor='w', padx=5)
            
            self.wavelength_vars.append(wavelength_var)
            self.wavelength_entries.append(wavelength_entry)
        
        # Save wavelength set button
        ttk.Button(wavelength_frame, text="Save Wavelength Set", command=self.save_wavelength_set).pack(anchor='w', padx=5, pady=(10, 5))

        # Right side - Results Display
        results_frame = ttk.LabelFrame(soa_main_frame, text="Results", padding="10")
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Action buttons at the top of results section
        action_frame = ttk.Frame(results_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(action_frame, text="Calculate", command=self.calculate_soa).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Reset", command=self.reset_soa).pack(side=tk.LEFT, padx=5)
        
        # Top section - Median Results
        median_results_frame = ttk.LabelFrame(results_frame, text="Median Loss Case", padding="5")
        median_results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.median_results_text = tk.Text(median_results_frame, height=10, width=50)
        median_results_scrollbar = ttk.Scrollbar(median_results_frame, orient="vertical", command=self.median_results_text.yview)
        self.median_results_text.configure(yscrollcommand=median_results_scrollbar.set)
        
        self.median_results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        median_results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom section - 3-Sigma Results
        sigma_results_frame = ttk.LabelFrame(results_frame, text="3σ Loss Case", padding="5")
        sigma_results_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.sigma_results_text = tk.Text(sigma_results_frame, height=10, width=50)
        sigma_results_scrollbar = ttk.Scrollbar(sigma_results_frame, orient="vertical", command=self.sigma_results_text.yview)
        self.sigma_results_text.configure(yscrollcommand=sigma_results_scrollbar.set)
        
        self.sigma_results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sigma_results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # EuropaPIC Tab
        self.pic_tab = ttk.Frame(notebook)
        notebook.add(self.pic_tab, text='EuropaPIC')
        ttk.Label(self.pic_tab, text="EuropaPIC Model Interface (placeholder)").pack(padx=10, pady=10)

        # Guide3A Tab
        self.guide3a_tab = ttk.Frame(notebook)
        notebook.add(self.guide3a_tab, text='Guide3A')
        ttk.Label(self.guide3a_tab, text="Guide3A Model Interface (placeholder)").pack(padx=10, pady=10)

    def calculate_soa(self):
        """Calculate SOA parameters based on input values using EuropaSOA class"""
        try:
            # Get input values
            w_um = float(self.w_um_var.get())
            l_active = float(self.l_active_var.get())
            temp_c = float(self.temp_var.get())
            
            # Get number of wavelengths and validate
            num_wavelengths = int(self.num_wavelengths_var.get())
            if num_wavelengths < 1 or num_wavelengths > 8:
                messagebox.showerror("Invalid Input", "Number of wavelengths must be between 1 and 8")
                return
            
            # Get wavelength values
            wavelengths = []
            for i in range(num_wavelengths):
                try:
                    wavelength = float(self.wavelength_vars[i].get())
                    if not (1290 <= wavelength <= 1330):
                        messagebox.showerror("Invalid Input", f"Wavelength {i+1} must be between 1290 and 1330 nm")
                        return
                    wavelengths.append(wavelength)
                except ValueError:
                    messagebox.showerror("Invalid Input", f"Wavelength {i+1} must be a valid number")
                    return
            
            # Check which link loss modes are selected
            median_selected = self.link_loss_modes["median-loss"].get()
            sigma_selected = self.link_loss_modes["3-sigma-loss"].get()
            
            if not median_selected and not sigma_selected:
                messagebox.showerror("Invalid Selection", "Please select at least one link loss mode.")
                return
            
            # Validate inputs
            if not (2.0 <= w_um <= 2.7):
                messagebox.showerror("Invalid Input", "Width must be between 2.0 and 2.7 µm")
                return
            if not (40 <= l_active <= 880):
                messagebox.showerror("Invalid Input", "Active Length must be between 40 and 880 µm")
                return
            if not (25 <= temp_c <= 80):
                messagebox.showerror("Invalid Input", "Temperature must be between 25 and 80 °C")
                return
            
            # Create EuropaSOA instance
            soa = EuropaSOA(L_active_um=l_active, W_um=w_um, verbose=False)
            
            # Calculate basic parameters
            device_area_cm2 = (w_um * l_active) / 10000  # Convert µm² to cm²
            
            # Clear both result sections
            self.median_results_text.delete(1.0, tk.END)
            self.sigma_results_text.delete(1.0, tk.END)
            
            # Display device and operation parameters in both sections
            wavelengths_str = ", ".join([f"{w:.2f}" for w in wavelengths])
            common_info = f"""Device Parameters:
- Width: {w_um:.1f} µm
- Active Length: {l_active:.0f} µm
- Device Area: {device_area_cm2:.4f} cm²
- Series Resistance: {soa.calculate_series_resistance_ohm():.3f} Ω

Operation Parameters:
- Number of Wavelengths: {num_wavelengths}
- Wavelengths: {wavelengths_str} nm
- Temperature: {temp_c:.0f} °C

"""
            
            if median_selected:
                pout_median = float(self.pout_median_var.get())
                j_density_median = float(self.j_density_median_var.get())
                
                if not (0 <= pout_median <= 20):
                    messagebox.showerror("Invalid Input", "Median Target P_out must be between 0 and 20 dBm")
                    return
                if j_density_median not in [3, 4, 5, 6, 7]:
                    messagebox.showerror("Invalid Input", "Median Current Density must be 3, 4, 5, 6, or 7")
                    return
                
                # Calculate using EuropaSOA
                current_ma_median = soa.calculate_current_mA_from_J(j_density_median)
                operating_voltage_median = soa.get_operating_voltage(current_ma_median)
                electrical_power_median = current_ma_median * operating_voltage_median
                
                # Calculate for each wavelength
                wavelength_results = []
                for i, wavelength in enumerate(wavelengths):
                    # Get unsaturated gain
                    unsaturated_gain_db = soa.get_unsaturated_gain(wavelength, temp_c, j_density_median)
                    
                    # Get saturation power
                    saturation_power_dbm = soa.get_output_saturation_power_dBm(wavelength, j_density_median, temp_c)
                    
                    # Find required input power for target output
                    target_pout_mw = 10**(pout_median / 10.0)
                    required_pin_mw = soa.find_Pin_for_target_Pout(target_pout_mw, current_ma_median, wavelength, temp_c)
                    
                    if required_pin_mw is not None:
                        # Calculate saturated gain and WPE
                        saturated_gain_db = soa.get_saturated_gain(wavelength, temp_c, j_density_median, required_pin_mw)
                        wpe_percent = soa.calculate_wpe(current_ma_median, wavelength, temp_c, required_pin_mw)
                        
                        wavelength_results.append(f"""Wavelength {i+1} ({wavelength:.2f} nm):
  - Unsaturated Gain: {unsaturated_gain_db:.2f} dB
  - Saturation Power: {saturation_power_dbm:.2f} dBm
  - Required P_in: {10*math.log10(required_pin_mw):.2f} dBm
  - Saturated Gain: {saturated_gain_db:.2f} dB
  - Wall Plug Efficiency: {wpe_percent:.2f} %""")
                    else:
                        wavelength_results.append(f"""Wavelength {i+1} ({wavelength:.2f} nm):
  - Unsaturated Gain: {unsaturated_gain_db:.2f} dB
  - Saturation Power: {saturation_power_dbm:.2f} dBm
  - Required P_in: Not achievable
  - Saturated Gain: N/A
  - Wall Plug Efficiency: N/A""")
                
                median_results = common_info + f"""Median Loss Case Results:
- Target P_out: {pout_median:.1f} dBm
- Current Density: {j_density_median:.1f} kA/cm²
- Operating Current: {current_ma_median:.2f} mA
- Operating Voltage: {operating_voltage_median:.3f} V
- Electrical Power: {electrical_power_median:.2f} mW

Wavelength Analysis:
{chr(10).join(wavelength_results)}"""
                
                self.median_results_text.insert(1.0, median_results)
            else:
                self.median_results_text.insert(1.0, "Median Loss Case: Not Selected")
            
            if sigma_selected:
                pout_sigma = float(self.pout_sigma_var.get())
                j_density_sigma = float(self.j_density_sigma_var.get())
                
                if not (0 <= pout_sigma <= 20):
                    messagebox.showerror("Invalid Input", "3σ Target P_out must be between 0 and 20 dBm")
                    return
                if j_density_sigma not in [3, 4, 5, 6, 7]:
                    messagebox.showerror("Invalid Input", "3σ Current Density must be 3, 4, 5, 6, or 7")
                    return
                
                # Calculate using EuropaSOA
                current_ma_sigma = soa.calculate_current_mA_from_J(j_density_sigma)
                operating_voltage_sigma = soa.get_operating_voltage(current_ma_sigma)
                electrical_power_sigma = current_ma_sigma * operating_voltage_sigma
                
                # Calculate for each wavelength
                wavelength_results = []
                for i, wavelength in enumerate(wavelengths):
                    # Get unsaturated gain
                    unsaturated_gain_db = soa.get_unsaturated_gain(wavelength, temp_c, j_density_sigma)
                    
                    # Get saturation power
                    saturation_power_dbm = soa.get_output_saturation_power_dBm(wavelength, j_density_sigma, temp_c)
                    
                    # Find required input power for target output
                    target_pout_mw = 10**(pout_sigma / 10.0)
                    required_pin_mw = soa.find_Pin_for_target_Pout(target_pout_mw, current_ma_sigma, wavelength, temp_c)
                    
                    if required_pin_mw is not None:
                        # Calculate saturated gain and WPE
                        saturated_gain_db = soa.get_saturated_gain(wavelength, temp_c, j_density_sigma, required_pin_mw)
                        wpe_percent = soa.calculate_wpe(current_ma_sigma, wavelength, temp_c, required_pin_mw)
                        
                        wavelength_results.append(f"""Wavelength {i+1} ({wavelength:.2f} nm):
  - Unsaturated Gain: {unsaturated_gain_db:.2f} dB
  - Saturation Power: {saturation_power_dbm:.2f} dBm
  - Required P_in: {10*math.log10(required_pin_mw):.2f} dBm
  - Saturated Gain: {saturated_gain_db:.2f} dB
  - Wall Plug Efficiency: {wpe_percent:.2f} %""")
                    else:
                        wavelength_results.append(f"""Wavelength {i+1} ({wavelength:.2f} nm):
  - Unsaturated Gain: {unsaturated_gain_db:.2f} dB
  - Saturation Power: {saturation_power_dbm:.2f} dBm
  - Required P_in: Not achievable
  - Saturated Gain: N/A
  - Wall Plug Efficiency: N/A""")
                
                sigma_results = common_info + f"""3σ Loss Case Results:
- Target P_out: {pout_sigma:.1f} dBm
- Current Density: {j_density_sigma:.1f} kA/cm²
- Operating Current: {current_ma_sigma:.2f} mA
- Operating Voltage: {operating_voltage_sigma:.3f} V
- Electrical Power: {electrical_power_sigma:.2f} mW

Wavelength Analysis:
{chr(10).join(wavelength_results)}"""
                
                self.sigma_results_text.insert(1.0, sigma_results)
            else:
                self.sigma_results_text.insert(1.0, "3σ Loss Case: Not Selected")
            
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all inputs are valid numbers.")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An error occurred during calculation: {e}")

    def reset_soa(self):
        """Reset all SOA inputs to default values"""
        self.w_um_var.set("2.0")
        self.l_active_var.set("790")
        self.pout_median_var.set("9")
        self.pout_sigma_var.set("13")
        self.j_density_median_var.set("4")
        self.j_density_sigma_var.set("7")
        self.num_wavelengths_var.set("8")
        
        # Reset wavelength values to defaults
        for i, wavelength_var in enumerate(self.wavelength_vars):
            wavelength_var.set(self.default_wavelengths[i])
        
        self.temp_var.set("40")
        self.link_loss_modes["median-loss"].set(True)
        self.link_loss_modes["3-sigma-loss"].set(True)
        self.median_results_text.delete(1.0, tk.END)
        self.sigma_results_text.delete(1.0, tk.END)

    def update_wavelength_inputs(self):
        """Update the wavelength input fields based on the number specified"""
        num_wavelengths = int(self.num_wavelengths_var.get())
        if num_wavelengths < 1 or num_wavelengths > 8:
            messagebox.showerror("Invalid Input", "Number of wavelengths must be between 1 and 8")
            return
        
        # Reset wavelength values to defaults
        for i, wavelength_var in enumerate(self.wavelength_vars):
            if i < num_wavelengths:
                wavelength_var.set(self.default_wavelengths[i])
            else:
                wavelength_var.set("")

    def save_wavelength_set(self):
        """Save the current wavelength set as defaults"""
        try:
            # Get current wavelength values
            new_defaults = []
            for i, wavelength_var in enumerate(self.wavelength_vars):
                wavelength_value = wavelength_var.get().strip()
                if wavelength_value:  # Only save non-empty values
                    try:
                        wavelength_float = float(wavelength_value)
                        if 1290 <= wavelength_float <= 1330:
                            new_defaults.append(wavelength_value)
                        else:
                            messagebox.showerror("Invalid Wavelength", f"Wavelength {i+1} must be between 1290 and 1330 nm")
                            return
                    except ValueError:
                        messagebox.showerror("Invalid Wavelength", f"Wavelength {i+1} must be a valid number")
                        return
                else:
                    new_defaults.append("")  # Keep empty for unused wavelengths
            
            # Update the default wavelengths
            self.default_wavelengths = new_defaults
            
            messagebox.showinfo("Wavelength Set Saved", "The current wavelength set has been saved as defaults.\nThese values will be used when updating wavelengths or resetting the form.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save wavelength set: {e}")

if __name__ == "__main__":
    app = Guide3GUI()
    app.mainloop() 