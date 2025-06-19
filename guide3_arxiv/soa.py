# Import necessary libraries
import math
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt # Replaced with plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.optimize import brentq # For root finding

# For Plotly to work in some environments like classic Jupyter Notebook, you might need:
# from plotly.offline import init_notebook_mode, iplot
# init_notebook_mode(connected=True)

# --- SOA class definition (Updated with g0 extrapolation and WPE method) ---
class SOA:
    """
    Represents a Semiconductor Optical Amplifier (SOA) based on the OpenLight PIC Application Note.
    Includes optical models (Gain, Psat, NF), an analytical I-V model, and WPE calculation.
    Unsaturated gain (g0) is linearly extrapolated for L_active_um > 440um up to 900um.
    Series resistance (Rs) uses its analytical formula; warnings are issued if Lt is outside Rs model validation.
    """
    def __init__(self, L_active_um: float, W_um: float = 2.0):
        self.L_active_um_orig = L_active_um # Store original for reference
        self.L_active_um = L_active_um 
        self.W_um = W_um
        self.L_tapers_total_um = 460.0
        self.V_turn_on = 1.05

        # --- Validation warnings ---
        if not (40 <= self.L_active_um_orig <= 440):
            if 440 < self.L_active_um_orig <= 900:
                print(f"Info: L_active_um ({self.L_active_um_orig} um) is > 440um. "
                      "Unsaturated gain (g0) will be linearly extrapolated based on model behavior at 430um and 440um, "
                      f"using L_eff={min(self.L_active_um_orig, 900.0)}um in extrapolation formula.")
            elif self.L_active_um_orig > 900:
                print(f"Warning: L_active_um ({self.L_active_um_orig} um) is > 900um. "
                      "Unsaturated gain (g0) will be linearly extrapolated using L_eff=900um as the cap in extrapolation formula. "
                      "This is significantly beyond model validation for optical parameters.")
            else: # L_active_um_orig < 40
                 print(f"Warning: L_active_um ({self.L_active_um_orig} um) is < 40um. "
                       "Optical model results are outside core validation range [40, 440]um and may be unreliable.")
        
        calculated_Lt_um_for_Rs_warning = self.L_active_um_orig + self.L_tapers_total_um
        if not (2.0 <= W_um <= 2.7):
             print(f"Warning (Rs Model): W_um ({W_um} um) is outside the Rs model validation range [2, 2.7] um. "
                   "The Rs formula (Eq.17) will be applied, but results may be less accurate.")
        
        min_Lt_Rs_valid = 500.0
        max_Lt_Rs_valid = 1100.0
        if not (min_Lt_Rs_valid <= calculated_Lt_um_for_Rs_warning <= max_Lt_Rs_valid):
             corresponding_Lactive_min_Rs = min_Lt_Rs_valid - self.L_tapers_total_um
             corresponding_Lactive_max_Rs = max_Lt_Rs_valid - self.L_tapers_total_um
             warning_message = (
                f"Warning (Rs Model): Lt_um ({calculated_Lt_um_for_Rs_warning:.1f} um, from L_active={self.L_active_um_orig:.1f}um) "
                f"is outside the Rs model validation range for Lt [{min_Lt_Rs_valid:.1f}, {max_Lt_Rs_valid:.1f}] um "
                f"(corresponding to L_active [{max(0,corresponding_Lactive_min_Rs):.1f}, {corresponding_Lactive_max_Rs:.1f}] um). "
                "The Rs formula (Eq.17) will be applied using the calculated Lt, but results may be less accurate."
            )
             print(warning_message)


    def _calculate_Lt_um(self) -> float:
        """Calculates total length Lt = L_active + L_tapers_total, using current self.L_active_um."""
        return self.L_active_um + self.L_tapers_total_um

    def calculate_series_resistance_ohm(self) -> float:
        """
        Calculates series resistance (Rs) in Ohms using Eq.17 from APP-002012 Rev 3.1.
        Uses the original L_active_um_orig for Lt calculation in Rs, as Rs is a device property.
        """
        Lt_um_for_Rs = self.L_active_um_orig + self.L_tapers_total_um 
        
        if self.W_um <= 1e-9 or Lt_um_for_Rs <= 1e-9: 
            return float('inf') 

        Rs_ohm = (4.34 / self.W_um) + (2151 / Lt_um_for_Rs) - 0.992
        return Rs_ohm if Rs_ohm > 0 else 1e-3 

    def get_operating_voltage(self, I_mA: float) -> float:
        """Calculates operating voltage V using Eq.16: V = V_turn-on + I*Rs."""
        Rs_ohm = self.calculate_series_resistance_ohm() 
        I_Amps = I_mA * 1e-3 
        voltage = self.V_turn_on + (I_Amps * Rs_ohm)
        return voltage

    def calculate_current_density_kA_cm2(self, I_mA: float) -> float:
        """
        Calculates current density J = I / (W * Lt) in kA/cm^2.
        Uses self.L_active_um, which should be set to self.L_active_um_orig before calling this
        if J is needed for the device's actual operating point for optical models that depend on L_active_um_orig.
        """
        Lt_um = self._calculate_Lt_um() # Uses current self.L_active_um
        if self.W_um <= 1e-9 or Lt_um <= 1e-9: 
            return 0.0
        J_kA_cm2 = (I_mA * 100.0) / (self.W_um * Lt_um)
        return J_kA_cm2
        
    def calculate_current_mA_from_J(self, J_kA_cm2: float) -> float:
        """Calculates drive current I_mA from current density J using L_active_um_orig."""
        Lt_um = self.L_active_um_orig + self.L_tapers_total_um 
        if self.W_um <= 1e-9 or Lt_um <= 1e-9:
            return 0.0
        I_mA = J_kA_cm2 * self.W_um * Lt_um / 100.0
        return I_mA


    def _get_g_pk_dB(self, T_C: float, J_kA_cm2: float) -> float:
        """Internal: uses current self.L_active_um for L in RSM."""
        L_for_RSM = self.L_active_um 
        if J_kA_cm2 <= 1e-9: return -float('inf') 
        Ln_J = math.log(J_kA_cm2) 
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        g_pk = (4.678 - 0.0729 * T_C + 10.098 * Ln_J - 0.001380 * L_plus_460_for_RSM
                - 0.00024 * (T_C - 60)**2 - 0.0081 * Ln_J * (T_C - 60) - 2.158 * Ln_J**2
                - 0.0001589 * (T_C - 60) * (L_for_RSM - 240) + 0.02311 * Ln_J * (L_for_RSM - 240)
                - 0.000001886 * (T_C - 60)**2 * (L_for_RSM - 240)
                - 0.00002088 * Ln_J * (T_C - 60) * (L_for_RSM - 240)
                - 0.005336 * Ln_J**2 * (L_for_RSM - 240))
        return g_pk

    def _get_lambda_pk_nm(self, T_C: float, J_kA_cm2: float) -> float:
        """Internal: uses current self.L_active_um for L in RSM."""
        L_for_RSM = self.L_active_um
        if J_kA_cm2 <= 1e-9: return float('nan') 
        Ln_J = math.log(J_kA_cm2)
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        lambda_pk = (1273.73 + 0.6817 * T_C - 28.73 * Ln_J + 0.01362 * L_plus_460_for_RSM
                     + 0.004585 * (T_C - 60)**2 - 0.1076 * Ln_J * (T_C - 60) + 8.787 * Ln_J**2
                     + 0.00004185 * (T_C - 60) * (L_for_RSM - 240) - 0.02367 * Ln_J * (L_for_RSM - 240)
                     - 0.0000002230 * (T_C - 60)**2 * (L_for_RSM - 240)
                     + 0.000136 * Ln_J * (T_C - 60) * (L_for_RSM - 240)
                     + 0.004894 * Ln_J**2 * (L_for_RSM - 240))
        return lambda_pk

    def _get_fwhm_nm(self, T_C: float, J_kA_cm2: float) -> float:
        """Internal: uses current self.L_active_um for L in RSM."""
        L_for_RSM = self.L_active_um
        if J_kA_cm2 <= 1e-9: return 1e-9 
        Ln_J = math.log(J_kA_cm2)
        L_plus_460_for_RSM = self.L_active_um + self.L_tapers_total_um
        fwhm = (120.15 - 0.0855 * T_C + 0.3837 * Ln_J - 0.07255 * L_plus_460_for_RSM
                + 0.00007784 * (T_C - 60)**2 + 0.2386 * Ln_J * (T_C - 60) + 2.759 * Ln_J**2
                - 0.0004342 * (T_C - 60) * (L_for_RSM - 240) + 0.003947 * Ln_J * (L_for_RSM - 240)
                + 0.00002085 * (T_C - 60)**2 * (L_for_RSM - 240)
                + 0.00009466 * Ln_J * (T_C - 60) * (L_for_RSM - 240)
                - 0.0007991 * Ln_J**2 * (L_for_RSM - 240))
        return fwhm if fwhm > 1e-9 else 1e-9 

    def _calculate_g0_linear_at_L(self, L_val_um: float, lambda_nm: float, T_C: float, J_kA_cm2: float) -> float:
        """Helper to calculate linear g0 for a specific L_val, T, J, lambda."""
        original_L_temp_store = self.L_active_um 
        self.L_active_um = L_val_um 
        
        g_pk_dB = self._get_g_pk_dB(T_C, J_kA_cm2)
        lambda_pk_nm = self._get_lambda_pk_nm(T_C, J_kA_cm2)
        fwhm_nm = self._get_fwhm_nm(T_C, J_kA_cm2)

        self.L_active_um = original_L_temp_store 

        if math.isnan(lambda_pk_nm) or g_pk_dB == -float('inf') or fwhm_nm <= 1e-9:
            return 0.0
        
        f_val_numerator = fwhm_nm
        f_val_denominator = (lambda_pk_nm - lambda_nm)**2 + (fwhm_nm / 2.0)**2
        
        if f_val_denominator < 1e-12: 
            g0_linear = 10**(g_pk_dB / 10.0) if abs(lambda_nm - lambda_pk_nm) < 1e-9 else 0.0
        else:
            f_val = f_val_numerator / f_val_denominator
            max_f_val = 4.0 / fwhm_nm 
            if abs(max_f_val) < 1e-12: g0_linear = 0.0
            else: g0_linear = (f_val * (10**(0.1 * g_pk_dB))) / max_f_val
        return g0_linear


    def get_unsaturated_gain(self, lambda_nm: float, T_C: float, J_kA_cm2: float, output_in_dB: bool = True) -> float:
        """
        Calculates unsaturated gain (g0). Linearly extrapolates for L_active_um_orig > 440um.
        """
        if J_kA_cm2 <= 1e-9: return -float('inf') if output_in_dB else 0.0

        if 40 <= self.L_active_um_orig <= 440:
            g0_linear = self._calculate_g0_linear_at_L(self.L_active_um_orig, lambda_nm, T_C, J_kA_cm2)
        elif self.L_active_um_orig > 440:
            L_extrap_input = min(self.L_active_um_orig, 900.0)
            L_ref1 = 440.0 
            L_ref2 = 430.0 
            if L_ref2 < 40.0: L_ref2 = 40.0 
            if L_ref1 <= L_ref2 : 
                g0_linear = self._calculate_g0_linear_at_L(L_ref1, lambda_nm, T_C, J_kA_cm2)
            else:
                g0_at_L_ref1_linear = self._calculate_g0_linear_at_L(L_ref1, lambda_nm, T_C, J_kA_cm2)
                g0_at_L_ref2_linear = self._calculate_g0_linear_at_L(L_ref2, lambda_nm, T_C, J_kA_cm2)
                delta_L_refs = L_ref1 - L_ref2
                if abs(delta_L_refs) < 1e-6: slope = 0.0
                else: slope = (g0_at_L_ref1_linear - g0_at_L_ref2_linear) / delta_L_refs
                g0_linear = g0_at_L_ref1_linear + slope * (L_extrap_input - L_ref1)
        else: # self.L_active_um_orig < 40
            g0_linear = self._calculate_g0_linear_at_L(self.L_active_um_orig, lambda_nm, T_C, J_kA_cm2)

        if g0_linear < 0: g0_linear = 0 

        if output_in_dB:
            return 10 * math.log10(g0_linear) if g0_linear > 1e-9 else -float('inf')
        else:
            return g0_linear

    def get_output_saturation_power_dBm(self, lambda_nm: float, J_kA_cm2: float, T_C: float) -> float:
        return (-74.08 + 0.06226 * lambda_nm - 0.008877 * T_C + 0.994 * J_kA_cm2 
                - 0.08721 * (J_kA_cm2 - 4.571)**2 + 0.01752 * (lambda_nm - 1310.8)**2
                - 0.00002341 * (T_C - 60.07)**2 - 0.001266 * (lambda_nm - 1310.8) * (T_C - 60.07)
                - 0.001763 * (T_C - 60.07) * (J_kA_cm2 - 4.571)
                - 0.008584 * (lambda_nm - 1310.8) * (J_kA_cm2 - 4.571))

    def _newton_iteration_for_gain(self, P_os_mW: float, g0_linear: float, P_in_mW: float) -> float:
        epsilon_1, epsilon_2, max_iter = 1e-5, 1e-4, 100
        if g0_linear <= 2.000001: return g0_linear
        denominator_Ps_calc = g0_linear * math.log(2.0)
        if abs(denominator_Ps_calc) < 1e-12: return g0_linear 
        P_s_mW = P_os_mW * (g0_linear - 2.0) / denominator_Ps_calc
        if P_s_mW <= 1e-12: return 0.0 if P_in_mW > 1e-9 else g0_linear
        x = g0_linear * 0.95 if P_in_mW > 1e-9 else g0_linear 
        x = max(x, 1e-9) 
        for _i in range(max_iter):
            exp_arg = (1.0 - x) * P_in_mW / P_s_mW
            try:
                if exp_arg > 700: exp_val = float('inf') 
                elif exp_arg < -700: exp_val = 0.0
                else: exp_val = math.exp(exp_arg)
            except OverflowError: exp_val = float('inf') 
            f_x = x - g0_linear * exp_val
            f_prime_coeff = g0_linear * (P_in_mW / P_s_mW) 
            f_prime_x = 1.0 + f_prime_coeff * exp_val
            if abs(f_prime_x) < 1e-9: break 
            x_next = x - f_x / f_prime_x
            if x_next < -0.1 * g0_linear or x_next > (1.5 * g0_linear +1) : break
            if x_next < 0: x_next = 1e-9 
            c1, c2 = abs(f_x), abs(x_next - x)
            x = x_next
            if c1 < epsilon_1 and c2 < epsilon_2: return max(0.0, x) 
        return max(0.0, x) 

    def get_saturated_gain(self, lambda_nm: float, T_C: float, J_kA_cm2: float, P_in_mW: float, output_in_dB: bool = True) -> float:
        if P_in_mW < -1e-12: raise ValueError("Input power (P_in_mW) cannot be negative.")
        if P_in_mW < 1e-9 : P_in_mW = 0.0 
        g0_linear = self.get_unsaturated_gain(lambda_nm, T_C, J_kA_cm2, output_in_dB=False)
        if g0_linear <= 1e-9 or P_in_mW == 0.0: g_saturated_linear = g0_linear
        else:
            P_os_dBm = self.get_output_saturation_power_dBm(lambda_nm, J_kA_cm2, T_C)
            P_os_mW = 10**(P_os_dBm / 10.0)
            g_saturated_linear = self._newton_iteration_for_gain(P_os_mW, g0_linear, P_in_mW)
        if output_in_dB:
            return 10 * math.log10(g_saturated_linear) if g_saturated_linear > 1e-9 else -float('inf')
        else:
            return g_saturated_linear

    def get_noise_figure_dB(self, lambda_nm: float, J_kA_cm2: float, T_C: float) -> float:
        if J_kA_cm2 <= 1e-9: return float('nan') 
        Ln_J = math.log(J_kA_cm2) 
        lambda_minus_1306_38 = lambda_nm - 1306.38
        T_minus_60 = T_C - 60.0
        NF_dB = (131.58 - 0.09959 * lambda_nm + 0.08972 * T_C - 5.0895 * Ln_J
                 + 2.7334 * Ln_J**2 + 0.0009195 * lambda_minus_1306_38**2
                 + 0.0007484 * T_minus_60**2 - 0.001299 * lambda_minus_1306_38 * T_minus_60
                 - 0.07995 * T_minus_60 * Ln_J + 0.103 * lambda_minus_1306_38 * Ln_J
                 + 0.0005740 * lambda_minus_1306_38 * T_minus_60 * Ln_J
                 + 0.0197 * (Ln_J**2) * T_minus_60 - 0.02785 * (Ln_J**2) * lambda_minus_1306_38
                 - 0.0003141 * (T_minus_60**2) * Ln_J
                 - 0.0001095 * (T_minus_60**2) * lambda_minus_1306_38
                 - 0.0002678 * (lambda_minus_1306_38**2) * Ln_J
                 + 0.000003281 * (lambda_minus_1306_38**2) * T_minus_60
                 - 0.4606 * (Ln_J**3) - 0.000002634 * (lambda_minus_1306_38**3) )
        return NF_dB

    def calculate_wpe(self, I_mA: float, 
                      lambda_nm: float, T_C: float, P_in_mW: float) -> float:
        """
        Calculates WPE using the SOA's analytical I-V model.
        """
        if I_mA <= 1e-9: return 0.0
        operating_voltage_V = self.get_operating_voltage(I_mA) 
        if operating_voltage_V <= 1e-9: return 0.0
        
        original_L_temp_calc_J = self.L_active_um
        self.L_active_um = self.L_active_um_orig 
        J_op_kA_cm2 = self.calculate_current_density_kA_cm2(I_mA)
        self.L_active_um = original_L_temp_calc_J 

        g_linear = self.get_saturated_gain(lambda_nm, T_C, J_op_kA_cm2, P_in_mW, output_in_dB=False)
        P_out_mW = g_linear * P_in_mW
        delta_P_optical_mW = P_out_mW - P_in_mW
        P_electrical_mW = I_mA * operating_voltage_V
        if P_electrical_mW <= 1e-9: return 0.0
        if delta_P_optical_mW < 0 : return 0.0 
        wpe_ratio = delta_P_optical_mW / P_electrical_mW
        return wpe_ratio * 100.0

    def plot_gain_and_wpe_vs_pout(self, lambda_nm: float, T_C: float, J_values_kA_cm2=None):
        """
        Plots Saturated Gain vs. Output Power and WPE vs. Output Power for the SOA instance using Plotly.
        """
        print(f"\n--- Generating Saturated Gain & WPE vs. Pout Plots (Plotly) ---")
        print(f"SOA Parameters: L_active = {self.L_active_um_orig} um, W = {self.W_um} um")
        print(f"Operating Conditions: Lambda = {lambda_nm} nm, T = {T_C} C")

        P_in_mW_sweep = np.logspace(-3, 1.3, 61) 
        P_in_dBm_sweep = 10 * np.log10(P_in_mW_sweep)

        if J_values_kA_cm2 is None:
            J_values_kA_cm2 = np.linspace(3, 7, 5) 

        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=(f'Saturated Gain vs. $P_{{out}}$', f'WPE vs. $P_{{out}}$'),
                            horizontal_spacing=0.1) 
        
        display_Lt_um = self.L_active_um_orig + self.L_tapers_total_um
        fig.update_layout(
            title_text=f'Performance for $L_{{active}}={self.L_active_um_orig} \\mu m, W={self.W_um} \\mu m, L_t={display_Lt_um:.0f} \\mu m, \\lambda={lambda_nm}nm, T={T_C}^\\circ C$',
            title_x=0.5, height=500, width=1000, 
            legend_title_text='J (kA/cm²)'
        )

        for J_kA_cm2_val in J_values_kA_cm2:
            P_out_dBm_list = []
            wpe_ratio_list = []
            saturated_gain_dB_list = []
            I_mA_val = self.calculate_current_mA_from_J(J_kA_cm2_val) 

            for idx, P_in_mW_val in enumerate(P_in_mW_sweep):
                gain_dB_val = self.get_saturated_gain(lambda_nm=lambda_nm, T_C=T_C, J_kA_cm2=J_kA_cm2_val, 
                                                      P_in_mW=P_in_mW_val, output_in_dB=True)
                if gain_dB_val == -float('inf') or P_in_dBm_sweep[idx] == -float('inf'):
                    P_out_dBm_val = -float('inf') 
                else: P_out_dBm_val = P_in_dBm_sweep[idx] + gain_dB_val
                P_out_dBm_list.append(P_out_dBm_val)
                saturated_gain_dB_list.append(gain_dB_val)
                wpe_val = self.calculate_wpe(I_mA=I_mA_val, lambda_nm=lambda_nm, T_C=T_C, P_in_mW=P_in_mW_val)
                wpe_ratio_list.append(wpe_val)

            valid_indices = [k for k, v_pout in enumerate(P_out_dBm_list) if v_pout > -100]
            if valid_indices:
                P_out_dBm_plot = np.array(P_out_dBm_list)[valid_indices]
                gain_plot = np.array(saturated_gain_dB_list)[valid_indices]
                wpe_plot = np.array(wpe_ratio_list)[valid_indices]
                
                fig.add_trace(go.Scatter(x=P_out_dBm_plot, y=gain_plot, mode='lines+markers', 
                                         name=f'{J_kA_cm2_val:.1f}', legendgroup=f'{J_kA_cm2_val:.1f}'), 
                              row=1, col=1)
                fig.add_trace(go.Scatter(x=P_out_dBm_plot, y=wpe_plot, mode='lines+markers', 
                                         name=f'{J_kA_cm2_val:.1f}', legendgroup=f'{J_kA_cm2_val:.1f}', showlegend=False), 
                              row=1, col=2)
        
        fig.update_xaxes(title_text='$P_{out}$ [dBm]', range=[-30, 20], row=1, col=1)
        fig.update_yaxes(title_text='Saturated Gain [dB]', range=[0, 25], row=1, col=1) 
        
        fig.update_xaxes(title_text='$P_{out}$ [dBm]', range=[-30, 20], row=1, col=2)
        fig.update_yaxes(title_text='WPE (%)', range=[0, 15], row=1, col=2) 
        
        fig.update_layout(legend_tracegroupgap = 5) 
        fig.show()

    def plot_wpe_vs_Lactive_for_fixed_Pout(self, T_C: float, target_Pout_dBm: float,
                                           L_active_sweep_um=None, J_values_kA_cm2=None):
        """
        Plots WPE vs. L_active_um for a fixed target_Pout_dBm over multiple lambdas (1300, 1310, 1320 nm)
        as subplots, with curves for different J values, using Plotly.
        """
        lambda_nm_list = [1300.0, 1310.0, 1320.0]
        print(f"\n--- Generating WPE vs. L_active for Fixed Pout ({target_Pout_dBm} dBm) across Lambdas (Plotly) ---")
        print(f"Operating Temperature: T = {T_C} C")

        if L_active_sweep_um is None:
            L_active_sweep_um = np.linspace(40, 840, 21) 
        if J_values_kA_cm2 is None:
            J_values_kA_cm2 = np.array([3.0, 4.0, 5.0, 6.0, 7.0]) 
        
        target_Pout_mW = 10**(target_Pout_dBm / 10.0)

        fig = make_subplots(rows=1, cols=len(lambda_nm_list), 
                            subplot_titles=[f"λ = {lam_val:.0f} nm" for lam_val in lambda_nm_list],
                            shared_yaxes=True, shared_xaxes=True,
                            horizontal_spacing=0.05)
        
        fig.update_layout(
            title_text=f'WPE vs. L_active for P_out = {target_Pout_dBm} dBm (T={T_C}C, W={self.W_um} um)',
            title_x=0.5, height=500, width=1200, # Adjusted width for 3 subplots
            legend_title_text='J (kA/cm²)'
        )
        
        show_legend_for_subplot = True # Show legend only for the first subplot group

        for col_idx, lambda_nm_val in enumerate(lambda_nm_list):
            for J_val in J_values_kA_cm2:
                wpe_values_for_J = []
                L_active_values_plotted = []
                
                for L_val in L_active_sweep_um:
                    temp_soa = SOA(L_active_um=L_val, W_um=self.W_um) 
                    I_mA_for_J = temp_soa.calculate_current_mA_from_J(J_val) 
                    
                    P_in_mW_req = temp_soa.find_Pin_for_target_Pout(target_Pout_mW, 
                                                                    I_mA_for_J, lambda_nm_val, T_C)
                    
                    if P_in_mW_req is not None:
                        current_wpe = temp_soa.calculate_wpe(I_mA_for_J, lambda_nm_val, T_C, P_in_mW_req)
                        wpe_values_for_J.append(current_wpe)
                        L_active_values_plotted.append(L_val)
                
                if L_active_values_plotted: 
                    fig.add_trace(go.Scatter(x=L_active_values_plotted, y=wpe_values_for_J,
                                             mode='lines+markers', name=f'{J_val:.1f}', 
                                             legendgroup=f'J{J_val:.1f}', # Group traces by J for legend
                                             showlegend=show_legend_for_subplot), 
                                  row=1, col=col_idx+1)
            
            fig.update_xaxes(title_text='L_active [µm]', row=1, col=col_idx+1)
            if col_idx == 0: # Only for the first subplot
                 fig.update_yaxes(title_text='WPE (%)', row=1, col=col_idx+1)
            
            show_legend_for_subplot = False # Show legend items only once

        fig.update_yaxes(rangemode='tozero') # Ensures y-axis starts at 0 for all subplots
        fig.update_xaxes(range=[min(L_active_sweep_um)-10 if L_active_sweep_um.size >0 else 0, 
                                 max(L_active_sweep_um)+10 if L_active_sweep_um.size >0 else 900])
        fig.show()
        
    def plot_gain_pin_vs_Lactive_fixed_Pout(self, target_Pout_dBm: float, T_C: float,
                                            L_active_sweep_um=None, J_values_kA_cm2=None):
        """
        Plots:
        Fig 1) Saturated Gain vs. L_active_um for different J values, in 3 subplots for lambdas.
        Fig 2) P_in_dBm vs. L_active_um for different J values, in 3 subplots for lambdas.
        Inputs: target_Pout_dBm, T_C
        """
        lambda_nm_list = [1300.0, 1310.0, 1320.0]
        print(f"\n--- Generating Gain & Pin vs. L_active for Fixed Pout ({target_Pout_dBm} dBm) across Lambdas (Plotly) ---")
        print(f"Operating Temperature: T = {T_C}°C")

        if L_active_sweep_um is None:
            L_active_sweep_um = np.linspace(40, 840, 21) 
        if J_values_kA_cm2 is None:
            J_values_kA_cm2 = np.array([3.0, 4.0, 5.0, 6.0, 7.0]) 
        
        target_Pout_mW = 10**(target_Pout_dBm / 10.0)

        # Figure 1: Saturated Gain vs L_active
        fig1 = make_subplots(rows=1, cols=len(lambda_nm_list), 
                             subplot_titles=[f"λ = {lam_val:.0f} nm" for lam_val in lambda_nm_list],
                             shared_yaxes=True, shared_xaxes=True, horizontal_spacing=0.05)
        fig1.update_layout(
            title_text=f'Saturated Gain vs. L_active for P_out = {target_Pout_dBm} dBm (T={T_C}C, W={self.W_um} um)',
            title_x=0.5, height=500, width=1200, legend_title_text='J (kA/cm²)'
        )
        
        # Figure 2: P_in_dBm vs L_active
        fig2 = make_subplots(rows=1, cols=len(lambda_nm_list), 
                             subplot_titles=[f"λ = {lam_val:.0f} nm" for lam_val in lambda_nm_list],
                             shared_yaxes=True, shared_xaxes=True, horizontal_spacing=0.05)
        fig2.update_layout(
            title_text=f'P_in vs. L_active for P_out = {target_Pout_dBm} dBm (T={T_C} C, W={self.W_um} um)',
            title_x=0.5, height=500, width=1200, legend_title_text='J (kA/cm²)'
        )

        show_legend_fig1 = True
        show_legend_fig2 = True

        for col_idx, lambda_nm_val in enumerate(lambda_nm_list):
            for J_val in J_values_kA_cm2:
                gain_values_for_J = []
                pin_dbm_values_for_J = []
                L_active_values_plotted = []
                
                for L_val in L_active_sweep_um:
                    temp_soa = SOA(L_active_um=L_val, W_um=self.W_um) 
                    I_mA_for_J = temp_soa.calculate_current_mA_from_J(J_val)
                    
                    P_in_mW_req = temp_soa.find_Pin_for_target_Pout(target_Pout_mW, 
                                                                    I_mA_for_J, lambda_nm_val, T_C)
                    
                    if P_in_mW_req is not None:
                        # Calculate actual saturated gain at this Pin and Pout
                        # P_out = Gain_lin * P_in => Gain_lin = P_out / P_in
                        if P_in_mW_req > 1e-9: # Avoid division by zero if Pin is effectively zero
                            gain_linear = target_Pout_mW / P_in_mW_req
                            gain_dB = 10 * math.log10(gain_linear) if gain_linear > 1e-9 else -float('inf')
                        elif target_Pout_mW <= 1e-9 : # If target Pout is zero, gain is not well-defined or could be considered 0dB if Pin is also 0
                            gain_dB = 0 
                        else: # Target Pout > 0 but Pin is zero, implies infinite gain, practically an error.
                            gain_dB = float('inf') # Or np.nan

                        gain_values_for_J.append(gain_dB)
                        pin_dbm_values_for_J.append(10 * math.log10(P_in_mW_req) if P_in_mW_req > 1e-9 else -float('inf'))
                        L_active_values_plotted.append(L_val)
            
                if L_active_values_plotted: 
                    # Fig 1: Gain
                    fig1.add_trace(go.Scatter(x=L_active_values_plotted, y=gain_values_for_J,
                                             mode='lines+markers', name=f'{J_val:.1f}', 
                                             legendgroup=f'J{J_val:.1f}', 
                                             showlegend=show_legend_fig1), 
                                  row=1, col=col_idx+1)
                    # Fig 2: Pin
                    fig2.add_trace(go.Scatter(x=L_active_values_plotted, y=pin_dbm_values_for_J,
                                             mode='lines+markers', name=f'{J_val:.1f}', 
                                             legendgroup=f'J{J_val:.1f}', 
                                             showlegend=show_legend_fig2), 
                                  row=1, col=col_idx+1)
            
            fig1.update_xaxes(title_text='L_active [µm]', row=1, col=col_idx+1)
            fig2.update_xaxes(title_text='L_active [µm]', row=1, col=col_idx+1)
            if col_idx == 0: 
                 fig1.update_yaxes(title_text='Saturated Gain [dB]', row=1, col=col_idx+1)
                 fig2.update_yaxes(title_text='P_in [dBm]', row=1, col=col_idx+1)
            
            show_legend_fig1 = False 
            show_legend_fig2 = False

        fig1.update_yaxes(rangemode='tozero') 
        fig1.update_xaxes(range=[min(L_active_sweep_um)-10 if L_active_sweep_um.size >0 else 0, 
                                 max(L_active_sweep_um)+10 if L_active_sweep_um.size >0 else 900])
        fig1.show()

        # fig2.update_yaxes(rangemode='normal') # P_in can be negative dBm
        fig2.update_xaxes(range=[min(L_active_sweep_um)-10 if L_active_sweep_um.size >0 else 0, 
                                 max(L_active_sweep_um)+10 if L_active_sweep_um.size >0 else 900])
        fig2.show()


    def find_Pin_for_target_Pout(self, target_Pout_mW: float, 
                                 I_mA: float, lambda_nm: float, T_C: float) -> float | None:
        """
        Finds Pin_mW for target_Pout_mW for THIS SOA instance.
        """
        original_L_temp = self.L_active_um
        self.L_active_um = self.L_active_um_orig 
        J_kA_cm2 = self.calculate_current_density_kA_cm2(I_mA)
        self.L_active_um = original_L_temp 
        
        if J_kA_cm2 <= 1e-9 and I_mA > 1e-9 : return None 
        if I_mA <= 1e-9 and target_Pout_mW > 1e-9 : return None

        def objective_func(Pin_mW_local: float) -> float:
            if Pin_mW_local <= 0: return target_Pout_mW * 100 + 1 
            gain_linear = self.get_saturated_gain(lambda_nm, T_C, J_kA_cm2, Pin_mW_local, output_in_dB=False)
            Pout_calculated_mW = gain_linear * Pin_mW_local
            return Pout_calculated_mW - target_Pout_mW

        if target_Pout_mW <= 1e-9:
            g_unsat_check = self.get_unsaturated_gain(lambda_nm, T_C, J_kA_cm2, output_in_dB=False)
            if g_unsat_check > 1e-9: return 0.0 
            else: return 0.0

        Pin_lower_bound_mW = 1e-7 
        Pin_upper_bound_mW = max(target_Pout_mW * 10, Pin_lower_bound_mW * 100) 
        if Pin_upper_bound_mW <= Pin_lower_bound_mW: Pin_upper_bound_mW = Pin_lower_bound_mW * 1.1

        try:
            obj_at_lower = objective_func(Pin_lower_bound_mW)
            obj_at_upper = objective_func(Pin_upper_bound_mW)
            if obj_at_lower > 0 and obj_at_upper > 0:
                 if abs(objective_func(0)) < 1e-6 : return 0.0
                 return None
            if obj_at_lower * obj_at_upper > 0 : return None
            Pin_solution_mW = brentq(objective_func, Pin_lower_bound_mW, Pin_upper_bound_mW, xtol=1e-7, rtol=1e-7)
            if Pin_solution_mW >= 0:
                final_pout_check = objective_func(Pin_solution_mW) + target_Pout_mW
                if abs(final_pout_check - target_Pout_mW) < 1e-5 * target_Pout_mW + 1e-7 :
                    return Pin_solution_mW
                else: return None
            else: return None
        except (ValueError, RuntimeError): return None
        except Exception: return None
# --- End of SOA class definition ---