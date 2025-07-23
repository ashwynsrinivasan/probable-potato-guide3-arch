import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import math
from scipy.optimize import brentq
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yaml

# --- EuropaSOA CLASS DEFINITION ---
class EuropaSOA:
    """
    Represents a Semiconductor Optical Amplifier (SOA) based on the OpenLight PIC Application Note.
    Includes optical models (Gain, Psat, NF), an analytical I-V model, and WPE calculation.
    Unsaturated gain (g0) is linearly extrapolated for L_active_um > 440um up to 900um.
    Series resistance (Rs) uses its analytical formula; warnings are issued if Lt is outside Rs model validation.
    Accepts 3-sigma delta values to modify nominal behavior.
    """
    def __init__(self, L_active_um: float, W_um: float = 2.0, verbose=False,
                 v_turn_on_delta=0.0, rs_ohm_delta=0.0, g_pk_db_delta=0.0):
        self.L_active_um_orig = L_active_um
        self.L_active_um = L_active_um
        self.W_um = W_um
        self.L_tapers_total_um = 460.0
        self.V_turn_on = 1.05 + v_turn_on_delta
        self.rs_ohm_delta = rs_ohm_delta
        self.g_pk_db_delta = g_pk_db_delta
        self.verbose = verbose

        if self.verbose:
            if not (40 <= self.L_active_um_orig <= 440):
                if 440 < self.L_active_um_orig <= 900:
                    print(f"Info: L_active_um ({self.L_active_um_orig} um) is > 440um. g0 will be linearly extrapolated.")
                elif self.L_active_um_orig > 900:
                    print(f"Warning: L_active_um ({self.L_active_um_orig} um) is > 900um. g0 extrapolated using L_eff=900um.")
                else:
                    print(f"Warning: L_active_um ({self.L_active_um_orig} um) is < 40um, outside validation range.")

            calculated_Lt_um_for_Rs_warning = self.L_active_um_orig + self.L_tapers_total_um
            if not (2.0 <= W_um <= 2.7):
                print(f"Warning (Rs Model): W_um ({W_um} um) is outside validation range [2, 2.7] um.")
            if not (500 <= calculated_Lt_um_for_Rs_warning <= 1100):
                print(f"Warning (Rs Model): Lt_um ({calculated_Lt_um_for_Rs_warning:.1f} um) is outside validation range [500, 1100] um.")

    def _calculate_Lt_um(self) -> float:
        return self.L_active_um + self.L_tapers_total_um

    def calculate_series_resistance_ohm(self) -> float:
        Lt_um_for_Rs = self.L_active_um_orig + self.L_tapers_total_um
        if self.W_um <= 1e-9 or Lt_um_for_Rs <= 1e-9: return float('inf')
        Rs_ohm_base = (4.34 / self.W_um) + (2151 / Lt_um_for_Rs) - 0.992
        Rs_ohm = Rs_ohm_base + self.rs_ohm_delta
        return Rs_ohm if Rs_ohm > 0 else 1e-3

    def get_operating_voltage(self, I_mA: float) -> float:
        Rs_ohm = self.calculate_series_resistance_ohm()
        I_Amps = I_mA * 1e-3
        return self.V_turn_on + (I_Amps * Rs_ohm)

    def calculate_current_density_kA_cm2(self, I_mA: float) -> float:
        Lt_um = self._calculate_Lt_um()
        if self.W_um <= 1e-9 or Lt_um <= 1e-9: return 0.0
        return (I_mA * 100.0) / (self.W_um * Lt_um)

    def calculate_current_mA_from_J(self, J_kA_cm2: float) -> float:
        Lt_um = self.L_active_um_orig + self.L_tapers_total_um
        if self.W_um <= 1e-9 or Lt_um <= 1e-9: return 0.0
        return J_kA_cm2 * self.W_um * Lt_um / 100.0

    def _get_g_pk_dB(self, T_C: float, J_kA_cm2: float) -> float:
        L_for_RSM = self.L_active_um
        if J_kA_cm2 <= 1e-9: return -float('inf')
        Ln_J = math.log(J_kA_cm2)
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        g_pk_base = (4.678 - 0.0729 * T_C + 10.098 * Ln_J - 0.001380 * L_plus_460_for_RSM -
                     0.00024 * (T_C - 60)**2 - 0.0081 * Ln_J * (T_C - 60) - 2.158 * Ln_J**2 -
                     0.0001589 * (T_C - 60) * (L_for_RSM - 240) + 0.02311 * Ln_J * (L_for_RSM - 240) -
                     0.000001886 * (T_C - 60)**2 * (L_for_RSM - 240) -
                     0.00002088 * Ln_J * (T_C - 60) * (L_for_RSM - 240) -
                     0.005336 * Ln_J**2 * (L_for_RSM - 240))
        return g_pk_base + self.g_pk_db_delta

    def _get_lambda_pk_nm(self, T_C: float, J_kA_cm2: float) -> float:
        L_for_RSM = self.L_active_um
        if J_kA_cm2 <= 1e-9: return float('nan')
        Ln_J = math.log(J_kA_cm2)
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        lambda_pk = (1273.73 + 0.6817 * T_C - 28.73 * Ln_J + 0.01362 * L_plus_460_for_RSM +
                     0.004585 * (T_C - 60)**2 - 0.1076 * Ln_J * (T_C - 60) + 8.787 * Ln_J**2 +
                     0.00004185 * (T_C - 60) * (L_for_RSM - 240) - 0.02367 * Ln_J * (L_for_RSM - 240) -
                     0.0000002230 * (T_C - 60)**2 * (L_for_RSM - 240) +
                     0.000136 * Ln_J * (T_C - 60) * (L_for_RSM - 240) +
                     0.004894 * Ln_J**2 * (L_for_RSM - 240))
        return lambda_pk

    def _get_fwhm_nm(self, T_C: float, J_kA_cm2: float) -> float:
        L_for_RSM = self.L_active_um
        if J_kA_cm2 <= 1e-9: return 1e-9
        Ln_J = math.log(J_kA_cm2)
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        fwhm = (120.15 - 0.0855 * T_C + 0.3837 * Ln_J - 0.07255 * L_plus_460_for_RSM +
                0.00007784 * (T_C - 60)**2 + 0.2386 * Ln_J * (T_C - 60) + 2.759 * Ln_J**2 -
                0.0004342 * (T_C - 60) * (L_for_RSM - 240) + 0.003947 * Ln_J * (L_for_RSM - 240) +
                0.00002085 * (T_C - 60)**2 * (L_for_RSM - 240) +
                0.00009466 * Ln_J * (T_C - 60) * (L_for_RSM - 240) -
                0.0007991 * Ln_J**2 * (L_for_RSM - 240))
        return fwhm if fwhm > 1e-9 else 1e-9

    def _calculate_g0_linear_at_L(self, L_val_um: float, lambda_nm: float, T_C: float, J_kA_cm2: float) -> float:
        original_L_temp_store = self.L_active_um
        self.L_active_um = L_val_um
        g_pk_dB = self._get_g_pk_dB(T_C, J_kA_cm2)
        lambda_pk_nm = self._get_lambda_pk_nm(T_C, J_kA_cm2)
        fwhm_nm = self._get_fwhm_nm(T_C, J_kA_cm2)
        self.L_active_um = original_L_temp_store
        if math.isnan(lambda_pk_nm) or g_pk_dB == -float('inf') or fwhm_nm <= 1e-9: return 0.0
        f_val_denominator = (lambda_pk_nm - lambda_nm)**2 + (fwhm_nm / 2.0)**2
        if f_val_denominator < 1e-12:
            return 10**(g_pk_dB / 10.0) if abs(lambda_nm - lambda_pk_nm) < 1e-9 else 0.0
        f_val = fwhm_nm / f_val_denominator
        max_f_val = 4.0 / fwhm_nm
        return 0.0 if abs(max_f_val) < 1e-12 else (f_val * (10**(0.1 * g_pk_dB))) / max_f_val

    def get_unsaturated_gain(self, lambda_nm: float, T_C: float, J_kA_cm2: float, output_in_dB: bool = True) -> float:
        if J_kA_cm2 <= 1e-9: return -float('inf') if output_in_dB else 0.0
        if 40 <= self.L_active_um_orig <= 440:
            g0_linear = self._calculate_g0_linear_at_L(self.L_active_um_orig, lambda_nm, T_C, J_kA_cm2)
        elif self.L_active_um_orig > 440:
            L_extrap_input = min(self.L_active_um_orig, 900.0)
            L_ref1, L_ref2 = 440.0, 430.0
            g0_at_L_ref1_linear = self._calculate_g0_linear_at_L(L_ref1, lambda_nm, T_C, J_kA_cm2)
            g0_at_L_ref2_linear = self._calculate_g0_linear_at_L(L_ref2, lambda_nm, T_C, J_kA_cm2)
            slope = (g0_at_L_ref1_linear - g0_at_L_ref2_linear) / (L_ref1 - L_ref2)
            g0_linear = g0_at_L_ref1_linear + slope * (L_extrap_input - L_ref1)
        else:
            g0_linear = self._calculate_g0_linear_at_L(self.L_active_um_orig, lambda_nm, T_C, J_kA_cm2)
        if g0_linear < 0: g0_linear = 0
        return 10 * math.log10(g0_linear) if output_in_dB and g0_linear > 1e-9 else g0_linear

    def get_output_saturation_power_dBm(self, lambda_nm: float, J_kA_cm2: float, T_C: float) -> float:
        return (-74.08 + 0.06226 * lambda_nm - 0.008877 * T_C + 0.994 * J_kA_cm2 -
                0.08721 * (J_kA_cm2 - 4.571)**2 + 0.01752 * (lambda_nm - 1310.8)**2 -
                0.00002341 * (T_C - 60.07)**2 - 0.001266 * (lambda_nm - 1310.8) * (T_C - 60.07) -
                0.001763 * (T_C - 60.07) * (J_kA_cm2 - 4.571) -
                0.008584 * (lambda_nm - 1310.8) * (J_kA_cm2 - 4.571))

    def _newton_iteration_for_gain(self, P_os_mW: float, g0_linear: float, P_in_mW: float) -> float:
        if g0_linear <= 2.000001: return g0_linear
        denominator_Ps_calc = g0_linear * math.log(2.0)
        if abs(denominator_Ps_calc) < 1e-12: return g0_linear
        P_s_mW = P_os_mW * (g0_linear - 2.0) / denominator_Ps_calc
        if P_s_mW <= 1e-12: return 0.0 if P_in_mW > 1e-9 else g0_linear
        x = g0_linear * 0.95 if P_in_mW > 1e-9 else g0_linear
        x = max(x, 1e-9)
        for _ in range(100):
            exp_arg = (1.0 - x) * P_in_mW / P_s_mW
            try: exp_val = math.exp(exp_arg) if -700 < exp_arg < 700 else (float('inf') if exp_arg >= 700 else 0.0)
            except OverflowError: exp_val = float('inf')
            f_x = x - g0_linear * exp_val
            f_prime_x = 1.0 + g0_linear * (P_in_mW / P_s_mW) * exp_val
            if abs(f_prime_x) < 1e-9: break
            x_next = x - f_x / f_prime_x
            if not (-0.1 * g0_linear < x_next < 1.5 * g0_linear + 1): break
            if x_next < 0: x_next = 1e-9
            c1, c2, x = abs(f_x), abs(x_next - x), x_next
            if c1 < 1e-5 and c2 < 1e-4: return max(0.0, x)
        return max(0.0, x)

    def get_saturated_gain(self, lambda_nm: float, T_C: float, J_kA_cm2: float, P_in_mW: float, output_in_dB: bool = True) -> float:
        if P_in_mW < 1e-9: P_in_mW = 0.0
        g0_linear = self.get_unsaturated_gain(lambda_nm, T_C, J_kA_cm2, output_in_dB=False)
        if g0_linear <= 1e-9 or P_in_mW == 0.0: g_saturated_linear = g0_linear
        else:
            P_os_dBm = self.get_output_saturation_power_dBm(lambda_nm, J_kA_cm2, T_C)
            P_os_mW = 10**(P_os_dBm / 10.0)
            g_saturated_linear = self._newton_iteration_for_gain(P_os_mW, g0_linear, P_in_mW)
        return 10 * math.log10(g_saturated_linear) if output_in_dB and g_saturated_linear > 1e-9 else g_saturated_linear

    def calculate_wpe(self, I_mA: float, lambda_nm: float, T_C: float, P_in_mW: float) -> float:
        if I_mA <= 1e-9: return 0.0
        operating_voltage_V = self.get_operating_voltage(I_mA)
        if operating_voltage_V <= 1e-9: return 0.0

        original_L_temp = self.L_active_um
        self.L_active_um = self.L_active_um_orig
        J_op_kA_cm2 = self.calculate_current_density_kA_cm2(I_mA)
        self.L_active_um = original_L_temp

        g_linear = self.get_saturated_gain(lambda_nm, T_C, J_op_kA_cm2, P_in_mW, output_in_dB=False)
        P_out_mW = g_linear * P_in_mW
        delta_P_optical_mW = P_out_mW - P_in_mW
        P_electrical_mW = I_mA * operating_voltage_V
        if P_electrical_mW <= 1e-9: return 0.0
        if delta_P_optical_mW < 0: return 0.0
        return (delta_P_optical_mW / P_electrical_mW) * 100.0

    def find_Pin_for_target_Pout(self, target_Pout_mW: float, I_mA: float, lambda_nm: float, T_C: float) -> float | None:
        original_L_temp = self.L_active_um
        self.L_active_um = self.L_active_um_orig
        J_kA_cm2 = self.calculate_current_density_kA_cm2(I_mA)
        self.L_active_um = original_L_temp
        if (J_kA_cm2 <= 1e-9 and I_mA > 1e-9) or (I_mA <= 1e-9 and target_Pout_mW > 1e-9): return None

        def objective_func(Pin_mW_local: float) -> float:
            if Pin_mW_local <= 0: return target_Pout_mW * 100 + 1
            gain_linear = self.get_saturated_gain(lambda_nm, T_C, J_kA_cm2, Pin_mW_local, output_in_dB=False)
            return gain_linear * Pin_mW_local - target_Pout_mW

        if target_Pout_mW <= 1e-9: return 0.0
        try:
            return brentq(objective_func, 1e-7, max(target_Pout_mW * 10, 1e-5))
        except (ValueError, RuntimeError):
            return None

