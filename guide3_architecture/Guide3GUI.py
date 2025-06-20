import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from EuropaSOA import EuropaSOA
import math
import yaml
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

class Guide3GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Guide3 GUI")
        # Set window size to 1500x1400 px and make it resizable
        self.geometry("1500x1400")
        self.resizable(True, True)
        self.link_loss_modes = {"median-loss": tk.BooleanVar(), "3-sigma-loss": tk.BooleanVar()}
        # Initialize default wavelengths
        self.default_wavelengths = ["1301.47", "1303.73", "1306.01", "1308.28", "1310.57", "1312.87", "1315.17", "1317.48"]
        
        # Default configuration
        self.default_config = {
            'device_parameters': {
                'width_um': 2.0,
                'active_length_um': 790
            },
            'operation_parameters': {
                'pout_median_dbm': 9.23,
                'pout_sigma_dbm': 12.23,
                'j_density_median': 3.76,
                'j_density_sigma': 7.15,
                'temperature_c': 40
            },
            'wavelength_config': {
                'num_wavelengths': 8,
                'wavelengths': self.default_wavelengths
            },
            'link_loss_modes': {
                'median_loss': True,
                'sigma_loss': True
            },
            'guide3a_parameters': {
                'fiber_input_type': 'pm',
                'pic_architecture': 'psrless',
                'num_fibers': 40,
                'operating_wavelength': 1310,
                'temperature': 40,
                'io_in_loss': 1.5,
                'io_out_loss': 1.5,
                'psr_loss': 0.5,
                'phase_shifter_loss': 0.5,
                'coupler_loss': 0.2,
                'target_pout': -3.3,
                'target_pout_3sigma': -0.3,
                'soa_penalty': 2,
                'soa_penalty_3sigma': 2,
                'idac_voltage_overhead': 0.4,
                'ir_drop_nominal': 0.1,
                'ir_drop_3sigma': 0.2,
                'vrm_efficiency': 80,
                'tec_cop_nominal': 2,
                'tec_cop_3sigma': 4,
                'tec_power_efficiency': 80,
                'driver_peripherals_power': 1.0,
                'mcu_power': 0.5,
                'misc_power': 0.25,
                'digital_core_efficiency': 80
            }
        }
        
        self._create_widgets()
        
        # Auto-calculate with default values
        self.auto_calculate_defaults()

    def _create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Top bar for common inputs
        topbar_frame = ttk.Frame(main_frame)
        topbar_frame.pack(fill='x', pady=(0, 10))

        # Link Loss Section (left of topbar)
        link_loss_frame = ttk.LabelFrame(topbar_frame, text="Link Loss", padding="10")
        link_loss_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(link_loss_frame, text="median-loss", variable=self.link_loss_modes["median-loss"]).pack(anchor='w')
        ttk.Checkbutton(link_loss_frame, text="3-σL-loss", variable=self.link_loss_modes["3-sigma-loss"]).pack(anchor='w')
        self.link_loss_modes["median-loss"].set(True)
        self.link_loss_modes["3-sigma-loss"].set(True)

        # Configuration Management (right of topbar)
        config_management_frame = ttk.Frame(topbar_frame)
        config_management_frame.pack(side=tk.LEFT, padx=(0, 10))
        # Defaults Management (left)
        defaults_frame = ttk.LabelFrame(config_management_frame, text="Defaults Management", padding="10")
        defaults_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(defaults_frame, text="Load Defaults", command=self.load_defaults).pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(defaults_frame, text="Update Defaults", command=self.update_defaults).pack(side=tk.LEFT, padx=5, pady=2)
        # Configuration Files (right)
        config_file_frame = ttk.LabelFrame(config_management_frame, text="Configuration Files", padding="10")
        config_file_frame.pack(side=tk.LEFT)
        ttk.Button(config_file_frame, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(config_file_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5, pady=2)

        # Wavelength Configuration (below topbar)
        wavelength_config_frame = ttk.LabelFrame(main_frame, text="Wavelength Configuration", padding="10")
        wavelength_config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Number of wavelengths (top row)
        wavelength_control_frame = ttk.Frame(wavelength_config_frame)
        wavelength_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(wavelength_control_frame, text="Number of Wavelengths:").pack(side=tk.LEFT, padx=(0, 5))
        self.num_wavelengths_var = tk.StringVar(value="8")
        self.num_wavelengths_entry = ttk.Entry(wavelength_control_frame, textvariable=self.num_wavelengths_var, width=10)
        self.num_wavelengths_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(wavelength_control_frame, text="Update Wavelengths", command=self.update_wavelength_inputs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(wavelength_control_frame, text="Save Wavelength Set", command=self.save_wavelength_set).pack(side=tk.LEFT, padx=(10, 0))
        
        # Individual wavelength inputs (grid layout: 4 rows x 8 columns) - below the controls
        self.wavelength_vars = []
        self.wavelength_entries = []
        
        # Create a frame for the wavelength grid
        wavelength_grid_frame = ttk.Frame(wavelength_config_frame)
        wavelength_grid_frame.pack(fill=tk.X)
        
        for row in range(4):
            for col in range(8):
                wavelength_index = row * 8 + col
                ttk.Label(wavelength_grid_frame, text=f"λ{wavelength_index+1}:").grid(row=row, column=col*2, padx=(0, 2), sticky='e')
                wavelength_var = tk.StringVar(value=self.default_wavelengths[wavelength_index] if wavelength_index < len(self.default_wavelengths) else "")
                wavelength_entry = ttk.Entry(wavelength_grid_frame, textvariable=wavelength_var, width=8)
                wavelength_entry.grid(row=row, column=col*2+1, padx=(0, 5), sticky='w')
                
                self.wavelength_vars.append(wavelength_var)
                self.wavelength_entries.append(wavelength_entry)

        # Notebook for tabs (model-specific content)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        # Guide3A Tab (first tab)
        self.guide3a_tab = ttk.Frame(notebook)
        notebook.add(self.guide3a_tab, text='Guide3A')
        
        # Create main frame for Guide3A
        guide3a_main_frame = ttk.Frame(self.guide3a_tab)
        guide3a_main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left side - Input parameters with scrolling (40% width)
        input_container = ttk.Frame(guide3a_main_frame)
        input_container.place(relx=0, rely=0, relwidth=0.4, relheight=1.0)
        
        # Create canvas with both scrollbars for input parameters
        input_canvas = tk.Canvas(input_container, width=600, height=1200)
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
        bottom_right_frame = ttk.Frame(input_scrollable_frame)
        bottom_right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(5, 0))
        
        # Bottom-right quadrant
        bottom_right_frame = ttk.Frame(input_scrollable_frame)
        bottom_right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=(5, 0))

        # --- Module Configuration (Top-left) ---
        module_config_frame = ttk.LabelFrame(top_left_frame, text="Module Configuration", padding="10")
        module_config_frame.pack(fill=tk.X, pady=5)
        
        # Fiber Input Type
        ttk.Label(module_config_frame, text="Fiber Input Type:").pack(pady=(5, 2), anchor='w')
        self.fiber_input_type_var = tk.StringVar(value="pm")
        self.fiber_input_type_combo = ttk.Combobox(module_config_frame, textvariable=self.fiber_input_type_var,
                                                  values=["pm", "sm"], width=20, state="readonly")
        self.fiber_input_type_combo.pack(anchor='w', padx=5, pady=(0, 10))
        
        # Bind callback to update architecture when fiber type changes
        self.fiber_input_type_combo.bind('<<ComboboxSelected>>', self.on_fiber_type_change)
        
        # PIC Architecture Selection
        ttk.Label(module_config_frame, text="PIC Architecture:").pack(pady=(5, 2), anchor='w')
        self.guide3a_architecture_var = tk.StringVar(value="psrless")
        self.guide3a_architecture_combo = ttk.Combobox(module_config_frame, textvariable=self.guide3a_architecture_var,
                                                      values=["psrless"], 
                                                      width=20, state="readonly")
        self.guide3a_architecture_combo.pack(anchor='w', padx=5, pady=(0, 10))
        # Ensure correct state for default fiber type
        if self.fiber_input_type_var.get() == "pm":
            self.guide3a_architecture_combo['state'] = "disabled"
        else:
            self.guide3a_architecture_combo['state'] = "readonly"
        
        # Number of Fibers
        ttk.Label(module_config_frame, text="Number of Fibers (multiple of 20):").pack(pady=(5, 2), anchor='w')
        self.num_fibers_var = tk.StringVar(value="40")
        self.num_fibers_entry = ttk.Entry(module_config_frame, textvariable=self.num_fibers_var, width=15)
        self.num_fibers_entry.pack(anchor='w', padx=5, pady=(0, 10))

        # Guide3A wavelength and temperature variables (hidden, used for calculations)
        self.guide3a_wavelength_var = tk.StringVar(value="1310")
        self.guide3a_temp_var = tk.StringVar(value="40")
        
        # Link Requirements Frame (moved below Module Configuration)
        link_requirements_frame = ttk.LabelFrame(top_left_frame, text="Link requirement per λ", padding="10")
        link_requirements_frame.pack(fill=tk.X, pady=5)
        
        # Target Pout
        ttk.Label(link_requirements_frame, text="Target Pout [dBm] [-10 to 20]:").pack(pady=(5, 2), anchor='w')
        self.guide3a_target_pout_var = tk.StringVar(value="-3.3")
        self.guide3a_target_pout_entry = ttk.Entry(link_requirements_frame, textvariable=self.guide3a_target_pout_var, width=15)
        self.guide3a_target_pout_entry.pack(anchor='w', padx=5)
        
        # Target Pout 3σ
        ttk.Label(link_requirements_frame, text="Target Pout 3σ [dBm] [-10 to 20]:").pack(pady=(5, 2), anchor='w')
        self.guide3a_target_pout_3sigma_var = tk.StringVar(value="-0.3")
        self.guide3a_target_pout_3sigma_entry = ttk.Entry(link_requirements_frame, textvariable=self.guide3a_target_pout_3sigma_var, width=15)
        self.guide3a_target_pout_3sigma_entry.pack(anchor='w', padx=5)
        
        # Penalty due to SOA
        ttk.Label(link_requirements_frame, text="Penalty due to SOA in dB:").pack(pady=(5, 2), anchor='w')
        self.guide3a_soa_penalty_var = tk.StringVar(value="2")
        self.guide3a_soa_penalty_entry = ttk.Entry(link_requirements_frame, textvariable=self.guide3a_soa_penalty_var, width=15)
        self.guide3a_soa_penalty_entry.pack(anchor='w', padx=5)
        
        # Penalty due to SOA 3σ
        ttk.Label(link_requirements_frame, text="Penalty due to SOA 3σ in dB:").pack(pady=(5, 2), anchor='w')
        self.guide3a_soa_penalty_3sigma_var = tk.StringVar(value="2")
        self.guide3a_soa_penalty_3sigma_entry = ttk.Entry(link_requirements_frame, textvariable=self.guide3a_soa_penalty_3sigma_var, width=15)
        self.guide3a_soa_penalty_3sigma_entry.pack(anchor='w', padx=5)
        
        # Loss Components Frame (moved below Link Requirements)
        loss_components_frame = ttk.LabelFrame(top_left_frame, text="Loss Components (dB)", padding="10")
        loss_components_frame.pack(fill=tk.X, pady=5)
        
        # I/O Loss
        ttk.Label(loss_components_frame, text="I/O Input Loss:").pack(pady=(5, 2), anchor='w')
        self.guide3a_io_in_loss_var = tk.StringVar(value="1.5")
        self.guide3a_io_in_loss_entry = ttk.Entry(loss_components_frame, textvariable=self.guide3a_io_in_loss_var, width=15)
        self.guide3a_io_in_loss_entry.pack(anchor='w', padx=5)
        
        ttk.Label(loss_components_frame, text="I/O Output Loss:").pack(pady=(5, 2), anchor='w')
        self.guide3a_io_out_loss_var = tk.StringVar(value="1.5")
        self.guide3a_io_out_loss_entry = ttk.Entry(loss_components_frame, textvariable=self.guide3a_io_out_loss_var, width=15)
        self.guide3a_io_out_loss_entry.pack(anchor='w', padx=5)
        
        # PSR Loss
        ttk.Label(loss_components_frame, text="PSR Loss:").pack(pady=(5, 2), anchor='w')
        self.guide3a_psr_loss_var = tk.StringVar(value="0.5")
        self.guide3a_psr_loss_entry = ttk.Entry(loss_components_frame, textvariable=self.guide3a_psr_loss_var, width=15)
        self.guide3a_psr_loss_entry.pack(anchor='w', padx=5)
        
        # Phase Shifter Loss
        ttk.Label(loss_components_frame, text="Phase Shifter Loss:").pack(pady=(5, 2), anchor='w')
        self.guide3a_phase_shifter_loss_var = tk.StringVar(value="0.5")
        self.guide3a_phase_shifter_entry = ttk.Entry(loss_components_frame, textvariable=self.guide3a_phase_shifter_loss_var, width=15)
        self.guide3a_phase_shifter_entry.pack(anchor='w', padx=5)
        
        # Coupler Loss
        ttk.Label(loss_components_frame, text="Coupler Loss:").pack(pady=(5, 2), anchor='w')
        self.guide3a_coupler_loss_var = tk.StringVar(value="0.2")
        self.guide3a_coupler_loss_entry = ttk.Entry(loss_components_frame, textvariable=self.guide3a_coupler_loss_var, width=15)
        self.guide3a_coupler_loss_entry.pack(anchor='w', padx=5)
        
        # Analog Section Frame (Bottom-left quadrant)
        module_parameters_frame = ttk.LabelFrame(bottom_right_frame, text="Analog Section", padding="10")
        module_parameters_frame.pack(fill=tk.X, pady=5)
        
        # IDAC Voltage Overhead
        ttk.Label(module_parameters_frame, text="IDAC Voltage Overhead (V):").pack(pady=(5, 2), anchor='w')
        self.guide3a_idac_voltage_overhead_var = tk.StringVar(value="0.4")
        self.guide3a_idac_voltage_overhead_entry = ttk.Entry(module_parameters_frame, textvariable=self.guide3a_idac_voltage_overhead_var, width=15)
        self.guide3a_idac_voltage_overhead_entry.pack(anchor='w', padx=5)
        
        # IR Drop - Nominal
        ttk.Label(module_parameters_frame, text="IR Drop - Nominal (V):").pack(pady=(5, 2), anchor='w')
        self.guide3a_ir_drop_nominal_var = tk.StringVar(value="0.1")
        self.guide3a_ir_drop_nominal_entry = ttk.Entry(module_parameters_frame, textvariable=self.guide3a_ir_drop_nominal_var, width=15)
        self.guide3a_ir_drop_nominal_entry.pack(anchor='w', padx=5)
        
        # IR Drop - 3σ
        ttk.Label(module_parameters_frame, text="IR Drop - 3σ (V):").pack(pady=(5, 2), anchor='w')
        self.guide3a_ir_drop_3sigma_var = tk.StringVar(value="0.2")
        self.guide3a_ir_drop_3sigma_entry = ttk.Entry(module_parameters_frame, textvariable=self.guide3a_ir_drop_3sigma_var, width=15)
        self.guide3a_ir_drop_3sigma_entry.pack(anchor='w', padx=5)
        
        # VRM Efficiency
        ttk.Label(module_parameters_frame, text="VRM Efficiency (%):").pack(pady=(5, 2), anchor='w')
        self.guide3a_vrm_efficiency_var = tk.StringVar(value="80")
        self.guide3a_vrm_efficiency_entry = ttk.Entry(module_parameters_frame, textvariable=self.guide3a_vrm_efficiency_var, width=15)
        self.guide3a_vrm_efficiency_entry.pack(anchor='w', padx=5)
        
        ttk.Label(module_parameters_frame, text="Digital Core Driver Efficiency (%):").pack(pady=(5, 2), anchor='w')
        self.guide3a_digital_core_efficiency_var = tk.StringVar(value="80")
        self.guide3a_digital_core_efficiency_entry = ttk.Entry(module_parameters_frame, textvariable=self.guide3a_digital_core_efficiency_var, width=15)
        self.guide3a_digital_core_efficiency_entry.pack(anchor='w', padx=5)
        
        # Action buttons will be placed under the results section
        
        # Right side - Results Display (60% width)
        guide3a_results_frame = ttk.LabelFrame(guide3a_main_frame, text="Guide3A Results", padding="10")
        guide3a_results_frame.place(relx=0.4, rely=0, relwidth=0.6, relheight=1.0)
        
        # Action buttons at the top of results section
        action_frame = ttk.Frame(guide3a_results_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(action_frame, text="Calculate", command=self.calculate_guide3a).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Reset", command=self.reset_guide3a).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Transfer to EuropaSOA", command=self.transfer_to_europasoa).pack(side=tk.LEFT, padx=5)
        
        # Create horizontal split for median and 3σ cases
        results_split_frame = ttk.Frame(guide3a_results_frame)
        results_split_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Median Case Results
        median_results_frame = ttk.LabelFrame(results_split_frame, text="Median Loss Case", padding="5")
        median_results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create canvas with scrollbars for median results
        guide3a_median_canvas = tk.Canvas(median_results_frame)
        guide3a_median_v_scrollbar = ttk.Scrollbar(median_results_frame, orient="vertical", command=guide3a_median_canvas.yview)
        
        self.guide3a_median_results_text = tk.Text(guide3a_median_canvas, wrap=tk.WORD, height=40)
        self.guide3a_median_results_text.configure(yscrollcommand=guide3a_median_v_scrollbar.set)
        
        guide3a_median_canvas.create_window((0, 0), window=self.guide3a_median_results_text, anchor="nw")
        guide3a_median_canvas.configure(yscrollcommand=guide3a_median_v_scrollbar.set)
        
        # Pack the canvas and scrollbars
        guide3a_median_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        guide3a_median_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right side - 3σ Case Results
        sigma_results_frame = ttk.LabelFrame(results_split_frame, text="3σ Loss Case", padding="5")
        sigma_results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Create canvas with scrollbars for sigma results
        guide3a_sigma_canvas = tk.Canvas(sigma_results_frame)
        guide3a_sigma_v_scrollbar = ttk.Scrollbar(sigma_results_frame, orient="vertical", command=guide3a_sigma_canvas.yview)
        
        self.guide3a_sigma_results_text = tk.Text(guide3a_sigma_canvas, wrap=tk.WORD, height=40)
        self.guide3a_sigma_results_text.configure(yscrollcommand=guide3a_sigma_v_scrollbar.set)
        
        guide3a_sigma_canvas.create_window((0, 0), window=self.guide3a_sigma_results_text, anchor="nw")
        guide3a_sigma_canvas.configure(yscrollcommand=guide3a_sigma_v_scrollbar.set)
        
        # Pack the canvas and scrollbars
        guide3a_sigma_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        guide3a_sigma_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure scroll regions when text content changes
        def configure_guide3a_median_scroll_region(event):
            guide3a_median_canvas.configure(scrollregion=guide3a_median_canvas.bbox("all"))
        
        def configure_guide3a_sigma_scroll_region(event):
            guide3a_sigma_canvas.configure(scrollregion=guide3a_sigma_canvas.bbox("all"))
        
        def resize_guide3a_median_canvas(event):
            # Update the text widget width and height to match canvas dimensions
            guide3a_median_canvas.itemconfig(1, width=event.width-10, height=event.height-10)  # Subtract some padding
        
        def resize_guide3a_sigma_canvas(event):
            # Update the text widget width and height to match canvas dimensions
            guide3a_sigma_canvas.itemconfig(1, width=event.width-10, height=event.height-10)  # Subtract some padding
        
        # Create text windows
        guide3a_median_canvas.create_window((0, 0), window=self.guide3a_median_results_text, anchor="nw")
        guide3a_sigma_canvas.create_window((0, 0), window=self.guide3a_sigma_results_text, anchor="nw")
        
        # Bind resize events
        guide3a_median_canvas.bind("<Configure>", resize_guide3a_median_canvas)
        guide3a_sigma_canvas.bind("<Configure>", resize_guide3a_sigma_canvas)
        
        self.guide3a_median_results_text.bind("<Configure>", configure_guide3a_median_scroll_region)
        self.guide3a_sigma_results_text.bind("<Configure>", configure_guide3a_sigma_scroll_region)

        # EuropaSOA Tab (second tab)
        self.soa_tab = ttk.Frame(notebook)
        notebook.add(self.soa_tab, text='EuropaSOA')
        
        # Create main horizontal frame for inputs and results
        soa_main_frame = ttk.Frame(self.soa_tab)
        soa_main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left side - Input parameters with scrolling
        input_container = ttk.Frame(soa_main_frame)
        input_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Create canvas with both scrollbars for input parameters
        input_canvas = tk.Canvas(input_container, width=600, height=1200)
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
        bottom_right_frame = ttk.Frame(input_scrollable_frame)
        bottom_right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(5, 0))
        
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

        # Target Pout for Median Loss
        self.median_pout_frame = ttk.Frame(operation_frame)
        self.median_pout_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.median_pout_frame, text="Target P_out - Median (dBm) [0-20]:").pack(pady=(5, 2), anchor='w')
        self.pout_median_var = tk.StringVar(value="9.23")
        self.pout_median_entry = ttk.Entry(self.median_pout_frame, textvariable=self.pout_median_var, width=15)
        self.pout_median_entry.pack(anchor='w', padx=5)

        # Target P_out for 3-Sigma Loss
        self.sigma_pout_frame = ttk.Frame(operation_frame)
        self.sigma_pout_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.sigma_pout_frame, text="Target P_out - 3σ (dBm) [0-20]:").pack(pady=(5, 2), anchor='w')
        self.pout_sigma_var = tk.StringVar(value="12.23")
        self.pout_sigma_entry = ttk.Entry(self.sigma_pout_frame, textvariable=self.pout_sigma_var, width=15)
        self.pout_sigma_entry.pack(anchor='w', padx=5)

        # Current Density for Median Loss
        self.median_current_frame = ttk.Frame(operation_frame)
        self.median_current_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.median_current_frame, text="Current Density - Median (kA/cm²):").pack(pady=(5, 2), anchor='w')
        self.j_density_median_var = tk.StringVar(value="3.76")
        self.j_density_median_entry = ttk.Entry(self.median_current_frame, textvariable=self.j_density_median_var, width=15)
        self.j_density_median_entry.pack(anchor='w', padx=5)

        # Current Density for 3-Sigma Loss
        self.sigma_current_frame = ttk.Frame(operation_frame)
        self.sigma_current_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.sigma_current_frame, text="Current Density - 3σ (kA/cm²):").pack(pady=(5, 2), anchor='w')
        self.j_density_sigma_var = tk.StringVar(value="7.15")
        self.j_density_sigma_entry = ttk.Entry(self.sigma_current_frame, textvariable=self.j_density_sigma_var, width=15)
        self.j_density_sigma_entry.pack(anchor='w', padx=5)

        ttk.Label(operation_frame, text="Temperature (°C) [25-80]:").pack(pady=(5, 2), anchor='w')
        self.temp_var = tk.StringVar(value="40")
        self.temp_entry = ttk.Entry(operation_frame, textvariable=self.temp_var, width=15)
        self.temp_entry.pack(anchor='w', padx=5)

        # Wavelength configuration moved to common section at top

        # Right side - Results Display
        results_frame = ttk.LabelFrame(soa_main_frame, text="Results", padding="10")
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        results_frame.pack_configure(expand=True, fill=tk.BOTH)
        results_frame.place(relx=0.2, rely=0, relwidth=0.8, relheight=1.0)
        
        # Action buttons at the top of results section
        action_frame = ttk.Frame(results_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(action_frame, text="Calculate", command=self.calculate_soa).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Reset", command=self.reset_soa).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Use Guide3A Results", command=self.use_guide3a_results).pack(side=tk.LEFT, padx=5)
        
        # Plot options frame
        plot_options_frame = ttk.LabelFrame(results_frame, text="Plot Options", padding="10")
        plot_options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create checkboxes for different plot types
        self.plot_vars = {
            'wpe_vs_length': tk.BooleanVar(),
            'gain_vs_length': tk.BooleanVar(),
            'pin_vs_length': tk.BooleanVar(),
            'wpe_vs_wavelength': tk.BooleanVar(),
            'gain_vs_wavelength': tk.BooleanVar(),
            'pin_vs_wavelength': tk.BooleanVar(),
            'saturation_vs_wavelength': tk.BooleanVar()
        }
        
        # Set defaults
        for var in self.plot_vars.values():
            var.set(True)
        
        # Create checkboxes in a grid
        row = 0
        col = 0
        for plot_name, var in self.plot_vars.items():
            display_name = plot_name.replace('_', ' ').replace('vs', 'vs').title()
            ttk.Checkbutton(plot_options_frame, text=display_name, variable=var).grid(
                row=row, column=col, sticky='w', padx=5, pady=2)
            col += 1
            if col > 3:  # 4 columns
                col = 0
                row += 1
        
        # Plot button - use grid instead of pack
        ttk.Button(plot_options_frame, text="Generate Plots", command=self.generate_plots).grid(
            row=row+1, column=0, columnspan=4, sticky='w', padx=5, pady=(10, 0))
        
        # Create horizontal split for median and 3σ cases
        results_split_frame = ttk.Frame(results_frame)
        results_split_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Median Results
        median_results_frame = ttk.LabelFrame(results_split_frame, text="Median Loss Case", padding="5")
        median_results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create canvas with scrollbars for median results
        median_canvas = tk.Canvas(median_results_frame)
        median_v_scrollbar = ttk.Scrollbar(median_results_frame, orient="vertical", command=median_canvas.yview)
        
        self.median_results_text = tk.Text(median_canvas, wrap=tk.WORD, height=40)
        self.median_results_text.configure(yscrollcommand=median_v_scrollbar.set)
        
        median_canvas.create_window((0, 0), window=self.median_results_text, anchor="nw")
        median_canvas.configure(yscrollcommand=median_v_scrollbar.set)
        
        # Pack the canvas and scrollbars
        median_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        median_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel scrolling for median results
        median_canvas.bind_all("<MouseWheel>", lambda event: median_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # Right side - 3-Sigma Results
        sigma_results_frame = ttk.LabelFrame(results_split_frame, text="3σ Loss Case", padding="5")
        sigma_results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Create canvas with scrollbars for sigma results
        sigma_canvas = tk.Canvas(sigma_results_frame)
        sigma_v_scrollbar = ttk.Scrollbar(sigma_results_frame, orient="vertical", command=sigma_canvas.yview)
        
        self.sigma_results_text = tk.Text(sigma_canvas, wrap=tk.WORD, height=40)
        self.sigma_results_text.configure(yscrollcommand=sigma_v_scrollbar.set)
        
        sigma_canvas.create_window((0, 0), window=self.sigma_results_text, anchor="nw")
        sigma_canvas.configure(yscrollcommand=sigma_v_scrollbar.set)
        
        # Pack the canvas and scrollbars
        sigma_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sigma_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel scrolling for sigma results
        sigma_canvas.bind_all("<MouseWheel>", lambda event: sigma_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # Configure scroll regions when text content changes
        def configure_soa_median_scroll_region(event):
            median_canvas.configure(scrollregion=median_canvas.bbox("all"))
        
        def configure_soa_sigma_scroll_region(event):
            sigma_canvas.configure(scrollregion=sigma_canvas.bbox("all"))
        
        def resize_soa_median_canvas(event):
            # Update the text widget width to match canvas width
            median_canvas.itemconfig(1, width=event.width-10)  # Subtract some padding
        
        def resize_soa_sigma_canvas(event):
            # Update the text widget width to match canvas width
            sigma_canvas.itemconfig(1, width=event.width-10)  # Subtract some padding
        
        # Bind resize events
        median_canvas.bind("<Configure>", resize_soa_median_canvas)
        sigma_canvas.bind("<Configure>", resize_soa_sigma_canvas)
        
        self.median_results_text.bind("<Configure>", configure_soa_median_scroll_region)
        self.sigma_results_text.bind("<Configure>", configure_soa_sigma_scroll_region)

        # Digital Core Driver Efficiency
        ttk.Label(module_parameters_frame, text="Digital Core Driver Efficiency (%):").pack(pady=(5, 2), anchor='w')
        self.guide3a_digital_core_efficiency_var = tk.StringVar(value="80")
        self.guide3a_digital_core_efficiency_entry = ttk.Entry(module_parameters_frame, textvariable=self.guide3a_digital_core_efficiency_var, width=15)
        self.guide3a_digital_core_efficiency_entry.pack(anchor='w', padx=5)
        
        # Action buttons will be placed under the results section

        # Digital Section (second)
        digital_section_frame = ttk.LabelFrame(bottom_right_frame, text="Digital Section", padding="10")
        digital_section_frame.pack(fill=tk.X, pady=5)
        
        # Driver Peripherals Power Consumption
        ttk.Label(digital_section_frame, text="Driver Peripherals Power (W):").pack(pady=(5, 2), anchor='w')
        self.guide3a_driver_peripherals_power_var = tk.StringVar(value="1.0")
        self.guide3a_driver_peripherals_power_entry = ttk.Entry(digital_section_frame, textvariable=self.guide3a_driver_peripherals_power_var, width=15)
        self.guide3a_driver_peripherals_power_entry.pack(anchor='w', padx=5)
        
        # MCU Power Consumption
        ttk.Label(digital_section_frame, text="MCU Power Consumption (W):").pack(pady=(5, 2), anchor='w')
        self.guide3a_mcu_power_var = tk.StringVar(value="0.5")
        self.guide3a_mcu_power_entry = ttk.Entry(digital_section_frame, textvariable=self.guide3a_mcu_power_var, width=15)
        self.guide3a_mcu_power_entry.pack(anchor='w', padx=5)
        
        # MISC Power Consumption
        ttk.Label(digital_section_frame, text="MISC Power Consumption (W):").pack(pady=(5, 2), anchor='w')
        self.guide3a_misc_power_var = tk.StringVar(value="0.25")
        self.guide3a_misc_power_entry = ttk.Entry(digital_section_frame, textvariable=self.guide3a_misc_power_var, width=15)
        self.guide3a_misc_power_entry.pack(anchor='w', padx=5)
        
        # Digital Core Driver Efficiency
        ttk.Label(digital_section_frame, text="Digital Core Driver Efficiency (%):").pack(pady=(5, 2), anchor='w')
        self.guide3a_digital_core_efficiency_var = tk.StringVar(value="80")
        self.guide3a_digital_core_efficiency_entry = ttk.Entry(digital_section_frame, textvariable=self.guide3a_digital_core_efficiency_var, width=15)
        self.guide3a_digital_core_efficiency_entry.pack(anchor='w', padx=5)
        
        # Thermal Section (third)
        thermal_section_frame = ttk.LabelFrame(bottom_right_frame, text="Thermal Section", padding="10")
        thermal_section_frame.pack(fill=tk.X, pady=5)
        
