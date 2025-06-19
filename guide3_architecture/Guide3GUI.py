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
        # Set window size to 1500x900 px and make it fixed size
        self.geometry("1500x900")
        self.resizable(False, False)
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
                'pout_median_dbm': 9,
                'pout_sigma_dbm': 13,
                'j_density_median': 4,
                'j_density_sigma': 7,
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
                'target_pout': -2.75,
                'target_pout_3sigma': 1.75,
                'soa_penalty': 2,
                'soa_penalty_3sigma': 2
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
        
        self.median_results_text = tk.Text(median_canvas, wrap=tk.WORD)
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
        
        self.sigma_results_text = tk.Text(sigma_canvas, wrap=tk.WORD)
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
        
        self.median_results_text.bind("<Configure>", configure_soa_median_scroll_region)
        self.sigma_results_text.bind("<Configure>", configure_soa_sigma_scroll_region)

        # Guide3A Tab (formerly EuropaPIC)
        self.guide3a_tab = ttk.Frame(notebook)
        notebook.add(self.guide3a_tab, text='Guide3A')
        
        # Create main frame for Guide3A
        guide3a_main_frame = ttk.Frame(self.guide3a_tab)
        guide3a_main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left side - Input parameters with scrolling (40% width)
        input_container = ttk.Frame(guide3a_main_frame)
        input_container.place(relx=0, rely=0, relwidth=0.4, relheight=1.0)
        
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
        self.guide3a_target_pout_var = tk.StringVar(value="-2.75")
        self.guide3a_target_pout_entry = ttk.Entry(link_requirements_frame, textvariable=self.guide3a_target_pout_var, width=15)
        self.guide3a_target_pout_entry.pack(anchor='w', padx=5)
        
        # Target Pout 3σ
        ttk.Label(link_requirements_frame, text="Target Pout 3σ [dBm] [-10 to 20]:").pack(pady=(5, 2), anchor='w')
        self.guide3a_target_pout_3sigma_var = tk.StringVar(value="1.75")
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
        
        # Loss Components Frame (Bottom-right quadrant)
        loss_components_frame = ttk.LabelFrame(bottom_right_frame, text="Loss Components (dB)", padding="10")
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
        
        # Action buttons will be placed under the results section
        
        # Right side - Results Display (60% width)
        guide3a_results_frame = ttk.LabelFrame(guide3a_main_frame, text="Guide3A Results", padding="10")
        guide3a_results_frame.place(relx=0.4, rely=0, relwidth=0.6, relheight=1.0)
        
        # Action buttons at the top of results section
        action_frame = ttk.Frame(guide3a_results_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(action_frame, text="Calculate", command=self.calculate_guide3a).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Reset", command=self.reset_guide3a).pack(side=tk.LEFT, padx=5)
        
        # Create horizontal split for median and 3σ cases
        results_split_frame = ttk.Frame(guide3a_results_frame)
        results_split_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Median Case Results
        median_results_frame = ttk.LabelFrame(results_split_frame, text="Median Loss Case", padding="5")
        median_results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Create canvas with scrollbars for median results
        guide3a_median_canvas = tk.Canvas(median_results_frame)
        guide3a_median_v_scrollbar = ttk.Scrollbar(median_results_frame, orient="vertical", command=guide3a_median_canvas.yview)
        
        self.guide3a_median_results_text = tk.Text(guide3a_median_canvas, wrap=tk.WORD)
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
        
        self.guide3a_sigma_results_text = tk.Text(guide3a_sigma_canvas, wrap=tk.WORD)
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
        
        self.guide3a_median_results_text.bind("<Configure>", configure_guide3a_median_scroll_region)
        self.guide3a_sigma_results_text.bind("<Configure>", configure_guide3a_sigma_scroll_region)

    def auto_calculate_defaults(self):
        """Automatically calculate and display results for default inputs"""
        # Calculate SOA results and display them
        self.calculate_soa()
        
        # Calculate Guide3A results and display them
        self.calculate_guide3a()

    def load_defaults(self):
        """Load the default configuration values"""
        try:
            # Load device parameters
            self.w_um_var.set(str(self.default_config['device_parameters']['width_um']))
            self.l_active_var.set(str(self.default_config['device_parameters']['active_length_um']))
            
            # Load operation parameters
            self.pout_median_var.set(str(self.default_config['operation_parameters']['pout_median_dbm']))
            self.pout_sigma_var.set(str(self.default_config['operation_parameters']['pout_sigma_dbm']))
            self.j_density_median_var.set(str(self.default_config['operation_parameters']['j_density_median']))
            self.j_density_sigma_var.set(str(self.default_config['operation_parameters']['j_density_sigma']))
            self.temp_var.set(str(self.default_config['operation_parameters']['temperature_c']))
            
            # Load wavelength configuration
            self.num_wavelengths_var.set(str(self.default_config['wavelength_config']['num_wavelengths']))
            wavelengths = self.default_config['wavelength_config']['wavelengths']
            for i, wavelength_var in enumerate(self.wavelength_vars):
                if i < len(wavelengths):
                    wavelength_var.set(wavelengths[i])
                else:
                    wavelength_var.set("")
            
            # Load link loss modes
            self.link_loss_modes["median-loss"].set(self.default_config['link_loss_modes']['median_loss'])
            self.link_loss_modes["3-sigma-loss"].set(self.default_config['link_loss_modes']['sigma_loss'])
            
            # Load Guide3A parameters
            if 'guide3a_parameters' in self.default_config:
                self.fiber_input_type_var.set(self.default_config['guide3a_parameters']['fiber_input_type'])
                self.guide3a_architecture_var.set(self.default_config['guide3a_parameters']['pic_architecture'])
                self.num_fibers_var.set(str(self.default_config['guide3a_parameters']['num_fibers']))
                self.guide3a_wavelength_var.set(str(self.default_config['guide3a_parameters']['operating_wavelength']))
                self.guide3a_temp_var.set(str(self.default_config['guide3a_parameters']['temperature']))
                self.guide3a_io_in_loss_var.set(str(self.default_config['guide3a_parameters']['io_in_loss']))
                self.guide3a_io_out_loss_var.set(str(self.default_config['guide3a_parameters']['io_out_loss']))
                self.guide3a_psr_loss_var.set(str(self.default_config['guide3a_parameters']['psr_loss']))
                self.guide3a_phase_shifter_loss_var.set(str(self.default_config['guide3a_parameters']['phase_shifter_loss']))
                self.guide3a_coupler_loss_var.set(str(self.default_config['guide3a_parameters']['coupler_loss']))
                self.guide3a_target_pout_var.set(str(self.default_config['guide3a_parameters']['target_pout']))
                self.guide3a_soa_penalty_var.set(str(self.default_config['guide3a_parameters']['soa_penalty']))
                self.guide3a_target_pout_3sigma_var.set(str(self.default_config['guide3a_parameters']['target_pout_3sigma']))
                self.guide3a_soa_penalty_3sigma_var.set(str(self.default_config['guide3a_parameters']['soa_penalty_3sigma']))
            
            messagebox.showinfo("Defaults Loaded", "Default configuration has been loaded successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load defaults: {e}")

    def update_defaults(self):
        """Update the default configuration with current values"""
        try:
            # Update device parameters
            self.default_config['device_parameters']['width_um'] = float(self.w_um_var.get())
            self.default_config['device_parameters']['active_length_um'] = float(self.l_active_var.get())
            
            # Update operation parameters
            self.default_config['operation_parameters']['pout_median_dbm'] = float(self.pout_median_var.get())
            self.default_config['operation_parameters']['pout_sigma_dbm'] = float(self.pout_sigma_var.get())
            self.default_config['operation_parameters']['j_density_median'] = float(self.j_density_median_var.get())
            self.default_config['operation_parameters']['j_density_sigma'] = float(self.j_density_sigma_var.get())
            self.default_config['operation_parameters']['temperature_c'] = float(self.temp_var.get())
            
            # Update wavelength configuration
            self.default_config['wavelength_config']['num_wavelengths'] = int(self.num_wavelengths_var.get())
            wavelengths = []
            for i, wavelength_var in enumerate(self.wavelength_vars):
                wavelength_value = wavelength_var.get().strip()
                if wavelength_value:
                    wavelengths.append(wavelength_value)
            self.default_config['wavelength_config']['wavelengths'] = wavelengths
            
            # Update link loss modes
            self.default_config['link_loss_modes']['median_loss'] = self.link_loss_modes["median-loss"].get()
            self.default_config['link_loss_modes']['sigma_loss'] = self.link_loss_modes["3-sigma-loss"].get()
            
            # Update Guide3A parameters
            if 'guide3a_parameters' in self.default_config:
                self.default_config['guide3a_parameters']['fiber_input_type'] = self.fiber_input_type_var.get()
                self.default_config['guide3a_parameters']['pic_architecture'] = self.guide3a_architecture_var.get()
                self.default_config['guide3a_parameters']['num_fibers'] = int(self.num_fibers_var.get())
                self.default_config['guide3a_parameters']['operating_wavelength'] = float(self.guide3a_wavelength_var.get())
                self.default_config['guide3a_parameters']['temperature'] = float(self.guide3a_temp_var.get())
                self.default_config['guide3a_parameters']['io_in_loss'] = float(self.guide3a_io_in_loss_var.get())
                self.default_config['guide3a_parameters']['io_out_loss'] = float(self.guide3a_io_out_loss_var.get())
                self.default_config['guide3a_parameters']['psr_loss'] = float(self.guide3a_psr_loss_var.get())
                self.default_config['guide3a_parameters']['phase_shifter_loss'] = float(self.guide3a_phase_shifter_loss_var.get())
                self.default_config['guide3a_parameters']['coupler_loss'] = float(self.guide3a_coupler_loss_var.get())
                self.default_config['guide3a_parameters']['target_pout'] = float(self.guide3a_target_pout_var.get())
                self.default_config['guide3a_parameters']['soa_penalty'] = float(self.guide3a_soa_penalty_var.get())
                self.default_config['guide3a_parameters']['target_pout_3sigma'] = float(self.guide3a_target_pout_3sigma_var.get())
                self.default_config['guide3a_parameters']['soa_penalty_3sigma'] = float(self.guide3a_soa_penalty_3sigma_var.get())
            
            messagebox.showinfo("Defaults Updated", "Default configuration has been updated with current values.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update defaults: {e}")

    def load_config(self):
        """Load configuration from a YAML file"""
        try:
            filename = filedialog.askopenfilename(
                title="Load Configuration",
                filetypes=[("YAML files", "*.yaml"), ("YML files", "*.yml"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r') as file:
                    config = yaml.safe_load(file)
                
                # Load device parameters
                if 'device_parameters' in config:
                    self.w_um_var.set(str(config['device_parameters'].get('width_um', 2.0)))
                    self.l_active_var.set(str(config['device_parameters'].get('active_length_um', 790)))
                
                # Load operation parameters
                if 'operation_parameters' in config:
                    self.pout_median_var.set(str(config['operation_parameters'].get('pout_median_dbm', 9)))
                    self.pout_sigma_var.set(str(config['operation_parameters'].get('pout_sigma_dbm', 13)))
                    self.j_density_median_var.set(str(config['operation_parameters'].get('j_density_median', 4)))
                    self.j_density_sigma_var.set(str(config['operation_parameters'].get('j_density_sigma', 7)))
                    self.temp_var.set(str(config['operation_parameters'].get('temperature_c', 40)))
                
                # Load wavelength configuration
                if 'wavelength_config' in config:
                    self.num_wavelengths_var.set(str(config['wavelength_config'].get('num_wavelengths', 8)))
                    wavelengths = config['wavelength_config'].get('wavelengths', self.default_wavelengths)
                    for i, wavelength_var in enumerate(self.wavelength_vars):
                        if i < len(wavelengths):
                            wavelength_var.set(str(wavelengths[i]))
                        else:
                            wavelength_var.set("")
                
                # Load link loss modes
                if 'link_loss_modes' in config:
                    self.link_loss_modes["median-loss"].set(config['link_loss_modes'].get('median_loss', True))
                    self.link_loss_modes["3-sigma-loss"].set(config['link_loss_modes'].get('sigma_loss', True))
                
                # Load Guide3A parameters
                if 'guide3a_parameters' in config:
                    self.fiber_input_type_var.set(config['guide3a_parameters'].get('fiber_input_type', 'pm'))
                    self.guide3a_architecture_var.set(config['guide3a_parameters'].get('pic_architecture', 'psrless'))
                    self.num_fibers_var.set(str(config['guide3a_parameters'].get('num_fibers', 40)))
                    self.guide3a_wavelength_var.set(str(config['guide3a_parameters'].get('operating_wavelength', 1310)))
                    self.guide3a_temp_var.set(str(config['guide3a_parameters'].get('temperature', 40)))
                    self.guide3a_io_in_loss_var.set(str(config['guide3a_parameters'].get('io_in_loss', 1.5)))
                    self.guide3a_io_out_loss_var.set(str(config['guide3a_parameters'].get('io_out_loss', 1.5)))
                    self.guide3a_psr_loss_var.set(str(config['guide3a_parameters'].get('psr_loss', 0.5)))
                    self.guide3a_phase_shifter_loss_var.set(str(config['guide3a_parameters'].get('phase_shifter_loss', 0.5)))
                    self.guide3a_coupler_loss_var.set(str(config['guide3a_parameters'].get('coupler_loss', 0.2)))
                    self.guide3a_target_pout_var.set(str(config['guide3a_parameters'].get('target_pout', -2.75)))
                    self.guide3a_soa_penalty_var.set(str(config['guide3a_parameters'].get('soa_penalty', 2)))
                    self.guide3a_target_pout_3sigma_var.set(str(config['guide3a_parameters'].get('target_pout_3sigma', 1.75)))
                    self.guide3a_soa_penalty_3sigma_var.set(str(config['guide3a_parameters'].get('soa_penalty_3sigma', 2)))
                
                messagebox.showinfo("Config Loaded", f"Configuration loaded from {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")

    def save_config(self):
        """Save current configuration to a YAML file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Configuration",
                defaultextension=".yaml",
                filetypes=[("YAML files", "*.yaml"), ("YML files", "*.yml"), ("All files", "*.*")]
            )
            
            if filename:
                config = {
                    'device_parameters': {
                        'width_um': float(self.w_um_var.get()),
                        'active_length_um': float(self.l_active_var.get())
                    },
                    'operation_parameters': {
                        'pout_median_dbm': float(self.pout_median_var.get()),
                        'pout_sigma_dbm': float(self.pout_sigma_var.get()),
                        'j_density_median': float(self.j_density_median_var.get()),
                        'j_density_sigma': float(self.j_density_sigma_var.get()),
                        'temperature_c': float(self.temp_var.get())
                    },
                    'wavelength_config': {
                        'num_wavelengths': int(self.num_wavelengths_var.get()),
                        'wavelengths': [wv.get().strip() for wv in self.wavelength_vars if wv.get().strip()]
                    },
                    'link_loss_modes': {
                        'median_loss': self.link_loss_modes["median-loss"].get(),
                        'sigma_loss': self.link_loss_modes["3-sigma-loss"].get()
                    },
                    'guide3a_parameters': {
                        'fiber_input_type': self.fiber_input_type_var.get(),
                        'pic_architecture': self.guide3a_architecture_var.get(),
                        'num_fibers': int(self.num_fibers_var.get()),
                        'operating_wavelength': float(self.guide3a_wavelength_var.get()),
                        'temperature': float(self.guide3a_temp_var.get()),
                        'io_in_loss': float(self.guide3a_io_in_loss_var.get()),
                        'io_out_loss': float(self.guide3a_io_out_loss_var.get()),
                        'psr_loss': float(self.guide3a_psr_loss_var.get()),
                        'phase_shifter_loss': float(self.guide3a_phase_shifter_loss_var.get()),
                        'coupler_loss': float(self.guide3a_coupler_loss_var.get()),
                        'target_pout': float(self.guide3a_target_pout_var.get()),
                        'soa_penalty': float(self.guide3a_soa_penalty_var.get()),
                        'target_pout_3sigma': float(self.guide3a_target_pout_3sigma_var.get()),
                        'soa_penalty_3sigma': float(self.guide3a_soa_penalty_3sigma_var.get())
                    }
                }
                
                with open(filename, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False, indent=2)
                
                messagebox.showinfo("Config Saved", f"Configuration saved to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def create_wavelength_table(self, wavelengths, results_data, case_name):
        """Create a formatted table for wavelength analysis results"""
        table = f"\n{case_name} Wavelength Analysis:\n"
        table += "=" * 80 + "\n"
        table += f"{'Wavelength':<12} {'Unsaturated':<12} {'Saturation':<12} {'Required':<12} {'Gain':<12} {'WPE':<8}\n"
        table += f"{'(nm)':<12} {'Gain (dB)':<12} {'Power (dBm)':<12} {'P_in (dBm)':<12} {'(dB)':<12} {'(%)':<8}\n"
        table += "-" * 80 + "\n"
        
        for i, (wavelength, data) in enumerate(zip(wavelengths, results_data)):
            if data['achievable']:
                table += f"{wavelength:<12.2f} {data['unsaturated_gain']:<12.2f} {data['saturation_power']:<12.2f} "
                table += f"{data['required_pin']:<12.2f} {data['saturated_gain']:<12.2f} {data['wpe']:<8.2f}\n"
            else:
                table += f"{wavelength:<12.2f} {data['unsaturated_gain']:<12.2f} {data['saturation_power']:<12.2f} "
                table += f"{'N/A':<12} {'N/A':<12} {'N/A':<8}\n"
        
        table += "=" * 80 + "\n"
        return table

    def calculate_soa(self):
        """Calculate SOA parameters based on input values using EuropaSOA class"""
        try:
            # Get input values
            w_um = float(self.w_um_var.get())
            l_active = float(self.l_active_var.get())
            temp_c = float(self.temp_var.get())
            
            # Get number of wavelengths and validate
            num_wavelengths = int(self.num_wavelengths_var.get())
            if num_wavelengths < 1 or num_wavelengths > 32:
                messagebox.showerror("Invalid Input", "Number of wavelengths must be between 1 and 32")
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
            
            # Get Guide3A SOA output requirements to use as target Pout
            from Guide3A import Guide3A
            
            # Get Guide3A parameters from GUI
            fiber_input_type = self.fiber_input_type_var.get()
            pic_architecture = self.guide3a_architecture_var.get()
            num_fibers = int(self.num_fibers_var.get())
            operating_wavelength = float(self.guide3a_wavelength_var.get())
            temperature = float(self.guide3a_temp_var.get())
            io_in_loss = float(self.guide3a_io_in_loss_var.get())
            io_out_loss = float(self.guide3a_io_out_loss_var.get())
            psr_loss = float(self.guide3a_psr_loss_var.get())
            phase_shifter_loss = float(self.guide3a_phase_shifter_loss_var.get())
            coupler_loss = float(self.guide3a_coupler_loss_var.get())
            target_pout = float(self.guide3a_target_pout_var.get())
            target_pout_3sigma = float(self.guide3a_target_pout_3sigma_var.get())
            soa_penalty = float(self.guide3a_soa_penalty_var.get())
            soa_penalty_3sigma = float(self.guide3a_soa_penalty_3sigma_var.get())
            
            # Create Guide3A instance to get SOA output requirements
            guide3a = Guide3A(
                pic_architecture=pic_architecture,
                fiber_input_type=fiber_input_type,
                num_fibers=num_fibers,
                operating_wavelength_nm=operating_wavelength,
                temperature_c=temperature,
                io_in_loss=io_in_loss,
                io_out_loss=io_out_loss,
                psr_loss=psr_loss,
                phase_shifter_loss=phase_shifter_loss,
                coupler_loss=coupler_loss,
                target_pout=target_pout,
                soa_penalty=soa_penalty,
                soa_penalty_3sigma=soa_penalty_3sigma
            )
            
            # Get SOA output requirements
            soa_output_calculation = guide3a.calculate_target_pout_after_soa(
                num_wavelengths=num_wavelengths,
                target_pout_3sigma=target_pout_3sigma,
                soa_penalty_3sigma=soa_penalty_3sigma
            )
            
            # Create SOA instance
            soa = EuropaSOA(L_active_um=l_active, W_um=w_um, verbose=False)
            
            # Clear results
            self.median_results_text.delete(1.0, tk.END)
            self.sigma_results_text.delete(1.0, tk.END)
            
            # Calculate and display results for each case
            if median_selected:
                median_results = self._calculate_soa_case_results(
                    soa, wavelengths, temp_c, "Median Loss",
                    soa_output_calculation['median_case']['soa_output_requirement_db'],
                    float(self.j_density_median_var.get())
                )
                self.median_results_text.insert(1.0, median_results)
            
            if sigma_selected and soa_output_calculation['sigma_case'] is not None:
                sigma_results = self._calculate_soa_case_results(
                    soa, wavelengths, temp_c, "3σ Loss",
                    soa_output_calculation['sigma_case']['soa_output_requirement_db'],
                    float(self.j_density_sigma_var.get())
                )
                self.sigma_results_text.insert(1.0, sigma_results)
            
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all values are valid numbers.")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An error occurred during calculation: {e}")

    def _calculate_soa_case_results(self, soa, wavelengths, temp_c, case_name, target_pout_db, j_density):
        """Calculate and format SOA results for a specific case"""
        results = f"""EuropaSOA Analysis Results - {case_name}
{'='*50}

Device Parameters:
- Width: {soa.W_um:.1f} µm
- Active Length: {soa.L_active_um:.0f} µm
- Temperature: {temp_c:.0f} °C
- Target Pout: {target_pout_db:.2f} dBm
- Current Density: {j_density:.0f} kA/cm²

Wavelength Analysis:
"""
        
        # Calculate current
        current_ma = soa.calculate_current_mA_from_J(j_density)
        target_pout_mw = 10**(target_pout_db / 10.0)
        
        # Create wavelength table
        results += f"{'Wavelength':<12} {'Unsaturated':<12} {'Saturation':<12} {'Required':<12} {'Gain':<12} {'WPE':<8}\n"
        results += f"{'(nm)':<12} {'Gain (dB)':<12} {'Power (dBm)':<12} {'P_in (dBm)':<12} {'(dB)':<12} {'(%)':<8}\n"
        results += "-" * 80 + "\n"
        
        for wavelength in wavelengths:
            # Get unsaturated gain
            unsaturated_gain_db = soa.get_unsaturated_gain(wavelength, temp_c, j_density)
            
            # Get saturation power
            saturation_power_dbm = soa.get_output_saturation_power_dBm(wavelength, j_density, temp_c)
            
            # Find required input power for target output
            required_pin_mw = soa.find_Pin_for_target_Pout(target_pout_mw, current_ma, wavelength, temp_c)
            
            if required_pin_mw is not None:
                # Calculate saturated gain
                saturated_gain_db = soa.get_saturated_gain(wavelength, temp_c, j_density, required_pin_mw)
                
                # Calculate WPE
                wpe = soa.calculate_wpe(current_ma, wavelength, temp_c, required_pin_mw)
                
                results += f"{wavelength:<12.2f} {unsaturated_gain_db:<12.2f} {saturation_power_dbm:<12.2f} "
                results += f"{10*math.log10(required_pin_mw):<12.2f} {saturated_gain_db:<12.2f} {wpe:<8.2f}\n"
            else:
                results += f"{wavelength:<12.2f} {unsaturated_gain_db:<12.2f} {saturation_power_dbm:<12.2f} "
                results += f"{'N/A':<12} {'N/A':<12} {'N/A':<8}\n"
        
        results += "=" * 80 + "\n"
        
        # Add summary information
        results += f"""
Summary:
- Operating Current: {current_ma:.1f} mA
- Operating Voltage: {soa.get_operating_voltage(current_ma):.2f} V
- Electrical Power: {current_ma * soa.get_operating_voltage(current_ma):.1f} mW
- Series Resistance: {soa.calculate_series_resistance_ohm():.2f} Ω

Note: Results are based on Guide3A SOA output requirements.
"""
        
        return results

    def reset_soa(self):
        """Reset all SOA inputs to default values"""
        self.w_um_var.set("2.0")
        self.l_active_var.set("790")
        self.pout_median_var.set("9")
        self.pout_sigma_var.set("13")
        self.j_density_median_var.set("4")
        self.j_density_sigma_var.set("7")
        self.num_wavelengths_var.set("8")
        
        # Reset wavelength values to defaults (first 8)
        for i, wavelength_var in enumerate(self.wavelength_vars):
            if i < len(self.default_wavelengths):
                wavelength_var.set(self.default_wavelengths[i])
            else:
                wavelength_var.set("")
        
        self.temp_var.set("40")
        self.link_loss_modes["median-loss"].set(True)
        self.link_loss_modes["3-sigma-loss"].set(True)
        self.median_results_text.delete(1.0, tk.END)
        self.sigma_results_text.delete(1.0, tk.END)

    def update_wavelength_inputs(self):
        """Update the wavelength input fields based on the number specified"""
        num_wavelengths = int(self.num_wavelengths_var.get())
        if num_wavelengths < 1 or num_wavelengths > 32:
            messagebox.showerror("Invalid Input", "Number of wavelengths must be between 1 and 32")
            return
        
        # Reset wavelength values to defaults or clear them
        for i, wavelength_var in enumerate(self.wavelength_vars):
            if i < num_wavelengths:
                if i < len(self.default_wavelengths):
                    wavelength_var.set(self.default_wavelengths[i])
                else:
                    wavelength_var.set("")  # Clear if no default available
            else:
                wavelength_var.set("")  # Clear unused fields

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
            
            # Update the default wavelengths (extend to 32 if needed)
            self.default_wavelengths = new_defaults[:32]  # Limit to 32 wavelengths
            
            messagebox.showinfo("Wavelength Set Saved", "The current wavelength set has been saved as defaults.\nThese values will be used when updating wavelengths or resetting the form.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save wavelength set: {e}")

    def generate_plots(self):
        """Generate the selected plots"""
        try:
            # Get selected plot types
            selected_plots = [name for name, var in self.plot_vars.items() if var.get()]
            
            if not selected_plots:
                messagebox.showwarning("No Plots Selected", "Please select at least one plot type.")
                return
            
            # Get current input values
            w_um = float(self.w_um_var.get())
            l_active = float(self.l_active_var.get())
            temp_c = float(self.temp_var.get())
            
            # Get number of wavelengths and validate
            num_wavelengths = int(self.num_wavelengths_var.get())
            if num_wavelengths < 1 or num_wavelengths > 32:
                messagebox.showerror("Invalid Input", "Number of wavelengths must be between 1 and 32")
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
            
            # Calculate Guide3A SOA output requirements to use as target Pout
            from Guide3A import Guide3A
            
            # Get Guide3A parameters from GUI
            fiber_input_type = self.fiber_input_type_var.get()
            pic_architecture = self.guide3a_architecture_var.get()
            num_fibers = int(self.num_fibers_var.get())
            operating_wavelength = float(self.guide3a_wavelength_var.get())
            temperature = float(self.guide3a_temp_var.get())
            io_in_loss = float(self.guide3a_io_in_loss_var.get())
            io_out_loss = float(self.guide3a_io_out_loss_var.get())
            psr_loss = float(self.guide3a_psr_loss_var.get())
            phase_shifter_loss = float(self.guide3a_phase_shifter_loss_var.get())
            coupler_loss = float(self.guide3a_coupler_loss_var.get())
            target_pout = float(self.guide3a_target_pout_var.get())
            target_pout_3sigma = float(self.guide3a_target_pout_3sigma_var.get())
            soa_penalty = float(self.guide3a_soa_penalty_var.get())
            soa_penalty_3sigma = float(self.guide3a_soa_penalty_3sigma_var.get())
            
            # Create Guide3A instance
            guide3a = Guide3A(
                pic_architecture=pic_architecture,
                fiber_input_type=fiber_input_type,
                num_fibers=num_fibers,
                operating_wavelength_nm=operating_wavelength,
                temperature_c=temperature,
                io_in_loss=io_in_loss,
                io_out_loss=io_out_loss,
                psr_loss=psr_loss,
                phase_shifter_loss=phase_shifter_loss,
                coupler_loss=coupler_loss,
                target_pout=target_pout,
                soa_penalty=soa_penalty,
                soa_penalty_3sigma=soa_penalty_3sigma
            )
            
            # Get SOA output requirements
            soa_output_calculation = guide3a.calculate_target_pout_after_soa(
                num_wavelengths=num_wavelengths,
                target_pout_3sigma=target_pout_3sigma,
                soa_penalty_3sigma=soa_penalty_3sigma
            )
            
            # Use SOA output requirements as target Pout for plots
            pout_median = soa_output_calculation['median_case']['soa_output_requirement_db'] if median_selected else None
            pout_sigma = soa_output_calculation['sigma_case']['soa_output_requirement_db'] if sigma_selected and soa_output_calculation['sigma_case'] is not None else None
            j_density_median = float(self.j_density_median_var.get()) if median_selected else None
            j_density_sigma = float(self.j_density_sigma_var.get()) if sigma_selected else None
            
            # Create SOA instance
            soa = EuropaSOA(L_active_um=l_active, W_um=w_um, verbose=False)
            
            # Generate plots
            self._create_plots(soa, selected_plots, wavelengths, temp_c, 
                             median_selected, sigma_selected,
                             pout_median, pout_sigma, j_density_median, j_density_sigma)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate plots: {e}")
    
    def _create_plots(self, soa, selected_plots, wavelengths, temp_c,
                     median_selected, sigma_selected, pout_median, pout_sigma, 
                     j_density_median, j_density_sigma):
        """Create the selected plots"""
        # Define active length range for length-based plots
        l_active_range = np.linspace(40, 880, 50)
        
        # Create subplots based on selected plots
        num_plots = len(selected_plots)
        cols = min(3, num_plots)
        rows = (num_plots + cols - 1) // cols
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[plot_name.replace('_', ' ').replace('vs', 'vs').title() 
                          for plot_name in selected_plots],
            specs=[[{"secondary_y": False}] * cols] * rows
        )
        
        plot_idx = 0
        for plot_name in selected_plots:
            row = plot_idx // cols + 1
            col = plot_idx % cols + 1
            
            if plot_name == 'wpe_vs_length':
                self._plot_wpe_vs_length(fig, soa, l_active_range, row, col, temp_c, wavelengths,
                                       median_selected, sigma_selected, pout_median, pout_sigma,
                                       j_density_median, j_density_sigma)
            elif plot_name == 'gain_vs_length':
                self._plot_gain_vs_length(fig, soa, l_active_range, row, col, temp_c, wavelengths,
                                        median_selected, sigma_selected, pout_median, pout_sigma,
                                        j_density_median, j_density_sigma)
            elif plot_name == 'pin_vs_length':
                self._plot_pin_vs_length(fig, soa, l_active_range, row, col, temp_c, wavelengths,
                                       median_selected, sigma_selected, pout_median, pout_sigma,
                                       j_density_median, j_density_sigma)
            elif plot_name == 'wpe_vs_wavelength':
                self._plot_wpe_vs_wavelength(fig, soa, row, col, temp_c, wavelengths,
                                           median_selected, sigma_selected, pout_median, pout_sigma,
                                           j_density_median, j_density_sigma)
            elif plot_name == 'gain_vs_wavelength':
                self._plot_gain_vs_wavelength(fig, soa, row, col, temp_c, wavelengths,
                                            median_selected, sigma_selected, pout_median, pout_sigma,
                                            j_density_median, j_density_sigma)
            elif plot_name == 'pin_vs_wavelength':
                self._plot_pin_vs_wavelength(fig, soa, row, col, temp_c, wavelengths,
                                           median_selected, sigma_selected, pout_median, pout_sigma,
                                           j_density_median, j_density_sigma)
            elif plot_name == 'saturation_vs_wavelength':
                self._plot_saturation_vs_wavelength(fig, soa, row, col, temp_c, wavelengths,
                                                  median_selected, sigma_selected, j_density_median, j_density_sigma)
            
            plot_idx += 1
        
        # Update layout
        fig.update_layout(
            height=200 * rows + 100,
            width=400 * cols,
            title_text="SOA Performance Analysis",
            showlegend=True
        )
        
        # Show the plot
        fig.show()
    
    def _plot_wpe_vs_length(self, fig, soa, l_active_range, row, col, temp_c, wavelengths,
                           median_selected, sigma_selected, pout_median, pout_sigma,
                           j_density_median, j_density_sigma):
        """Plot WPE vs Active Length"""
        wpe_median = []
        wpe_sigma = []
        
        for l_active in l_active_range:
            # Create SOA instance for this length
            soa_temp = EuropaSOA(L_active_um=l_active, W_um=soa.W_um, verbose=False)
            
            if median_selected:
                current_ma = soa_temp.calculate_current_mA_from_J(j_density_median)
                target_pout_mw = 10**(pout_median / 10.0)
                required_pin_mw = soa_temp.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelengths[0], temp_c)
                if required_pin_mw is not None:
                    wpe = soa_temp.calculate_wpe(current_ma, wavelengths[0], temp_c, required_pin_mw)
                    wpe_median.append(wpe)
                else:
                    wpe_median.append(None)
            
            if sigma_selected:
                current_ma = soa_temp.calculate_current_mA_from_J(j_density_sigma)
                target_pout_mw = 10**(pout_sigma / 10.0)
                required_pin_mw = soa_temp.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelengths[0], temp_c)
                if required_pin_mw is not None:
                    wpe = soa_temp.calculate_wpe(current_ma, wavelengths[0], temp_c, required_pin_mw)
                    wpe_sigma.append(wpe)
                else:
                    wpe_sigma.append(None)
        
        if median_selected:
            fig.add_trace(
                go.Scatter(x=l_active_range, y=wpe_median, mode='lines', 
                          name='Median Loss', line=dict(color='blue')),
                row=row, col=col
            )
        
        if sigma_selected:
            fig.add_trace(
                go.Scatter(x=l_active_range, y=wpe_sigma, mode='lines', 
                          name='3σ Loss', line=dict(color='red')),
                row=row, col=col
            )
        
        fig.update_xaxes(title_text="Active Length (µm)", row=row, col=col)
        fig.update_yaxes(title_text="Wall Plug Efficiency (%)", row=row, col=col)
    
    def _plot_gain_vs_length(self, fig, soa, l_active_range, row, col, temp_c, wavelengths,
                            median_selected, sigma_selected, pout_median, pout_sigma,
                            j_density_median, j_density_sigma):
        """Plot SOA Gain vs Active Length"""
        gain_median = []
        gain_sigma = []
        
        for l_active in l_active_range:
            # Create SOA instance for this length
            soa_temp = EuropaSOA(L_active_um=l_active, W_um=soa.W_um, verbose=False)
            
            if median_selected:
                current_ma = soa_temp.calculate_current_mA_from_J(j_density_median)
                target_pout_mw = 10**(pout_median / 10.0)
                required_pin_mw = soa_temp.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelengths[0], temp_c)
                if required_pin_mw is not None:
                    gain = soa_temp.get_saturated_gain(
                        wavelengths[0], temp_c, j_density_median, required_pin_mw)
                    gain_median.append(gain)
                else:
                    gain_median.append(None)
            
            if sigma_selected:
                current_ma = soa_temp.calculate_current_mA_from_J(j_density_sigma)
                target_pout_mw = 10**(pout_sigma / 10.0)
                required_pin_mw = soa_temp.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelengths[0], temp_c)
                if required_pin_mw is not None:
                    gain = soa_temp.get_saturated_gain(
                        wavelengths[0], temp_c, j_density_sigma, required_pin_mw)
                    gain_sigma.append(gain)
                else:
                    gain_sigma.append(None)
        
        if median_selected:
            fig.add_trace(
                go.Scatter(x=l_active_range, y=gain_median, mode='lines', 
                          name='Median Loss', line=dict(color='blue'), showlegend=False),
                row=row, col=col
            )
        
        if sigma_selected:
            fig.add_trace(
                go.Scatter(x=l_active_range, y=gain_sigma, mode='lines', 
                          name='3σ Loss', line=dict(color='red'), showlegend=False),
                row=row, col=col
            )
        
        fig.update_xaxes(title_text="Active Length (µm)", row=row, col=col)
        fig.update_yaxes(title_text="Gain (dB)", row=row, col=col)
    
    def _plot_pin_vs_length(self, fig, soa, l_active_range, row, col, temp_c, wavelengths,
                           median_selected, sigma_selected, pout_median, pout_sigma,
                           j_density_median, j_density_sigma):
        """Plot P_in vs Active Length"""
        pin_median = []
        pin_sigma = []
        
        for l_active in l_active_range:
            # Create SOA instance for this length
            soa_temp = EuropaSOA(L_active_um=l_active, W_um=soa.W_um, verbose=False)
            
            if median_selected:
                current_ma = soa_temp.calculate_current_mA_from_J(j_density_median)
                target_pout_mw = 10**(pout_median / 10.0)
                required_pin_mw = soa_temp.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelengths[0], temp_c)
                if required_pin_mw is not None:
                    pin_median.append(10 * np.log10(required_pin_mw))
                else:
                    pin_median.append(None)
            
            if sigma_selected:
                current_ma = soa_temp.calculate_current_mA_from_J(j_density_sigma)
                target_pout_mw = 10**(pout_sigma / 10.0)
                required_pin_mw = soa_temp.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelengths[0], temp_c)
                if required_pin_mw is not None:
                    pin_sigma.append(10 * np.log10(required_pin_mw))
                else:
                    pin_sigma.append(None)
        
        if median_selected:
            fig.add_trace(
                go.Scatter(x=l_active_range, y=pin_median, mode='lines', 
                          name='Median Loss', line=dict(color='blue'), showlegend=False),
                row=row, col=col
            )
        
        if sigma_selected:
            fig.add_trace(
                go.Scatter(x=l_active_range, y=pin_sigma, mode='lines', 
                          name='3σ Loss', line=dict(color='red'), showlegend=False),
                row=row, col=col
            )
        
        fig.update_xaxes(title_text="Active Length (µm)", row=row, col=col)
        fig.update_yaxes(title_text="Required P_in (dBm)", row=row, col=col)
    
    def _plot_wpe_vs_wavelength(self, fig, soa, row, col, temp_c, wavelengths,
                               median_selected, sigma_selected, pout_median, pout_sigma,
                               j_density_median, j_density_sigma):
        """Plot WPE vs Wavelength"""
        wpe_median = []
        wpe_sigma = []
        
        for wavelength in wavelengths:
            if median_selected:
                current_ma = soa.calculate_current_mA_from_J(j_density_median)
                target_pout_mw = 10**(pout_median / 10.0)
                required_pin_mw = soa.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelength, temp_c)
                if required_pin_mw is not None:
                    wpe = soa.calculate_wpe(current_ma, wavelength, temp_c, required_pin_mw)
                    wpe_median.append(wpe)
                else:
                    wpe_median.append(None)
            
            if sigma_selected:
                current_ma = soa.calculate_current_mA_from_J(j_density_sigma)
                target_pout_mw = 10**(pout_sigma / 10.0)
                required_pin_mw = soa.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelength, temp_c)
                if required_pin_mw is not None:
                    wpe = soa.calculate_wpe(current_ma, wavelength, temp_c, required_pin_mw)
                    wpe_sigma.append(wpe)
                else:
                    wpe_sigma.append(None)
        
        if median_selected:
            fig.add_trace(
                go.Scatter(x=wavelengths, y=wpe_median, mode='lines+markers', 
                          name='Median Loss', line=dict(color='blue'), showlegend=False),
                row=row, col=col
            )
        
        if sigma_selected:
            fig.add_trace(
                go.Scatter(x=wavelengths, y=wpe_sigma, mode='lines+markers', 
                          name='3σ Loss', line=dict(color='red'), showlegend=False),
                row=row, col=col
            )
        
        fig.update_xaxes(title_text="Wavelength (nm)", row=row, col=col)
        fig.update_yaxes(title_text="Wall Plug Efficiency (%)", row=row, col=col)
    
    def _plot_gain_vs_wavelength(self, fig, soa, row, col, temp_c, wavelengths,
                                median_selected, sigma_selected, pout_median, pout_sigma,
                                j_density_median, j_density_sigma):
        """Plot SOA Gain vs Wavelength"""
        gain_median = []
        gain_sigma = []
        
        for wavelength in wavelengths:
            if median_selected:
                current_ma = soa.calculate_current_mA_from_J(j_density_median)
                target_pout_mw = 10**(pout_median / 10.0)
                required_pin_mw = soa.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelength, temp_c)
                if required_pin_mw is not None:
                    gain = soa.get_saturated_gain(
                        wavelength, temp_c, j_density_median, required_pin_mw)
                    gain_median.append(gain)
                else:
                    gain_median.append(None)
            
            if sigma_selected:
                current_ma = soa.calculate_current_mA_from_J(j_density_sigma)
                target_pout_mw = 10**(pout_sigma / 10.0)
                required_pin_mw = soa.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelength, temp_c)
                if required_pin_mw is not None:
                    gain = soa.get_saturated_gain(
                        wavelength, temp_c, j_density_sigma, required_pin_mw)
                    gain_sigma.append(gain)
                else:
                    gain_sigma.append(None)
        
        if median_selected:
            fig.add_trace(
                go.Scatter(x=wavelengths, y=gain_median, mode='lines+markers', 
                          name='Median Loss', line=dict(color='blue'), showlegend=False),
                row=row, col=col
            )
        
        if sigma_selected:
            fig.add_trace(
                go.Scatter(x=wavelengths, y=gain_sigma, mode='lines+markers', 
                          name='3σ Loss', line=dict(color='red'), showlegend=False),
                row=row, col=col
            )
        
        fig.update_xaxes(title_text="Wavelength (nm)", row=row, col=col)
        fig.update_yaxes(title_text="Gain (dB)", row=row, col=col)
    
    def _plot_pin_vs_wavelength(self, fig, soa, row, col, temp_c, wavelengths,
                               median_selected, sigma_selected, pout_median, pout_sigma,
                               j_density_median, j_density_sigma):
        """Plot P_in vs Wavelength"""
        pin_median = []
        pin_sigma = []
        
        for wavelength in wavelengths:
            if median_selected:
                current_ma = soa.calculate_current_mA_from_J(j_density_median)
                target_pout_mw = 10**(pout_median / 10.0)
                required_pin_mw = soa.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelength, temp_c)
                if required_pin_mw is not None:
                    pin_median.append(10 * np.log10(required_pin_mw))
                else:
                    pin_median.append(None)
            
            if sigma_selected:
                current_ma = soa.calculate_current_mA_from_J(j_density_sigma)
                target_pout_mw = 10**(pout_sigma / 10.0)
                required_pin_mw = soa.find_Pin_for_target_Pout(
                    target_pout_mw, current_ma, wavelength, temp_c)
                if required_pin_mw is not None:
                    pin_sigma.append(10 * np.log10(required_pin_mw))
                else:
                    pin_sigma.append(None)
        
        if median_selected:
            fig.add_trace(
                go.Scatter(x=wavelengths, y=pin_median, mode='lines+markers', 
                          name='Median Loss', line=dict(color='blue'), showlegend=False),
                row=row, col=col
            )
        
        if sigma_selected:
            fig.add_trace(
                go.Scatter(x=wavelengths, y=pin_sigma, mode='lines+markers', 
                          name='3σ Loss', line=dict(color='red'), showlegend=False),
                row=row, col=col
            )
        
        fig.update_xaxes(title_text="Wavelength (nm)", row=row, col=col)
        fig.update_yaxes(title_text="Required P_in (dBm)", row=row, col=col)
    
    def _plot_saturation_vs_wavelength(self, fig, soa, row, col, temp_c, wavelengths,
                                      median_selected, sigma_selected, j_density_median, j_density_sigma):
        """Plot Saturation Power vs Wavelength"""
        saturation_median = []
        saturation_sigma = []
        
        for wavelength in wavelengths:
            if median_selected:
                saturation = soa.get_output_saturation_power_dBm(
                    wavelength, j_density_median, temp_c)
                saturation_median.append(saturation)
            
            if sigma_selected:
                saturation = soa.get_output_saturation_power_dBm(
                    wavelength, j_density_sigma, temp_c)
                saturation_sigma.append(saturation)
        
        if median_selected:
            fig.add_trace(
                go.Scatter(x=wavelengths, y=saturation_median, mode='lines+markers', 
                          name='Median Loss', line=dict(color='blue'), showlegend=False),
                row=row, col=col
            )
        
        if sigma_selected:
            fig.add_trace(
                go.Scatter(x=wavelengths, y=saturation_sigma, mode='lines+markers', 
                          name='3σ Loss', line=dict(color='red'), showlegend=False),
                row=row, col=col
            )
        
        fig.update_xaxes(title_text="Wavelength (nm)", row=row, col=col)
        fig.update_yaxes(title_text="Saturation Power (dBm)", row=row, col=col)

    def calculate_guide3a(self):
        """Calculate Guide3A parameters based on input values"""
        try:
            # Get input values
            w_um = float(self.w_um_var.get())
            l_active = float(self.l_active_var.get())
            temp_c = float(self.temp_var.get())
            
            # Get number of wavelengths and validate
            num_wavelengths = int(self.num_wavelengths_var.get())
            if num_wavelengths < 1 or num_wavelengths > 32:
                messagebox.showerror("Invalid Input", "Number of wavelengths must be between 1 and 32")
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
            
            # Calculate Guide3A parameters
            from Guide3A import Guide3A
            
            # Create Guide3A instance
            guide3a = Guide3A(
                pic_architecture=self.guide3a_architecture_var.get(),
                fiber_input_type=self.fiber_input_type_var.get(),
                num_fibers=int(self.num_fibers_var.get()),
                operating_wavelength_nm=float(self.guide3a_wavelength_var.get()),
                temperature_c=float(self.guide3a_temp_var.get()),
                io_in_loss=float(self.guide3a_io_in_loss_var.get()),
                io_out_loss=float(self.guide3a_io_out_loss_var.get()),
                psr_loss=float(self.guide3a_psr_loss_var.get()),
                phase_shifter_loss=float(self.guide3a_phase_shifter_loss_var.get()),
                coupler_loss=float(self.guide3a_coupler_loss_var.get()),
                target_pout=float(self.guide3a_target_pout_var.get()),
                soa_penalty=float(self.guide3a_soa_penalty_var.get()),
                soa_penalty_3sigma=float(self.guide3a_soa_penalty_3sigma_var.get())
            )
            
            # Get comprehensive analysis
            total_loss = guide3a.get_total_loss()
            loss_breakdown = guide3a.get_loss_breakdown()
            performance_metrics = guide3a.get_performance_metrics()
            component_count = guide3a.get_component_count()
            architecture_description = guide3a.get_architecture_description()
            module_config = guide3a.get_module_configuration()
            
            # Calculate target Pout for all wavelengths
            num_wavelengths = int(self.num_wavelengths_var.get())
            target_pout_calculation = guide3a.calculate_target_pout_all_wavelengths(
                num_wavelengths=num_wavelengths,
                target_pout_3sigma=float(self.guide3a_target_pout_3sigma_var.get()),
                soa_penalty_3sigma=float(self.guide3a_soa_penalty_3sigma_var.get())
            )
            
            # Calculate SOA output requirements
            soa_output_calculation = guide3a.calculate_target_pout_after_soa(
                num_wavelengths=num_wavelengths,
                target_pout_3sigma=float(self.guide3a_target_pout_3sigma_var.get()),
                soa_penalty_3sigma=float(self.guide3a_soa_penalty_3sigma_var.get())
            )
            
            # Clear results
            self.guide3a_median_results_text.delete(1.0, tk.END)
            self.guide3a_sigma_results_text.delete(1.0, tk.END)
            
            # Create common header information
            common_header = f"""Module Configuration:
- Fiber Input Type: {module_config['fiber_input_type'].upper()}
- PIC Architecture: {module_config['pic_architecture'].upper()}
- Effective Architecture: {module_config['effective_architecture'].upper()}
- Number of Fibers: {module_config['num_fibers']}
- Number of SOAs: {module_config['num_soas']}
- Number of PICs: {module_config['num_pics']}
- Number of Unit Cells: {module_config['num_unit_cells']}

Performance Parameters:
- Operating Wavelength: {float(self.guide3a_wavelength_var.get()):.0f} nm
- Temperature: {float(self.guide3a_temp_var.get()):.0f} °C

Target Pout for All Wavelengths:
- Number of Wavelengths: {target_pout_calculation['num_wavelengths']}
- Wavelength Penalty: {target_pout_calculation['wavelength_penalty_db']:.2f} dB (10*log10({target_pout_calculation['num_wavelengths']}))

SOA Output Requirements (After Output Losses Only):
- Total Output Loss: {soa_output_calculation['total_output_loss_db']:.2f} dB

Component Count:
"""
            
            for component, count in component_count.items():
                common_header += f"- {component.replace('_', ' ').title()}: {count}\n"
            
            common_header += f"""
Loss Breakdown:
- I/O Input Loss: {loss_breakdown['io_losses']['io_in_loss']:.1f} dB
- I/O Output Loss: {loss_breakdown['io_losses']['io_out_loss']:.1f} dB
- Total I/O Loss: {loss_breakdown['io_losses']['total_io_loss']:.1f} dB
"""
            
            # Add architecture-specific losses
            arch_losses = loss_breakdown['architecture_specific']
            for loss_type, value in arch_losses.items():
                if 'total' in loss_type:
                    common_header += f"- {loss_type.replace('_', ' ').title()}: {value:.1f} dB\n"
                elif loss_type == 'note':
                    common_header += f"- {value}\n"
            
            common_header += f"""
Performance Metrics:
- Total Loss: {loss_breakdown['total_loss']:.1f} dB
- Power Penalty: {performance_metrics['power_budget']['power_penalty_db']:.1f} dB
- Link Margin: {performance_metrics['power_budget']['link_margin_db']:.1f} dB
- Required TX Power: {performance_metrics['power_budget']['required_tx_power_db']:.1f} dBm
- Optical Efficiency: {performance_metrics['efficiency_metrics']['optical_efficiency_percent']:.1f}%
- Insertion Loss: {performance_metrics['efficiency_metrics']['insertion_loss_db']:.1f} dB
- Return Loss: {performance_metrics['efficiency_metrics']['return_loss_db']:.1f} dB

Architecture-Specific Analysis:
"""
            
            effective_arch = module_config['effective_architecture']
            if effective_arch == 'psr':
                common_header += f"- PSR Components: 2 × {float(self.guide3a_psr_loss_var.get()):.1f} dB = {2*float(self.guide3a_psr_loss_var.get()):.1f} dB (PSR in/out)\n"
            elif effective_arch == 'pol_control':
                common_header += f"- PSR Components: 2 × {float(self.guide3a_psr_loss_var.get()):.1f} dB = {2*float(self.guide3a_psr_loss_var.get()):.1f} dB (PSR in/out)\n"
                common_header += f"- Phase Shifter Components: 2 × {float(self.guide3a_phase_shifter_loss_var.get()):.1f} dB = {2*float(self.guide3a_phase_shifter_loss_var.get()):.1f} dB (Phase shifter in/out)\n"
                common_header += f"- Coupler Components: 2 × {float(self.guide3a_coupler_loss_var.get()):.1f} dB = {2*float(self.guide3a_coupler_loss_var.get()):.1f} dB (Coupler in/out)\n"
            elif effective_arch == 'psrless':
                common_header += f"- No additional components beyond I/O in PSRless architecture\n"
            
            common_header += f"""
Summary:
- Base I/O Loss: {loss_breakdown['io_losses']['total_io_loss']:.1f} dB
- Architecture-Specific Loss: {loss_breakdown['total_loss'] - loss_breakdown['io_losses']['total_io_loss']:.1f} dB
- Total System Loss: {loss_breakdown['total_loss']:.1f} dB

"""
            
            # Create median case content
            median_content = common_header + f"""MEDIAN LOSS CASE ANALYSIS
{'='*30}

Performance Parameters:
- Target Pout - Median: {float(self.guide3a_target_pout_var.get()):.2f} dBm
- SOA Penalty - Median: {float(self.guide3a_soa_penalty_var.get()):.1f} dB

Target Pout Calculation:
- Base Target Pout: {target_pout_calculation['median_case']['base_target_pout_db']:.2f} dBm
- SOA Penalty: {target_pout_calculation['median_case']['soa_penalty_db']:.1f} dB
- Total Target Pout: {target_pout_calculation['median_case']['total_target_pout_db']:.2f} dBm

SOA Requirements (Output Losses Only):
- Final Target Pout: {soa_output_calculation['median_case']['final_target_pout_db']:.2f} dBm
- Required SOA Output: {soa_output_calculation['median_case']['soa_output_requirement_db']:.2f} dBm
- Loss Breakdown:
  * I/O Output Loss: {soa_output_calculation['median_case']['loss_breakdown']['io_out_loss']:.1f} dB
  * Architecture Output Loss: {soa_output_calculation['median_case']['loss_breakdown']['architecture_output_loss']:.1f} dB
"""
            
            # Create 3σ case content
            sigma_content = common_header + f"""3σ LOSS CASE ANALYSIS
{'='*30}

Performance Parameters:
- Target Pout - 3σ: {float(self.guide3a_target_pout_3sigma_var.get()):.2f} dBm
- SOA Penalty - 3σ: {float(self.guide3a_soa_penalty_3sigma_var.get()):.1f} dB

"""
            
            if target_pout_calculation['sigma_case'] is not None:
                sigma_content += f"""Target Pout Calculation:
- Base Target Pout: {target_pout_calculation['sigma_case']['base_target_pout_db']:.2f} dBm
- SOA Penalty: {target_pout_calculation['sigma_case']['soa_penalty_db']:.1f} dB
- Total Target Pout: {target_pout_calculation['sigma_case']['total_target_pout_db']:.2f} dBm

"""
            else:
                sigma_content += "Target Pout Calculation: Not available\n\n"
            
            if soa_output_calculation['sigma_case'] is not None:
                sigma_content += f"""SOA Requirements (Output Losses Only):
- Final Target Pout: {soa_output_calculation['sigma_case']['final_target_pout_db']:.2f} dBm
- Required SOA Output: {soa_output_calculation['sigma_case']['soa_output_requirement_db']:.2f} dBm
- Loss Breakdown:
  * I/O Output Loss: {soa_output_calculation['sigma_case']['loss_breakdown']['io_out_loss']:.1f} dB
  * Architecture Output Loss: {soa_output_calculation['sigma_case']['loss_breakdown']['architecture_output_loss']:.1f} dB
"""
            else:
                sigma_content += "SOA Requirements: Not available"
            
            # Display results in respective text widgets
            self.guide3a_median_results_text.insert(1.0, median_content)
            self.guide3a_sigma_results_text.insert(1.0, sigma_content)
            
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all values are valid numbers.")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An error occurred during calculation: {e}")

    def reset_guide3a(self):
        """Reset all Guide3A inputs to default values"""
        self.fiber_input_type_var.set("pm")
        self.guide3a_architecture_var.set("psrless")
        self.num_fibers_var.set("40")
        
        # Reset performance parameters (matching EuropaSOA defaults)
        self.guide3a_wavelength_var.set("1310")
        self.guide3a_temp_var.set("40")
        
        # Reset loss components
        self.guide3a_io_in_loss_var.set("1.5")
        self.guide3a_io_out_loss_var.set("1.5")
        self.guide3a_psr_loss_var.set("0.5")
        self.guide3a_phase_shifter_loss_var.set("0.5")
        self.guide3a_coupler_loss_var.set("0.2")
        
        # Reset link requirements
        self.guide3a_target_pout_var.set("-2.75")
        self.guide3a_target_pout_3sigma_var.set("1.75")
        self.guide3a_soa_penalty_var.set("2")
        self.guide3a_soa_penalty_3sigma_var.set("2")
        
        self.guide3a_median_results_text.delete(1.0, tk.END)
        self.guide3a_sigma_results_text.delete(1.0, tk.END)

    def on_fiber_type_change(self, event):
        """Callback function to update PIC architecture when fiber input type changes"""
        fiber_type = self.fiber_input_type_var.get()
        
        if fiber_type == "pm":
            # For PM fiber, automatically set to psrless
            self.guide3a_architecture_var.set("psrless")
            # Update combobox values to only show psrless
            self.guide3a_architecture_combo['values'] = ["psrless"]
            self.guide3a_architecture_combo['state'] = "disabled"
        else:
            # For SM fiber, allow psr or pol_control
            self.guide3a_architecture_var.set("psr")
            # Update combobox values to show psr and pol_control
            self.guide3a_architecture_combo['values'] = ["psr", "pol_control"]
            self.guide3a_architecture_combo['state'] = "readonly"

if __name__ == "__main__":
    app = Guide3GUI()
    app.mainloop() 