class EuropaPIC:
    """
    Represents a Europa Photonic Integrated Circuit (PIC).
    """
    def __init__(self, pic_architecture: str):
        self.pic_architecture = pic_architecture
        self.io_in_loss = 1.5  # dB
        self.io_out_loss = 1.5 # dB
        self.psr_loss = 0.5 #dB
        self.phase_shifter_loss = 0.5 # dB
        self.coupler_loss = 0.2 # dB

    def get_total_loss(self):
        total_loss = self.io_in_loss + self.io_out_loss
        if self.pic_architecture == 'psr':
            total_loss += 2 * self.psr_loss # psr_in and psr_out
        elif self.pic_architecture == 'pol_control':
            total_loss += 2 * self.psr_loss # psr_in and psr_out
            total_loss += 2 * self.phase_shifter_loss # phase_shifter_in_1, phase_shifter_in_2
            total_loss += 2 * self.coupler_loss # coupler_in_1, coupler_in_2
        return total_loss

class Guide3A:
    """
    Represents a module with multiple PICs, each with a EuropaSOA.
    """
    def __init__(self, num_fibers: int, fiber_input_type: str, pic_architecture: str, soa_configs: dict):
        if num_fibers % 20 != 0:
            raise ValueError("Number of fibers must be a multiple of 20.")
        
        self.num_fibers = num_fibers
        self.fiber_input_type = fiber_input_type
        
        if self.fiber_input_type == 'pm':
            self.pic_architecture = 'psrless'
        else:
            self.pic_architecture = pic_architecture

        if self.pic_architecture == 'psrless':
            self.num_soas = self.num_fibers
        else:
            self.num_soas = 2 * self.num_fibers

        self.num_pics = math.ceil(self.num_soas / 20)
        self.num_unit_cells = self.num_pics

        self.pics = [EuropaPIC(pic_architecture) for _ in range(self.num_pics)]
        self.soas = [EuropaSOA(**soa_configs) for _ in range(self.num_soas)]

