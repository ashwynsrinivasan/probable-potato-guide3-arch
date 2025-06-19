import tkinter as tk
from tkinter import ttk, messagebox

class Guide3GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Guide3 GUI")
        self.geometry("800x600")
        self.link_loss_mode = tk.StringVar(value="median-loss")
        self._create_widgets()

    def _create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Link Loss Section
        link_loss_frame = ttk.LabelFrame(main_frame, text="Link Loss", padding="10")
        link_loss_frame.pack(fill='x', pady=(0, 10))

        ttk.Radiobutton(link_loss_frame, text="median-loss", 
                       variable=self.link_loss_mode, value="median-loss").pack(anchor='w')
        ttk.Radiobutton(link_loss_frame, text="3-σL-loss", 
                       variable=self.link_loss_mode, value="3-sigma-loss").pack(anchor='w')

        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        # EuropaSOA Tab
        self.soa_tab = ttk.Frame(notebook)
        notebook.add(self.soa_tab, text='EuropaSOA')
        
        # Create main horizontal frame for inputs and results
        soa_main_frame = ttk.Frame(self.soa_tab)
        soa_main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left side - Input parameters
        input_frame = ttk.Frame(soa_main_frame)
        input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Create scrollable frame for input parameters
        input_canvas = tk.Canvas(input_frame, width=300)
        input_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=input_canvas.yview)
        input_scrollable_frame = ttk.Frame(input_canvas)

        input_scrollable_frame.bind(
            "<Configure>",
            lambda e: input_canvas.configure(scrollregion=input_canvas.bbox("all"))
        )

        input_canvas.create_window((0, 0), window=input_scrollable_frame, anchor="nw")
        input_canvas.configure(yscrollcommand=input_scrollbar.set)

        input_canvas.pack(side="left", fill="both", expand=True)
        input_scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel scrolling
        input_canvas.bind_all("<MouseWheel>", lambda event: input_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

        # --- Device Parameters ---
        device_frame = ttk.LabelFrame(input_scrollable_frame, text="Device Parameters", padding="10")
        device_frame.pack(fill=tk.X, pady=5)

        ttk.Label(device_frame, text="Width (µm) [2.0-2.7]:").pack(pady=(5, 2), anchor='w')
        self.w_um_var = tk.StringVar(value="2.0")
        self.w_um_entry = ttk.Entry(device_frame, textvariable=self.w_um_var, width=15)
        self.w_um_entry.pack(anchor='w', padx=5)

        ttk.Label(device_frame, text="Active Length (µm) [40-880]:").pack(pady=(5, 2), anchor='w')
        self.l_active_var = tk.StringVar(value="440")
        self.l_active_entry = ttk.Entry(device_frame, textvariable=self.l_active_var, width=15)
        self.l_active_entry.pack(anchor='w', padx=5)

        # --- Operation Parameters ---
        operation_frame = ttk.LabelFrame(input_scrollable_frame, text="Operation Parameters", padding="10")
        operation_frame.pack(fill=tk.X, pady=5)

        ttk.Label(operation_frame, text="Target P_out (dBm) [0-20]:").pack(pady=(5, 2), anchor='w')
        self.pout_var = tk.StringVar(value="10")
        self.pout_entry = ttk.Entry(operation_frame, textvariable=self.pout_var, width=15)
        self.pout_entry.pack(anchor='w', padx=5)

        ttk.Label(operation_frame, text="Current Density (kA/cm²):").pack(pady=(5, 2), anchor='w')
        self.j_density_var = tk.StringVar(value="5")
        self.j_density_combo = ttk.Combobox(operation_frame, textvariable=self.j_density_var,
                                            values=["3", "4", "5", "6", "7"], width=12)
        self.j_density_combo.pack(anchor='w', padx=5)

        ttk.Label(operation_frame, text="Wavelength(s) (nm) [1290-1330]:").pack(pady=(5, 2), anchor='w')
        self.lambda_var = tk.StringVar(value="1310")
        self.lambda_entry = ttk.Entry(operation_frame, textvariable=self.lambda_var, width=15)
        self.lambda_entry.pack(anchor='w', padx=5)

        ttk.Label(operation_frame, text="Temperature (°C) [25-80]:").pack(pady=(5, 2), anchor='w')
        self.temp_var = tk.StringVar(value="40")
        self.temp_entry = ttk.Entry(operation_frame, textvariable=self.temp_var, width=15)
        self.temp_entry.pack(anchor='w', padx=5)

        # --- Action Buttons ---
        action_frame = ttk.Frame(input_scrollable_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="Calculate", command=self.calculate_soa).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Reset", command=self.reset_soa).pack(side=tk.LEFT, padx=5)

        # Right side - Results Display
        results_frame = ttk.LabelFrame(soa_main_frame, text="Results", padding="10")
        results_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.results_text = tk.Text(results_frame, height=20, width=50)
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # EuropaPIC Tab
        self.pic_tab = ttk.Frame(notebook)
        notebook.add(self.pic_tab, text='EuropaPIC')
        ttk.Label(self.pic_tab, text="EuropaPIC Model Interface (placeholder)").pack(padx=10, pady=10)

        # Guide3A Tab
        self.guide3a_tab = ttk.Frame(notebook)
        notebook.add(self.guide3a_tab, text='Guide3A')
        ttk.Label(self.guide3a_tab, text="Guide3A Model Interface (placeholder)").pack(padx=10, pady=10)

    def calculate_soa(self):
        """Calculate SOA parameters based on input values"""
        try:
            # Get input values
            w_um = float(self.w_um_var.get())
            l_active = float(self.l_active_var.get())
            pout_dbm = float(self.pout_var.get())
            j_density = float(self.j_density_var.get())
            lambda_nm = float(self.lambda_var.get())
            temp_c = float(self.temp_var.get())
            
            # Validate inputs
            if not (2.0 <= w_um <= 2.7):
                messagebox.showerror("Invalid Input", "Width must be between 2.0 and 2.7 µm")
                return
            if not (40 <= l_active <= 880):
                messagebox.showerror("Invalid Input", "Active Length must be between 40 and 880 µm")
                return
            if not (0 <= pout_dbm <= 20):
                messagebox.showerror("Invalid Input", "Target P_out must be between 0 and 20 dBm")
                return
            if j_density not in [3, 4, 5, 6, 7]:
                messagebox.showerror("Invalid Input", "Current Density must be 3, 4, 5, 6, or 7")
                return
            if not (1290 <= lambda_nm <= 1330):
                messagebox.showerror("Invalid Input", "Wavelength must be between 1290 and 1330 nm")
                return
            if not (25 <= temp_c <= 80):
                messagebox.showerror("Invalid Input", "Temperature must be between 25 and 80 °C")
                return
            
            # Calculate basic parameters (placeholder calculations)
            device_area_cm2 = (w_um * l_active) / 10000  # Convert µm² to cm²
            current_ma = j_density * device_area_cm2 * 10  # Convert kA/cm² to mA
            
            # Display results
            results = f"""SOA Calculation Results:
            
Device Parameters:
- Width: {w_um:.1f} µm
- Active Length: {l_active:.0f} µm
- Device Area: {device_area_cm2:.4f} cm²

Operation Parameters:
- Target P_out: {pout_dbm:.1f} dBm
- Current Density: {j_density:.1f} kA/cm²
- Wavelength: {lambda_nm:.0f} nm
- Temperature: {temp_c:.0f} °C

Calculated Values:
- Operating Current: {current_ma:.2f} mA
- Device Area: {device_area_cm2:.4f} cm²

Note: This is a placeholder calculation. 
Actual SOA model calculations would be implemented here."""
            
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, results)
            
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all inputs are valid numbers.")

    def reset_soa(self):
        """Reset all SOA inputs to default values"""
        self.w_um_var.set("2.0")
        self.l_active_var.set("440")
        self.pout_var.set("10")
        self.j_density_var.set("5")
        self.lambda_var.set("1310")
        self.temp_var.set("40")
        self.results_text.delete(1.0, tk.END)

if __name__ == "__main__":
    app = Guide3GUI()
    app.mainloop() 