class Guide3GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SOA Performance Analyzer")
        self.geometry("1200x800")

        # --- Instance variables to store last used inputs ---
        self.last_inputs = None

        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Control Panel using a Notebook (Tabs) ---
        control_notebook = ttk.Notebook(main_frame)
        control_notebook.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # --- EuropaSOA Tab ---
        europa_tab = ttk.Frame(control_notebook, padding="10")
        control_notebook.add(europa_tab, text='EuropaSOA')
        
        # --- Create a canvas and a scrollbar for the tab content ---
        canvas = tk.Canvas(europa_tab)
        scrollbar = ttk.Scrollbar(europa_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- Bind mouse wheel scrolling ---
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        

        # --- Top Button Bar ---
        top_button_frame = ttk.Frame(scrollable_frame)
        top_button_frame.pack(fill=tk.X, pady=(0, 5), anchor='n')
        ttk.Button(top_button_frame, text="Load Defaults", command=self.load_default_inputs).pack(fill=tk.X, pady=(0, 2))
        ttk.Button(top_button_frame, text="Update Defaults", command=self.load_last_used_inputs).pack(fill=tk.X, pady=(2, 0))

        # --- Device Parameters ---
        device_frame = ttk.LabelFrame(scrollable_frame, text="Device Parameters", padding="10")
        device_frame.pack(fill=tk.X, pady=5)

        ttk.Label(device_frame, text="Width (µm) [2.0-2.7]:").pack(pady=(5, 2), anchor='w')
        self.w_um_var = tk.StringVar()
        self.w_um_entry = ttk.Entry(device_frame, textvariable=self.w_um_var, width=15)
        self.w_um_entry.pack(anchor='w', padx=5)

        ttk.Label(device_frame, text="Active Length (µm) [40-880]:").pack(pady=(5, 2), anchor='w')
        self.l_active_var = tk.StringVar()
        self.l_active_entry = ttk.Entry(device_frame, textvariable=self.l_active_var, width=15)
        self.l_active_entry.pack(anchor='w', padx=5)

        # --- Operation Parameters ---
        operation_frame = ttk.LabelFrame(scrollable_frame, text="Operation Parameters", padding="10")
        operation_frame.pack(fill=tk.X, pady=5)

        ttk.Label(operation_frame, text="Target P_out (dBm) [0-20]:").pack(pady=(5, 2), anchor='w')
        self.pout_var = tk.StringVar()
        self.pout_entry = ttk.Entry(operation_frame, textvariable=self.pout_var, width=15)
        self.pout_entry.pack(anchor='w', padx=5)

        ttk.Label(operation_frame, text="Current Density (kA/cm²):").pack(pady=(5, 2), anchor='w')
        self.j_nominal_var = tk.StringVar()
        self.j_nominal_combo = ttk.Combobox(operation_frame, textvariable=self.j_nominal_var,
                                            values=[3, 4, 5, 6, 7], width=12)
        self.j_nominal_combo.pack(anchor='w', padx=5)

        ttk.Label(operation_frame, text="Wavelength(s) (nm) [1290-1330]:").pack(pady=(5, 2), anchor='w')
        self.lambda_var = tk.StringVar()
        self.lambda_entry = ttk.Entry(operation_frame, textvariable=self.lambda_var, width=15)
        self.lambda_entry.pack(anchor='w', padx=5)

        ttk.Label(operation_frame, text="Temperature (°C) [25-80]:").pack(pady=(5, 2), anchor='w')
        self.temp_var = tk.StringVar()
        self.temp_entry = ttk.Entry(operation_frame, textvariable=self.temp_var, width=15)
        self.temp_entry.pack(anchor='w', padx=5)

        # --- Operation Selection ---
        op_mode_frame = ttk.LabelFrame(scrollable_frame, text="Operation Mode", padding="10")
        op_mode_frame.pack(fill=tk.X, pady=(5, 5))
        self.nominal_var = tk.BooleanVar()
        self.sigma_var = tk.BooleanVar()
        ttk.Checkbutton(op_mode_frame, text="Nominal", variable=self.nominal_var).pack(anchor='w')
        ttk.Checkbutton(op_mode_frame, text="3-sigma", variable=self.sigma_var).pack(anchor='w')

        # --- 3-sigma Condition Inputs ---
        sigma_frame = ttk.LabelFrame(scrollable_frame, text="3σ Conditions", padding="10")
        sigma_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sigma_frame, text="Target P_out (dBm) [0-20]:").pack(pady=(5, 2), anchor='w')
        self.pout_var_3s = tk.StringVar()
        self.pout_entry_3s = ttk.Entry(sigma_frame, textvariable=self.pout_var_3s, width=15)
        self.pout_entry_3s.pack(anchor='w', padx=5)
        ttk.Label(sigma_frame, text="Current Density (kA/cm²):").pack(pady=(5, 2), anchor='w')
        self.j_3sigma_var = tk.StringVar()
        self.j_3sigma_combo = ttk.Combobox(sigma_frame, textvariable=self.j_3sigma_var,
                                           values=[3, 4, 5, 6, 7], width=12)
        self.j_3sigma_combo.pack(anchor='w', padx=5)

        # --- Calculated Outputs Display ---
        self.output_frame = ttk.LabelFrame(scrollable_frame, text="Calculated Outputs", padding="10")
        self.output_frame.pack(fill=tk.X, pady=5)
        self.calc_button = ttk.Button(self.output_frame, text="Update Outputs", command=self.update_output_display)
        self.calc_button.pack(pady=5)


        # --- Plot Selection ---
        plot_select_frame = ttk.LabelFrame(scrollable_frame, text="Plots to Generate", padding="10")
        plot_select_frame.pack(fill=tk.X, pady=5)
        self.plot_wpe_var = tk.BooleanVar()
        self.plot_gain_var = tk.BooleanVar()
        self.plot_pin_var = tk.BooleanVar()
        ttk.Checkbutton(plot_select_frame, text="WPE vs. Active Length", variable=self.plot_wpe_var).pack(anchor='w', padx=5)
        ttk.Checkbutton(plot_select_frame, text="SOA Gain vs. Active Length", variable=self.plot_gain_var).pack(anchor='w', padx=5)
        ttk.Checkbutton(plot_select_frame, text="P_in vs. Active Length", variable=self.plot_pin_var).pack(anchor='w', padx=5)

        # --- Action Buttons ---
        action_button_frame = ttk.Frame(scrollable_frame)
        action_button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(action_button_frame, text="Generate Plots vs. Length", command=self.generate_plots).pack(fill=tk.X, pady=(0, 2))
        ttk.Button(action_button_frame, text="Plot vs. Wavelength", command=self.plot_performance_vs_wavelength).pack(fill=tk.X, pady=(2, 0))

        # --- Configuration Buttons ---
        config_button_frame = ttk.Frame(scrollable_frame)
        config_button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(config_button_frame, text="Load Config", command=self.load_configuration).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(config_button_frame, text="Save Config", command=self.save_configuration).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))
        
        # --- Guide 3A Tab ---
        guide3a_tab = ttk.Frame(control_notebook, padding="10")
        control_notebook.add(guide3a_tab, text='Guide 3A')
        
        guide3a_canvas = tk.Canvas(guide3a_tab)
        guide3a_scrollbar = ttk.Scrollbar(guide3a_tab, orient="vertical", command=guide3a_canvas.yview)
        guide3a_scrollable_frame = ttk.Frame(guide3a_canvas)

        guide3a_scrollable_frame.bind(
            "<Configure>",
            lambda e: guide3a_canvas.configure(
                scrollregion=guide3a_canvas.bbox("all")
            )
        )

        guide3a_canvas.create_window((0, 0), window=guide3a_scrollable_frame, anchor="nw")
        guide3a_canvas.configure(yscrollcommand=guide3a_scrollbar.set)

        guide3a_canvas.pack(side="left", fill="both", expand=True)
        guide3a_scrollbar.pack(side="right", fill="y")
        
        guide3a_canvas.bind_all("<MouseWheel>", lambda event: guide3a_canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        
        # --- Guide 3A Inputs ---
        guide3a_inputs_frame = ttk.LabelFrame(guide3a_scrollable_frame, text="Module Configuration", padding="10")
        guide3a_inputs_frame.pack(fill=tk.X, pady=5)

        ttk.Label(guide3a_inputs_frame, text="Fiber Input Type:").pack(pady=(5, 2), anchor='w')
        self.fiber_type_var = tk.StringVar()
        self.fiber_type_combo = ttk.Combobox(guide3a_inputs_frame, textvariable=self.fiber_type_var, values=['pm', 'sm'])
        self.fiber_type_combo.pack(anchor='w', padx=5)
        self.fiber_type_combo.bind("<<ComboboxSelected>>", self.update_pic_architecture_options)

        ttk.Label(guide3a_inputs_frame, text="PIC Architecture:").pack(pady=(5, 2), anchor='w')
        self.pic_arch_var = tk.StringVar()
        self.pic_arch_combo = ttk.Combobox(guide3a_inputs_frame, textvariable=self.pic_arch_var)
        self.pic_arch_combo.pack(anchor='w', padx=5)

        ttk.Label(guide3a_inputs_frame, text="Number of Fibers (multiple of 20):").pack(pady=(5, 2), anchor='w')
        self.num_fibers_var = tk.StringVar()
        self.num_fibers_entry = ttk.Entry(guide3a_inputs_frame, textvariable=self.num_fibers_var, width=15)
        self.num_fibers_entry.pack(anchor='w', padx=5)

        ttk.Button(guide3a_inputs_frame, text="Calculate Module", command=self.calculate_guide3a).pack(pady=10)
        
        # --- Guide 3A Outputs ---
        guide3a_outputs_frame = ttk.LabelFrame(guide3a_scrollable_frame, text="Module Calculation", padding="10")
        guide3a_outputs_frame.pack(fill=tk.X, pady=5)

        self.num_soas_var = tk.StringVar(value="N/A")
        self.num_pics_var = tk.StringVar(value="N/A")
        self.num_unit_cells_var = tk.StringVar(value="N/A")

        ttk.Label(guide3a_outputs_frame, text="Number of SOAs:").pack(pady=(5, 2), anchor='w')
        ttk.Label(guide3a_outputs_frame, textvariable=self.num_soas_var).pack(anchor='w', padx=5)
        ttk.Label(guide3a_outputs_frame, text="Number of PICs:").pack(pady=(5, 2), anchor='w')
        ttk.Label(guide3a_outputs_frame, textvariable=self.num_pics_var).pack(anchor='w', padx=5)
        ttk.Label(guide3a_outputs_frame, text="Number of Unit Cells:").pack(pady=(5, 2), anchor='w')
        ttk.Label(guide3a_outputs_frame, textvariable=self.num_unit_cells_var).pack(anchor='w', padx=5)

        # --- Plot Frame ---
        self.plot_frame = ttk.Frame(main_frame)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Load Initial Defaults ---
        self.load_default_inputs()
        self.load_guide3a_defaults()
        self.update_pic_architecture_options()
        self.update_output_display()

    def load_guide3a_defaults(self):
        self.fiber_type_var.set('pm')
        self.num_fibers_var.set('40')
        
    def update_pic_architecture_options(self, event=None):
        if self.fiber_type_var.get() == 'pm':
            self.pic_arch_combo['values'] = ['psrless']
            self.pic_arch_var.set('psrless')
            self.pic_arch_combo.config(state='disabled')
        else:
            self.pic_arch_combo['values'] = ['psr', 'pol_control']
            self.pic_arch_var.set('psr')
            self.pic_arch_combo.config(state='readonly')
            
    def calculate_guide3a(self):
        try:
            num_fibers = int(self.num_fibers_var.get())
            fiber_type = self.fiber_type_var.get()
            pic_arch = self.pic_arch_var.get()
            
            soa_configs = {
                'L_active_um': float(self.l_active_var.get()),
                'W_um': float(self.w_um_var.get())
            }


            if num_fibers % 20 != 0:
                messagebox.showerror("Invalid Input", "Number of fibers must be a multiple of 20.")
                return

            guide3a_module = Guide3A(num_fibers=num_fibers, fiber_input_type=fiber_type, pic_architecture=pic_arch, soa_configs=soa_configs)
            
            self.num_soas_var.set(guide3a_module.num_soas)
            self.num_pics_var.set(guide3a_module.num_pics)
            self.num_unit_cells_var.set(guide3a_module.num_unit_cells)
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of fibers must be an integer.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def load_default_inputs(self):
        """ Sets all GUI inputs to their default values. """
        self.nominal_var.set(True)
        self.sigma_var.set(True)
        self.temp_var.set("40")
        self.l_active_var.set("790")
        self.w_um_var.set("2.0")
        self.lambda_var.set("1300; 1320")
        self.plot_wpe_var.set(False)
        self.plot_gain_var.set(False)
        self.plot_pin_var.set(False)
        self.pout_var.set("8")
        self.j_nominal_var.set("3")
        self.pout_var_3s.set("12.5")
        self.j_3sigma_var.set("6")
        
    def _capture_last_inputs(self):
        """ Saves the current state of all input fields. """
        self.last_inputs = {
            'nominal_var': self.nominal_var.get(),
            'sigma_var': self.sigma_var.get(),
            'temp_var': self.temp_var.get(),
            'l_active_var': self.l_active_var.get(),
            'w_um_var': self.w_um_var.get(),
            'lambda_var': self.lambda_var.get(),
            'plot_wpe_var': self.plot_wpe_var.get(),
            'plot_gain_var': self.plot_gain_var.get(),
            'plot_pin_var': self.plot_pin_var.get(),
            'pout_var': self.pout_var.get(),
            'j_nominal_var': self.j_nominal_var.get(),
            'pout_var_3s': self.pout_var_3s.get(),
            'j_3sigma_var': self.j_3sigma_var.get()
        }

    def load_last_used_inputs(self):
        """ Loads the last used inputs into the GUI fields. """
        if self.last_inputs is None:
            messagebox.showinfo("Info", "No inputs have been used yet. Generate a plot first.")
            return

        self.nominal_var.set(self.last_inputs['nominal_var'])
        self.sigma_var.set(self.last_inputs['sigma_var'])
        self.temp_var.set(self.last_inputs['temp_var'])
        self.l_active_var.set(self.last_inputs['l_active_var'])
        self.w_um_var.set(self.last_inputs['w_um_var'])
        self.lambda_var.set(self.last_inputs['lambda_var'])
        self.plot_wpe_var.set(self.last_inputs['plot_wpe_var'])
        self.plot_gain_var.set(self.last_inputs['plot_gain_var'])
        self.plot_pin_var.set(self.last_inputs['plot_pin_var'])
        self.pout_var.set(self.last_inputs['pout_var'])
        self.j_nominal_var.set(self.last_inputs['j_nominal_var'])
        self.pout_var_3s.set(self.last_inputs['pout_var_3s'])
        self.j_3sigma_var.set(self.last_inputs['j_3sigma_var'])


    def save_configuration(self):
        """ Gathers current GUI inputs and saves them to a YAML file. """
        config_data = {
            'common_parameters': {
                'temperature_C': self.temp_var.get(),
                'active_length_um': self.l_active_var.get(),
                'width_um': self.w_um_var.get(),
                'wavelengths_nm': self.lambda_var.get()
            },
            'operation_mode': {
                'nominal': self.nominal_var.get(),
                '3_sigma': self.sigma_var.get()
            },
            'plots_to_generate': {
                'wpe_vs_length': self.plot_wpe_var.get(),
                'gain_vs_length': self.plot_gain_var.get(),
                'pin_vs_length': self.plot_pin_var.get()
            },
            'nominal_conditions': {
                'target_pout_dbm': self.pout_var.get(),
                'current_density_ka_cm2': self.j_nominal_var.get()
            },
            '3_sigma_conditions': {
                'target_pout_dbm': self.pout_var_3s.get(),
                'current_density_ka_cm2': self.j_3sigma_var.get()
            }
        }

        file_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML Files", "*.yaml"), ("All Files", "*.*")],
            title="Save Configuration As"
        )

        if not file_path:
            return  # User cancelled

        try:
            with open(file_path, 'w') as f:
                yaml.dump(config_data, f, sort_keys=False, default_flow_style=False)
            messagebox.showinfo("Success", f"Configuration saved to\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def load_configuration(self):
        """ Loads GUI inputs from a selected YAML file. """
        file_path = filedialog.askopenfilename(
            filetypes=[("YAML Files", "*.yaml"), ("All Files", "*.*")],
            title="Load Configuration"
        )

        if not file_path:
            return  # User cancelled

        try:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Set values using .get() for safety against missing keys
            # Common Parameters
            self.temp_var.set(config_data.get('common_parameters', {}).get('temperature_C', '35'))
            self.l_active_var.set(config_data.get('common_parameters', {}).get('active_length_um', '440'))
            self.w_um_var.set(config_data.get('common_parameters', {}).get('width_um', '2.0'))
            self.lambda_var.set(config_data.get('common_parameters', {}).get('wavelengths_nm', '1310'))

            # Operation Mode
            self.nominal_var.set(config_data.get('operation_mode', {}).get('nominal', True))
            self.sigma_var.set(config_data.get('operation_mode', {}).get('3_sigma', False))

            # Plots to Generate
            self.plot_wpe_var.set(config_data.get('plots_to_generate', {}).get('wpe_vs_length', True))
            self.plot_gain_var.set(config_data.get('plots_to_generate', {}).get('gain_vs_length', True))
            self.plot_pin_var.set(config_data.get('plots_to_generate', {}).get('pin_vs_length', True))

            # Nominal Conditions
            self.pout_var.set(config_data.get('nominal_conditions', {}).get('target_pout_dbm', '10'))
            self.j_nominal_var.set(config_data.get('nominal_conditions', {}).get('current_density_ka_cm2', '5'))

            # 3-sigma Conditions
            self.pout_var_3s.set(config_data.get('3_sigma_conditions', {}).get('target_pout_dbm', '13'))
            self.j_3sigma_var.set(config_data.get('3_sigma_conditions', {}).get('current_density_ka_cm2', '5'))

            messagebox.showinfo("Success", f"Configuration loaded from\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")

    def update_output_display(self):
        """Calculates and displays key metrics based on the current selections."""
        # Clear previous results
        for widget in self.output_frame.winfo_children():
            if widget != self.calc_button:
                widget.destroy()

        try:
            T_C = float(self.temp_var.get())
            l_active = float(self.l_active_var.get())
            w_um = float(self.w_um_var.get())
            
            lambda_nm_list_str = self.lambda_var.get().split(';')
            if not lambda_nm_list_str or not lambda_nm_list_str[0].strip():
                 messagebox.showerror("Input Error", "Please enter at least one wavelength.")
                 return
            lambda_nm_list = [float(l.strip()) for l in lambda_nm_list_str if l.strip()]

            
            # --- Helper function to avoid code duplication ---
            def calculate_and_display(condition_name, j_val, p_out_dbm, g_pk_delta=0.0, start_row=0):
                soa_inst = EuropaSOA(L_active_um=l_active, W_um=w_um, verbose=False, g_pk_db_delta=g_pk_delta)
                
                I_mA = soa_inst.calculate_current_mA_from_J(j_val)
                V_op = soa_inst.get_operating_voltage(I_mA)
                P_elec_mW = V_op * I_mA

                min_P_os_dBm = float('inf')
                wl_at_min_P_os = None
                for wl in lambda_nm_list:
                    P_os_dBm = soa_inst.get_output_saturation_power_dBm(wl, j_val, T_C)
                    if P_os_dBm < min_P_os_dBm:
                        min_P_os_dBm = P_os_dBm
                        wl_at_min_P_os = wl
                
                P_out_mW = 10**(p_out_dbm / 10.0)
                first_lambda_nm = lambda_nm_list[0]
                P_in_mW = soa_inst.find_Pin_for_target_Pout(P_out_mW, I_mA, first_lambda_nm, T_C)
                
                wpe = float('nan')
                if P_in_mW is not None:
                    wpe = soa_inst.calculate_wpe(I_mA, first_lambda_nm, T_C, P_in_mW)

                
                ttk.Label(self.output_frame, text=f"--- {condition_name} ---", font=("", 10, "bold")).grid(row=start_row, column=0, columnspan=2, sticky='w', pady=(5,0))

                results = {
                    "Saturation Power": f"{min_P_os_dBm:.2f} dBm (at {wl_at_min_P_os} nm)",
                    "SOA Voltage": f"{V_op:.2f} V",
                    "SOA Current": f"{I_mA:.2f} mA",
                    "Output Optical Power": f"{p_out_dbm:.2f} dBm ({P_out_mW:.2f} mW)",
                    "Input Electrical Power": f"{P_elec_mW:.2f} mW",
                    "Wall Plug Efficiency": f"{wpe:.2f} %"
                }

                for i, (text, value) in enumerate(results.items()):
                    ttk.Label(self.output_frame, text=f"{text}:").grid(row=start_row + i + 1, column=0, sticky='w', padx=2, pady=1)
                    ttk.Label(self.output_frame, text=value).grid(row=start_row + i + 1, column=1, sticky='w', padx=2, pady=1)
                
                return start_row + len(results) + 1


            next_row = 1 # Start displaying results from row 1, as button is in row 0
            if self.nominal_var.get():
                j_nominal = float(self.j_nominal_var.get())
                pout_nominal = float(self.pout_var.get())
                next_row = calculate_and_display("Nominal", j_nominal, pout_nominal, start_row=next_row)

            if self.sigma_var.get():
                j_3sigma = float(self.j_3sigma_var.get())
                pout_3s = float(self.pout_var_3s.get())
                # Example: Assuming 3-sigma affects peak gain. Replace with actual delta if needed.
                g_pk_delta_3s = 0.5 
                calculate_and_display("3-Sigma", j_3sigma, pout_3s, g_pk_delta=g_pk_delta_3s, start_row=next_row)

        except (ValueError, IndexError) as e:
            messagebox.showerror("Input Error", f"Could not calculate outputs. Please check your inputs.\nError: {e}")
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An unexpected error occurred: {e}")


    def validate_inputs(self):
        try:
            temp = float(self.temp_var.get())
            if not (25 <= temp <= 80): messagebox.showerror("Invalid Input", "Temperature must be between 25 and 80 °C."); return None
        except ValueError: messagebox.showerror("Invalid Input", "Temperature must be a numeric value."); return None
        
        try:
            w_um = float(self.w_um_var.get())
            if not (2.0 <= w_um <= 2.7): messagebox.showerror("Invalid Input", "Width must be between 2.0 and 2.7 µm."); return None
        except ValueError: messagebox.showerror("Invalid Input", "Width must be a numeric value."); return None

        try:
            lambda_nm_list = [float(l.strip()) for l in self.lambda_var.get().split(';') if l.strip()]
            if not lambda_nm_list:
                messagebox.showerror("Invalid Input", "Wavelength input cannot be empty.")
                return None
            for l_val in lambda_nm_list:
                if not (1290 <= l_val <= 1330):
                    messagebox.showerror("Invalid Input", f"Wavelength {l_val} must be between 1290 and 1330 nm.")
                    return None
        except ValueError:
            messagebox.showerror("Invalid Input", "Wavelength must be a semicolon-separated list of numeric values.")
            return None

        try:
            pout_nominal = float(self.pout_var.get())
            if not (0 <= pout_nominal <= 20): messagebox.showerror("Invalid Input", "Nominal Target P_out must be between 0 and 20 dBm."); return None
        except ValueError: messagebox.showerror("Invalid Input", "Nominal Target P_out must be a numeric value."); return None

        try:
            pout_3s = float(self.pout_var_3s.get())
            if not (0 <= pout_3s <= 20): messagebox.showerror("Invalid Input", "3σ Target P_out must be between 0 and 20 dBm."); return None
        except ValueError: messagebox.showerror("Invalid Input", "3σ Target P_out must be a numeric value."); return None

        try:
            j_nominal = float(self.j_nominal_var.get())
            if j_nominal not in [3, 4, 5, 6, 7]: messagebox.showerror("Invalid Input", "Nominal Current Density must be 3, 4, 5, 6, or 7."); return None
        except ValueError: messagebox.showerror("Invalid Input", "Nominal Current Density must be a numeric value."); return None

        try:
            j_3sigma = float(self.j_3sigma_var.get())
            if j_3sigma not in [3, 4, 5, 6, 7]: messagebox.showerror("Invalid Input", "3σ Current Density must be 3, 4, 5, 6, or 7."); return None
        except ValueError: messagebox.showerror("Invalid Input", "3σ Current Density must be a numeric value."); return None

        try:
            l_active = float(self.l_active_var.get())
            if not (40 <= l_active <= 880): messagebox.showerror("Invalid Input", "Active Length must be between 40 and 880 µm."); return None
        except ValueError: messagebox.showerror("Invalid Input", "Active Length must be a numeric value."); return None

        return temp, w_um, lambda_nm_list, pout_nominal, pout_3s, j_nominal, j_3sigma, l_active

    def generate_plots(self):
        validated_data = self.validate_inputs()
        if validated_data is None: return
        
        self._capture_last_inputs()

        T_C, w_um, lambda_nm_list, target_Pout_dBm_nominal, target_Pout_dBm_3s, j_nominal, j_3sigma, l_active_annotate = validated_data
        lambda_to_plot = max(lambda_nm_list)

        plot_window = tk.Toplevel(self)
        plot_window.title("SOA Performance Plots")
        
        selected_plots = []
        if self.plot_wpe_var.get(): selected_plots.append('wpe')
        if self.plot_gain_var.get(): selected_plots.append('gain')
        if self.plot_pin_var.get(): selected_plots.append('pin')

        if not selected_plots:
            messagebox.showinfo("No Selection", "Please select at least one plot to generate.")
            return

        num_plots = len(selected_plots)
        fig, axes = plt.subplots(num_plots, 1, figsize=(10, 5 * num_plots), sharex=True)
        if num_plots == 1:
            axes = [axes]

        fig.suptitle(f'SOA Performance vs. Active Length (W={w_um}µm, T={T_C:.0f}°C, λ={lambda_to_plot:.0f}nm)', fontsize=16)

        plot_map = {
            'wpe': {'ax': None, 'data_key': 'wpe', 'ylabel': 'WPE (%)'},
            'gain': {'ax': None, 'data_key': 'gain', 'ylabel': 'SOA Gain (dB)'},
            'pin': {'ax': None, 'data_key': 'pin', 'ylabel': 'Required P_in (dBm)'}
        }

        ax_idx = 0
        for plot_key in selected_plots:
            plot_map[plot_key]['ax'] = axes[ax_idx]
            ax_idx += 1

        if self.nominal_var.get():
            plot_data_nominal = self.calculate_plot_data(target_Pout_dBm_nominal, w_um, T_C, lambda_to_plot)
            for J_val, data in plot_data_nominal.items():
                for plot_key in selected_plots:
                    plot_map[plot_key]['ax'].plot(data['L_active'], data[plot_map[plot_key]['data_key']], marker='.', linestyle='-', label=f'J={J_val:.1f} (Nominal)')

        if self.sigma_var.get():
            plot_data_3s = self.calculate_plot_data(target_Pout_dBm_3s, w_um, T_C, lambda_to_plot)
            for J_val, data in plot_data_3s.items():
                for plot_key in selected_plots:
                    plot_map[plot_key]['ax'].plot(data['L_active'], data[plot_map[plot_key]['data_key']], marker='x', linestyle='--', label=f'J={J_val:.1f} (3σ)')

        if l_active_annotate:
            if self.nominal_var.get() and j_nominal in plot_data_nominal:
                data_for_j = plot_data_nominal[j_nominal]
                for plot_key in selected_plots:
                    ax = plot_map[plot_key]['ax']
                    y_interp = np.interp(l_active_annotate, data_for_j['L_active'], data_for_j[plot_map[plot_key]['data_key']])
                    ax.axvline(x=l_active_annotate, color='b', linestyle='--', linewidth=1)
                    ax.plot(l_active_annotate, y_interp, 'b*', markersize=12, label=f'Nominal Annotation')
                    ax.annotate(f'Nominal: {y_interp:.2f}', (l_active_annotate, y_interp), textcoords="offset points", xytext=(5,-15), ha='left', color='b')

            if self.sigma_var.get() and j_3sigma in plot_data_3s:
                data_for_j = plot_data_3s[j_3sigma]
                for plot_key in selected_plots:
                    ax = plot_map[plot_key]['ax']
                    y_interp = np.interp(l_active_annotate, data_for_j['L_active'], data_for_j[plot_map[plot_key]['data_key']])
                    ax.axvline(x=l_active_annotate, color='r', linestyle='--', linewidth=1)
                    ax.plot(l_active_annotate, y_interp, 'r*', markersize=12, label=f'3σ Annotation')
                    ax.annotate(f'3σ: {y_interp:.2f}', (l_active_annotate, y_interp), textcoords="offset points", xytext=(5,5), ha='left', color='r')

        for plot_key in selected_plots:
            ax = plot_map[plot_key]['ax']
            ax.set_ylabel(plot_map[plot_key]['ylabel'])
            ax.grid(True)
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys())

        axes[-1].set_xlabel('Active Length (µm)')
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        self.embed_plot(fig, plot_window)

    def calculate_plot_data(self, target_Pout_dBm, w_um, T_C, lambda_nm, v_delta=0, rs_delta=0, gpk_delta=0):
        L_active_sweep_um = np.linspace(40, 840, 41)
        J_values_kA_cm2 = np.array([3.0, 4.0, 5.0, 6.0, 7.0])
        target_Pout_mW = 10**(target_Pout_dBm / 10.0)

        results = {J_val: {'L_active': [], 'wpe': [], 'gain': [], 'pin': []} for J_val in J_values_kA_cm2}

        for J_val in J_values_kA_cm2:
            for L_val in L_active_sweep_um:
                temp_soa = EuropaSOA(L_active_um=L_val, W_um=w_um, verbose=False, v_turn_on_delta=v_delta, rs_ohm_delta=rs_delta, g_pk_db_delta=gpk_delta)
                I_mA = temp_soa.calculate_current_mA_from_J(J_val)
                P_in_req = temp_soa.find_Pin_for_target_Pout(target_Pout_mW, I_mA, lambda_nm, T_C)

                if P_in_req is not None:
                    wpe = temp_soa.calculate_wpe(I_mA, lambda_nm, T_C, P_in_req)

                    if P_in_req > 1e-9:
                        gain_db = 10 * math.log10(target_Pout_mW / P_in_req)
                        pin_dbm = 10 * math.log10(P_in_req)
                    else:
                        gain_db, pin_dbm = float('nan'), float('nan')

                    results[J_val]['L_active'].append(L_val)
                    results[J_val]['wpe'].append(wpe)
                    results[J_val]['gain'].append(gain_db)
                    results[J_val]['pin'].append(pin_dbm)
        return results

    def plot_performance_vs_wavelength(self):
        validated_data = self.validate_inputs()
        if validated_data is None: return

        self._capture_last_inputs()

        T_C, w_um, lambda_nm_list, target_Pout_dBm_nominal, target_Pout_dBm_3s, j_nominal, j_3sigma, l_active = validated_data

        plot_window = tk.Toplevel(self)
        plot_window.title("SOA Performance vs. Wavelength")

        lambda_sweep_nm = np.linspace(min(lambda_nm_list), max(lambda_nm_list), 41)

        fig, axes = plt.subplots(4, 1, figsize=(10, 18), sharex=True)
        fig.suptitle(f'SOA Performance vs. Wavelength\n(W={w_um}µm, L_active={l_active:.0f}µm, T={T_C:.0f}°C)', fontsize=16)

        if self.nominal_var.get():
            plot_data = self.calculate_vs_wavelength_data(l_active, w_um, T_C, j_nominal, target_Pout_dBm_nominal, lambda_sweep_nm)
            axes[0].plot(plot_data['lambda'], plot_data['wpe'], marker='o', linestyle='-', label=f'Nominal (J={j_nominal:.1f}, Pout={target_Pout_dBm_nominal:.1f}dBm)')
            axes[1].plot(plot_data['lambda'], plot_data['gain'], marker='o', linestyle='-', label=f'Nominal (J={j_nominal:.1f}, Pout={target_Pout_dBm_nominal:.1f}dBm)')
            axes[2].plot(plot_data['lambda'], plot_data['pin'], marker='o', linestyle='-', label=f'Nominal (J={j_nominal:.1f}, Pout={target_Pout_dBm_nominal:.1f}dBm)')
            axes[3].plot(plot_data['lambda'], plot_data['psat'], marker='o', linestyle='-', label=f'Nominal (J={j_nominal:.1f})')

        if self.sigma_var.get():
            plot_data_3s = self.calculate_vs_wavelength_data(l_active, w_um, T_C, j_3sigma, target_Pout_dBm_3s, lambda_sweep_nm, g_pk_delta=0.5)
            axes[0].plot(plot_data_3s['lambda'], plot_data_3s['wpe'], marker='x', linestyle='--', label=f'3σ (J={j_3sigma:.1f}, Pout={target_Pout_dBm_3s:.1f}dBm)')
            axes[1].plot(plot_data_3s['lambda'], plot_data_3s['gain'], marker='x', linestyle='--', label=f'3σ (J={j_3sigma:.1f}, Pout={target_Pout_dBm_3s:.1f}dBm)')
            axes[2].plot(plot_data_3s['lambda'], plot_data_3s['pin'], marker='x', linestyle='--', label=f'3σ (J={j_3sigma:.1f}, Pout={target_Pout_dBm_3s:.1f}dBm)')
            axes[3].plot(plot_data_3s['lambda'], plot_data_3s['psat'], marker='x', linestyle='--', label=f'3σ (J={j_3sigma:.1f})')

        axes[0].set_ylabel('WPE (%)'); axes[0].grid(True); axes[0].legend()
        axes[1].set_ylabel('SOA Gain (dB)'); axes[1].grid(True); axes[1].legend()
        axes[2].set_ylabel('Required P_in (dBm)'); axes[2].grid(True); axes[2].legend()
        axes[3].set_ylabel('Saturation Power (dBm)'); axes[3].set_xlabel('Wavelength (nm)'); axes[3].grid(True); axes[3].legend()

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        self.embed_plot(fig, plot_window)

    def calculate_vs_wavelength_data(self, l_active, w_um, T_C, J_val, target_Pout_dBm, lambda_sweep, g_pk_delta=0.0):
        target_Pout_mW = 10**(target_Pout_dBm / 10.0)
        results = {'lambda': [], 'wpe': [], 'gain': [], 'pin': [], 'psat': []}

        soa_inst = EuropaSOA(L_active_um=l_active, W_um=w_um, verbose=False, g_pk_db_delta=g_pk_delta)
        I_mA = soa_inst.calculate_current_mA_from_J(J_val)

        for lambda_nm in lambda_sweep:
            P_in_req = soa_inst.find_Pin_for_target_Pout(target_Pout_mW, I_mA, lambda_nm, T_C)
            P_os_dBm = soa_inst.get_output_saturation_power_dBm(lambda_nm, J_val, T_C)

            if P_in_req is not None:
                wpe = soa_inst.calculate_wpe(I_mA, lambda_nm, T_C, P_in_req)
                if P_in_req > 1e-9:
                    gain_db = 10 * math.log10(target_Pout_mW / P_in_req)
                    pin_dbm = 10 * math.log10(P_in_req)
                else:
                    gain_db, pin_dbm = float('nan'), float('nan')

                results['lambda'].append(lambda_nm)
                results['wpe'].append(wpe)
                results['gain'].append(gain_db)
                results['pin'].append(pin_dbm)
                results['psat'].append(P_os_dBm)
        return results

    def embed_plot(self, fig, window):
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    app = Guide3GUI()
    app.mainloop()
